#coding=utf-8

import scrapy
from scrapy.selector import Selector
#Item Loaders提供了一种便捷的方式填充抓取到的 :Items
from scrapy.loader import ItemLoader, Identity
from scrapy.http import Request,FormRequest

from douban.items import DoubanItem
from douban.settings import *
from urlparse import urlparse
import time
import random

class TestSpider(scrapy.Spider):
    name = 'test'
    allowed_domains = ["douban.com"]
    start_urls = [
            "https://movie.douban.com/subject/1866479/comments?status=P",
            "https://movie.douban.com/subject/25827935/comments?status=P"
        ]

    headers = {
                #"Host":"accounts.douban.com",
                "User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:49.0) Gecko/20100101 Firefox/49.0",
                "Accept":"*/*",
                "Accept-Language":"zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3",
                "Accept-Encoding":"gzip, deflate, br",
                "Connection":"keep-alive",
                "Cookie":"bid=aASBX_5vB8w; ps=y",
                "Upgrade-Insecure-Requests":"1"
            }

    def start_requests(self):
        for i, url in enumerate(self.start_urls):
            sleepRandom = random.randint(0,5)
            time.sleep(sleepRandom)
            yield FormRequest(url, meta = {'cookiejar': i}, \
                    headers = self.headers, \
                    callback = self.parse_item)#jump to login page

    def parse_item(self, response):
        
        #sel是页面源代码，载入scrapy.selector
        sel = Selector(text=response.body)
        url = response.url
        start_index = url.find('comments')
        subject_index = url.find('subject')

        URL = url[0:start_index+8]
        subject_id = url[subject_index+len('subject/'):(start_index-1)]
        #print "subject_id:"+subject_id

        #get the comment content
        for comment in sel.xpath('//div[@id="comments"]/div[@class="comment-item"]/div[@class="comment"]'):
            item = DoubanItem() 
            try:
                item['subject_id'] = subject_id
                item['comment'] = comment.xpath('p/text()').extract()[0].strip()
                item['grade'] = comment.xpath('h3/span[@class="comment-info"]/span[contains(@class,"allstar")]/@title').extract()[0]
                item['votes'] = comment.xpath('h3/span[@class="comment-vote"]/span[contains(@class,"votes")]/text()').extract()[0]
                #print item
                yield item
            except:
                pass

        #nextPageXpath获取翻页的div,nextUrl保存生成的下一页URL
        nextPageXpath = sel.xpath('//*[@id="paginator"]')
        nextUrl = ""

        #第一次访问的xpath和第二次访问的xpath不同，需要区别对待
        if nextPageXpath.xpath('span/span/a/@href').extract():
            for nextPage in nextPageXpath.xpath('span/span/a/@href').extract():
                nextUrl = URL+nextPage
        else:
            for nextPage in nextPageXpath.xpath('a[@class="next"]/@href').extract():
                nextUrl = URL+nextPage

        #print nextUrl
        #请求下一页评论
        if nextUrl != "":
            yield scrapy.Request(nextUrl,
                        meta={'cookiejar':response.meta['cookiejar']},
                        headers = self.headers,
                        callback = self.parse_item
                    )
