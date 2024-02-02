import codecs
import os
import pandas as pd
import glob
import numpy as np
from feature import FeatureExtractor
from db.db_init import DB
from bson.objectid import ObjectId


class DataLoader:
    """
    This class is responsible for loading features and labels from raw data sources.
    """

    def __init__(self, label_file_path, db: DB, model):
        # self.data_path = data_path
        self.label_file_path = label_file_path
        self.db = db
        self.model = model

    def load_data(self, mode='test'):
        # 读取.xlsx文件
        label_data = pd.read_excel(self.label_file_path)

        if mode == 'train':
            coll = self.db.get_mongo('train')
        elif mode == 'test':
            coll = self.db.get_mongo('test')
        elif mode == 'black':
            coll = self.db.get_mongo('black')
        elif mode == 'white':
            coll = self.db.get_mongo('white')
        else:
            raise ValueError('Invalid mode')
        # coll = self.db.get_mongo()

        features = []
        labels = []

        for id, label in zip(label_data['_id'], label_data['label']):
            # 在数据库中查询该名称文档的'name'，'description', 'full_description'
            # text = coll.find_one({"name": name}, {"name": 1, "description": 1, "full_description": 1})
            doc = coll.find_one({"_id": ObjectId(id)})
            # print(id)
            extractor = FeatureExtractor(doc, self.model)
            features.append(extractor.total_features())
            if label == 1:
                labels.append('abuse')
            else:
                labels.append('non-abuse')

            # author = doc['namespace']
            # name = doc['name']
            # 如果text存在，进行键值判断和拼接
            # if doc and "name" in doc:
            #     text_str = doc["name"]
            #     if "description" in doc and doc["description"] is not None:
            #         text_str += ' ' + doc["description"]
            #     if "full_description" in doc and doc["full_description"] is not None:
            #         text_str += ' ' + doc["full_description"]
            #     # 确保拼接后的文本非空再提取特征
            #     if text_str.strip():
            #         # 提取特征
            #         extractor = FeatureExtractor(doc, self.model)
            #         features.append(extractor.total_features())
            #         if label == 1:
            #             labels.append('abuse')
            #         else:
            #             labels.append('non-abuse')

        self.db.close_mongo()

        # features_norm = extractor.feature_normalize(features)

        return features, labels

    def load_data_nuget(self):
        # 读取.xlsx文件
        # 读取表格数据，假设文件名为data.xlsx
        data = pd.read_excel('./data/nuget.xlsx')

        column1_data = data.iloc[:, 0]
        # print(type(column1_data))
        column3_data = data.iloc[:, 2]
        text_data = column1_data + column3_data
        label_data = data.iloc[:, 4]

        features = []
        labels = []

        for text, label in zip(text_data, label_data):
            # print(text)
            # print(label)
            extractor = FeatureExtractor(text, self.model)
            features.append(extractor.total_features())
            if label == 1:
                labels.append('abuse')
            else:
                labels.append('non-abuse')

        features_norm = extractor.feature_normalize(features)

        return features_norm, labels

    def load_data_npm(self, mode='npm'):
        # 读取.xlsx文件
        label_data = pd.read_excel(self.label_file_path)
        coll = self.db.get_mongo('npm')

        features = []
        labels = []

        for name, label in zip(label_data['name'], label_data['label']):
            # 在数据库中查询该名称文档的'name'，'description', 'full_description'
            text = coll.find_one({"name": name}, {"name": 1, "readme": 1})
            # 如果text存在，进行键值判断和拼接
            if text and "name" in text:
                text_str = text["name"]
                if "readme" in text:
                    text_str += ' ' + text["readme"]
                # 确保拼接后的文本非空再提取特征
                if text_str.strip():
                    # 提取特征
                    extractor = FeatureExtractor(text_str, self.model)
                    features.append(extractor.total_features())
                    if label == 1:
                        labels.append('abuse')
                    else:
                        labels.append('non-abuse')

        self.db.close_mongo()

        features_norm = extractor.feature_normalize(features)

        return features_norm, labels


    def load_data_3(self):
        # 读取.xlsx文件
        tag_data = pd.read_excel(self.label_file_path)
        tag_dict = dict(zip(tag_data.name, tag_data.tag))

        # 获取所有.md文件的路径
        folders = ['p2pshnik', 'non_p2pshnik', 'case', 'normal']

        features = []
        labels = []

        for folder in folders:
            # 在路径模式中使用**来表示任何文件和任意多级的子文件夹
            md_files = glob.glob('./package/{0}/**/*.md'.format(folder), recursive=True)

            for file in md_files:
                with codecs.open(file, 'r', 'utf-8') as f:
                    text = f.read()
                    extractor = FeatureExtractor(text)
                    features.append(extractor.total_features())

                file_dir = os.path.dirname(file)
                dir_name = file_dir.split("\\")[1]
                print(dir_name)

                if tag_dict[os.path.basename(dir_name)] == 1:
                    labels.append('abuse')
                else:
                    labels.append('non-abuse')

        features_norm = extractor.feature_normalize(features)

        return features_norm, labels

        '''
        for name, label in zip(label_data['name'], label_data['label']):
            # 在数据库中查询该名称的文档
            text = coll.find_one({"name": name}, {"full_description": 1})
            # print(text)
            if text and "full_description" in text:
                # 提取特征
                extractor = FeatureExtractor(text["full_description"])
                features.append(extractor.total_features())
                if label == 1:
                    labels.append('abuse')
                else:
                    labels.append('non-abuse')
        '''
