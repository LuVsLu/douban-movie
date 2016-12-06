#coding=utf8
import scrapy

class DemoSpider(scrapy.Spider):
    name = "demo"
    allowed_domains = ["douban.com"]
    start_urls = [
        "https://movie.douban.com/subject/1866479/comments?status=P"    
    ]

    def parse(self, response):
        filename = response.url.split("/")[-2]
        with open(filename, 'wb') as f:
            f.write(response.body)
