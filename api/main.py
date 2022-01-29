# -*- coding:utf-8 -*-

from fastapi import FastAPI, Form
import uvicorn
import leancloud
import os
import requests
import oss2
import json

from leancloud import user


app = FastAPI()

def initleancloud():
    # leancloud.init(os.environ["LEANCLOUD_ID"], os.environ["LEANCLOUD_KEY"])
    leancloud.init("L1XyQ3J4YBI3EeT0yipKT3Bp-MdYXbMMI", "oF8IWsza21H2pQlgtgqLB2Qo")

@app.get("/api")
async def all(start: int = 0, end: int = -1, rule: str = "created"):
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
    
    article_data = []
    for item in query_list:
        itemlist = {}
        for elem in list:
            itemlist[elem] = item.get(elem)
        article_data.append(itemlist)
    
    if end == -1: end = min(article_num, 1000)
    if start < 0 or start >= min(article_num, 1000):
        return {"message": "start error"}
    if end <= 0 or end > min(article_num, 1000):
        return {"message": "end error"}
    if rule != "created" and rule != "updated":
        return {"message": "rule error, please use 'created'/'updated'"}
    article_data.sort(key=lambda x : x[rule], reverse=True)
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


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1")