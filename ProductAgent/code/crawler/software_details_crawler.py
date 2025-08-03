"""
Function: 从software_list爬取每款软件的详细信息

CreateDay: 20250702
Author: HongfengAi
History:
20250702    HongfengAi  第一版
"""
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
import tempfile
import urllib.parse
from datetime import datetime


sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from configs import USER_AGENT, SOFTWARE_EXPRESS_ROOT_PATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from crawler.crawler_utils import open_browser
from utils import set_proxy, unset_proxy, safe_title_func
from wechat_utils.upload_material import WeChatPermanentMaterialUploader

class SoftwareDetailsCrawler:
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
            filename = f"image_{int(time.time())}.png"
            
            # 确保文件名有正确的扩展名
            if not any(filename.lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp']):
                filename += '.png'
            
            local_path = os.path.join(save_dir, filename)
            
            # 下载图片
            print(f"正在下载图片: {image_url}")
            session = requests.Session()
            session.trust_env = False
            
            response = session.get(image_url, timeout=60, stream=True)
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
        

    def extract_software_details(self, producthunt_url:str, title:str):
        """
        从Product Hunt软件页面提取详细信息
        
        Args:
            producthunt_url: 软件在Product Hunt上的URL
            title: 软件标题
        Returns:
            dict: 软件详细信息
        """
        # 访问软件页面
        print(f"正在访问软件页面: {producthunt_url}")
        self.browser.get(producthunt_url)
        
        # 等待页面加载
        time.sleep(4)
        
        # 处理可能的通知弹窗
        notification_buttons = self.browser.find_elements(By.XPATH, "//button[contains(text(), 'Block') or contains(text(), '阻止') or contains(text(), 'Not now') or contains(text(), '以后再说')]")
        if notification_buttons:
            notification_buttons[0].click()
            print("已关闭通知弹窗")
            time.sleep(1)
        
        software_details = {}
        
        # 提取软件描述
        try:
            content_discription = self.browser.find_element(By.XPATH, "//*[@id='root-container']/div[3]/div/main/div[1]/div[2]/div/p")
        except NoSuchElementException:
            content_discription = self.browser.find_element(By.XPATH, "//*[@id='root-container']/div[3]/div/main/div[1]/div[1]/div/p")
        except NoSuchElementException:
            content_discription = ""

        software_details['content_discription'] = content_discription.text

        # 提取星级评分
        try:    
            rating_element = self.browser.find_element(By.XPATH, "//*[@id='root-container']/div[3]/div/main/div[1]/section/div[1]/span/a[1]/span")
            software_details['rating'] = rating_element.text
        except NoSuchElementException:
            software_details['rating'] = ""

        # 粉丝数 1.2K followers
        fans_element = self.browser.find_element(By.XPATH, "//*[@id='root-container']/div[3]/div/main/div[1]/section/div[1]/span/p")
        software_details['fans'] = fans_element.text.replace(' followers', '').strip()

        # 产品网站
        product_website_element = self.browser.find_element(By.XPATH, "//*[@id='root-container']/div[3]/div/main/div[1]/section/div[2]/a")
        software_details['product_website'] = product_website_element.get_attribute('href')

        # 抽取图片
        software_details['images_upload_url'] = []
        image_elements = self.browser.find_elements(By.XPATH, "//*[@id='root-container']/div[3]/div/main/section[1]/div/div[1]/section/*")
        if not image_elements:
            # 如果第一个路径没有找到元素，尝试第二个路径
            image_elements = self.browser.find_elements(By.XPATH, "//*[@id='root-container']/div[3]/div/main/div[2]/div[1]/div/div[1]/section/*")
        if not image_elements:
            image_elements = self.browser.find_elements(By.XPATH, "//*[@id='root-container']/div[3]/div/main/div[3]/div[1]/div/div[1]/section/*")
        if not image_elements:
            image_elements = self.browser.find_elements(By.XPATH, "//*[@id='root-container']/div[3]/div/main/div[3]/div/div/div[3]/div/div[1]/section/*")

        for image_element in image_elements:
            try:
                image_element = image_element.find_element(By.XPATH, ".//div/img")
                
                # 优先获取高清图片URL
                image_url = None
                
                # 1. 尝试获取srcset中的最高分辨率图片
                srcset = image_element.get_attribute('srcset')
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
                    image_url = image_element.get_attribute('src')
                
                # 3. URL优化：获取更高分辨率的原图
                # if image_url and 'ph-files.imgix.net' in image_url:
                #     # 提取基础URL（文件ID部分）
                #     if '?' in image_url:
                #         base_url = image_url.split('?')[0]
                #     else:
                #         base_url = image_url
                    
                    # 重构为高清参数，同比例缩放2倍
                    # optimized_url = f"{base_url}?auto=format&fit=max&q=95&dpr=2"
                    # print(f"原始URL: {image_url}")
                    # print(f"优化为2倍分辨率URL: {optimized_url}")
                    # image_url = optimized_url
                
                if not image_url:
                    print("未找到有效的图片URL，跳过")
                    continue
                    
            except NoSuchElementException:
                continue
                
            local_path = self.download_image_from_url(image_url)
            result = self.media_uploader.upload_specific_file(local_path, title=title)
            # 删除本地图片
            os.remove(local_path)
            try:
                software_details['images_upload_url'].append(result['url'])
            except Exception as e:
                print(f"图片上传失败: {e}")

        return software_details


    def crawl_software_details_from_list(self, software_list_file, output_dir, max_software=None):
        """
        从论文列表文件中读取论文信息并爬取详情
        
        Args:
            software_list_file: 软件列表JSON文件路径
            output_dir: 输出目录
            max_software: 最大爬取软件数量，None表示爬取所有
            
        Returns:
            None
        """
        # 读取论文列表
        with open(software_list_file, 'r', encoding='utf-8') as f:
            software_list = json.load(f)
        
        print(f"找到 {len(software_list)} 款软件")
        
        # 限制爬取数量
        if max_software:
            software_list = software_list[:max_software]
            print(f"限制爬取前 {max_software} 款软件")
        
        # 创建输出目录
        os.makedirs(output_dir, exist_ok=True)
        
        crawled_software = []
        
        for i, software in enumerate(software_list):
            print(f"\n正在处理第 {i+1}/{len(software_list)} 款软件: {software.get('title', 'Unknown')}")

            # 打开浏览器
            self.open_browser()

            # 爬取软件详情
            software_details = self.extract_software_details(software['producthunt_url'], software['title'])

            # 关闭浏览器
            self.close_browser()
            
            # 合并基本信息和详细信息
            combined_software_info = {
                **software,  # 原有的基本信息
                **software_details  # 新爬取的详细信息
            }
            
            crawled_software.append(combined_software_info)
            
            # 为每篇论文创建单独的文件
            safe_title = safe_title_func(software.get('title', f'{i+1}_software'))
            software_path = os.path.join(output_dir, f"{software['index']}_{safe_title}")
            software_file = os.path.join(software_path, f"software_details.json")
            
            with open(software_file, 'w', encoding='utf-8') as f:
                json.dump(combined_software_info, f, ensure_ascii=False, indent=2)
            
            print(f"已保存软件详情到: {software_file}")
            
            # 避免请求过快
            time.sleep(2)
        
        # 保存所有软件的详细信息汇总
        summary_file = os.path.join(output_dir, "all_software_details.json")
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(crawled_software, f, ensure_ascii=False, indent=2)
        
        print(f"\n爬取完成！共处理 {len(crawled_software)} 款软件")
        print(f"详细信息已保存到: {summary_file}")


if __name__ == "__main__":
    # import argparse
    
    # parser = argparse.ArgumentParser(description='软件详情爬虫')
    # parser.add_argument('--software_list', type=str, required=True, default='C:/Users/alvin/Downloads/software_express/2025_26/software_list_26.json', help='软件列表JSON文件路径')
    # parser.add_argument('--output_dir', type=str, required=True, default='C:/Users/alvin/Downloads/software_express/2025_26', help='输出目录')
    # parser.add_argument('--max_software', type=int, required=True, default=10, help='最大爬取软件数量')
    
    # args = parser.parse_args()
    
    # crawler = SoftwareDetailsCrawler()
    # crawler.crawl_software_details_from_list(
    #     software_list_file=args.software_list,
    #     output_dir=args.output_dir,
    #     max_software=args.max_software
    # )
    
    software_list = 'C:/Users/alvin/Downloads/software_express/2025_26/software_list_26.json'
    output_dir = 'C:/Users/alvin/Downloads/software_express/2025_26'
    max_software = 10
    
    crawler = SoftwareDetailsCrawler()
    crawler.crawl_software_details_from_list(
        software_list_file=software_list,
        output_dir=output_dir,
        max_software=max_software
    )
