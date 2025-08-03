"""
Function: 爬取ProductHunt Weekly产品列表

CreateDay: 20250701
Author: HongfengAi
History:
20250701    HongfengAi  第一版
"""
import datetime
import json
import time
import os
import sys
import requests
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import re
import argparse
import tempfile
import urllib.parse

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from configs import USER_AGENT, SOFTWARE_EXPRESS_ROOT_PATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from crawler.crawler_utils import open_browser
from utils import set_proxy, unset_proxy, safe_title_func, get_previous_week
from wechat_utils.upload_material import WeChatPermanentMaterialUploader


class ProductHuntWeeklyProductsCrawler:
    def __init__(self):
        self.browser = None
        self.wait = None
        self.media_uploader = WeChatPermanentMaterialUploader()
        
    def open_browser(self):
        """打开浏览器"""
        self.browser, self.wait = open_browser()
        
    def close_browser(self):
        """关闭浏览器"""
        if self.browser:
            self.browser.quit()

    def download_image_from_url(self, image_url: str, save_dir: str = None) -> str:
        """
        从URL下载图片到本地
        
        Args:
            image_url: 图片URL
            save_dir: 保存目录，如果为None则使用临时目录
            
        Returns:
            str: 本地文件路径
        """
        try:
            # 创建保存目录
            if save_dir is None:
                save_dir = tempfile.gettempdir()
            os.makedirs(save_dir, exist_ok=True)
            
            # 从URL获取文件名和扩展名
            parsed_url = urllib.parse.urlparse(image_url)
            filename = f"app_icon.png"
            
            # 确保文件名有正确的扩展名
            if not any(filename.lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp']):
                filename += '.png'
            
            local_path = os.path.join(save_dir, filename)
            
            # 下载图片
            print(f"正在下载图片: {image_url}")
            session = requests.Session()
            session.trust_env = False
            
            response = session.get(image_url, timeout=30, stream=True)
            response.raise_for_status()
            
            # 保存到本地
            with open(local_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            print(f"图片下载成功: {local_path}")
            return local_path
            
        except Exception as e:
            print(f"下载图片失败: {e}")
            raise e

    def crawl_weekly_software_list(self, week_url, save_dir, topk):
        """
        爬取指定周的软件列表
        
        Args:
            week_url: 周软件列表URL，如 https://www.producthunt.com/leaderboard/weekly/2025/26
            save_dir: 保存目录
            
        Returns:
            list: 软件信息列表
        """
        try:
            # 打开浏览器
            self.open_browser()
            
            # 访问页面
            print(f"正在访问: {week_url}")
            self.browser.get(week_url)
            
            # 等待页面加载
            time.sleep(3)
            
            # 滚动到页面底部确保所有内容加载
            self.browser.execute_script("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(2)
            
            # 查找所有软件条目
            # 根据页面结构，软件条目通常在特定的容器中
            software_elements = []
            software_elements = self.browser.find_elements(By.XPATH, '//*[@id="root-container"]/div[3]/div/main/div/div/div[2]/*')
            if len(software_elements) == 0:
                software_elements = self.browser.find_elements(By.XPATH, '//*[@id="root-container"]/div[3]/div/main/div/div/*')

            software_data = []
            valid_software_count = 0
            for i, software_element in enumerate(software_elements):
                # 跳过广告
                if software_element.get_attribute('data-sentry-component') == 'Ad':
                    print(f"跳过广告: {i+1}")
                    continue

                try:
                    software_info = {}
                    
                    # 提取软件图片
                    software_img_element = software_element.find_element(By.XPATH, './/img')
                    srcset = software_img_element.get_attribute('srcset')
                    if srcset:
                        print(f"发现srcset: {srcset}")
                        # 解析srcset，获取最高DPI版本
                        srcset_urls = []
                        for src_item in srcset.split(','):
                            src_item = src_item.strip()
                            if src_item:
                                url_part = src_item.split(' ')[0]
                                srcset_urls.append(url_part)
                        if srcset_urls:
                            image_url = srcset_urls[-1]  # 取最后一个（最高DPI）
                            print(f"选择最高DPI图片: {image_url}")
                    
                    # 2. 如果没有srcset，使用src
                    if not image_url:
                        image_url = software_img_element.get_attribute('src')

                    software_info['img_url'] = image_url

                    # 提取软件标题
                    title_element = software_element.find_element(By.XPATH, './/div/a')
                    software_info['title'] = title_element.text.strip()

                    # 获取软件链接
                    software_info['producthunt_url'] = title_element.get_attribute('href')

                    # 获取一句话描述
                    description_element = software_element.find_element(By.XPATH, './/div/a[2]')
                    software_info['sentence_description'] = description_element.text.strip()

                    # 获取标签
                    tag_elements = software_element.find_elements(By.XPATH, './/div/div/*')
                    tags = []   
                    for tag_element in tag_elements:
                        if tag_element.get_attribute('data-sentry-component') == 'TagList':
                            tags.extend(tag_element.text.replace('•','').strip().split('\n\n'))
                            break
                    software_info['tags'] = tags

                    # 提取评论数
                    comment_element = software_element.find_element(By.XPATH, './/button[1]/div/p')
                    software_info['comments'] = str(comment_element.text.strip())

                    # 提取点赞数
                    upvote_element = software_element.find_element(By.XPATH, './/button[2]/div/p')
                    software_info['upvotes'] = str(upvote_element.text.strip())
                        
                    if software_info['img_url']:
                        # 下载并上传媒体文件
                        safe_software_title = safe_title_func(software_info['title'])
                        app_icon_dir = os.path.join(save_dir, f'{i+1}_{safe_software_title}')
                        local_path = self.download_image_from_url(software_info['img_url'], app_icon_dir)
                        result = self.media_uploader.upload_specific_file(local_path, title=software_info['title'])
                        software_info['app_icon_local_path'] = local_path
                        software_info['app_icon_upload_url'] = result['url']
                    else:
                        software_info['app_icon_local_path'] = None
                        software_info['app_icon_upload_url'] = None
                            
                    # 添加索引
                    software_info['index'] = i + 1
                    valid_software_count += 1
                    software_data.append(software_info)

                    if valid_software_count >= topk:
                        break
                    
                    print(f"已处理第 {i+1} 篇软件: {software_info['title'][:50]}...")
                    
                except Exception as e:
                    print(f"处理第 {i+1} 篇软件时出错: {e}")
                    continue
            
            # 保存数据到JSON文件
            output_file = os.path.join(save_dir, f"software_list_{week_url.split('/')[-1]}.json")
            os.makedirs(save_dir, exist_ok=True)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(software_data, f, ensure_ascii=False, indent=2)
            
            print(f"爬取完成！共获取 {len(software_data)} 篇软件信息")
            print(f"数据已保存到: {output_file}")
            
            return software_data
            
        except Exception as e:
            print(f"爬取过程中出错: {e}")
            return []
            
        finally:
            self.close_browser()
    

    def crawl_specific_week(self, year, week, topk=20):
        """
        爬取指定年份和周的software
        
        Args:
            year: 年份，如 2025
            week: 周数，如 W26
            topk: 获取前k个软件
            
        Returns:
            list: 软件信息列表
        """
        week_url = f"https://www.producthunt.com/leaderboard/weekly/{year}/{week}"
        return self.crawl_weekly_software_list(week_url, os.path.join(SOFTWARE_EXPRESS_ROOT_PATH, f"{year}_{week}"), topk)




if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("--topk", type=int, default=10, help="Top k papers")
    args = arg_parser.parse_args()
    topk = args.topk

    crawler = ProductHuntWeeklyProductsCrawler()

    # 获取上一周
    prev_year, prev_week = get_previous_week()
    print(f"上一周: {prev_year}年 {prev_week}")
    # 爬取上一周的软件
    softwares = crawler.crawl_specific_week(prev_year, prev_week, topk)
    
    # 打印结果
    for software in softwares:
        print(f"\n软件 {software['index']}: {software['title']}")
        print(f"  点赞数: {software['upvotes']}")
        print(f"  评论数: {software['comments']}")
        print(f"  产品主页: {software['producthunt_url']}")
        print(f"  一句话描述: {software['sentence_description']}")
        print(f"  标签: {software['tags']}")
        print(f"  应用图标本地路径: {software['app_icon_local_path']}")
        print(f"  应用图标上传URL: {software['app_icon_upload_url']}")