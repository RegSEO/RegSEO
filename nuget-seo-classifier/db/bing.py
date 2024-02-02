from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time


class BingSearch:
    def __init__(self, word, max_page=10):
        self.driver = webdriver.Chrome()
        self.word = word
        self.num = max_page
        self.data = []
        self.start()

    def __del__(self):
        self.driver.quit()

    def get_data(self):
        for i in range(self.num):
            WebDriverWait(self.driver, 30).until(EC.presence_of_element_located((By.CLASS_NAME, 'sb_pagN')))
            time.sleep(1)
            lis = self.driver.find_elements(By.XPATH, "//li[@class='b_algo']")
            for li in lis:
                title = li.find_element(By.XPATH, './/h2').text  # 子相对路径
                print(title)
                try:
                    content = li.find_element(By.XPATH, './/div/p').text
                except:
                    content = li.find_element(By.CLASS_NAME, 'b_caption').text
                print(content)
                self.data.append([title, content])
            time.sleep(2)
            try:
                self.driver.find_element(By.CLASS_NAME, 'sb_pagN').click()
            except:
                try:
                    time.sleep(5)
                    self.driver.find_element(By.CLASS_NAME, 'sb_pagN').click()
                except:
                    break

    def start(self):
        self.driver.get("https://cn.bing.com")
        self.driver.find_element(By.ID, 'est_en').click()
        time.sleep(1)
        self.driver.find_element(By.ID, "sb_form_q").send_keys(self.word)
        time.sleep(1)
        self.driver.find_element(By.ID, "sb_form_q").send_keys(Keys.ENTER)
        self.driver.find_element(By.ID, 'est_en').click()
        self.get_data()
        bing_info = ''
        for i in self.data:
            bing_info += i[0]  # title
            bing_info += i[1]  # content
            bing_info += '\n'
        return bing_info

    # def save_data(self):
    #     with open(self.word + '.txt', 'w', encoding='utf-8') as f:
    #         for i in self.data:
    #             f.write('Title:  {}\nContent:  {}\n\n'.format(i[0], i[1]))


# if __name__ == '__main__':
#     word = 'python'  # 关键词
#     page = 20  # 页数
#     BingSearch(word, page)
