from time import sleep
from lxml import etree
import requests

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


if __name__ == '__main__':
    word = 'site:npmjs.com'
    page = 10  # 页数
    google = GoogleSearch(word, page)
    info = google.start()
    with open('npm.txt', 'a', encoding='utf-8') as f:
        f.write(info)
