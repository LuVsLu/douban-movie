# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html
from douban import settings
import json
import datetime

import MySQLdb
import logging
import sys   
reload(sys)
sys.setdefaultencoding('utf-8') 

'''
保存评论到其对应的电影ID文件中
'''
class DoubanPipeline(object):

    star = {u'力荐':'5',u'推荐':'4',u'还行':'3',u'较差':'2',u'很差':'1'}

    def __init__(self):
        #date = datetime.datetime.now().strftime("%Y-%m-%d")
        #self.file = open('douban/comments/items-'+date+'.txt', 'ab')
        pass

    def process_item(self, item, spider):
        if 'title' in item:
            return item
        
        filename = 'douban/comments/'+item['subject_id']+".txt"
        with open(filename, 'ab') as f:
            line = self.star[item['grade']]+' '+item['votes']+' '+item['comment'].encode('utf-8')+"\n"
            f.write(line)       
        #print item
        return item

'''
保存热门电影列表,用于去重,备份
'''
class MoviePipeline(object):
    def __init__(self, mysql_host, mysql_user, mysql_pwd, mysql_db):
        self.host = mysql_host
        self.user = mysql_user
        self.pwd = mysql_pwd
        self.db = mysql_db
        self.conn = MySQLdb.connect(self.host, self.user, self.pwd, self.db)
        print self.host,self.user,self.pwd,self.db

    @classmethod
    def from_crawler(cls, crawler):
        
        return cls(
            mysql_host=crawler.settings.get('MYSQL_HOST'),
            mysql_user=crawler.settings.get('MYSQL_USER'),
            mysql_pwd=crawler.settings.get('MYSQL_PWD'),
            mysql_db=crawler.settings.get('MYSQL_DB')
        )

    def open_spider(self, spider):
        self.conn = MySQLdb.connect(self.host, self.user, self.pwd, self.db,charset='utf8')

    def close_spider(self, spider):
        self.conn.close() 

    def process_item(self, item, spider):

        if 'comment' in item : 
            return item

        #print item
        cursor = self.conn.cursor()
        sql = '''INSERT INTO hot_movies(
                        title, 
                        url, 
                        rate, 
                        cover_x, 
                        cover, 
                        object_id, 
                        cover_y 
                        )  
                        VALUES('{0}','{1}','{2}','{3}','{4}','{5}','{6}')'''
        #for k,v in item.items():
        #    self.file.write( "%s : %s \n\n" % (k, v.encode('utf8')))
        sql = sql.format(item['title'].encode('utf8'), 
                item['url'], 
                item['rate'], 
                item['cover_x'], 
                item['cover'],
                item['id'],
                item['cover_y'])
    
        #print sql
        try:
            cursor.execute(sql)
            self.conn.commit()
        except MySQLdb.Warning, w:
            sqlWarning =  "Warning:%s" % str(w)
            print sqlWarning
        except MySQLdb.Error, e:
            sqlError =  "Error:%s" % str(e)
            print sqlError
        except:
            self.conn.rollback()
        return item
