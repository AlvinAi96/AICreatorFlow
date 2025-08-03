"""
Function: 爬取给定比赛的discussion列表

CreateDay: 20250525
Author: HongfengAi
History:
20250525    HongfengAi  第一版
"""
import json
import time
from selenium.webdriver.common.by import By

import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from crawler.crawler_utils import open_browser
from configs import COMP_REVIEW_ROOT_PATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import safe_title_func


class CompDisListCrawler():
    def __init__(self):
        pass
        
    def open_browser(self):
        self.browser, self.wait = open_browser()
       
    def parse_page(self, url, page_limit=5):
        self.url = url + "/discussion?sort=published"
        # 打开模拟浏览器
        self.open_browser()
        topics = []
        page_num = 1
        
        while page_num <= page_limit:
            print(f"正在爬取第 {page_num} 页...")
            # 进入点击进入Competitions详细列表网页
            self.browser.get(f"{self.url}&page={page_num}")
            time.sleep(5)  # 等待页面加载

            # 下拉到最低，保证页面完整加载
            self.browser.execute_script("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(3)  # 等待页面加载
            
            # 若该页没东西直接跳过
            try:
                  # 使用正确的XPath查找"No discussions found"元素
                  content = self.browser.find_element(By.XPATH, '//*[@id="site-content"]/div[2]/div/div/div[6]/div/div/div[2]/div/div[4]/div[2]/h2').text
                  if content == "No discussions found":
                        print('已超出最后一页，跳出')
                        break
            except:
                  pass

            # 获取标题（只在第一页获取）
            if page_num == 1:
                title = self.browser.find_element(By.XPATH, '//*[@id="site-content"]/div[2]/div/div/div[2]/div[2]/div[1]/h1').text
            
            disussion_elements = self.browser.find_elements(By.XPATH, '//*[@id="site-content"]/div[2]/div/div/div[6]/div/div/div[2]/div/div[4]/ul[1]/*')
            found_all_topics = False
            
            for element in disussion_elements:
                # 检查是否是h3标题
                if element.tag_name == 'h3':
                    if element.text == 'All other topics':
                        found_all_topics = True
                    continue
                    
                # 只有在找到"All other topics"后才开始收集数据
                if (page_num > 1 or found_all_topics) and element.tag_name == 'li':
                    try:
                        # 提取讨论帖的标题
                        disc_title = element.find_element(By.XPATH, './/div/a/div/div[2]/div/div').text
                        # 提取讨论帖的链接
                        disc_link = element.find_element(By.XPATH, './/div/a').get_attribute('href')
                        # 提取作者信息
                        author_element = element.find_element(By.XPATH, './/div/a/div/div[2]/span/span[1]/a')
                        author = author_element.text
                        author_link = author_element.get_attribute('href')
                        # 提取发布时间
                        post_time = element.find_element(By.XPATH, './/div/a/div/div[2]/span/span[2]/span').text                    
                        # 提取点赞数量
                        likes = element.find_element(By.XPATH, './/div/div/div/div[1]/span').text
                        
                        # 将信息添加到列表中
                        topics.append({
                            'title': disc_title,
                            'link': disc_link,
                            'author': author,
                            'author_link': author_link,
                            'post_time': post_time,
                            'likes': likes
                        })
                        
                    except Exception as e:
                        print(f'解析帖子时出错: {e}')
                        continue
            
            page_num += 1
        
        # 关闭浏览器
        self.browser.quit()
        
        # 将结果保存为JSON文件到比赛名称文件夹下
        if len(topics) > 0:
            safe_title = safe_title_func(title)
            folder_path = f'{COMP_REVIEW_ROOT_PATH}/{safe_title}'
            os.makedirs(folder_path, exist_ok=True)
            
            # 保存JSON文件到对应文件夹
            save_path = f'{folder_path}/comp_dis_list.json'
            
            with open(save_path, 'w', encoding='utf-8') as f:
                json.dump(topics, f, ensure_ascii=False, indent=4)
            print(f'数据已保存到 {save_path}，共获取 {len(topics)} 条讨论')
        
        return topics
    

if __name__ == '__main__':
    # 执行爬虫并显示结果
    clspider = CompDisListCrawler()
    result = clspider.parse_page(url="https://www.kaggle.com/competitions/openai-to-z-challenge", 
                                 page_limit=5)
    print(f'爬取完成')

    # 正在爬取第 1 页...
    # 正在爬取第 2 页...
    # 正在爬取第 3 页...
    # 正在爬取第 4 页...
    # 正在爬取第 5 页...
    # 数据已保存到 E:/kaggle_agent/output\comp_review/openai_to_z_challenge/comp_dis_list.json，共获取 93 条讨论
    # 爬取完成