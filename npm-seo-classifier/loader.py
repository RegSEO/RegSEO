import codecs
import os
import re
import pandas as pd
import glob
import json
import numpy as np
from urllib.parse import urlparse
from feature import FeatureExtractor
import tarfile

class DataLoader:

    def __init__(self, label_file_path, model, flag):
        # self.data_path = data_path
        self.label_file_path = label_file_path
        self.model = model
        self.flag = flag
        if flag=='black':
            self.dir = 'black_sample_npm'
            self.dir_json = 'black_sample_json'
        else:
            self.dir = 'white_sample_npm'
            self.dir_json = 'white_sample_json'
            
    
    def load_data(self):
        # 读取.xlsx文件 
        label_data = pd.read_excel(self.label_file_path)
        features = []
        labels = []
        true_black = 0
        true_white = 0
        
        for line, label in zip(label_data['name'], label_data['label']):

            line=line.rstrip('\n')
            root_path='/data/black_seo_research/npm_pkg/'
            urlss = []
            
            homepage_sub_domain=''
            repo_url=''
            des_text=''
            name_text=''
            # homepage & repo & name & des
            try:
                json_path = root_path+self.dir+'/'+line
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
                            homepage_sub_domain=''
                            print("tag 1111")
                            print(reason)
            except Exception as reason:
                print("tag 222222")
                print(reason)
            
            
                    
            # 如果无名字就不分类了
            if name_text=='':
                continue
            

                
            # 再读readme
            read_me_text=''
            latin_flag=0
            num_files=0
            try:
                readme_path = root_path+self.dir+'/'+line
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
                            num_files = len(file_list)
                        except Exception as reason:
                            print("tag 33333")
                            num_files=0     
                            print(reason)
                        
                        try:
                            # 获取指定路径文件的File对象
                            file = tar.extractfile(target_file_path)
                            # 读取文件内容
                            read_me_text = file.read().decode("utf-8")
                        except Exception as reason:
                            print("tag 44444")
                            print(reason)
                            latin_flag=1
                            
                        
                        if latin_flag==1:
                            try:
                                # 获取指定路径文件的File对象
                                file = tar.extractfile(target_file_path)
                                # 读取文件内容
                                read_me_text = file.read().decode("Latin-1")
                            except Exception as reason:
                                print("tag 55555")
                                read_me_text=''
                                print(reason)
                    else:
                        read_me_text=''
                        num_files=0
            except Exception as reason:
                print("tag 66666")
                read_me_text=''
                num_files=0
            finally:
                # 如果readme实在是太短了就不分类了(目前认为redme为空则不分类)
                if len(read_me_text.strip())<1:
                    continue
                
            
            # 提取推广链接
            # hrefs = re.findall(r'\[[^]]+\]\(([^)]+)\)', read_me_text)
            # hrefs = list(set(hrefs))
            # for href in hrefs:
            #     if href.startswith('http'):
            #         urlss.append(href)
                    
            # if latin_flag==1:
            #     hrefs = re.findall(r'href=[\'"]?([^\'" >]+)', read_me_text)
            #     hrefs = list(set(hrefs))
            #     for href in hrefs:
            #         if href.startswith('http'):
            #             urlss.append(href)
                        
                        
                        
                
            try:
                text_str = name_text + ' ' + des_text + ' ' +read_me_text
            except Exception as reason:
                print("tag 77777")
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
                tar_json_path = root_path + self.dir_json +'/' +line+'.json'
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
                print("tag 88888")
                print(e)
                user_name=''
                user_email=''
            finally:
                # print("user_name: ",user_name,"  user_email: ",user_email)
                if tar_json_f in locals():
                    tar_json_f.close()
                
            
            if text_str.strip():
                try:
                    
                    extractor = FeatureExtractor(text_str, self.model ,"dir_path",homepage_sub_domain,repo_url,read_me_flag,user_name, user_email,num_files)
                    # urlss = extractor.return_urls
                    features.append(extractor.total_features())
                    if label == 1:
                        print(line,'abuse')
                        labels.append('abuse')
                        true_black = true_black + 1
                    else:
                        labels.append('non-abuse')
                        print(line,'non-abuse')
                        true_white = true_white + 1
                except Exception as e:
                    print("tag 999999")
                    print(e)
                    continue
        print("true_white: ",true_white)
        print("true_black: ",true_black)
                    
                    
                    
        return features, labels