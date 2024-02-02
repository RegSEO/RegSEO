import codecs
import joblib
from gensim.models import KeyedVectors

from feature import FeatureExtractor
from db.db_init import DB
import pymysql
import time
import bson
import re
from bson.objectid import ObjectId


class mysql_docker:
    def __init__(self) -> None:
        pass
    
    def conn(self):
        self.mysql_conn = pymysql.connect(host='host',
                       user='user',
                       password='passwd',
                       database='databse',
                       port=3306,
                       charset='utf8')

        self.cursor = self.mysql_conn.cursor()

    def insertdata(self,docker_id,name,result,author,date_registered, last_updated):
        insert_sql = "insert into black_seo.docker_new (name,date,result,docker_id,author,date_registered, last_updated) values ('"+name+"','"+time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+"','"+result+"','"+docker_id+"','"+author+"','"+date_registered+"', '"+last_updated+"')"
        # 执行语句
        print(insert_sql)
        self.cursor.execute(insert_sql)
        # 提交数据
        self.mysql_conn.commit()
        
    def insertnull(self,docker_id):  # name null
        insert_null_sql = "insert into black_seo.docker_new (name,date,result,docker_id,author,date_registered,last_updated) values ('null','"+time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+"','null','"+docker_id+"','null','null','null')"
        # 执行语句
        self.cursor.execute(insert_null_sql)
        # 提交数据
        self.mysql_conn.commit()
        
    def inserturl(self,url_list,docker_id):
        for url in url_list:
            if url!="" and url is not None:
                insert_url_sql = "insert into black_seo.docker_urls (url,docker_id,test_time,promotion) values ('"+url[:255]+"','"+docker_id+"','"+time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+"',1)"
                print(insert_url_sql)
                # 执行语句
                self.cursor.execute(insert_url_sql)
        self.mysql_conn.commit()


class classify:
    def __init__(self) -> None:
        self.my_d = mysql_docker()
        self.my_d.conn()
    
    def load_model(self): 
        # load the word2vec
        print("start loading")
        self.word2vec = KeyedVectors.load_word2vec_format('/path/to/wiki.en.vec') # path to wiki.en.vec
        print("finished")
        # load the classifier
        self.classifier = joblib.load('./model/RFC.joblib')
        
    def load_mongo(self):
        self.db = DB()
        self.coll = self.db.get_mongo('qianxin_docker')
        self.type = self.db.get_mongo('qianxin_type')
        # # 每次查询5000条数据
        self.chunk_size = 5000

    def analysis(self):
        last_id=None
        try:
            with open('last_id', 'r') as file:
                content = file.read()
                if content.strip():
                    last_id=ObjectId(content.strip())
        except FileNotFoundError:
            pass
        while(True):
            try:
                query = {}  # 可以根据需要设置查询条件
                if last_id:
                    query['_id'] = {'$gt': last_id}
                cursor = self.coll.find(query).limit(self.chunk_size)
                _count=0
                
                # 开始对每页的数据进行遍历
                for item in cursor:
                    _count=_count+1
                    last_id = item['_id']  # 记录当前数据的标识
                    date_registered = "null"
                    last_updated = "null"
                    if item and 'date_registered' in item and item['date_registered']!='':
                        date_registered = item['date_registered']
                    if item and 'last_updated' in item and item['last_updated']!='':
                        last_updated = item['last_updated']
                    
                    # 如果name不存在，则不进行记录
                    if "name" not in item or item['name'] == "" or item["name"] is None:
                        self.my_d.insertnull(bson.objectid.ObjectId(item['_id']).__str__())
                        continue
                    if "namespace" not in item or item["namespace"]=="" or item["namespace"] is None:
                        self.my_d.insertdata(bson.objectid.ObjectId(item['_id']).__str__(),item["name"],"null", "null", date_registered, last_updated)
                        continue
                    if "full_description" not in item or item["full_description"]=="" or item["full_description"] is None:
                        self.my_d.insertdata(bson.objectid.ObjectId(item['_id']).__str__(),item["name"],"no_overview", item["namespace"], date_registered, last_updated)
                        continue
                    url_pattern = re.compile(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')
                    if not url_pattern.search(item['full_description']):
                        self.my_d.insertdata(bson.objectid.ObjectId(item['_id']).__str__(),item["name"],"overview_no_link", item["namespace"], date_registered, last_updated)
                        continue
                    doc = self.type.find_one({"slug": item["namespace"] + "/" + item['name']}, {"filter_type": 1})
                    if doc and doc["filter_type"]!="community":
                        self.my_d.insertdata(bson.objectid.ObjectId(item['_id']).__str__(),item["name"],"non-abuse", item["namespace"], date_registered, last_updated)
                    else:
                        features = []
                        extractor = FeatureExtractor(item, self.word2vec)
                        features.append(extractor.total_features())
                        label_pred = self.classifier.predict(features)
                        print(label_pred[0])
                        self.my_d.insertdata(bson.objectid.ObjectId(item['_id']).__str__(),item["name"],label_pred[0], item["namespace"], date_registered, last_updated)
                        hrefs = re.findall(r'href=[\'"]?([^\'" >]+)', item['full_description'])
                        hrefs = list(set(hrefs))
                        url_list = []
                        for href in hrefs:
                            if href.startswith('http'):
                                url_list.append(href)
                        self.my_d.inserturl(url_list,bson.objectid.ObjectId(item['_id']).__str__())

                # 到达最后一页，结束循环
                if _count < 5000:  
                    break
            except Exception as e:
                print(e) #打印异常说明
                continue
            finally:
                # 记录下一页的开始记录
                with open('last_id', 'w') as file:
                    file.write(bson.objectid.ObjectId(last_id).__str__())
                    
                    

if __name__ == "__main__":
    classifier = classify()
    classifier.load_model()
    classifier.load_mongo()
    classifier.analysis()
    