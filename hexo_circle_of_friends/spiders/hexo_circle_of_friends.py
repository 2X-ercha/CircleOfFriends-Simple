# -*- coding:utf-8 -*-

import time
import scrapy
import queue
from scrapy import Request
from hexo_circle_of_friends.utils.regulations import *
import yaml


# from hexo_circle_of_friends import items todo use items
class FriendpageLinkSpider(scrapy.Spider):
    name = 'hexo_circle_of_friends'
    allowed_domains = ['*']
    start_urls = []

    def __init__(self, name=None, **kwargs):
        self.friend_poor = queue.Queue()
        self.friend_list = queue.Queue()

        super().__init__(name, **kwargs)

    def start_requests(self):
        # 从友链配置文件 ./config/link.yml 导入友链列表
        with open("config/link.yml",  "r", encoding="utf-8") as f:
            friends = yaml.load(f.read())
        for friend in friends:
            self.friend_poor.put(friend)
        
        # 请求atom / rss
        rule_mate = {"atom": self.post_atom_parse, "rss": self.post_rss_parse}
        while not self.friend_poor.empty():
            friend = self.friend_poor.get()
            self.friend_list.put(friend)
            friend["link"] += "/" if not friend["link"].endswith("/") else ""
            yield Request(friend["link"] + friend["feed"], callback=rule_mate[friend["rule"]], meta={"friend": friend}, dont_filter=True, errback=self.errback_handler)
            
        # 将获取到的朋友列表传递到管道
        '''
        while not self.friend_list.empty():
            yield self.friend_list.get()
        '''

    def post_atom_parse(self, response):
        # print("post_atom_parse---------->" + response.url)
        friend = response.meta.get("friend")
        sel = scrapy.Selector(text=response.text.replace('<![CDATA[', '').replace(']]>', ''))
        title = sel.css("entry title::text").extract()
        link = sel.css("entry title+link::attr(href)").extract()
        published = sel.css("entry published::text").extract()
        updated = sel.css("entry updated::text").extract()
 
        if len(title) == len(link) == len(published) == len(updated):
            l = len(title) if len(title) < 5 else 5
            try:
                for i in range(l):
                    post_info = {
                        'title': title[i],
                        'created': published[i][:10],
                        'updated': updated[i][:10],
                        'link': link[i],
                        'name': friend["name"],
                        'avatar': friend["avatar"],
                        'rule': "atom"
                    }
                    yield post_info
            except:
                pass

    def post_rss_parse(self, response):
        # print("post_rss_parse---------->" + response.url)
        friend = response.meta.get("friend")
        sel = scrapy.Selector(text=response.text)
        title = sel.css("item title::text").extract()
        link = [comm.split("#")[0] for comm in sel.css("item link+comments::text").extract()]  # 紧跟link后的首个comments
        if len(link) == 0: link = [comm.split("#")[0] for comm in sel.css("item comments::text").extract()]
        pubDate = sel.css("item pubDate::text").extract()
        # print(link)

        if len(title) == len(link) == len(pubDate):
            l = len(title) if len(title) < 5 else 5
            try:
                for i in range(l):
                    m = pubDate[i].split(" ")
                    ts = time.strptime(m[3] + "-" + m[2] + "-" + m[1], "%Y-%b-%d")
                    date = time.strftime("%Y-%m-%d", ts)
                    post_info = {
                        'title': title[i],
                        'created': date,
                        'updated': date,
                        'link': link[i],
                        'name': friend["name"],
                        'avatar': friend["avatar"],
                        'rule': "rss"
                    }
                    yield post_info
            except:
                pass

    def errback_handler(self, error):
        # 错误回调
        # todo error???
        # print("errback_handler---------->")
        # print(error)
        # request = error.request
        # meta = error.request.meta
        pass

    def typecho_errback_handler(self,error):
        yield Request(error.request.url,callback=self.post_atom_parse,dont_filter=True,meta=error.request.meta,errback=self.errback_handler)
