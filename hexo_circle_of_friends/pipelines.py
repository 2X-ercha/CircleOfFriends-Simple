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
        self.nonerror_data = set() # 未失联友链link集合

        self.total_post_num = 0
        self.total_friend_num = 0
        self.err_friend_num = 0

        # 友链去重
        self.friend_set = set()
        with open("./hexo_circle_of_friends/config/link.yml",  "r", encoding="utf-8") as f:
            self.friends = yaml.load(f.read())
        for friend in self.friends:
            if friend["link"] not in self.friend_set:
                self.friend_info.append(friend)
    
    def open_spider(self, spider):
        '''
        leancloud.init(sys.argv[1], sys.argv[2])
        self.Friendslist = leancloud.Object.extend('friend_list')
        self.Friendspoor = leancloud.Object.extend('friend_poor')
        self.query_friendslist()
        self.query_friendspoor()
        # 友链清洗
        for query_j in self.query_friend_list:
            delete = self.Friendslist.create_without_data(query_j.get('objectId'))
            delete.destroy()
        '''

        conn = "sqlite:///data.db"
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
        self.query_friendspoor()


    def process_item(self, item, spider):
        self.nonerror_data.add(item["name"])
        # rss创建时间保留
        for query_item in self.query_post_list:
            if query_item.link == item["link"]:
                item["created"] = min(item['created'], query_item.get('created'))
                '''
                delete = self.Friendspoor.create_without_data(query_item.get('objectId'))
                delete.destroy()
                '''
                self.session.query(models.Post).filter_by(id=query_item.id).delete()
                self.session.commit()
        self.friendpoor_push(item)
        return item

    def close_spider(self, spider):
        self.friendlist_push()
        self.outdate_clean(settings.OUTDATE_CLEAN)

        print("----------------------")
        print("友链总数 : %d" % self.total_friend_num)
        print("失联友链数 : %d" % self.err_friend_num)
        print("共 %d 篇文章" % self.total_post_num)
        self.session.close()
        print("done!")


    # 文章数据查询
    def query_friendspoor(self):
        try:
            '''
            query = self.Friendspoor.query
            query.select('title', 'created', 'link', 'updated')
            query.limit(1000)
            self.query_post_list = query.find()
            # print(self.query_post_list)
            '''
            self.query_post_list = self.session.query(models.Post).all()
        except:
            self.query_post_list=[]
    
    '''
    # 友链数据查询
    def query_friendslist(self):
        try:
            query = self.Friendslist.query
            query.select('name', 'link', 'avatar', 'error')
            query.limit(1000)
            self.query_friend_list = query.find()
        except:
            self.query_friend_list=[]
    '''

    # 超时清洗
    def outdate_clean(self,time_limit):
        out_date_post = 0
        for query_i in self.query_post_list:
            updated = query_i.updated
            query_time = datetime.datetime.strptime(updated, "%Y-%m-%d")
            if (datetime.datetime.today() - query_time).days > time_limit:
                '''
                delete = self.Friendspoor.create_without_data(query_i.get('objectId'))
                out_date_post += 1
                delete.destroy()
                '''
                self.session.query(models.Post).filter_by(id=query_i.id).delete()
                out_date_post += 1
                self.session.commit()

    # 友链数据上传
    def friendlist_push(self):
        for item in self.friend_info:
            '''
            friendlist = self.Friendslist()
            friendlist.set('name', item["name"])
            friendlist.set('link', item["link"])
            friendlist.set('avatar', item["avatar"])
            friendlist.set('descr', item["descr"])
            '''
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
        '''
        friendpoor = self.Friendspoor()
        friendpoor.set('title', item['title'])
        friendpoor.set('created', item['created'])
        friendpoor.set('updated', item['updated'])
        friendpoor.set('link', item['link'])
        friendpoor.set('author', item['name'])
        friendpoor.set('avatar', item['avatar'])
        friendpoor.set('rule', item['rule'])
        friendpoor.save()
        '''
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
        print("----------------------")
        print(item["name"])
        print("《{}》\n文章发布时间：{}\t\t采取的爬虫规则为：{}".format(item["title"], item["updated"], item["rule"]))
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
        else:
            self.poor_set.add(link)
            return item