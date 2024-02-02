import json
import re
import numpy as np
import pandas as pd
from urllib.parse import urlparse
from db.db_init import get_locale
from db.db_init import DB
from word2vec import TextPreprocessor, TextVectorizer
import random
# from context import ContextCrawl
from collections import Counter


class FeatureExtractor:
    def __init__(self, doc, model):
        self.author = doc['namespace']  # author_name
        self.name = doc['name']  # package_name
        self.overview = ''
        self.pull_count = 0
        if doc and "name" in doc:
            self.text = doc["name"]
            if "description" in doc and doc["description"] is not None:
                self.text += ' ' + doc["description"]
            if "full_description" in doc and doc["full_description"] is not None:
                self.text += ' ' + doc["full_description"]
                self.overview = doc["full_description"]
            if "pull_count" in doc and doc["pull_count"] is not None:
                self.pull_count = doc["pull_count"]
        self.model = model
        self.vectorizer = TextVectorizer(model)
        self.keywords = self.get_keywords()
        # self.word_features = self.get_word_features()
        self.code_features = self.get_code_features()
        self.semantics_features = self.get_plat_semantics_features()
        self.url_features = self.get_url_features()
        self.ctx_features = self.get_ctx_features()
        self.metadata_features = self.get_metadata_features()


    def get_metadata_features(self):
        return [1 / (self.pull_count + 1)]
        
    def get_keywords(self):
        processor = TextPreprocessor()
        keywords = processor.get_top_words(self.text)
        print(keywords)
        return keywords

    def total_features(self):
        """
        This function returns a list that includes all features.
        """
        total_features = self.code_features + self.semantics_features + self.url_features + self.ctx_features + self.metadata_features
        print(total_features)
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

    def get_code_features(self):
        # if .md or not
        md_flag = 0
        if self.overview == '':
            return [1, 0]
        lines = self.overview.split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith('#') or line.startswith('* ') or line.startswith('>') \
                    or '[' in line and ']' in line and '(' in line and ')' in line:
                md_flag = 1
        # if html tags
        html_tags=['</p>', '</li>', '</ol>', '</a>', '</h1>', '</h2>', '</h3>', '</h4>',
                   '</h5>', '</h6>', '<br>']
        for tag in html_tags:
            if tag in self.overview:
                md_flag = 0
        # num of code blocks
        if md_flag:
            code_blocks = re.findall(r'```.*?```|~~~.*?~~~', self.overview, re.DOTALL)
            if len(code_blocks) == 0:
                return [1, 1]
            return [1, 1 / len(code_blocks)]
        return [0, 1]

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
        # 统计重复的url
        element_count = Counter(urls)
        count_of_duplicates_url = sum(1 for count in element_count.values() if count > 1)

        # url_features = [domains_num, external_urls_num, short_urls_num]
        url_features = [external_urls_num / (total_urls_num + 1),
                        short_urls_num / (total_urls_num + 1),
                        1 / (domains_num + 1),
                        external_score / (external_urls_num + 1),
                        1 / (count_of_duplicates_url + 1)]
        # print(url_features)

        return url_features

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
            platwords = key['docker']

        plat_semantics_features = self.vectorizer.get_average_distances(self.keywords, platwords)
        print("differences:")
        print(plat_semantics_features)

        if len(plat_semantics_features) == 0:
            return [1,1,1,1,1,1,1,1,1,1]
        
        while len(plat_semantics_features) < 10:
            random_elements = random.sample(plat_semantics_features, min(10 - len(plat_semantics_features), len(plat_semantics_features)))
            plat_semantics_features.extend(random_elements)
        return plat_semantics_features

    def get_ctx_features(self):
        current_features = self.url_features + self.code_features + self.semantics_features
        db = DB()
        coll = db.get_mongo('ctx')
        doc = coll.find_one({"namespace": self.author})
        if not doc:
            ctx_features = current_features
            doc = {"namespace": self.author, "last1": current_features, "last2": None}
            coll.insert_one(doc)
        else:
            if doc.get("last2") is None:
                ctx_features = doc.get("last1")
            else:
                ctx_features = [0.6*x + 0.4*y for x, y in zip(doc.get("last1"), doc.get("last2"))]
            coll.update_one(
                {"namespace": self.author},
                {"$set": {"last2": doc["last1"], "last1": current_features}}
            )
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