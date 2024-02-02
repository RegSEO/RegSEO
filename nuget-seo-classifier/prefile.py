import zipfile
import os
import glob
import re


class FilePreprocessor:
    def __init__(self, filename, date):
        self.file = filename
        self.date = date
        self.dir = '/data/black_seo_research/nuget_pkg/' + date + '/release/' + filename
        self.author = ''
        self.description = ''
        self.metadata = ''
        self.projectURL = ''
        self.repository = ''
        self.files_num = 0
        self.dir_num = 0
        self.license = 0
        self.readme_tag = 0

    def unzip(self):
        # 打开zip文件
        file_path = '/data/black_seo_research/nuget_pkg/' + self.date + '/' + self.file + '.nupkg'
        print(file_path)
        try:
            with zipfile.ZipFile(file_path, 'r') as zip_file:
                self.files_num += len(zip_file.infolist())
                print(self.files_num)
                all_zip_info = zip_file.infolist()
                # 获取所有目录的数量
                try:
                    self.dir_num = sum(1 for zip_info in all_zip_info if zip_info.is_dir())
                except Exception as e:
                    print(e)
                    self.dir_num = 0
                # 解压全部文件到指定目录
                for file in zip_file.namelist():
                    if file.endswith('.nuspec') or file.endswith('.md'):
                        zip_file.extract(file, self.dir)
                return 0
        except Exception as e:
            print("Error: File is not a zip file")
            return 1

    def get_content(self):
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

        # for file_path in glob.glob(folder_path + '/*.nuspec'):
        #     with open(file_path, 'r') as f:
        #         metadata = f.read()
        # file_path = self.dir + '/' + self.file + '.nuspec'
        # with open(file_path, 'r', encoding='utf-8') as file:
        #     content = file.read()

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
        
        if os.path.isfile(os.path.join(folder_path, 'Readme.md')):
            try:
                # 读取 readme.md 文件内容
                with open(os.path.join(folder_path, 'Readme.md'), 'r') as file:
                    readme = file.read()
                    # print(readme)
                    if readme != ' ':
                        readme_tag = 1
                        name = self.file +'\n'
                        with open("Readme_file.txt", "a") as file:
                            file.write(name)
            except UnicodeDecodeError:
                print("UnicodeDecodeError: 无法解码Readme文件", self.file)
                name = self.file +'\n'
                with open("readme_error.txt", "a") as file:
                    file.write(name)
        
        if os.path.isfile(os.path.join(folder_path, 'README.md')):
            try:
                # 读取 readme.md 文件内容
                with open(os.path.join(folder_path, 'README.md'), 'r') as file:
                    readme = file.read()
                    # print(readme)
                    if readme != ' ':
                        readme_tag = 1
                        name = self.file +'\n'
                        with open("README_file.txt", "a") as file:
                            file.write(name)
            except UnicodeDecodeError:
                print("UnicodeDecodeError: 无法解码README文件", self.file)
                name = self.file +'\n'
                with open("readme_error.txt", "a") as file:
                    file.write(name)
        
        self.readme_tag = readme_tag
        self.metadata = metadata
        self.description = readme

    def get_structure(self):
        # 获取解压后的文件数量
        self.files_num += sum([len(files) for _, _, files in os.walk(self.dir)])
        print(self.files_num)

    def extract_info(self):
        error_flag = self.unzip()
        if error_flag:
            return self.author, self.description, self.files_num, self.license, self.readme_tag, self.projectURL, self.repository
            
        self.get_content()
        # self.get_structure()
        metadata = self.metadata
        # author
        start_tag = '<authors>'
        end_tag = '</authors>'
        start_index = metadata.find(start_tag) + len(start_tag)
        end_index = metadata.find(end_tag)
        self.author += metadata[start_index:end_index]
        # print(author)
        # description
        start_tag = '<description>'
        end_tag = '</description>'
        start_index = metadata.find(start_tag) + len(start_tag)
        end_index = metadata.find(end_tag)
        self.description += metadata[start_index:end_index]
        # print(description)
        # projectURL
        start_tag = '<projectUrl>'
        end_tag = '</projectUrl>'
        start_index = metadata.find(start_tag) + len(start_tag)
        end_index = metadata.find(end_tag)
        if start_index == -1 or end_index == -1:
            self.projectURL = " "
        else:
            self.projectURL = metadata[start_index:end_index]
        # repository
        start_tag = '<repository'
        end_tag = '/>'
        start_index = metadata.find(start_tag) + len(start_tag)
        end_index = metadata.find(end_tag)
        string = metadata[start_index:end_index]
        url_pattern = re.compile(r'url="(.*?)"')
        urls = url_pattern.findall(string)
        for url in urls:
            self.repository += url
            self.repository += " "
        # licenseUrl
        license_tag = '<licenseUrl>'
        index = metadata.find(license_tag)
        # print(index)
        if index != -1:
            self.license = 1
            # print(license)
        return self.author, self.description, self.files_num,self.dir_num, self.license, self.readme_tag, self.projectURL, self.repository
        