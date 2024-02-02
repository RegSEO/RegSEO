import pandas as pd
from db.db_init import DB


class LabelWriter:
    def __init__(self, db: DB):
        self.db = db

    def write_labels_to_excel(self, filename):
        coll = self.db.get_mongo('test')
        # data = coll.find({}, {"name": 1}).limit(100)
        data = coll.find({}, {"name": 1}).skip(3200).limit(7000)
        names = [item["name"] for item in data if "name" in item]
        df = pd.DataFrame(names, columns=["name"])
        df["label"] = 1
        df.to_excel(filename, index=False)

    def write_labels_to_excel_2(self, filename):
        coll = self.db.get_mongo('npm')
        # data = coll.find({}, {"name": 1}).limit(100)
        data = coll.find({'readme': {'$exists': True}}, {"name": 1}).skip(1000).limit(10000)
        names = [item["name"] for item in data if "name" in item]
        df = pd.DataFrame(names, columns=["name"])
        df["label"] = 1
        df.to_excel(filename, index=False)


if __name__ == "__main__":
    db = DB()
    label_writer = LabelWriter(db)
    label_writer.write_labels_to_excel_2("test_label_npm_2.xlsx")
    db.close_mongo()

'''
    label_writer = LabelWriter(db)
    label_writer.write_labels_to_excel("train_label_2.xlsx")
    df1 = pd.read_excel('train_label_2.xlsx')
    df2 = pd.read_excel('test_label.xlsx')
    result = pd.concat([df1, df2], ignore_index=True)
    result.to_excel('test_label_2.xlsx', index=False)
'''
