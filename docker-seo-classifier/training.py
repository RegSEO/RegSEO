from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
import joblib
from loader import DataLoader
from db.db_init import DB
from gensim.models.keyedvectors import KeyedVectors


class Loader:
    def __init__(self, black_loader: DataLoader, white_loader: DataLoader):
        self.features_train, self.labels_train = None, None
        self.features_test, self.labels_test = None, None
        self.black_loader = black_loader
        self.white_loader = white_loader

    def load_data(self):
        black_features, black_labels = self.black_loader.load_data('black')
        black_features_train, black_features_test, black_labels_train, black_labels_test = train_test_split(
            black_features, black_labels, test_size=0.3, random_state=0)

        white_features, white_labels = self.white_loader.load_data('white')
        white_features_train, white_features_test, white_labels_train, white_labels_test = train_test_split(
            white_features, white_labels, test_size=0.3, random_state=0)

        self.features_train = black_features_train + white_features_train
        self.labels_train = black_labels_train + white_labels_train
        self.features_test = black_features_test + white_features_test
        self.labels_test = black_labels_test + white_labels_test

        return self.features_train, self.labels_train, self.features_test, self.labels_test


class ModelTrainer:
    def __init__(self, model, features, labels):
        self.model = model
        # self.loader = loader
        self.features_train, self.labels_train = features, labels

    def train(self, modelfile='./model/RFC.joblib', datafile='./model/train_data.joblib'):
        # self.load_train_data()
        self.train_model()
        self.save_train_data(datafile)
        self.save_model(modelfile)

    # def load_train_data(self):
    #     self.features_train, self.labels_train = self.loader.load_data('train')
        '''
        # 获取特征和标签
        features, labels = self.loader.load_data()
        # 划分训练集和测试集
        self.features_train, self.features_test, self.labels_train, self.labels_test = train_test_split(features, labels, test_size=0.3, random_state=0)
        '''

    def train_model(self):
        self.model.fit(self.features_train, self.labels_train)

    def save_train_data(self, datafile):
        train_data = {'features_train': self.features_train, 'labels_train': self.labels_train}
        joblib.dump(train_data, datafile)

    def save_model(self, modelfile):
        joblib.dump(self.model, modelfile)

    '''
    def save_model_data(self, model_filename, data_filename):
        # 将训练数据和模型保存到文件中
        data = {'features_train': self.features_train, 'features_test': self.features_test,
                'labels_train': self.labels_train, 'labels_test': self.labels_test}
        joblib.dump(data, data_filename)
        joblib.dump(self.model, model_filename)
    '''


class ModelTester:
    def __init__(self, model, features, labels):
        self.model = model
        # self.loader = loader
        self.features_test, self.labels_test = features, labels

    def test(self, datafile='./model/test_data.joblib'):
        # self.load_test_data()
        self.predict()
        self.save_test_data(datafile)

    # def load_test_data(self):
    #     self.features_test, self.labels_test = self.loader.load_data('test')
        # self.features_test, self.labels_test = self.loader.load_data_nuget()
        # self.features_test, self.labels_test = self.loader.load_data_npm('npm')

    def predict(self):
        self.predictions = self.model.predict(self.features_test)

    def calculate_metrics(self):
        accuracy = accuracy_score(self.labels_test, self.predictions)
        precision = precision_score(self.labels_test, self.predictions, average='weighted')
        recall = recall_score(self.labels_test, self.predictions, average='weighted')
        f1 = f1_score(self.labels_test, self.predictions, average='weighted')
        return accuracy, precision, recall, f1

    def save_test_data(self, datafile):
        test_data = {'features_test': self.features_test, 'labels_test': self.labels_test}
        joblib.dump(test_data, datafile)


if __name__ == "__main__":
    db = DB()

    # classifier = joblib.load("RFC.joblib")

    print("start loading")
    # word2vec = KeyedVectors.load_word2vec_format('./model/wiki.en.vec')
    word2vec = KeyedVectors.load_word2vec_format('/home/miniwmy/Scam/npm_abuse/wiki.en.vec') 
    # word2vec = KeyedVectors.load_word2vec_format('./model/wiki-news.vec')
    print("finished")

    classifier = RandomForestClassifier(n_estimators=100)

    black_loader = DataLoader(label_file_path='./data/black_label.xlsx', db=db, model=word2vec)
    white_loader = DataLoader(label_file_path='./data/white_label.xlsx', db=db, model=word2vec)
    data_loader = Loader(black_loader, white_loader)
    features_train, labels_train, features_test, labels_test = data_loader.load_data()

    # train_loader = DataLoader(label_file_path='./data/train_label_2.xlsx', db=db, model=word2vec)
    trainer = ModelTrainer(classifier, features_train, labels_train)
    trainer.train()

    # test_loader = DataLoader(label_file_path='./data/test_label_2.xlsx', db=db, model=word2vec)
    tester = ModelTester(classifier, features_test, labels_test)
    tester.test()
    accuracy, precision, recall, f1 = tester.calculate_metrics()
    print(f"Accuracy: {accuracy}, Precision: {precision}, Recall: {recall}, F1: {f1}")

    # trainer.save_model_data('classifier.joblib', 'data.joblib')
    importances = classifier.feature_importances_

    # 输出特征重要性评估结果
    for i, importance in enumerate(importances):
        print(f"Feature {i}: {importance}")