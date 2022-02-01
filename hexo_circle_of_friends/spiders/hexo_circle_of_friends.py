# -*- coding:utf-8 -*-

import time
import scrapy
import queue
import feedparser
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
        while not self.friend_poor.empty():
            friend = self.friend_poor.get()
            self.friend_list.put(friend)
            friend["link"] += "/" if not friend["link"].endswith("/") else ""
            yield Request(friend["feed"], callback=self.post_feed_parse, meta={"friend": friend}, dont_filter=True, errback=self.errback_handler)
            
    def post_feed_parse(self, response):
        # print("post_feed_parse---------->" + response.url)
        friend = response.meta.get("friend")
        xml_text = feedparser.parse(response.text)
        feedlink = xml_text.feed.link
        entries = xml_text.entries
        rule = xml_text.version
        l = len(entries) if len(entries) < 5 else 5
        for i in range(l):
            entry = entries[i]
            # 文章标题
            entrytitle = entry.title
            # 文章链接
            entrylink = entry.link
            if not entrylink.startswith('http'): entrylink = feedlink + entrylink # 相对链接校验
            # 创建时间
            try: entrycreated_parsed = entry.created_parsed
            except: 
                try: entrycreated_parsed = entry.published_parsed
                except: entrycreated_parsed = entry.updated_parsed
            entrycreated = "{:4d}-{:02d}-{:02d}".format(entrycreated_parsed[0], entrycreated_parsed[1], entrycreated_parsed[2])
            # 更新时间
            try: entryupdated_parsed = entry.updated_parsed
            except: 
                try: entryupdated_parsed = entry.published_parsed
                except: entryupdated_parsed = entry.created_parsed
            entryupdated = "{:4d}-{:02d}-{:02d}".format(entryupdated_parsed[0], entryupdated_parsed[1], entryupdated_parsed[2])
            
            # 建立文章信息
            post_info = {
                'title': entrytitle,
                'created': entrycreated,
                'updated': entryupdated,
                'link': entrylink,
                'name': friend["name"],
                'avatar': friend["avatar"],
                'rule': rule
            }
            yield post_info

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
