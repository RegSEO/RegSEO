      
import requests
from datetime import datetime,timedelta
import time
from dateutil.parser import isoparse
import json

PACKAGE_STATUS_UNLIST = 0
PACKAGE_STATUS_NORMAL = 1
DOWNLOAD_STATUS_PENDING_DOWNLOAD = 0

def sync_nuget_changes():
    # 开始时间和结束时间
    last_update_time = __reformat_nuget_date('2023-05-20T00:00:00.0000000Z').timestamp()
    to_time = __reformat_nuget_date('2023-05-20T23:59:59.9999999Z').timestamp()

    savepath = 'pkg/2023_5_20.txt'

    # step 1: 获取所有pages
    pages = __get_catalog_pages()
    for page in pages:
        page_time = __reformat_nuget_date(page['commitTimeStamp']).timestamp()
        if page_time < last_update_time or page_time > to_time:
            continue
        page_url = page['@id']
        print(f'should update  {page_url}\t' + page['commitTimeStamp'])
        actions = __get_catalog_page_detail(page_url)
        for action in actions:
            # 解析每次action
            parse_nuget_pkg_version(action['@id'],savepath)

def parse_nuget_pkg_version(pkg_version_link,savepath):
    # 获取某一特定version的详情，例如：https://api.nuget.org/v3/catalog0/data/2016.04.10.01.57.40/forerunnersdk.4.0.465.json
    pkg_version_link = pkg_version_link.replace('https://api.nuget.org/','https://globalcdn.nuget.org/')
    pkg_version = {}
    try:
        with requests.get(pkg_version_link, timeout=60) as r:
            
            r.raise_for_status()
            
            pkg_info = r.json()
            downloads = []
            if pkg_info.get('packageEntries') is not None:
                for entry in pkg_info['packageEntries']:
                    download_info = {}
                    download_info['name'] = entry['fullName']
                    download_info['url'] = entry['@id']
                    downloads.append(download_info)
            pkg_version['download_info'] = downloads
            pkg_version['language'] = 'cSharp'
            pkg_version['source'] = 'official'
            pkg_version['package_name'] = pkg_info['id']
            pkg_version['version'] = pkg_info['version']
            if not pkg_info.get('listed'):
                pkg_version['status'] = PACKAGE_STATUS_UNLIST
            else:
                pkg_version['status'] = PACKAGE_STATUS_NORMAL

            pkg_version['download_status'] = DOWNLOAD_STATUS_PENDING_DOWNLOAD
            pkg_version['publish_time'] = pkg_info['created']  # 用created而不是Published，因为后者在unlist时会归零
            pkg_version['metadata'] = pkg_info

        # 由数据库操作替换
        with open(savepath,'a+') as fw:
            fw.write(json.dumps(pkg_version)+'\n')  
        ###
            
    except Exception as e:
        print(e)
        pass


def __get_catalog_service():
    # 这里存的是Catalog的入口url
    # change api -> globalcdn
    url = "https://api.nuget.org/v3/index.json"
    url = url.replace('https://api.nuget.org/','https://globalcdn.nuget.org/')
    with requests.get(url, timeout=60) as r:
        r.raise_for_status()
        service_list = r.json()
        for service in service_list['resources']:
            if service['@type'] == 'Catalog/3.0.0':
                return service['@id']


def __get_catalog_pages():
    # 这里存了所有的page：https://api.nuget.org/v3/catalog0/index.json
    catalog_url = __get_catalog_service()
    catalog_url = catalog_url.replace('https://api.nuget.org/','https://globalcdn.nuget.org/')
    with requests.get(catalog_url, timeout=60) as r:
        r.raise_for_status()
        page_list = r.json()
        return page_list['items']


def __get_catalog_page_detail(page_url):
    while True:
        try:
            # 这里存了该page下所有的action，例如：https://api.nuget.org/v3/catalog0/page1553.json
            page_url = page_url.replace('https://api.nuget.org/','https://globalcdn.nuget.org/')
            with requests.get(page_url, timeout=60) as r:
                r.raise_for_status()
                page_list = r.json()
                return page_list['items']
        except requests.exceptions.ProxyError as e:
            print(
                f'func: get_catalog_page_detail , {e}, sleep 60s and try to reconnect...')
            time.sleep(60)


def __reformat_nuget_date(d):
    return datetime.fromisoformat(isoparse(d).strftime('%Y-%m-%dT%H:%M:%S'))

def main():
    sync_nuget_changes()

if __name__ == '__main__':
    main()
