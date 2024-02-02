import requests
from db.db_init import DB
import time
from lxml import etree
import sys

db = DB()
npm = db.get_mongo('test')  # .fraud_detection['docker_abuse']
proxies = {
    'http': 'http://127.0.0.1:4780',
    'https': 'http://127.0.0.1:4780'  # https -> http
}


def get_html(pkg_name):
    if pkg_name in done:
        return
    print(pkg_name)
    url = "https://www.npmjs.com/search/suggestions?q=" + pkg_name
    r = requests.get(url)
    for item in r.json():
        npm.insert(item)
    done.add(pkg_name)
    done_file.write(pkg_name + '\n')


def get_user_all_pkg_num(user):
    url = "https://www.npmjs.com/~" + user
    r = requests.get(url)
    # print(url)
    if r.status_code != 200:
        return 0
    tree = etree.HTML(r.text)
    pkgs = tree.xpath('//*[@id="package-tab-packages"]/span/span[1]')
    if len(pkgs) == 0:
        return 0
    count = int(pkgs[0].text)
    done.add(user)
    done_file.write(user + '\n')
    return count


def get_docker_user_all_pkg(user):
    for i in range(500):
        pid = i + 1
        url = "https://hub.docker.com/v2/repositories/" + user + "?page=" + str(
            pid) + "&page_size=25&ordering=last_updated"
        # url = "https://hub.docker.com/v2/repositories/portainer?page=1&page_size=25&ordering=last_updated"
        r = requests.get(url, proxies=proxies)
        print(r.status_code)
        if r.status_code != 200:
            return
        for item in r.json()['results']:
            # print("hhh")
            if item['name'] in done:
                continue
            npm.insert_one(item)
            done.add(item['name'])
            done_file.write(item['name'] + '\n')


def get_docker_users(keywords):
    for i in range(177):
        pid = i + 1
        url = "https://hub.docker.com/api/content/v1/products/search?page_size=25&q=" + keywords + "&page=" + str(pid)
        headers = {
            'authority': 'hub.docker.com',
            'accept': 'application/json',
            'dnt': '1',
            'x-requested-with': 'XMLHttpRequest',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/537.36 \
                (KHTML, like Gecko) Chrome/85.0.4183.121 Safari/537.36',
            'content-type': 'application/json',
            'origin': 'https://hub.docker.com',
            'sec-fetch-site': 'same-origin',
            'sec-fetch-mode': 'cors',
            'sec-fetch-dest': 'empty',
            'referer': f'https://hub.docker.com/search?q=download-free&page={i}',
            'accept-language': 'en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7',
        }
        cookies = {
            "domain": ".docker.com",
            "expirationDate": 1719837499,
            "hostOnly": False,
            "httpOnly": False,
            "name": "OptanonConsent",
            "path": "/",
            "sameSite": "lax",
            "secure": False,
            "session": False,
            "storeId": "0",
            "value": "isGpcEnabled=0&datestamp=Sun+Jul+02+2023+20%3A38%3A19+GMT%2B0800+(%E4%B8%AD%E5%9B%BD%E6%A0%87%E5%87%86%E6%97%B6%E9%97%B4)&version=202209.1.0&isIABGlobal=false&hosts=&consentId=c9297c97-089c-438b-91d8-c382a2bc2b59&interactionCount=1&landingPath=NotLandingPage&groups=C0003%3A1%2CC0001%3A1%2CC0002%3A1%2CC0004%3A1&AwaitingReconsent=false",
            "id": 9
        }
        r = requests.get(url, headers=headers, cookies=cookies)

        if r.status_code != 200:
            return
        for item in r.json()['summaries']:
            print(item)
            name = item['publisher']['name']
            if item['name'] in done:
                continue
            done.add(item['name'])
            done_file.write(item['name'] + '\n')


def get_user_from_docker_html():
    with open('done.html', 'r') as f:
        html = f.read()
    tree = etree.HTML(html)
    for i in range(1, 26):
        user = tree.xpath(f'//*[@id="searchResults"]/div/a[{i}]/div/div/div[2]/div[1]/div/div[2]/p/a')
        if len(user) == 0:
            continue
        users.write(user[0].text + '\n')


# 想提url
def get_docker_pkg_des(namespace, pkg):
    url = "https://hub.docker.com/v2/repositories/" + namespace + '/' + pkg
    r = requests.get(url, proxies=proxies)
    if r.status_code != 200:
        return
    data = r.json()
    if 'full_description' not in data:
        return
    npm.update_one({'name': pkg}, {'$set': {'full_description': data['full_description']}})


if __name__ == "__main__":
    if sys.argv[1] == 'docker':
        with open('done.txt', 'r') as f:
            done = set(f.read().split('\n'))
        done_file = open('done.txt', 'a+')
        users = open('./data/docker_user.txt', 'r')
        # get_docker_user_all_pkg('pretasemfreeg1986')
        # get_docker_users('download-free')
        # get_docker_users('ebookpdf')

        username = set([i.strip() for i in users])
        print(len(username))
        done_users = npm.find({}, {'namespace': 1})
        done_users = set([i['namespace'] for i in done_users])
        print(done_users)
        username = username - done_users
        print(len(username))
        for user in username:
            try:
                get_docker_user_all_pkg(user.strip())
            except:
                print(user)
                time.sleep(120)
        exit()
    elif sys.argv[1] == 'get_docker_user':
        users = open('docker_user_new.txt', 'a+')
        get_user_from_docker_html()
        exit()
    elif sys.argv[1] == 'get_docker_pkg_des':
        pkgs = npm.find({'full_description': {"$exists": False}}, {'namespace': 1, 'name': 1})
        # print(list(pkgs))
        for pkg in pkgs:
            print(pkg)
            get_docker_pkg_des(pkg['namespace'], pkg['name'])
        exit()
    else:
        names = open('uploader.csv', 'r')
        pkgnum = open('pkgnum.csv', 'a+')

        with open('done.txt', 'r') as f:
            done = set(f.read().split('\n'))
        done_file = open('done.txt', 'a+')
        for name in names:
            # part_name = name.split(',')[1].split('-')[:2]
            try:
                #     get_html(part_name[0] + '-' + part_name[1]+'-')
                count = get_user_all_pkg_num(name.split(',')[0])
                print(name.strip() + ',' + str(count))
                same = 1
                if name.split(',')[2] != str(count):
                    same = 0
                pkgnum.write(name.strip() + ',' + str(count) + ',' + str(same) + '\n')
            except Exception as e:
                print(e)
                time.sleep(60)
