import scrapy

class TextSpider(scrapy.Spider):
    name = 'text'
    allowed_domains = ['*']
    start_urls = ['https://noionion.top/rss.xml']

    def parse(self, response):
        # print(response.text) # 打印网站文本
        sel = scrapy.Selector(text=response.text)
        items = sel.xpath("//item")
        for item in items:
            print(item.xpath("//title"))
