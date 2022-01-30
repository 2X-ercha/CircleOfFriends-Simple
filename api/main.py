# -*- coding:utf-8 -*-

from fastapi import FastAPI
import uvicorn
import leancloud
import os
import random

from leancloud import user
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

@app.get("/api")
async def all(start: int = 0, end: int = -1, rule: str = "updated"):
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
    
    if end == -1: end = min(article_num, 1000)
    if start < 0 or start >= min(article_num, 1000):
        return {"message": "start error"}
    if end <= 0 or end > min(article_num, 1000):
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


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1")