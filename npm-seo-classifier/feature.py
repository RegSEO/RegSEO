import json
import re
import os
import numpy as np
from urllib.parse import urlparse
from db.db_init import get_locale
import pandas as pd
from word2vec import TextPreprocessor, TextVectorizer
import pymysql
import time
import requests
import random
from hashlib import md5
import hashlib
from langdetect import detect_langs
from langdetect import DetectorFactory
from collections import Counter


class FeatureExtractor:
    def __init__(self, text, model, path, homepage_sub_domain,repo_path,read_me_flag,user_name,user_email):
        self.user_ctx_databse="user_ctx"
        try:
            self.text_trans = self.translate_baidu(text)
        except Exception as e:
            print(e)
            self.text_trans = text  
        self.return_urls = []
        self.text = text
        self.model = model
        self.overview = text
        self._external_urls_num = 0
        self._media_urls_num = 0
        self._external_domains_num = 0
        self.user_name = user_name
        self.user_email = user_email
        self.read_me_flag = read_me_flag
        self.init_db()
        self.keywords = self.get_keywords()
        self.word_features = self.get_word_features()
        
        # self.path_features = self.get_path_features(path) # 文件的数量
        self.code_feature = self.get_code_features() # 代码段的数量
        self.semantics_features = self.get_plat_semantics_features()
        self.url_features = self.get_url_features(homepage_sub_domain)
        self.repo_homepage_feature = self.get_repo_homepage_feature(homepage_sub_domain,repo_path)
        self.email_rank_feature = self.get_email_rank_feature(user_email)
        self.total_exec_features = self.get_total_exec_features()
        self.user_ctx_features = self.get_user_ctx_features(user_name,user_email)


    def init_db(self):
        self.mysql_conn = pymysql.connect(host='host',
                            port=6612,
                            user='user',
                            password='passwd',
                            database='db')
        
        self.cursor = self.mysql_conn.cursor()
        
    def get_keywords(self):
        processor = TextPreprocessor()
        keywords = processor.get_top_words(self.text_trans)
        # print(keywords)
        return keywords


    def get_user_ctx_features(self,user_name,user_email):
        ctx_features = self.total_exec_features
        if user_name=="" or user_name is None:
            return ctx_features
        get_sql = "select last_1,last_2 from black_seo."+ self.user_ctx_databse +" where user_name = '"+user_name+"';"
        try:
            self.cursor.execute(get_sql)
            results = self.cursor.fetchall()
            if len(results)==0:
                str_ctx_feature = ','.join(str(x) for x in ctx_features)
                insert_sql="insert into black_seo."+ self.user_ctx_databse +" (user_name,user_email,last_1) values ('"+user_name+"','"+user_email+"','"+str_ctx_feature+"');"
                self.cursor.execute(insert_sql)
                # 提交到数据库执行
                self.mysql_conn.commit()
            else:
                if results[0][1] is None:
                    temp_features = results[0][0].lstrip('[').rstrip(']').split(',')
                    ctx_features = []
                    for item in temp_features:
                        ctx_features.append(float(item.strip()))
                else:
                    temp_features_1 = results[0][0].lstrip('[').rstrip(']').split(',')
                    temp_features_2 = results[0][1].lstrip('[').rstrip(']').split(',')
                    ctx_features = []
                    ctx_features = [0.6*float(x.strip()) + 0.4*float(y.strip()) for x, y in zip(temp_features_1, temp_features_2)]
                str_ctx_feature = ','.join(str(x) for x in self.total_exec_features)
                update_sql = "update black_seo."+ self.user_ctx_databse +" set last_1 = '"+str_ctx_feature+"', last_2 = '"+results[0][0]+"' where user_name = '"+user_name+"';"
                self.cursor.execute(update_sql)
                # 提交到数据库执行
                self.mysql_conn.commit()
        except Exception as e:
            print(e)
            self.mysql_conn.rollback()
            ctx_features = self.total_exec_features
        finally:
            self.mysql_conn.close()
        return ctx_features
        
                
        
    
    def total_features(self):
        return self.total_exec_features + self.user_ctx_features
        
    def get_total_exec_features(self):
        total_features = self.code_feature + self.semantics_features + self.url_features + self.repo_homepage_feature + self.email_rank_feature + [self.read_me_flag]
        return total_features

    def get_word_features(self):
        """
        This function extracts * features:
        - Feature 1: counts of download words in the text
        - Feature 2: counts of drug words in the text
        - Feature 3: ...
        """
        with open(get_locale("keyword-word"), 'r') as f:
            key = json.load(f)
            download_words = key['download']
            drug_words = key['drug']
            gambling_words = key['gambling']

        # counts of download words
        download_words_num = 0
        for word in download_words:
            download_words_num += self.text_trans.count(word)

        # counts of drug words
        drug_words_num = 0
        for word in drug_words:
            drug_words_num += self.text_trans.count(word)

        # counts of gambling words
        gambling_words_num = 0
        for word in gambling_words:
            gambling_words_num += self.text_trans.count(word)

        word_features = [download_words_num, drug_words_num, gambling_words_num]
        # print(word_features)

        return word_features

    def get_ibt_semantics_features(self):
        with open(get_locale("keyword-ibt"), 'r') as f:
            key = json.load(f)
            ibtwords = key['ibt']

        vectorizer = TextVectorizer(self.model)
        ibt_similarites = vectorizer.get_min_distances(self.keywords, ibtwords)
        # print("similarites:")
        # print(ibt_similarites)

        if len(ibt_similarites) == 0:
            return [1, 1, 1]

        ibt_semantics_features = [min(ibt_similarites), max(ibt_similarites), sum(ibt_similarites) / len(ibt_similarites)]
        return ibt_semantics_features

    def get_plat_semantics_features(self):
        with open(get_locale("keyword-plat"), 'r') as f:
            key = json.load(f)
            # platwords = key['docker']
            platwords = key['npm']

        plat_semantics_features = self.vectorizer.get_average_distances(self.keywords, platwords)
        print("differences:")
        print(plat_semantics_features)

        if len(plat_semantics_features) == 0:
            return [1,1,1,1,1,1,1,1,1,1]
        
        while len(plat_semantics_features) < 10:
            random_elements = random.sample(plat_semantics_features, min(10 - len(plat_semantics_features), len(plat_semantics_features)))
            plat_semantics_features.extend(random_elements)
        return plat_semantics_features

    def feature_normalize(self, features):
        features_array = np.array(features)
        if (features_array.max(0) != features_array.min(0)).all():
            features_norm = (features_array - features_array.min(0)) / features_array.ptp(0)
        else:
            features_norm = features_array
        # features_norm = (features_array - features_array.min(0)) / features_array.ptp(0)
        # print(features_norm.tolist())
        return features_norm.tolist()


    # def get_path_features(self,path):
    #     path_feature = []
    #     if self.num_files<=1:
    #         path_feature.append(1)
    #     else:
    #         path_feature.append(2/self.num_files)
    #     if self.num_dir<=1:
    #         path_feature.append(1)
    #     else:
    #         path_feature.append(2/self.num_dir)
    #     return path_feature
        
    def get_code_features(self):
        code_blocks = re.findall(r'```.*?```|~~~.*?~~~', self.overview, re.DOTALL)
        if len(code_blocks) == 0:
            return [1]
        return [1 / len(code_blocks)]

    def get_url_features(self,homepage_sub_domain):
        # get urls
        url_pattern = re.compile(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')
        urls = url_pattern.findall(self.text)
        self.return_urls = urls
        total_urls_num = len(urls)

        # load files
        with open(get_locale("keyword-url"), 'r') as f:
            key = json.load(f)
            internal_urls = key['internal-url']
            if homepage_sub_domain!='' and homepage_sub_domain!=None:
                internal_urls.append(homepage_sub_domain)
            short_urls = key['short-url']

        with open(get_locale("keyword-media"), 'r') as f:
            key = json.load(f)
            media_suffix = key['image']  # get media suffix

        df = pd.read_csv('./db/rank_domain.csv')

        # counts of domains, external urls and short urls
        domains_num = 0
        external_urls_num = 0
        short_urls_num = 0
        media_urls_num = 0
        external_score = 0
        domains = set()
        external_domains = set()

        for url in urls:
            try:
                domain = urlparse(url).netloc
            except ValueError as e:
                # 如果解析出现ValueError错误，执行以下操作
                print("无效的IPv6地址: ", e)
                continue  # 跳过当前循环，继续执行下一个迭代
            domains.add(domain)
            sub_domain = ".".join(domain.split('.')[-2:])
            if sub_domain not in internal_urls:
                # if not any(internal in domains for internal in internal_urls):
                external_urls_num += 1
                external_domains.add(sub_domain)
                for suffix in media_suffix:
                    if url.endswith(suffix):
                        media_urls_num += 1
                if sub_domain in df['domain'].values:
                    rank = df[df['domain'] == sub_domain]['rank'].values[0]
                    rank_score = 1 - rank / 1000000
                    external_score += rank_score
            if sub_domain in short_urls:
                # if any(short in domains for short in short_urls):
                short_urls_num += 1

        domains_num = len(domains)  # 不同的域名
        external_domains_num = len(external_domains)


        self._external_urls_num = external_urls_num
        self._media_urls_num = media_urls_num
        self._external_domains_num = external_domains_num
        
        # 统计重复的url
        element_count = Counter(urls)
        count_of_duplicates_url = sum(1 for count in element_count.values() if count > 1)

        # url_features = [domains_num, external_urls_num, short_urls_num]
        url_features = [external_urls_num / (total_urls_num + 1),
                        short_urls_num / (total_urls_num + 1),
                        1 / (domains_num + 1),
                        external_score / (external_urls_num + 1),
                        1 / (count_of_duplicates_url + 1)]

        return url_features
    
    def get_repo_homepage_feature(self,homepage_sub_domain,repo_path):
        if homepage_sub_domain=='' and repo_path=='':
            return [0,0]
        else:
            if homepage_sub_domain!='':
                df = pd.read_csv('./db/rank_domain.csv')
                if homepage_sub_domain in df['domain'].values:
                    rank = df[df['domain'] == homepage_sub_domain]['rank'].values[0]
                    rank_score = 1 - rank / 1000000
                else:
                    rank_score = 0
                if repo_path=='':
                    return [0,rank_score]
                else:
                    return [1,rank_score]
            else:
                return [1,0]
            
    def get_email_rank_feature(self,email):
        if email==None or email=='':
            return [0]
        else:
            df = pd.read_csv('./db/rank_domain.csv')
            pattern = r'@(.+)$'
            match = re.search(pattern, email)
            if match:
                email_sub_domain = match.group(1)
            else:
                return [0]
            if email_sub_domain in df['domain'].values:
                rank = df[df['domain'] == email_sub_domain]['rank'].values[0]
                rank_score = 1 - rank / 1000000
            else:
                rank_score = 0
            return [rank_score]
        
    def translate_baidu(self, text):
        DetectorFactory.seed = 0
        en_flag = 0
        lang_results = detect_langs(text)
        for result in lang_results:
            if result.lang == 'en' and result.prob > 0.8:
                en_flag = 1
        if en_flag == 1:
            return text
        else:
            appid = "appid"
            key = "key"
            url = "http://api.fanyi.baidu.com/api/trans/vip/translate?q="
            salt = str(time.time())
            regex = r"[^\w\s]"
            text = re.sub(regex, "", text)
            str1 = appid + text + salt + key
            # print(str)
            sign = hashlib.md5(str1.encode('utf-8')).hexdigest()
            query = url + text + "&from=auto" + "&to=en" + "&appid=" + appid + "&salt=" + salt + "&sign=" + sign
            response = requests.get(query)
            # print(response.text)
            list = response.json()["trans_result"]
            trans = ""
            for text in list:
                trans += text["dst"]
            # print(trans)
            return trans.lower()