import codecs
import joblib
import os
from gensim.models import KeyedVectors

from feature import FeatureExtractor
from db.db_init import DB
import pymysql
import time
import bson
import re
from prefile import FilePreprocessor
from bson.objectid import ObjectId

import requests
from datetime import datetime,timedelta
import time
from dateutil.parser import isoparse
import json
import os, sys
import argparse

import sys
import threading
import subprocess


class mysql_docker:
    def __init__(self) -> None:
        pass
    
    def conn(self):
        self.mysql_conn = pymysql.connect(host='host',
                       user='user',
                       password='passwd',
                       database='db',
                       port=6612,
                       charset='utf8')

        self.cursor = self.mysql_conn.cursor()
    
    def close(self):
        self.cursor.close()
        self.mysql_conn.close()

    def insertdata(self,date,name,result,author,url_info):
        try:
            if name == '': name = "null"
            if author == '': author = "null"
            
            if name.count("'") > 0:
                name = name.replace("'", "''")
                print(name)
            if author.count("'") > 0:
                author = author.replace("'", "''")
                print(author)
            if url_info.count("'") > 0:
                url_info = url_info.replace("'", "''")
                print(url_info)

            insert_sql = "insert into black_seo.nuget_new (name,time,result,date,author,urls) values ('"+name+"','"+time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+"','"+result+"','"+date+"','"+author+"','"+url_info+"')"
            # 执行语句
            self.cursor.execute(insert_sql)
            # 提交数据
            self.mysql_conn.commit()
            return 1
        except Exception as e:
            return 0
            print("插入其它时发生异常：", e)
    
    def insertlink(self,date,name,author):
        try:
            if name == '': name = "null"
            if author == '': author = "null"
            
            if name.count("'") > 0:
                name = name.replace("'", "''")
                print(name)
            if author.count("'") > 0:
                author = author.replace("'", "''")
                print(author)

            insert_sql = "insert into black_seo.nuget_new (name,time,result,date,author,urls) values ('"+name+"','"+time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+"','non-abuse','"+date+"','"+author+"','no_url')"
            # 执行语句
            self.cursor.execute(insert_sql)
            print("www")
            # 提交数据
            self.mysql_conn.commit()
            return 1
        except Exception as e:
            print("插入链接时发生异常：", e)
            return 0

class classify:
    def __init__(self) -> None:
        self.date = ''
    
    def load_model(self): 
        # load the word2vec
        print("start loading")
        # load the word2vec
        self.model = KeyedVectors.load_word2vec_format('/path/to/wiki.en.vec') # 奇安信服务器2上的版本
        # self.model=''
        print("finished")
        # load the classifier
        self.classifier = joblib.load('./model/RFC.joblib')

    def analysis(self, date):
        self.date = date
        self.my_d = mysql_docker()
        self.my_d.conn()

        folder_path = '/path/to/nuget_pkg/' + self.date
        file_list = os.listdir(folder_path)

        record_name = 'record_new/' + self.date + '.txt'
        if not os.path.exists(record_name):
            with open(record_name, "w") as f:
                f.write(self.date + '\n')
                print(f"'{record_name}' created successfully.")
        else:
            print(f"'{record_name}' already exists.")

        # print(file_list)
        id=1
        for filename in file_list: 
            filename = filename.split('.nupkg')[0]   
            # print(filename)
            if filename == 'release': continue

            # 检查是否已经处理过该文件
            file_processed = False
            with open('record_new/' + self.date + '.txt', 'r') as f:
                content = f.readlines()
                if content:
                    for line in content:
                        if filename == line.strip():
                            file_processed = True
                            break                            
            if file_processed:
                continue

            processor = FilePreprocessor(filename, self.date)

            author, description, filenums,dirnum, license, readme, projectURL, repository = processor.extract_info()
            # if description=='': continue
            # short description
            
            if len(description.strip())<20: 
                print(description)
                id = id + 1
                with open('record_new/' + self.date + '.txt', 'a') as f:
                    f.write(filename + '\n')
                continue
            # no url at all
            url_pattern = re.compile(r'http[s]?://(?:[^\s;()"])+')
            urls = url_pattern.findall(description)
            # total_urls_num = len(urls)

            if len(urls) == 0: 
                flag = self.my_d.insertlink(self.date,filename,author)
                id = id + 1
                if flag:
                    with open('record_new/' + self.date + '.txt', 'a') as f:
                        f.write(filename + '\n')
                continue
            
            # extract urls
            urls = []
            # markdown
            hrefs = re.findall(r'\[[^]]+\]\(([^)]+)\)', description)
            hrefs = list(set(hrefs))
            for href in hrefs:
                if href.startswith('http'):
                    urls.append(href)
            
            # html
            hrefs = re.findall(r'href=[\'"]?([^\'" >]+)', description)
            hrefs = list(set(hrefs))
            for href in hrefs:
                if href.startswith('http'):
                    urls.append(href)

            if len(urls) == 0:
                url_string = 'no_url'
                print(url_string)
            else:
                url_string = "\n".join(urls)
                print(url_string)

            extractor = FeatureExtractor(filename, author, description, license, readme, projectURL, repository, self.model)

            features = []
            features.append(extractor.total_features())
            label_pred = self.classifier.predict(features)
            
            flag = self.my_d.insertdata(self.date,filename,label_pred[0], author, url_string)
            id = id + 1

            if flag: 
                with open('record_new/' + self.date + '.txt', 'a') as f:
                    f.write(filename + '\n')   
        
        self.my_d.close()

def main(month):
    print("start classify: " + month)
    classifier = classify()
    classifier.load_model()

    # flag = 0
    flag = 1

    for day in range(1, 32):
        day_str = str(day).zfill(2)
        date = month + '-' + day_str
        record_path = 'record_new/' + date + '.txt'
        release_path = '/path/to/nuget_pkg/' + date + '/' + 'release'
        if os.path.exists(record_path):
            if not os.path.exists(release_path):
                continue
            if os.path.exists(release_path):
                print(release_path)
                flag = 0
        # print(date + '.txt')
        if datetime.strptime(date, "%Y-%m-%d"):
            if flag == 0:
                classifier.analysis(date)  # 分类
                dir = '/path/to/nuget_pkg/' + date # 删除
                subprocess.run(['rm', '-r', dir])
                flag = 1  
            else:
                arg = '--dir=' + date
                subprocess.run(['python', 'nuget_daily.py', arg]) # 下载
                classifier.analysis(date)  # 分类
                dir = '/path/to/nuget_pkg/' + date # 删除
                subprocess.run(['rm', '-r', dir])             

if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    # 在参数构造器中添加两个命令行参数
    # 格式 python ./classify_npm.py --dir=2023-07-20
    parser.add_argument('--dir', type=str, default = None)
    args = parser.parse_args()
    if(args.dir==None):
        print("需要指定日期")
    else:
        main(args.dir)
    