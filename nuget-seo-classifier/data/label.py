import pandas as pd
import os
# from db.db_init import DB


# class LabelWriter:
#     def __init__(self):
#         # self.db = db
            
#     def write_labels_to_excel(self, filename):
#         folder_path = 'pkg/nuget_sample/'
#         file_list = os.listdir(folder_path)
#         df = pd.DataFrame(columns=['name', 'label'])

#         for filename in file_list:
#             name = filename.split('.nupkg')[0]
#             df = df.append({'name': name, 'label': 1}, ignore_index=True)

#         df.to_csv(filename, index=False)


def write_labels_to_excel(filename):
    folder_path = '/data/black_seo_research/nuget_pkg/white_most'
    file_list = os.listdir(folder_path)

    id = 0
    data = []
    for filename in file_list:
        name = filename.split('.nupkg')[0]
        data.append({'name': name, 'label': 0})
        id = id + 1
        print(id)

    df = pd.DataFrame(data)
    df.to_csv(filename, index=False)

if __name__ == "__main__":
    # label_writer = LabelWriter()
    write_labels_to_excel("white_label.csv")

'''
    label_writer = LabelWriter(db)
    label_writer.write_labels_to_excel("train_label_2.xlsx")
    df1 = pd.read_excel('train_label_2.xlsx')
    df2 = pd.read_excel('test_label.xlsx')
    result = pd.concat([df1, df2], ignore_index=True)
    result.to_excel('test_label_2.xlsx', index=False)
'''
