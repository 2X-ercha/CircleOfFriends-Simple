import requests
import json
import xml.etree.ElementTree as ET
from ruamel import yaml
from queue import Queue
from threading import Thread
import os

headers = {
    "content-type": "application/json",
    "authorization": "Bearer {}".format(os.getenv("github-token"))
}

try:
    f = requests.get("https://api.github.com/repos/saveweb/rss-list/releases/latest", headers=headers).text
    f = json.loads(f)
    index = -1
    for i, item in enumerate(f['assets']):
        if item['name'] == "Blog.opml.xml":
            index = i
            break
    if index == -1:
        print("none")
    else:
        print("saveweb get start")
        url = f['assets'][index]['browser_download_url']
        f = requests.get(url)
        f.encoding = 'utf-8'
        f = f.text
        tree = ET.XML(f)
        list = tree[1][0]
        friends = []

        def gen(item):
            global friends
            try:
                icon = requests.get("https://besticon-demo.herokuapp.com/allicons.json?url={}".format(item.get("htmlUrl"))).text
                iconjson = json.loads(icon)
                avatar = iconjson["icons"][0]["url"]
            except:
                avatar = "https://besticon-demo.herokuapp.com/icon?url={}&size=80..120..200".format(item.get("htmlUrl"))

            friend_info = {
                "name": item.get("text"),
                "link": item.get("htmlUrl"),
                "feed": item.get("xmlUrl"),
                "avatar": avatar,
                "descr": item.get("description")
            }
            friends.append(friend_info)

        # multithread process
        # ---------- #
        Q = Queue()

        for i in range(len(list)):
            Q.put(i)

        def multitask():
            while not Q.empty():
                i= Q.get()
                item = list[i]
                gen(item)

        cores = 256
        threads = []
        for _ in range(cores):
            t = Thread(target=multitask)
            threads.append(t)
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        # ---------- #

        with open("hexo_circle_of_friends/config/From_saveweb.yml", "w", encoding="utf-8") as f:
            yaml.dump(friends, f, Dumper=yaml.RoundTripDumper, allow_unicode=True)

    print("saveweb get ok")
except:
    print("saveweb get error")