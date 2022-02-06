# -*- coding:utf-8 -*-

from fastapi import FastAPI
import uvicorn
import leancloud
import os
import random
import requests
import json

from fastapi.middleware.cors import CORSMiddleware


app = FastAPI()

origins = [
    "*"
]


app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def initleancloud():
    leancloud.init(os.environ["LEANCLOUD_ID"], os.environ["LEANCLOUD_KEY"])

@app.get("/all")
async def all(start: int = 0, end: int = -1, rule: str = "updated"):
    '''返回数据库统计信息和文章信息列表

    :param start: 【可选】文章信息列表从 按rule排序后的顺序 的开始位置，默认为0，超出范围返回{"message": "start error"}

    :param end: 【可选】文章信息列表从 按rule排序后的顺序 的结束位置，默认为-1（即最大），其它非正数返回{"message": "end error"}
    
    :param rule: 【可选】文章排序规则（创建时间/更新时间），默认为updated，参数错误返回{"message": "rule error, please use 'created'/'updated'"}
    '''
    list = ['title','created','updated','link','author','avatar']
    # Verify key
    initleancloud()

    # Declare class
    Friendspoor = leancloud.Object.extend('friend_poor')
    query = Friendspoor.query
    query.descending('created')
    query.limit(1000)

    # Choose class
    query.select('title','created','updated','link','author','avatar','createdAt')

    query_list = query.find()
    Friendlist = leancloud.Object.extend('friend_list')
    query_userinfo = Friendlist.query
    query_userinfo.limit(1000)
    query_userinfo.select('name','link','avatar','error')
    query_list_user = query_userinfo.find()


    # Result to arr
    api_json = {}
    friends_num = len(query_list_user)
    active_num = len(set([item.get('author') for item in query_list]))
    error_num = len([friend for friend in query_list_user if friend.get('error') == 'true'])
    article_num = len(query_list)
    last_updated_time = max([item.get('createdAt').strftime('%Y-%m-%d %H:%M:%S') for item in query_list])
    
    api_json['statistical_data'] = {
        'friends_num': friends_num,
        'active_num': active_num,
        'error_num': error_num,
        'article_num': article_num,
        'last_updated_time': last_updated_time
    }
    
    article_data_init = []
    article_data = []
    for item in query_list:
        itemlist = {}
        for elem in list:
            itemlist[elem] = item.get(elem)
        article_data_init.append(itemlist)
    
    if end == -1 or end > min(article_num, 1000): end = min(article_num, 1000)
    if start < 0 or start >= min(article_num, 1000):
        return {"message": "start error"}
    if end <= 0:
        return {"message": "end error"}
    if rule != "created" and rule != "updated":
        return {"message": "rule error, please use 'created'/'updated'"}
    article_data_init.sort(key=lambda x : x[rule], reverse=True)
    index = 1
    for item in article_data_init:
        item["floor"] = index
        index += 1
        article_data.append(item)

    api_json['article_data'] = article_data[start:end]
    return api_json

@app.get("/friend")
async def friend():
    '''返回数据库友链列表（无额外参数）
    '''
    list = ['name', 'link', 'avatar', 'descr']
    # Verify key
    initleancloud()

    Friendlist = leancloud.Object.extend('friend_list')
    query_userinfo = Friendlist.query
    query_userinfo.limit(1000)
    query_userinfo.select('name','link','avatar','descr')
    query_list_user = query_userinfo.find()

    # Result to arr
    friend_list_json = []
    for item in query_list_user:
        itemlist = {}
        for elem in list:
            itemlist[elem] = item.get(elem)
        friend_list_json.append(itemlist)

    return friend_list_json

@app.get("/randomfriend")
async def randomfriend():
    '''随机返回一个友链信息（无额外参数）
    '''
    list = ['name', 'link', 'avatar', 'descr']
    # Verify key
    initleancloud()

    Friendlist = leancloud.Object.extend('friend_list')
    query_userinfo = Friendlist.query
    query_userinfo.limit(1000)
    query_userinfo.select('name','link','avatar','descr')
    query_list_user = query_userinfo.find()

    # Result to arr
    friend_list_json = []
    for item in query_list_user:
        itemlist = {}
        for elem in list:
            itemlist[elem] = item.get(elem)
        friend_list_json.append(itemlist)

    return random.choice(friend_list_json)

@app.get("/randompost")
async def randompost(rule: str = "updated"):
    '''随机返回一篇文章信息（无额外参数）
    '''
    list = ['title','created','updated','link','author','avatar']
    # Verify key
    initleancloud()

    # Declare class
    Friendspoor = leancloud.Object.extend('friend_poor')
    query = Friendspoor.query
    query.descending('created')
    query.limit(1000)
    query_list = query.find()

    article_data_init = []
    article_data = []
    for item in query_list:
        itemlist = {}
        for elem in list:
            itemlist[elem] = item.get(elem)
        article_data_init.append(itemlist)
    
    article_data_init.sort(key=lambda x : x[rule], reverse=True)
    index = 1
    for item in article_data_init:
        item["floor"] = index
        index += 1
        article_data.append(item)
    
    return random.choice(article_data)

@app.get("/post")
async def post(link: str = None, num: int = -1, rule: str = "updated"):
    '''返回指定链接的数据库内文章信息列表

    :param link: 【可选】链接地址，例如 https://noionion.top/ 或 noionion.top，默认为None（即随机返回一个链接的文章信息列表）

    :param num: 【可选】指定链接的文章信息列表 按rule排序后的顺序 的前num篇，默认为-1（即最大）

    :param rule: 【可选】文章排序规则（创建时间/更新时间），默认为updated，参数错误返回{"message": "rule error, please use 'created'/'updated'"}
    '''
    list = ['title','link','created','updated']
    # Verify key
    initleancloud()

    # Declare class
    Friendspoor = leancloud.Object.extend('friend_poor')
    query = Friendspoor.query
    query.descending('created')
    query.limit(1000)
    query.select('title','created','updated','link','author','avatar','createdAt')
    query_list = query.find()

    Friendlist = leancloud.Object.extend('friend_list')
    query_userinfo = Friendlist.query
    query_userinfo.limit(1000)
    query_userinfo.select('name','link','avatar','descr')
    query_list_user = query_userinfo.find()
    
    if link == None:
        link = random.choice(query_list_user).get('link')
    author = None
    avatar = None
    article_num  = None
    api_json = {}
    
    if link.startswith('http'):
        links = link.split('/')[2]
    else:
        links = link
    article_data_init = []
    article_data = []
    for item in query_list:
        itemlist = {}
        if links in item.get('link'):
            if author == None: author = item.get('author')
            if avatar == None: avatar = item.get('avatar')
            for elem in list:
                itemlist[elem] = item.get(elem)
            article_data_init.append(itemlist)
    
    article_num = len(article_data_init)
    api_json['statistical_data'] = {
        "author": author,
        "link": link,
        "avatar": avatar,
        "article_num": article_num
    }
    
    if num < 0 or num > min(article_num, 1000): num = min(article_num, 1000)
    if rule != "created" and rule != "updated":
        return {"message": "rule error, please use 'created'/'updated'"}
    article_data_init.sort(key=lambda x : x[rule], reverse=True)
    index = 1
    for item in article_data_init:
        item["floor"] = index
        index += 1
        article_data.append(item)

    api_json['article_data'] = article_data[:num]
    return api_json

@app.get("/postjson")
async def postjson(jsonlink: str, start: int = 0, end: int = -1, rule: str = "updated"):
    '''获取公共库中指定链接列表的文章信息列表

    :param jsonlink: 【必选】友链链接json的cdn地址，json格式为["https://noionion.top/", "https://akilar.top/", ...]，参数如jsonlist=https://pub-noionion.oss-cn-hangzhou.aliyuncs.com/friendlink.json

    :param start: 【可选】文章信息列表从 按rule排序后的顺序 的开始位置，默认为0，超出范围返回{"message": "start error"}

    :param end: 【可选】文章信息列表从 按rule排序后的顺序 的结束位置，默认为-1（即最大），其它非正数返回{"message": "end error"}
    
    :param rule: 【可选】文章排序规则（创建时间/更新时间），默认为updated，参数错误返回{"message": "rule error, please use 'created'/'updated'"}
    '''
    list = ['title','created','updated','link','author','avatar']
    # Verify key
    initleancloud()

    # Declare class
    Friendspoor = leancloud.Object.extend('friend_poor')
    query = Friendspoor.query
    query.descending('created')
    query.limit(1000)

    # Choose class
    query.select('title','created','updated','link','author','avatar','createdAt')
    query_list = query.find()

    headers = {
        "Cookie": "arccount62298=c; arccount62019=c",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36 Edg/87.0.664.66"
    }
    jsonhtml = requests.get(jsonlink, headers=headers).text
    linklist = json.loads(jsonhtml)
    
    linkset = set()
    for link in linklist: linkset.add(link)

    api_json = {}
    
    article_data_init = []
    article_data = []
    linkinPubLibrary_set = set()
    for item in query_list:
        for link in linklist:
            if link.startswith('http'):
                links = link.split('/')[2]
            else:
                links = link
            if links in item.get('link'):
                linkinPubLibrary_set.add(link)
                itemlist = {}
                for elem in list:
                    itemlist[elem] = item.get(elem)
                article_data_init.append(itemlist)
                break
    
    article_num = len(article_data_init)
    if end == -1 or end > min(article_num, 1000): end = min(article_num, 1000)
    if start < 0 or start >= min(article_num, 1000):
        return {"message": "start error"}
    if end <= 0:
        return {"message": "end error"}
    if rule != "created" and rule != "updated":
        return {"message": "rule error, please use 'created'/'updated'"}
    article_data_init.sort(key=lambda x : x[rule], reverse=True)
    index = 1
    for item in article_data_init:
        item["floor"] = index
        index += 1
        article_data.append(item)

    friends_num = len(linkset)
    linkinPubLibrary_num = len(linkinPubLibrary_set)
    linknoninPub_list = [link for link in linklist if link not in linkinPubLibrary_set]
    linknoninPub_num = len(linknoninPub_list)
    last_updated_time = max([item.get('createdAt').strftime('%Y-%m-%d %H:%M:%S') for item in query_list])

    api_json['statistical_data'] = {
        'friends_num': friends_num,
        'linkinPubLibrary_num': linkinPubLibrary_num,
        'linknoninPub_num': linknoninPub_num,
        'article_num': article_num,
        'last_updated_time': last_updated_time,
        'linknoninPub_list': linknoninPub_list
    }
    api_json['article_data'] = article_data[start:end]
    return api_json


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1")
