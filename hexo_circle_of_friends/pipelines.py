# -*- coding:utf-8 -*-

import datetime
import re
import yaml
from scrapy.exceptions import DropItem
from hexo_circle_of_friends import settings,models
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker,scoped_session


class HexoCircleOfFriendsPipeline:
    def __init__(self):
        self.friend_info = []
        self.friend_poor = []
        self.nonerror_data = set() # 未失联友链link集合

        self.total_post_num = 0
        self.total_friend_num = 0
        self.err_friend_num = 0
        self.new_post_num = 0
        self.old_post_num = 0
        self.update_post_num = 0

        # 友链去重
        self.friend_set = set()
        # 从友链配置文件 ./config/link.yml 导入友链列表
        with open("./hexo_circle_of_friends/config/link.yml",  "r", encoding="utf-8") as f:
            friends = yaml.load(f.read())
        with open("./hexo_circle_of_friends/config/From_saveweb.yml",  "r", encoding="utf-8") as f:
            From_saveweb = yaml.load(f.read())
        
        self.friends = friends + From_saveweb
        for friend in self.friends:
            if friend["link"] not in self.friend_set:
                self.friend_set.add(friend["link"])
                self.friend_info.append(friend)
    
    def open_spider(self, spider):
        conn = "sqlite:///data.db" + "?check_same_thread=False"
        try:
            self.engine = create_engine(conn,pool_recycle=-1)
        except:
            raise Exception("sqlite连接失败")
        Session = sessionmaker(bind=self.engine)
        self.session = scoped_session(Session)
        # 创建表
        models.Model.metadata.create_all(self.engine)
        # 删除friend表
        self.session.query(models.Friend).delete()
        # 获取post表数据
        self.query_post()

    def process_item(self, item, spider):
        self.nonerror_data.add(item["name"])
        post = self.session.query(models.Post).get(item["link"])
        if post != None:
            if post.updated < item["updated"]:
                post.title = item["title"]
                post.updated = item["updated"]
                self.session.commit()
                self.update_post_num += 1
                # print("[updated] 《{}》已更新".format(item["title"]))
            else:
                self.old_post_num += 1
                # print("[old] 《{}》无变动".format(item["title"]))
            self.total_post_num += 1
        else:
            self.new_post_num += 1
            # print("[new] 新增文章《{}》".format(item["title"]))
            self.friendpoor_push(item)


    def close_spider(self, spider):
        print("----------------------")
        self.friendlist_push()
        print("----------------------")
        
        self.query_post()
        self.outdate_clean(settings.OUTDATE_CLEAN)

        print("----------------------")
        print("友链总数 : %d" % self.total_friend_num)
        print("失联友链数 : %d" % self.err_friend_num)
        print("新增文章数 : %d" % self.new_post_num)
        print("更新文章数 : %d" % self.update_post_num)
        print("本次爬取共获取 %d 篇文章" % self.total_post_num)
        self.session.close()
        print("done!")


    # 文章数据查询
    def query_post(self):
        try:
            self.query_post_list = self.session.query(models.Post).all()
        except:
            self.query_post_list=[]

    # 超时清洗
    def outdate_clean(self,time_limit):
        out_date_post = 0
        l, i = len(self.query_post_list), 0
        for query_i in self.query_post_list:
            updated = query_i.updated
            query_time = datetime.datetime.strptime(updated, "%Y-%m-%d")
            if (datetime.datetime.today() - query_time).days > time_limit:
                self.session.delete(self.session.query(models.Post).get(query_i.link))
                out_date_post += 1
            i += 1
            # print("文章过期清洗进度：{:.3f}%".format( i/l*100 ), end = "\r")
        self.session.commit()
        print("文章过期清洗完成，共清洗{}篇文章".format(out_date_post))

    # 友链数据上传
    def friendlist_push(self):
        for item in self.friend_info:
            friend = models.Friend(
                name = item['name'],
                link = item['link'],
                avatar = item['avatar'],
                descr = item['descr']
            )

            if item['name'] in self.nonerror_data:
                friend.error = False
            else:
                self.err_friend_num += 1
                print("请求失败，请检查链接： %s" % item["feed"])
                friend.error = True
            self.session.add(friend)
            self.session.commit()
            self.total_friend_num+=1

    # 文章数据上传
    def friendpoor_push(self,item):
        post = models.Post(
            title = item['title'],
            created = item['created'],
            updated = item['updated'],
            link = item['link'],
            author = item['name'],
            avatar = item['avatar'],
            rule = item['rule']
        )
        self.session.add(post)
        self.session.commit()
        ## print("----------------------")
        ## print("{}: 《{}》\n文章发布时间：{}\t\t采取的爬虫规则为：{}".format(item["name"], item["title"], item["updated"], item["rule"]))
        self.total_post_num +=1
    



class DuplicatesPipeline:
    def __init__(self):
        self.poor_set = set() # posts filter set 用于对文章数据的去重
    
    def process_item(self, item, spider):
        # 上传前本地审核
        link = item["link"]
        if link in self.poor_set or link=="":
            # 重复数据清洗
            raise DropItem("Duplicate found:%s" % link)
        elif not link.startswith("http"):
            # 链接必须是http开头，不能是相对地址
            raise DropItem("invalid link")
        elif not re.match("^\d+",item["created"]):
            # 时间不是xxxx-xx-xx格式，丢弃
            raise DropItem("invalid time")
        elif not re.match("^\d+",item["updated"]):
            # 时间不是xxxx-xx-xx格式，丢弃
            raise DropItem("invalid time")
        elif (datetime.datetime.today() - datetime.datetime.strptime(item['updated'], "%Y-%m-%d")).days < 0:
            raise DropItem("invalid feature")
        elif (datetime.datetime.today() - datetime.datetime.strptime(item['created'], "%Y-%m-%d")).days < 0:
            raise DropItem("invalid feature")
        else:
            self.poor_set.add(link)
            return item
