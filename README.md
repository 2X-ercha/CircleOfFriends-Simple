# 友链朋友圈公共库

这里是友链朋友圈公共收录库，目的是提供一个公共的友圈以及提供无需后端的友圈部署方案

项目主仓库（即个人部署方案）地址：https://github.com/Rock-Candy-Tea/hexo-circle-of-friends

## api 列表

api地址：https://circle-of-friends-simple.vercel.app/
公共库api 会逐步与私人部署方案的 api 同步，目前 api 列表如下

> `/all`

返回数据库统计信息和文章信息列表

    start: 文章信息列表从 按rule排序后的顺序 的开始位置
    end: 文章信息列表从 按rule排序后的顺序 的结束位置
    rule: 文章排序规则（创建时间/更新时间）

> `/friend`

返回数据库友链列表（无额外参数）

> `/randomfriend`

随机返回一个友链信息（无额外参数）

> `/randompost`

随机返回一篇文章信息（无额外参数）

> `/post`

返回指定链接的数据库内文章信息列表

    link: 链接地址
    num: 指定链接的文章信息列表 按rule排序后的顺序的前num篇
    rule: 文章排序规则（创建时间/更新时间）

例如：
```
https://circle-of-friends-simple.vercel.app/post?link=https://noionion.top
```

> `/postjson`

获取公共库中指定链接列表的文章信息列表

    jsonlink: 友链链接json的cdn地址
    start: 文章信息列表从 按rule排序后的顺序 的开始位置
    end: 文章信息列表从 按rule排序后的顺序 的结束位置
    rule: 文章排序规则（创建时间/更新时间）

例如：
```
https://circle-of-friends-simple.vercel.app/postjson?jsonlink=https://pub-noionion.oss-cn-hangzhou.aliyuncs.com/friendlink.json
```

提供的json地址应该是一个带`http`或`https`的纯链接数组，例如：
```json
[
    "https://noionion.top/",
    "https://akilar.top/",
    "https://blog.zhheo.com/",
    "https://zfe.space/"
]
```

完整的api使用方案你可以查看 https://circle-of-friends-simple.vercel.app/docs

--------

## 如何让你的文章被收录到友圈公共库

按格式在文件最后添加上您的友链信息：https://github.com/2X-ercha/CircleOfFriends-Simple/blob/master/hexo_circle_of_friends/config/link.yml 并PR仓库，待PR通过后即可

目前友链朋友圈公共库已获得以下项目的授权并进行追踪获取，故以下项目收录的中文博客链接一并收录到库中：

https://github.com/saveweb/rss-list