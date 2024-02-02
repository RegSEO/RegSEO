import codecs
import joblib
import json
from gensim.models import KeyedVectors
from urllib.parse import urlparse
import argparse
from feature import FeatureExtractor
from db.db_init import DB
import pymysql
import time
import bson
import re
import tarfile
import sys
import threading
import subprocess
import os
from multiprocessing import Pool
import sys
import calendar

# 获取命令行参数
args = sys.argv

# 打印命令行参数
year = int(args[1])
month = int(args[2])
table = "npm_"+str(year)
table_url = "urls_"+str(year)


mysql_conn = pymysql.connect(host='host',
                user='user',
                password='passwd',
                database='db',
                port=6612,
                charset='utf8')

cursor = mysql_conn.cursor()
        
def insertdata(from_dir,name,result,release_date,user_name,user_email,urlss):
    return_sqls = [] 
    try:
        limited_from_dir = from_dir[:95]
        limited_name = name[:95]
        if user_name!='':
            limited_user_name = user_name[:95]
        else:
            limited_user_name = 'NULL'
        if user_email!='':
            limited_user_email = user_email[:95]
        else:
            limited_user_email = 'NULL'
        insert_sql = "insert into black_seo."+table+" (name,date,result,tar_name,release_date,user_name,user_email) values ('"+limited_name+"','"+time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+"','"+result+"','"+limited_from_dir+"','"+release_date+"','"+limited_user_name+"','"+limited_user_email+"')"
        return_sqls.append(insert_sql)
        if result=='abuse':
            for _url_ in urlss:
                if _url_ == '':
                    continue
                # _url_1 = re.findall(r'https?://[a-zA-Z0-9\-_.?/=]+\b', _url_)
                # if len(_url_1)>0:
                limited_url = _url_[:254]
                insert_sql_url = "insert into black_seo."+table_url+"(url,release_date,tar_name) values ('"+limited_url+"','"+release_date+"','"+limited_from_dir+"')"
                return_sqls.append(insert_sql_url)
    except Exception as reason:
        print(reason)
    finally:
        return return_sqls
        

        
def insert_name_null(from_dir,release_date):
    return_sqls = [] 
    try:
        limited_from_dir = from_dir[:95]
        insert_null_sql = "insert into black_seo."+table+" (name,date,result,tar_name,release_date) values ('name_null','"+time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+"','name_n','"+limited_from_dir+"','"+release_date+"')"
        return_sqls.append(insert_null_sql)
    except Exception as reason:
        print(reason)
    finally:
        return return_sqls
        
def insert_readme_null(from_dir,name,release_date):
    return_sqls = [] 
    try:
        limited_from_dir = from_dir[:95]
        limited_name = name[:95]
        insert_null_sql = "insert into black_seo."+table+" (name,date,result,tar_name,release_date) values ('"+limited_name+"','"+time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+"','rdm_n','"+limited_from_dir+"','"+release_date+"')"
        return_sqls.append(insert_null_sql)
    except Exception as reason:
        print(reason)
    finally:
        return return_sqls
        
def insert_database(sqls):
    mysql_conn.begin()
    for sql in sqls:
        for true_sql in sql:
            try:
                print(true_sql)
                cursor.execute(true_sql)
            except Exception as e:
                # 处理报错（例如记录错误日志）
                print(f"执行SQL语句出错：{true_sql}，错误信息：{str(e)}")
    mysql_conn.commit()

# class classify:
min_readme_len=1
print("start loading")
word2vec = KeyedVectors.load_word2vec_format('/path/to/wiki.en.vec') # 奇安信服务器2上的版本
print("finished")
classifier = joblib.load('./model/RFC.joblib')
    
    
    

def analysis(dir_name,line):
    urlss = []
    res_sqls = []
    line=line.rstrip('\n')
    root_path='/path/to/npm_pkg/'
    # 先读名字
    dir_path = "no_use"
    homepage_sub_domain=''
    repo_url=''
    des_text=''
    name_text=''
    # homepage & repo & name & des
    try:
        json_path = root_path+dir_name+'/'+line
        targetjson_file_path = "package/package.json"  # 需要读取的文件在.tar包中的路径
        # 打开.tar包
        with tarfile.open(json_path, "r") as tar:
            # 检查.tar包中是否存在指定路径的文件
            if targetjson_file_path in tar.getnames():
                # 获取指定路径文件的File对象
                file = tar.extractfile(targetjson_file_path)
                
                # 读取文件内容
                try:
                    json_text = file.read().decode("utf-8")
                    content = json.loads(json_text)
                    if 'name' in content:
                        name_text=content['name']
                    else:
                        name_text=''
                    if 'description' in content:
                        des_text=content['description']
                    else:
                        des_text=''
                    if 'homepage' in content and content["homepage"]!="":
                        domain = urlparse(content['homepage']).netloc
                        homepage_sub_domain = ".".join(domain.split('.')[-2:])
                    else:
                        homepage_sub_domain=''
                    if 'repository' in content and 'url' in content['repository'] and content['repository']['url']!="":
                        repo_url = content['repository']['url']
                    else:
                        repo_url=''
                except Exception as reason:
                    repo_url=''
                    des_text=''
                    name_text=''
                    print(reason)
    except Exception as reason:
        print(reason)
    
    
            
    # 如果无名字就不分类了
    if name_text=='':
        # print(line,": no name")
        res_sqls = res_sqls+insert_name_null(line,dir_name)
        return res_sqls
    

        
    # 再读readme
    read_me_text=''
    latin_flag=0
    try:
        readme_path = root_path+dir_name+'/'+line
        rdm_file_path1 = "package/README.md"
        rdm_file_path2 = "package/readme.md"
        rdm_file_path3 = "package/Readme.md"
        rdm_file_path4 = "package/README.MD"
        target_file_path = ""  # 需要读取的文件在.tar包中的路径
        # 打开.tar包
        with tarfile.open(readme_path, "r") as tar:
            # 检查.tar包中是否存在指定路径的文件
            if rdm_file_path1 in tar.getnames():
                target_file_path = rdm_file_path1
            elif rdm_file_path2 in tar.getnames():
                target_file_path = rdm_file_path2
            elif rdm_file_path3 in tar.getnames():
                target_file_path = rdm_file_path3
            elif rdm_file_path4 in tar.getnames():
                target_file_path = rdm_file_path4
            if target_file_path in tar.getnames():
                try:
                    #  获取.tar包中的所有文件列表
                    file_list = tar.getnames()
                    # 计算文件数量
                    # num_files = len(file_list)
                    # 计算目录数量
                    # all_members = tar.getmembers()
                    # 获取所有目录的数量
                    # num_dir = sum(1 for member in all_members if member.isdir())
                except Exception as reason:
                    print(reason)
                
                try:
                    # 获取指定路径文件的File对象
                    file = tar.extractfile(target_file_path)
                    # 读取文件内容
                    read_me_text = file.read().decode("utf-8")
                except Exception as reason:
                    print(reason)
                    latin_flag=1
                    
                
                if latin_flag==1:
                    try:
                        # 获取指定路径文件的File对象
                        file = tar.extractfile(target_file_path)
                        # 读取文件内容
                        read_me_text = file.read().decode("Latin-1")
                    except Exception as reason:
                        read_me_text=''
                        print(reason)
            else:
                read_me_text=''
    except Exception as reason:
        read_me_text=''
        print(reason)
    finally:
        # 如果readme实在是太短了就不分类了(目前认为redme为空则不分类)
        if len(read_me_text.strip())<min_readme_len:
            res_sqls = res_sqls+insert_readme_null(line,name_text,dir_name)
            return res_sqls
        
    # 提取推广链接
    hrefs = re.findall(r'\[[^]]+\]\(([^)]+)\)', read_me_text)
    hrefs = list(set(hrefs))
    for href in hrefs:
        if href.startswith('http'):
            urlss.append(href)
            
    if latin_flag==1:
        hrefs = re.findall(r'href=[\'"]?([^\'" >]+)', read_me_text)
        hrefs = list(set(hrefs))
        for href in hrefs:
            if href.startswith('http'):
                urlss.append(href)
                
                
                
        
    try:
        text_str = name_text + ' ' + des_text + ' ' +read_me_text
    except Exception as reason:
        text_str=read_me_text
    
    if read_me_text=='':
        read_me_flag=0
    else: 
        read_me_flag=1
        
        
        
        
    # 读取user的 name 与 email 字段
    user_name = None
    user_email = None
    tar_json_f = None
    try:
        tar_json_path = root_path+ dir_name + '_json/'+line+'.json'
        # 打开文件
        tar_json_f = open(tar_json_path, 'r', errors='ignore')
        tar_json=tar_json_f.read()
        pattern = r"'_npmUser'.*?}"
        match = re.search(pattern, tar_json)
        if match:
            matched_string = match.group()
            match_array = matched_string.split("'")
            user_name=match_array[5]
            user_email=match_array[9]
        else:
            user_name=''
            user_email=''
    except Exception as e:
        print(e)
        user_name=''
        user_email=''
    finally:
        # print("user_name: ",user_name,"  user_email: ",user_email)
        if tar_json_f in locals():
            tar_json_f.close()
        
    
    if text_str.strip():
        features = []
        extractor = FeatureExtractor(text_str, word2vec,dir_path,homepage_sub_domain,repo_url,read_me_flag,user_name, user_email)
        # urlss = extractor.return_urls
        features.append(extractor.total_features())
        label_pred = classifier.predict(features)
        print(dir_name,"--",line,"------",label_pred[0])
        res_sqls = res_sqls+insertdata(line,name_text,label_pred[0],dir_name,user_name,user_email,urlss)
    
    return res_sqls


def get_name_in_dir(date):
    all_file_name_list = []
    root_path='/path/to/npm_pkg/'
    name_path = root_path + date
    file_list = os.listdir(name_path)
    return file_list
    

if __name__ == '__main__':
    if month>=1 and month<=9:
        month_str="0"+str(month)
    else:
        month_str=str(month)
    dates = []
    delete_str = '/path/to/npm_pkg/' + str(year)+'-'+month_str+'*'
    if month==1 or month==3 or month==5 or month==7 or month==8 or month==10 or month==12:
        for item in range(1,32):
            if item>=1 and item<=9:
                day_str="0"+str(item)
            else:
                day_str=str(item)
            dates.append(str(year)+'-'+month_str+'-'+day_str)
    elif month==2:
        if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0):
            for item in range(1,30):
                if item>=1 and item<=9:
                    day_str="0"+str(item)
                else:
                    day_str=str(item)
                dates.append(str(year)+'-'+month_str+'-'+day_str)
        else:
            for item in range(1,29):
                if item>=1 and item<=9:
                    day_str="0"+str(item)
                else:
                    day_str=str(item)
                dates.append(str(year)+'-'+month_str+'-'+day_str)
    else:
        for item in range(1,31):
            if item>=1 and item<=9:
                day_str="0"+str(item)
            else:
                day_str=str(item)
            dates.append(str(year)+'-'+month_str+'-'+day_str)
    
    print(dates)
    for item in dates:
        file_list = []
        file_list = get_name_in_dir(item)
        file_list_500 = file_list[:500]
        file_list = file_list[500:]
        while len(file_list_500)!=0:
            dates_array = [item for i in range(len(file_list_500))]
            pool = Pool(processes=64) # None 表示自动根据 CPU 核心数设置进程数
            sqls = pool.starmap(analysis, zip(dates_array,file_list_500))
            pool.close() # 关闭进程池，不再接受新的任务
            pool.join() # 等待所有子进程完成
            insert_database(sqls)
            file_list_500 = file_list[:500]
            file_list = file_list[500:]
    mysql_conn.close()
    try:
        process2 = subprocess.Popen(["rm", "-rf", delete_str])
        process2.wait()
    except Exception as e:
        print(e)