"""
Function: 爬取给定比赛总览信息

CreateDay: 20250525
Author: HongfengAi
History:
20250525    HongfengAi  第一版
"""
import json
import time
import selenium
from selenium.webdriver.common.by import By
import requests

import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from configs import COMP_EXPRESS_ROOT_PATH
from crawler.crawler_utils import open_browser
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import safe_title_func, set_proxy, unset_proxy
from wechat_utils.upload_material import WeChatPermanentMaterialUploader

class CompOverviewCrawler():
    def __init__(self):
        self.img_uploader = WeChatPermanentMaterialUploader()
        
    def open_browser(self):
        self.browser, self.wait = open_browser()

    def parse_p_with_math(self, element):
        """处理包含数学公式的p标签，将数学公式用$包围并按顺序拼接"""
        try:
            # 获取p标签的HTML内容
            html_content = element.get_attribute('innerHTML')
            
            # 找到所有的数学公式脚本标签
            import re
            from bs4 import BeautifulSoup
            
            # 解析HTML
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # 移除所有MathJax相关的元素，但保留script标签
            for tag in soup.find_all(['span'], class_=['MathJax_Preview', 'MathJax_SVG', 'MJX_Assistive_MathML']):
                tag.decompose()
            
            # 移除其他MathJax相关的span标签
            for tag in soup.find_all('span', {'class': re.compile(r'MathJax|MJX')}):
                tag.decompose()
            
            # 找到所有的math/tex脚本
            math_scripts = soup.find_all('script', {'type': re.compile(r'math/tex')})
            
            # 替换script标签为$包围的数学公式
            for script in math_scripts:
                math_content = script.get_text().strip()
                math_formatted = f'${math_content}$'
                # 用格式化的数学公式替换script标签
                script.replace_with(math_formatted)
            
            # 获取最终的文本内容
            final_content = soup.get_text()
            
            # 清理多余的空白字符
            final_content = re.sub(r'\s+', ' ', final_content).strip()
            
            return final_content if final_content else ""
                
        except Exception as e:
            print(f'处理包含数学公式的p标签时出错: {e}')
            # 出错时返回原始文本
            return element.text if element.text else ""

    def parse_diff_type_elements(self, xpath:str):
        """某div下存在多个不同类型的元素，按顺序获取"""
        # 获取评估部分的所有直接子元素
        elements = self.browser.find_elements(By.XPATH, xpath)    
        
        # 收集不同类型的元素
        content = []
        img_count = 0
        for element in elements:
            try:
                # 获取元素的标签名
                tag_name = element.tag_name
                
                if tag_name == 'p':
                    # 处理包含数学公式的p标签
                    p_content = self.parse_p_with_math(element)
                    if p_content:
                        content.append({'type': tag_name, 'content': p_content})
                
                    # 检查是否包含图片并提取src链接
                    img_elements = element.find_elements(By.XPATH, './/img')
                    if img_elements:
                        img_src = ""
                        for img in img_elements:
                            img_src = img.get_attribute('src')
                        if img_src:
                            # 将其下载到本地
                            # 创建使用代理的session
                            set_proxy()
                            session = requests.Session()
                            session.trust_env = True  # 禁用环境变量中的代理设置
                            
                            # 设置超时和重试
                            session.mount('https://', requests.adapters.HTTPAdapter(max_retries=3))
                            session.mount('http://', requests.adapters.HTTPAdapter(max_retries=3))
                            
                            # 下载图片
                            img_name = f'{img_count}.png'
                            img_path = f'{COMP_EXPRESS_ROOT_PATH}/{self.safe_title}/images'
                            os.makedirs(img_path, exist_ok=True)
                            
                            # 添加请求头，模拟浏览器
                            headers = {
                                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                            }
                            
                            response = session.get(img_src, headers=headers, timeout=10)
                            response.raise_for_status()  # 检查HTTP错误
                            
                            with open(f'{img_path}/{img_name}', 'wb') as f:
                                f.write(response.content)
                            img_count += 1
                            unset_proxy()

                            # 将其上传到永久素材库
                            img_upload_result = self.img_uploader.upload_specific_file(f'{img_path}/{img_name}')
                            if img_upload_result:
                                img_url = img_upload_result['url']
                                content.append({'type': 'image', 'content': img_url})
                    
                # 有序列表
                elif tag_name == 'ol':
                    # 处理列表
                    list_items = element.find_elements(By.XPATH, './/li')
                    list_content = ""
                    for i, li in enumerate(list_items, 1):
                        if li.text:
                            list_content += f"{i}. " + li.text + "\n"
                    content.append({'type': tag_name, 'content': list_content})
                
                # 无序列表
                elif tag_name == 'ul':
                    # 处理列表
                    list_items = element.find_elements(By.XPATH, './/li')
                    list_content = ""
                    for i, li in enumerate(list_items, 1):
                        if li.text:
                            list_content += "● " + li.text + "\n"
                    content.append({'type': tag_name, 'content': list_content})
                
                elif tag_name == 'table':
                    # 直接获取table的HTML格式
                    table_html = element.get_attribute('outerHTML')
                    if table_html:
                        content.append({'type': tag_name, 'content': table_html})

                else:
                    # 处理其他类型的元素
                    if element.text.strip():
                        content.append({'type': tag_name, 'content': element.text})
                        
            except Exception as e:
                print(f'处理元素时出错: {e}')
                continue
        
        return content      
    
      
    def parse_page(self, url):
        self.url = url
        # 打开模拟浏览器
        self.open_browser()
        
        # 进入点击进入Competitions详细列表网页
        self.browser.get(self.url)
        
        # 下拉到最低，保证页面完整加载
        self.browser.execute_script("window.scrollTo(0, document.body.scrollHeight)")
        time.sleep(3)  # 等待页面加载   
             
        comp_overview = {}
        try:
            # title
            title = self.browser.find_element(By.XPATH, '//*[@id="site-content"]/div[2]/div/div/div[2]/div[2]/div[1]/h1').text
            self.safe_title = safe_title_func(title)
            
            # overview
            # overview = self.browser.find_element(By.XPATH, '//*[@id="abstract"]/div[1]/div[2]/div/p').text
            overview = self.parse_diff_type_elements(xpath = '//*[@id="abstract"]/div[1]/div[2]/div/*')

            # start_time
            # 已开始的比赛和已结束的比赛不一样
            try:
                start_time = self.browser.find_element(By.XPATH, '//*[@id="abstract"]/div[2]/div/div/div[1]/div[1]/span/span').get_attribute("title")
            except:
                # 有时在title，有时在text内
                start_time = self.browser.find_element(By.XPATH, '//*[@id="abstract"]/div[2]/div/div/div[1]/div[1]/span').get_attribute("title")
                if not start_time:
                    start_time = self.browser.find_element(By.XPATH, '//*[@id="abstract"]/div[2]/div/div/div[1]/div[1]/span').text
                    
            # end_time
            try:
                end_time = self.browser.find_element(By.XPATH, '//*[@id="abstract"]/div[2]/div/div/div[1]/div[2]/span/span').get_attribute("title")
            except:
                # 有时在title，有时在text内
                end_time = self.browser.find_element(By.XPATH, '//*[@id="abstract"]/div[2]/div/div/div[1]/div[2]/span').get_attribute("title")
                if not end_time:
                    end_time = self.browser.find_element(By.XPATH, '//*[@id="abstract"]/div[2]/div/div/div[1]/div[2]/span').text
                
            # description
            description = self.parse_diff_type_elements(xpath = '//*[@id="description"]/div/div[2]/div/div/*')
            
            # host
            comp_host = self.browser.find_element(By.XPATH, '//*[@id="site-content"]/div[2]/div/div/div[6]/div[4]/div/div[1]/div[1]/p').text
            
            # participation
            participation = []
            part_elements = self.browser.find_elements(By.XPATH, '//*[@id="site-content"]/div[2]/div/div/div[6]/div[4]/div/div[3]/div/p')
            
            for element in part_elements:
                participation.append(element.text)
                
            # tags
            tags = []
            tag_elements = self.browser.find_elements(By.XPATH, '//*[@id="combo-tags-menu-chipset"]/a/span')
            for element in tag_elements:
                tags.append(element.text)
                
            # evaluation
            evaluation = self.parse_diff_type_elements(xpath = '//*[@id="evaluation"]/div/div[2]/div/div/*')
            
            # timeline
            timeline = self.parse_diff_type_elements(xpath = '//*[@id="timeline"]/div/div[2]/div/div/*')
            
            # prize 
            prize = self.parse_diff_type_elements(xpath = '//*[@id="prizes"]/div/div[2]/div/div/*')
            
            # 整理数据
            comp_overview = {
                'url': self.url,
                'title': title,
                'overview': overview,
                'start_time': start_time,
                'end_time': end_time,
                'description': description,
                'host': comp_host,
                'participation': participation,
                'evaluation': evaluation,
                'timeline': timeline,
                'prize': prize
            }
        
        except selenium.common.exceptions.TimeoutException:
            print('parse_page: TimeoutException 网页超时')
            
        except selenium.common.exceptions.StaleElementReferenceException:
            print('turn_page: StaleElementReferenceException 某元素因JS刷新已过时没出现在页面中')
            print('刷新并重新解析网页...')
            self.browser.refresh()
            time.sleep(2)
            
        except Exception as e:
            print(f'发生错误: {e}')
        
        # 将结果保存为JSON文件
        if comp_overview:
            save_path = f'{COMP_EXPRESS_ROOT_PATH}/{self.safe_title}'
            os.makedirs(save_path, exist_ok=True)
            save_fpath = f'{save_path}/comp_overview.json'
            
            with open(save_fpath, 'w', encoding='utf-8') as f:
                json.dump(comp_overview, f, ensure_ascii=False, indent=4)
            print(f'数据已保存到 {save_fpath}')
        
        # 关闭浏览器
        self.browser.quit()
        
        return comp_overview
    

if __name__ == '__main__':
    # 执行爬虫并显示结果
    import argparse
    parser = argparse.ArgumentParser(description="爬取给定比赛总览信息")
    parser.add_argument("--comp_url", type=str, default="https://www.kaggle.com/competitions/drw-crypto-market-prediction", help="比赛URL")
    args = parser.parse_args()

    clspider = CompOverviewCrawler()
    result = clspider.parse_page(url=args.comp_url)
    print(f'爬取完成')
    
    # 数据已保存到 E:/kaggle_agent/output\comp_express/drw__crypto_market_prediction/comp_overview.json
