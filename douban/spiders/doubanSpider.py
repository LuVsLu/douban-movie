#coding=utf-8

import scrapy
from scrapy.selector import Selector
#Item Loaders提供了一种便捷的方式填充抓取到的 :Items
from scrapy.loader import ItemLoader, Identity
from scrapy.http import Request,FormRequest
from scrapy.spiders import CrawlSpider, Rule
from scrapy.selector import Selector
from scrapy.linkextractors.sgml import SgmlLinkExtractor
from scrapy.http.cookies import CookieJar

from douban.items import DoubanItem
from douban.items import MovieItem
from douban.settings import *
from urlparse import urlparse
from urllib import urlencode

import time
import random
import json

class DoubanSpider(CrawlSpider):
    name = 'douban'
    allowed_domains = ["douban.com"]
    start_urls = []
  
    #爬取"热门电影"种子url
    seed_url = "https://movie.douban.com/j/search_subjects?"
    #豆瓣登录页
    login_url = "https://accounts.douban.com/login?source=movie"

    cookie_jar = CookieJar()    #跟踪cookie
    page_num = 1      #爬取"热门电影"列表的页数
    page_limit = 20   #爬取"热门电影"列表每页包含的电影数
    time_sleep = 8    #爬取评论的时间间隔,单位s

    #伪造请求头
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

    #登录提交表单信息
    formdict = {
                'source':'movie',
                'redir':'https://movie.douban.com/',
                'form_email':'763976651@qq.com',
                'form_password':'qian13700522530'
            }

    #伪造请求"热门电影"列表的query
    query = {
            "type":"movie",
            "tag":"热门",
            "sort":"recommend",
            "page_limit":"100",
            "page_start":"0"
        }

    '''
    构造函数，从setting内读取配置信息
    '''
    def __init__(self):
        #self.headers = HEADER      #伪造请求头
        #self.formdict = FROMDICT   #构造表单
        #self.query =  QUERY        #伪造电影列表query

        #构造请求"热门电影"列表的URL,并保存到start_urls
        for i in range(0,self.page_num):
            self.query["page_start"] = str(i)
            self.query["page_limit"] = str(self.page_limit)
            url = self.seed_url+urlencode(self.query)
            self.start_urls.append(url)

    '''
    请求登录页
    '''
    def start_requests(self):
        return [Request(self.login_url,\
                meta={'cookiejar':self.cookie_jar},\
                headers = self.headers,\
                callback = self.post_login)]

    '''
    模拟登录，输入用户名，密码，验证码
    '''
    def post_login(self, response):
        print 'Start login...'
        
        sel = Selector(response)
        #获取是否包含验证码
        captcha = sel.xpath('//*[@id="captcha_image"]/@src').extract()
        
        #这里输入验证码，目前使用手动输入的方式
        if captcha:
            print "验证码地址:"+captcha[0]+"\n输入验证码:"
            xerf = raw_input()
            self.formdict['captcha-solution'] = xerf  #填写验证码

        return [FormRequest.from_response(response,\
                meta = {'cookiejar': response.meta['cookiejar']}, \
                headers = self.headers, \
                formdata = self.formdict,
                callback = self.after_login, #jump to login page
                dont_filter = True
                )]

    '''
    登录成功后，保存cookie，请求json列表
    '''
    def after_login(self, response):
        print "after login..."

        #保存cookie
        self.cookie_jar = response.meta['cookiejar']

        #登录失败
        if "authentication failed" in response.body:
            self.log("login failed", level = log.ERROR)
        
        #请求“热门电影”json列表
        sel = scrapy.Selector(response)
        for url in self.start_urls:
            #print url
            yield scrapy.Request(url,
                    meta={'cookiejar':response.meta['cookiejar']},
                    headers = self.headers,
                    callback=self.parse_json)

    '''
    解析热门电影json列表，将电影列表保存到数据库，并请求下载电影评论
    '''
    def parse_json(self, response):
        #解析response中的字符串
        json_str = response.body
        jsonDict = json.loads(json_str)
        #如果没有返回json,结束遍历
        if jsonDict is None:
            return

        for subject in jsonDict["subjects"]:
            item = MovieItem()
            item['title'] = subject['title']
            item['url'] = subject['url']
            item['rate'] = subject['rate']
            item['cover_x'] = subject['cover_x']
            item['is_beetle_subject'] = subject['is_beetle_subject']
            item['playable'] = subject['playable']
            item['cover'] = subject['cover']
            item['id'] = subject['id']
            item['cover_y'] = subject['cover_y']
            item['is_new'] = subject['is_new']
            yield item
            
            url = item['url']+"comments?status=P"
            yield scrapy.Request(url,meta={'cookiejar':response.meta['cookiejar']},
                        headers = self.headers,
                        callback = self.parse_item
                    )

    '''
    解析评论页面，保存评论信息，并爬取下一页.
    '''
    def parse_item(self, response):

        #sel是页面源代码，载入scrapy.selector
        sel = Selector(text=response.body)
        url = response.url
        start_index = url.find('comments')
        subject_index = url.find('subject')

        URL = url[0:start_index+8]
        subject_id = url[subject_index+len('subject/'):(start_index-1)]
        #print URL

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

        print nextUrl

        #设置翻页的间隔,随机sleep 0-time_sleep秒，模拟正常用户访问间隔
        sleepRandom = random.randint(0,self.time_sleep)
        time.sleep(sleepRandom)

        #请求下一页评论
        if nextUrl != "":
            yield scrapy.Request(nextUrl,
                        meta={'cookiejar':response.meta['cookiejar']},
                        headers = self.headers,
                        callback = self.parse_item
                    )
