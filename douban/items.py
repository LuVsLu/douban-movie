# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy

class DoubanItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    comment = scrapy.Field()
    grade = scrapy.Field()
    votes = scrapy.Field()
    subject_id = scrapy.Field()
    pass

class MovieItem(scrapy.Item):
    title = scrapy.Field()
    url = scrapy.Field()
    rate = scrapy.Field()
    cover_x = scrapy.Field()
    is_beetle_subject = scrapy.Field()
    playable = scrapy.Field()
    cover = scrapy.Field()
    id = scrapy.Field()
    cover_y = scrapy.Field()
    is_new = scrapy.Field()
    pass
