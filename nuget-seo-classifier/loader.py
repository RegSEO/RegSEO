import codecs
import os
import pandas as pd
import glob
import numpy as np
from feature import FeatureExtractor
from db.db_init import DB
from bson.objectid import ObjectId
from prefile_training import FilePreprocessor


class DataLoader:
    """
    This class is responsible for loading features and labels from raw data sources.
    """

    def __init__(self, label_file_path, model):
        # self.data_path = data_path
        self.label_file_path = label_file_path
        self.model = model

    def load_data_nuget(self):
        data = pd.read_csv(self.label_file_path)
        filename_data = data.iloc[:, 0]
        label_data = data.iloc[:, 1]

        features = []
        labels = []

        for filename, label in zip(filename_data, label_data):
            processor = FilePreprocessor(filename)
            author, description, filenums, license, readme, projectURL, repository = processor.extract_info()
            if description=='': continue
            extractor = FeatureExtractor(filename, author, description, filenums, license, readme, projectURL, repository, self.model)
            features.append(extractor.total_features())
            if label == 1:
                labels.append('abuse')
            else:
                labels.append('non-abuse')

        return features, labels

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