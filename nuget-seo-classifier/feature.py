import json
import re
import numpy as np
import pandas as pd
from urllib.parse import urlparse
from db.db_init import get_locale
from db.db_init import DB
from word2vec import TextPreprocessor, TextVectorizer
import pymysql
import random
from collections import Counter
# from context import ContextCrawl


class FeatureExtractor:
    def __init__(self, filename, author, description, license, readme, projectURL, repository, model):
        self.user_ctx_databse = "nuget_ctx"
        self.init_db()

        self.author = author  # author_name
        self.name = filename  # package_name
        self.overview = description
        self.text = filename + description
        self.license = license
        self.readme_tag = readme
        self.projectURL = projectURL
        self.repository = repository
        
        self.model = model
        self.vectorizer = TextVectorizer(model)
        self.keywords = self.get_keywords()
        # self.word_features = self.get_word_features()
        
        # self.file_features = self.get_file_features()
        self.code_features = self.get_code_features()
        self.semantics_features = self.get_plat_semantics_features()  
        self.url_features = self.get_url_features()
        self.license_features = self.get_license_features()
        self.repo_features = self.get_repo_features()
        self.ctx_features = self.get_ctx_features()

    def init_db(self):
        self.mysql_db = pymysql.connect(host='host',
                                        port=6612,
                                        user='user',
                                        password='passwd',
                                        database='db')

    def get_keywords(self):
        processor = TextPreprocessor()
        keywords = processor.get_top_words(self.text)
        print(keywords)
        return keywords

    def total_features(self):
        """
        This function returns a list that includes all features.
        """
        total_features = self.code_features + self.semantics_features + self.url_features + self.license_features + self.repo_features + self.ctx_features
        # total_features = self.url_features + self.repo_features + self.code_features + self.file_features + self.license_features + self.semantics_features + self.ctx_features
        print(total_features)
        return total_features

    # def get_file_features(self):
    #     return [1 / (self.filenums + 1),1 / (self.dirnum + 1)]

    def get_license_features(self):
        return [self.license]
    
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
            download_words_num += self.text.count(word)

        # counts of drug words
        drug_words_num = 0
        for word in drug_words:
            drug_words_num += self.text.count(word)

        # counts of gambling words
        gambling_words_num = 0
        for word in gambling_words:
            gambling_words_num += self.text.count(word)

        word_features = [download_words_num, drug_words_num, gambling_words_num]
        # print(word_features)

        return word_features

    # def get_code_features(self):
    #     # if .md or not
    #     md_flag = 0
    #     if self.overview == '':
    #         return [1, 0]
    #     lines = self.overview.split('\n')
    #     for line in lines:
    #         line = line.strip()
    #         if line.startswith('#') or line.startswith('* ') or line.startswith('>') \
    #                 or '[' in line and ']' in line and '(' in line and ')' in line:
    #             md_flag = 1
    #     # if html tags
    #     html_tags=['</p>', '</li>', '</ol>', '</a>', '</h1>', '</h2>', '</h3>', '</h4>',
    #                '</h5>', '</h6>', '<br>']
    #     for tag in html_tags:
    #         if tag in self.overview:
    #             md_flag = 0
    #     # num of code blocks
    #     if md_flag:
    #         code_blocks = re.findall(r'```.*?```|~~~.*?~~~', self.overview, re.DOTALL)
    #         if len(code_blocks) == 0:
    #             return [1, 1]
    #         return [1, 1 / len(code_blocks)]
    #     return [0, 1]

    def get_code_features(self):
        # # if .md or not
        # md_flag = 0
        # if self.overview == '':
        #     return [1]
        # lines = self.overview.split('\n')
        # for line in lines:
        #     line = line.strip()
        #     if line.startswith('#') or line.startswith('* ') or line.startswith('>') \
        #             or '[' in line and ']' in line and '(' in line and ')' in line:
        #         md_flag = 1
        #         name = self.name +'\n'
        #         with open("md_tag.txt", "a") as file:
        #             file.write(name)

        # # if html tags
        # html_tags=['</p>', '</li>', '</ol>', '</a>', '</h1>', '</h2>', '</h3>', '</h4>',
        #            '</h5>', '</h6>', '<br>']
        # for tag in html_tags:
        #     if tag in self.overview:
        #         md_flag = 0
        #         name = self.name +'\n'
        #         with open("html_tag.txt", "a") as file:
        #             file.write(name)                
        return [self.readme_tag]
        # num of code blocks
        # if md_flag:
        #     code_blocks = re.findall(r'```.*?```|~~~.*?~~~', self.overview, re.DOTALL)
        #     if len(code_blocks) == 0:
        #         return [1]
        #     return [1]

    def get_url_features(self):
        # get urls
        url_pattern = re.compile(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')
        urls = url_pattern.findall(self.text)
        total_urls_num = len(urls)

        # load files
        with open(get_locale("keyword-url"), 'r') as f:
            key = json.load(f)
            internal_urls = key['internal-url']
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

        for url in urls:
            try:
                domain = urlparse(url).netloc
            except ValueError as e:
                print("无效的IPv6地址: ", e)
                continue 
            domains.add(domain)
            sub_domain = ".".join(domain.split('.')[-2:])
            if sub_domain not in internal_urls:
                # if not any(internal in domains for internal in internal_urls):
                external_urls_num += 1
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

        if media_urls_num / (external_urls_num + 1) != 0:
            name = self.name +'\n'
            with open("media_url.txt", "a") as file:
                file.write(name)

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
    
    def get_repo_features(self):
        # load files
        df = pd.read_csv('./db/rank_domain.csv')

        pj_score = 0
        repo_score = 0

        # projectURL
        if self.projectURL != "":
            url = self.projectURL
            try:
                domain = urlparse(url).netloc
                sub_domain = ".".join(domain.split('.')[-2:])
                if sub_domain in df['domain'].values:
                    rank = df[df['domain'] == sub_domain]['rank'].values[0]
                    rank_score = 1 - rank / 1000000
                    pj_score += rank_score
            except ValueError as e:
                print("无效的IPv6地址: ", e) 

        # repository

        if self.repository != "":
            url_pattern = re.compile(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')
            urls = url_pattern.findall(self.repository)

            repo_num = 0

            for url in urls:
                try:
                    domain = urlparse(url).netloc
                    repo_num += 1
                except ValueError as e:
                    print("无效的IPv6地址: ", e)
                    continue 
                sub_domain = ".".join(domain.split('.')[-2:])
                if sub_domain in df['domain'].values:
                    rank = df[df['domain'] == sub_domain]['rank'].values[0]
                    rank_score = 1 - rank / 1000000
                    repo_score += rank_score
            
            if repo_num != 0:
                repo_score = repo_score / repo_num

        score = (pj_score + repo_score) / 2

        repo_features = [score]

        return repo_features

    def get_ibt_semantics_features(self):
        with open(get_locale("keyword-ibt"), 'r') as f:
            key = json.load(f)
            ibtwords = key['ibt']

        ibt_similarites = self.vectorizer.get_min_distances(self.keywords, ibtwords)
        print("similarites:")
        print(ibt_similarites)

        if len(ibt_similarites) == 0:
            return [1, 1, 1]

        ibt_semantics_features = [min(ibt_similarites), max(ibt_similarites),
                                  sum(ibt_similarites) / len(ibt_similarites)]
        return ibt_semantics_features

    def get_plat_semantics_features(self):
        with open(get_locale("keyword-plat"), 'r') as f:
            key = json.load(f)
            platwords = key['nuget']

        plat_semantics_features = self.vectorizer.get_average_distances(self.keywords, platwords)
        print("differences:")
        print(plat_semantics_features)

        if len(plat_semantics_features) == 0:
            return [1,1,1,1,1,1,1,1,1,1]
        
        while len(plat_semantics_features) < 10:
            random_elements = random.sample(plat_semantics_features, min(10 - len(plat_semantics_features), len(plat_semantics_features)))
            plat_semantics_features.extend(random_elements)
        
        return plat_semantics_features

    # def get_ctx_features(self):
    #     current_features = self.url_features + self.code_features + self.file_features + self.license_features + self.semantics_features
    #     db = DB()
    #     coll = db.get_mongo('ctx')
    #     doc = coll.find_one({"namespace": self.author})
    #     if not doc:
    #         ctx_features = current_features
    #         doc = {"namespace": self.author, "last1": current_features, "last2": None}
    #         coll.insert_one(doc)
    #     else:
    #         if doc.get("last2") is None:
    #             ctx_features = doc.get("last1")
    #         else:
    #             ctx_features = [0.6*x + 0.4*y for x, y in zip(doc.get("last1"), doc.get("last2"))]
    #         coll.update_one(
    #             {"namespace": self.author},
    #             {"$set": {"last2": doc["last1"], "last1": current_features}}
    #         )
    #     return ctx_features

    def get_ctx_features(self):
        current_features = self.url_features + self.repo_features + self.code_features + self.file_features + self.license_features + self.semantics_features
        ctx_features = current_features
        author = self.author
        if author == "" or author is None:
            return current_features
        cursor = self.mysql_db.cursor()
        get_sql = "select last_1,last_2 from black_seo." + self.user_ctx_databse + " where author = '" + author + "';"
        try:
            cursor.execute(get_sql)
            results = cursor.fetchall()
            if len(results) == 0:
                str_ctx_feature = ','.join(str(x) for x in current_features)
                insert_sql = "insert into black_seo." + self.user_ctx_databse + " (author,last_1) values ('" + author + "','" + str_ctx_feature + "');"
                cursor.execute(insert_sql)
                # 提交到数据库执行
                self.mysql_db.commit()
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
                    ctx_features = [0.6 * float(x.strip()) + 0.4 * float(y.strip()) for x, y in
                                    zip(temp_features_1, temp_features_2)]
                str_ctx_feature = ','.join(str(x) for x in current_features)
                update_sql = "update black_seo." + self.user_ctx_databse + " set last_1 = '" + str_ctx_feature + "', last_2 = '" + \
                                results[0][0] + "' where author = '" + author + "';"
                cursor.execute(update_sql)
            # 提交到数据库执行
            self.mysql_db.commit()
        except Exception as e:
            print(e)
            self.mysql_db.rollback()
        finally:
            self.mysql_db.close()
        return ctx_features

    def feature_normalize(self, features, fetures_array=None):
        features_array = np.array(features)
        if (features_array.max(0) != features_array.min(0)).all():
            features_norm = (features_array - fetures_array.min(0)) / features_array.ptp(0)
        else:
            features_norm = features_array
        # features_norm = (features_array - features_array.min(0)) / features_array.ptp(0)
        # print(features_norm.tolist())
        return features_norm.tolist()