from db.sys_config import config
from pymongo import MongoClient
from pymongo.database import Database
from pymongo.collection import Collection
from db.locale_config import default as locale
import json


def get_locale(entry: str) -> str:
    try:
        return locale[entry]
    except KeyError:
        print(f"No entry: {entry}")
        return ''


class DB:
    def __init__(self):
        self._mongo = None

    def get_mongo(self, mode='test'):  # config=config['mongo']):
        if mode == 'train':
            mode_config = config['mongo_train']
        elif mode == 'test':
            mode_config = config['mongo_test']
        elif mode == 'black':
            mode_config = config['black']
        elif mode == 'white':
            mode_config = config['white']
        elif mode == 'npm':
            mode_config = config['npm']
        elif mode == 'qianxin_docker':
            mode_config = config['qianxin_docker']
        else:
            raise ValueError('Invalid mode, choose either "train" or "test"')

        url = mode_config['url']
        database = mode_config['database']
        collection = mode_config['collection']
        self.__client: MongoClient = MongoClient(url)
        try:
            self.__database = Database(self.__client, database)
            self.__collection = Collection(self.__database, collection)
        except KeyError as ke:
            # print("ke")
            print(ke)

        return self.__collection

    def close_mongo(self):
        if hasattr(self, '_mongo') and self._mongo is not None:
            self._mongo.close()

    def copy_documents(self, num=100):
        # 获取test数据库中的前100个文档
        test_collection = self.get_mongo('black')
        documents = list(test_collection.find().skip(3200).limit(num))

        # 将这些文档插入到train数据库中
        train_collection = self.get_mongo('test')
        train_collection.insert_many(documents)

    def copy_documents_2(self, num=100):
        # 获取black数据库中的文档，从第3200个文档开始（索引从0开始）
        test_collection = self.get_mongo('black')
        documents = list(test_collection.find(
            {'full_description': {'$exists': True}},
            {'_id': 0}).skip(3200).limit(num))
        # 将这些文档插入到train数据库中
        train_collection = self.get_mongo('test')
        train_collection.insert_many(documents)

    def delete_documents(self, num=27000):
        # 获取需要删除的文档
        collection = self.get_mongo('test')
        documents = list(collection.find().skip(3200).limit(num))

        # 删除文档
        if documents:
            document_ids = [doc['_id'] for doc in documents]  # 假设文档的唯一标识字段为 "_id"
            collection.delete_many({"_id": {"$in": document_ids}})
            print(f"Deleted {len(document_ids)} documents")
        else:
            print("No documents found to delete")