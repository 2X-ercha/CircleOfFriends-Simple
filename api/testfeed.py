# -*- coding:utf-8 -*-
import requests
import feedparser

def testfeed(feedlink):
    retjson = {
        "error": False,
        "rule": None,
        "suggestion": []
    }
    t1, t2 = False, False
    u1, u2 = False, False
    try:
        xml_text = feedparser.parse(requests.get(feedlink).text)
        try: feedlink = xml_text.feed.link
        except: pass
        entries = xml_text.entries
        retjson["rule"] = xml_text.version
        entry = entries[0]
        # 文章链接
        entrylink = entry.link
        if not entrylink.startswith('http'):
            retjson["suggestion"].append("文章链接为相对链接或无https协议头")
        # 创建时间
        try: entrycreated_parsed = entry.created_parsed
        except:
            try:
                if retjson["rule"].startswith("rss"):
                    retjson["suggestion"].append("文章无创建时间")
                    u1 = True
                entrycreated_parsed = entry.published_parsed
            except:
                if not u1: retjson["suggestion"].append("文章无创建时间")
                u1 = True
                try: entrycreated_parsed = entry.updated_parsed
                except: t1 = True
        try: entrycreated = "{:4d}-{:02d}-{:02d}".format(entrycreated_parsed[0], entrycreated_parsed[1], entrycreated_parsed[2])
        except:
            if not u1: retjson["suggestion"].append("创建时间解析错误")
            t1 = True
        try: entryupdated_parsed = entry.updated_parsed
        except:
            retjson["suggestion"].append("文章无更新时间")
            u2 = True
            try: entryupdated_parsed = entry.published_parsed
            except:
                try: entryupdated_parsed = entry.created_parsed
                except: t2 = True
        try: entryupdated = "{:4d}-{:02d}-{:02d}".format(entryupdated_parsed[0], entryupdated_parsed[1], entryupdated_parsed[2])
        except:
            if not u2: retjson["suggestion"].append("更新时间解析错误")
            t2 = True
    except:
        retjson["error"] = True
    retjson["error"] = t1 & t2
    return retjson