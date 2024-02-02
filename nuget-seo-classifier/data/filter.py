import zipfile
import os
import glob
import re

short_num = no_url = 0

class FilePreprocessor:
    def __init__(self, filename):
        self.file = filename
        self.dir = '/path/to/nuget-seo-classifier/data/pkg/black/release/' + filename
        self.author = ''
        self.description = ''
        self.metadata = ''
        self.files_num = 0
        self.license = 0
        self.readme_tag = 0

    def unzip(self):
        # 打开zip文件
        file_path = '/path/to/nuget-seo-classifier/data/pkg/black/' + self.file + '.nupkg'
        print(file_path)
        try:
            with zipfile.ZipFile(file_path, 'r') as zip_file:
                # 解压全部文件到指定目录
                zip_file.extractall(self.dir)
                return 0
        except zipfile.BadZipFile:
            print("Error: File is not a zip file")
            return 1

    def get_content(self):
        # error_flag = self.unzip()
        # if error_flag:
        #     return 0

        metadata = ''
        readme = ''
        # 读取解压后的文件内容
        folder_path = self.dir  # 指定文件夹路径
        for file_path in glob.glob(folder_path + '/*.nuspec'):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    metadata = f.read()
            except UnicodeDecodeError:
                try:
                    with open(file_path, 'r', encoding='utf-16') as f:
                        metadata = f.read()
                except UnicodeDecodeError:
                    print("UnicodeDecodeError: 无法解码nuspec文件", self.file)
                    name = self.file + '\n'
                    with open("nuspec_error.txt", "a") as file:
                        file.write(name)

        readme_tag = 0
        if os.path.isfile(os.path.join(folder_path, 'readme.md')):
            try:
                # 读取 readme.md 文件内容
                with open(os.path.join(folder_path, 'readme.md'), 'r') as file:
                    readme = file.read()
                    # print(readme)
                    if readme != ' ':
                        readme_tag = 1
                        name = self.file +'\n'
                        with open("readme_file.txt", "a") as file:
                            file.write(name)
            except UnicodeDecodeError:
                print("UnicodeDecodeError: 无法解码readme文件", self.file)
                name = self.file +'\n'
                with open("readme_error.txt", "a") as file:
                    file.write(name)
        
        self.description = readme

        start_tag = '<description>'
        end_tag = '</description>'
        start_index = metadata.find(start_tag) + len(start_tag)
        end_index = metadata.find(end_tag)
        self.description += metadata[start_index:end_index]
        # print(self.description)

        global short_num
        global no_url
        if len(self.description.strip())<20: 
            print(self.file)
            print(self.description)
            print(len(self.description.strip()))
            short_num += 1

        url_pattern = re.compile(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+(?=[;().\s]|(?<=http))')
        urls = url_pattern.findall(self.description)
        total_urls_num = len(urls)

        if len(urls) == 0: 
            no_url += 1

sum = 0
folder_path = '/path/to/nuget-seo-classifier/data/pkg/black/'
file_list = os.listdir(folder_path)
for filename in file_list: 
    filename = filename.split('.nupkg')[0]   
    if filename == 'release': continue
    processor = FilePreprocessor(filename)
    processor.get_content()
    sum += 1
    

print("short text: " + str(short_num))
print("no url: " + str(no_url))
print("sum: " + str(sum))

# with open('test.txt', 'r', encoding='utf-8') as f:
#     metadata = f.read()

# description = ''
# start_tag = '<description>'
# end_tag = '</description>'
# start_index = metadata.find(start_tag) + len(start_tag)
# end_index = metadata.find(end_tag)
# description += metadata[start_index:end_index]
# print(len(description.strip()))