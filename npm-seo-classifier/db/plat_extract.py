import json
import re
from time import sleep

import nltk
import requests
import wikipedia
from bs4 import BeautifulSoup
from lxml import etree
from nltk.tokenize import word_tokenize
from gensim.parsing.preprocessing import STOPWORDS
from pygoogletranslation import Translator

from db.bing import BingSearch
from db.db_init import get_locale

proxies = {
    'http': 'http://127.0.0.1:4780',
    'https': 'http://127.0.0.1:4780'  # https -> http
}

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36',
    'cookie': 'CONSENT=PENDING+551; SOCS=CAISHwgBEhJnd3NfMjAyMjExMzAtMF9SQzIaBXpoLUNOIAEaBgiA3tmcBg; AEC=Ad49MVFNHe5k2XMDJ5NF-JiDfxXZe1bkx47D8z536ZytRZQIG2oI7Bzqtgo; OTZ=7125642_24_24__24_; 1P_JAR=2023-07-21-03; GOOGLE_ABUSE_EXEMPTION=ID=d1c9ed33a5425456:TM=1689910444:C=r:IP=104.28.211.105-:S=qpMWfoQTxOh2651_pZpGdfE; DV=89xOZpsPdMgQMMNiN6YW-gbkbjBolxg; NID=511=D_LfxdocmquIlp3oCpAvhuHFfRJOZl-GgqxEDfzxSCtWEuTBsB5hku__78oYy0N8eJ6YfpI-3bFkLHyT59beFvNJFXcReVijQn4hpA3iqDdFafgYiEPCAoEyoCiRVPqF7IGA2RGcTwFkD2ty6DHGbLkv14xQ1s6rDqCSUd0q7FvjQ795vdMQijFE3ne8yA-stRC11TEBYwHo3D4DhrNVpFuM_Ub8gRjUd42fryEamCp4HjUj'
}


class GoogleSearch:
    # need to verify
    def __init__(self, word, max_page=10):
        self.word = word
        self.sum = 0
        self.max_page = max_page
        pass

    def request_url(self, url):
        while True:
            try:
                res = requests.get(url=url, headers=headers, proxies=proxies).text
                break
            except:
                sleep(1)
                print('error')
                continue
        return res

    def parse_text(self, res):
        text = res.split(r",'[\x22https://")
        # print(text)
        text_data = []
        for row in text:
            if r'\x22,1,\x22zh\x22,\x22JP\x22,null' not in row:
                continue
            else:
                data = row.split(r'\x22,1,\x22zh\x22,\x22JP\x22,null')[0]
                data = data.split(r'\x22,\x22')
                del data[0]
                text_data.append(''.join(data))
        return text_data

    def next_url(self, res):
        tree = etree.HTML(res)
        return tree.xpath('//a[@id="pnnext"]/@href')

    def start(self):
        google_info = ''
        url = f'https://www.google.com/search?q={self.word}'
        page = 1
        while page <= self.max_page:
            res = self.request_url(url)
            data = self.parse_text(res)
            for info in data:
                print(info)
                google_info += info
                google_info += '\n'
                self.sum += 1
            print('一共爬取', self.sum, '条数据')
            print(f'第{page}页采集完成')
            page += 1
            new_url = self.next_url(res)
            if new_url:
                url = 'https://www.google.com' + new_url[0]
                sleep(5)
            else:
                break
        return google_info


class PlatInfoCollector:
    def __init__(self, plat):
        self.plat = plat
        self.wikipedia_info = self.get_wikipedia_info()
        self.google_info = self.get_google_info()
        self.bing_info = self.get_bing_info()

    def get_plat_info(self):
        plat_info = self.wikipedia_info + self.google_info + self.bing_info
        # plat_info = self.google_info
        filename = self.plat + ".txt"
        with open(filename, 'w', encoding='utf-8') as file:
            file.write(plat_info)
        return plat_info

    def get_wikipedia_info(self):
        wiki_list = wikipedia.search(self.plat)
        print(wiki_list)
        count = 0
        wikipedia_info = ''
        for title in wiki_list:
            try:
                # print(title)
                wikipedia_info += wikipedia.page(title).summary
                count = count + 1
            except Exception as e:
                # print(de.options)
                continue
            if count == 2:
                break
        return wikipedia_info

    def get_google_info(self):
        google = GoogleSearch(self.plat, 10)
        google_info = google.start()
        return google_info

    def get_bing_info(self):
        bing = BingSearch(self.plat, 10)
        bing_info = bing.start()
        return bing_info


class KeyExtractor:
    def __init__(self):
        self.translator = Translator(proxies=proxies)
        self.stopwords = set(STOPWORDS)
        with open(get_locale("new-stopword"), 'r') as f:
            new_data = json.load(f)
        self.stopwords.update(new_data['stopword'])

    def translate(self, text):
        translation = self.translator.translate(text, dest='en')
        return translation.text

    def tokenize_text(self, text):
        # text = self.translate(text)
        tokens = word_tokenize(text.lower())
        # delete symbols
        tokens = [token for token in tokens if token.isalpha()]
        # delete stopwords
        tokens = [token for token in tokens if token not in self.stopwords]
        # POS
        tagged_words = nltk.pos_tag(tokens)
        filtered_tokens = [word for (word, pos) in tagged_words if pos.startswith('N') or pos.startswith('V')]
        return filtered_tokens

    def get_top_words(self, text, num_words=20):
        tokens = self.tokenize_text(text)
        word_frequencies = {}
        for token in tokens:
            if token not in word_frequencies:
                word_frequencies[token] = 0
            word_frequencies[token] += 1
        sorted_words = sorted(word_frequencies.items(), key=lambda x: x[1], reverse=True)
        top_words = [word for word, _ in sorted_words[:num_words]]
        return top_words


if __name__ == "__main__":
    # plat = "npm"
    # collector = PlatInfoCollector(plat)
    # plat_info = collector.get_plat_info()
    with open("npm.txt", 'r', encoding='utf-8') as file:
        plat_info = file.read()
    extractor = KeyExtractor()
    keywords = extractor.get_top_words(plat_info)
    with open("keyword-plat.json", 'r', encoding='utf-8') as file:
        json_data = json.load(file)
    json_data["npm"] = keywords
    with open("keyword-plat.json", 'w', encoding='utf-8') as file:
        json.dump(json_data, file, indent=2)

