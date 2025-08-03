"""
Function: 爬取Hugging Face Weekly论文列表

CreateDay: 20250625
Author: HongfengAi
History:
20250625    HongfengAi  第一版
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
import fitz  # PyMuPDF for PDF processing
from PIL import Image
import io

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from configs import USER_AGENT, PAPER_EXPRESS_ROOT_PATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from crawler.crawler_utils import open_browser
from utils import set_proxy, unset_proxy, safe_title_func, get_previous_week
from wechat_utils.upload_material import WeChatPermanentMaterialUploader


class HFWeeklyPapersCrawler:
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
            
    def extract_pdf_cover(self, hf_url, paper_title, save_dir):
        """从论文PDF中提取封面图
        
        Args:
            hf_url: HuggingFace论文URL，如 https://huggingface.co/papers/2506.13585
            paper_title: 论文标题
            save_dir: 保存目录
            
        Returns:
            tuple: (local_path, upload_url)
        """
        # 转换HF URL为ArXiv PDF URL
        paper_id = hf_url.split('/')[-1]
        pdf_url = f"https://arxiv.org/pdf/{paper_id}"
        
        print(f"正在下载PDF: {pdf_url}")
        
        # 创建保存目录
        os.makedirs(save_dir, exist_ok=True)
        
        # 创建使用代理的session
        set_proxy()
        session = requests.Session()
        session.trust_env = True
        
        # 设置超时和重试
        session.mount('https://', requests.adapters.HTTPAdapter(max_retries=3))
        session.mount('http://', requests.adapters.HTTPAdapter(max_retries=3))
        
        # 添加请求头，模拟浏览器
        headers = {
            'User-Agent': USER_AGENT
        }
        
        # 下载PDF文件
        response = session.get(pdf_url, headers=headers, timeout=60)
        response.raise_for_status()
        
        unset_proxy()
        
        # 使用PyMuPDF处理PDF
        pdf_doc = fitz.open(stream=response.content, filetype="pdf")
        
        # 获取第一页
        first_page = pdf_doc[0]
        
        # 将第一页转换为图片 (设置较高的分辨率)
        mat = fitz.Matrix(2.0, 2.0)  # 2倍缩放以获得更高质量
        pix = first_page.get_pixmap(matrix=mat)
        
        # 将pixmap转换为PIL Image
        img_data = pix.tobytes("png")
        img = Image.open(io.BytesIO(img_data))
        
        # 调整图片尺寸为1200x648
        target_size = (1200, 648)
        
        # 计算裁剪区域以保持比例
        img_ratio = img.width / img.height
        target_ratio = target_size[0] / target_size[1]
        
        if img_ratio > target_ratio:
            # 图片太宽，需要裁剪宽度
            new_width = int(img.height * target_ratio)
            left = (img.width - new_width) // 2
            img = img.crop((left, 0, left + new_width, img.height))
        else:
            # 图片太高，需要裁剪高度，从顶部开始裁剪
            new_height = int(img.width / target_ratio)
            top = 0  # 从顶部开始裁剪
            img = img.crop((0, top, img.width, top + new_height))
        
        # 调整到目标尺寸
        img = img.resize(target_size, Image.LANCZOS)
        
        # 保存图片
        filename = "cover_material.png"
        filepath = os.path.join(save_dir, filename)
        img.save(filepath, "PNG", quality=95)
        
        # 关闭PDF文档
        pdf_doc.close()
        
        print(f"PDF封面图提取成功: {filepath}")
        
        # 上传到永久素材库
        upload_result = self.media_uploader.upload_specific_file(filepath)
        
        if upload_result:
            media_upload_url = upload_result['url']
            return filepath, media_upload_url
        else:
            return filepath, None
            

    def download_and_upload_media(self, media_url, media_type,
                                  paper_title, save_dir, hf_url=None):
        """下载论文封面图片并上传到素材库，如果是视频则改为提取PDF封面"""
        if not media_url:
            return None, None

        # 如果是视频，改为提取PDF封面
        if media_type == 'video' and hf_url:
            print(f"检测到视频，改为提取PDF封面: {paper_title}")
            return self.extract_pdf_cover(hf_url, paper_title, save_dir)

        # 创建保存目录
        os.makedirs(save_dir, exist_ok=True)
                    
        # 创建使用代理的session
        set_proxy()
        session = requests.Session()
        session.trust_env = True
        
        # 设置超时和重试
        session.mount('https://', requests.adapters.HTTPAdapter(max_retries=3))
        session.mount('http://', requests.adapters.HTTPAdapter(max_retries=3))
        
        # 添加请求头，模拟浏览器
        headers = {
            'User-Agent': USER_AGENT
        }
        
        # 下载媒体文件
        response = session.get(media_url, headers=headers, timeout=30)
        response.raise_for_status()
        
        # 生成安全的文件名
        safe_title = safe_title_func(paper_title)
        
        # 确定文件扩展名 (现在只处理图片)
        if 'jpeg' in media_url.lower() or 'jpg' in media_url.lower():
            ext = '.jpg'
        elif 'png' in media_url.lower():
            ext = '.png'
        else:
            ext = '.png'  # 默认
                
        filename = f"cover_material{ext}"
        filepath = os.path.join(save_dir, filename)
        
        # 保存文件
        with open(filepath, 'wb') as f:
            f.write(response.content)
        
        unset_proxy()
        
        # 处理图片尺寸调整
        if media_type == 'image':
            try:
                img = Image.open(filepath)
                target_size = (1200, 648)
                
                # 计算裁剪区域以保持比例
                img_ratio = img.width / img.height
                target_ratio = target_size[0] / target_size[1]
                
                if img_ratio > target_ratio:
                    # 图片太宽，需要裁剪宽度
                    new_width = int(img.height * target_ratio)
                    left = (img.width - new_width) // 2
                    img = img.crop((left, 0, left + new_width, img.height))
                else:
                    # 图片太高，需要裁剪高度，从顶部开始裁剪
                    new_height = int(img.width / target_ratio)
                    top = 0  # 从顶部开始裁剪
                    img = img.crop((0, top, img.width, top + new_height))
                
                # 调整到目标尺寸
                img = img.resize(target_size, Image.LANCZOS)
                img.save(filepath, quality=95)
                
            except Exception as e:
                print(f"调整图片尺寸时出错: {e}")
        
        # 上传到永久素材库
        upload_result = self.media_uploader.upload_specific_file(filepath)
            
        if upload_result:
            media_upload_url = upload_result['url']
            return filepath, media_upload_url
        else:
            return filepath, None
            
    
    
    def crawl_weekly_paper_list(self, week_url, save_dir, topk):
        """
        爬取指定周的论文列表
        
        Args:
            week_url: 周论文列表URL，如 https://huggingface.co/papers/week/2025-W26
            save_dir: 保存目录
            
        Returns:
            list: 论文信息列表
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
            
            # 查找所有论文条目
            # 根据页面结构，论文条目通常在特定的容器中
            paper_elements = self.browser.find_elements(By.XPATH, '/html/body/div[1]/main/div[2]/section/div[2]/*')
            paper_elements = paper_elements[:min(topk, len(paper_elements))]

            papers_data = []
            
            for i, paper_element in enumerate(paper_elements):
                try:
                    paper_info = {}
                    
                    # 提取论文标题
                    title_element = paper_element.find_element(By.XPATH, './/h3/a')
                    paper_info['title'] = title_element.text.strip()

                    # 获取论文链接
                    paper_info['hf_url'] = title_element.get_attribute('href')

                    # 提取点赞数
                    like_element = paper_element.find_element(By.XPATH, './/a/div/div')
                    paper_info['likes'] = int(like_element.text.strip())

                    # 提取作者数量
                    author_element = paper_element.find_element(By.XPATH, './/div/a/ul/li[6]/div')
                    paper_info['author_count'] = int(author_element.text.strip().split(' ')[0].replace('·\n',''))

                    # 提取GitHub stars
                    github_page_elements = paper_element.find_elements(By.XPATH, './article/div[2]/div/div[2]/div/div/*')
                    if len(github_page_elements) == 2:
                        github_element = github_page_elements[0]
                        paper_info['github_stars'] = github_element.find_element(By.XPATH, './span').text.strip()
                    else:
                        paper_info['github_stars'] = None

                    # 提取论文封面图片/视频
                    # 查找article下的媒体链接
                    media_link_element = paper_element.find_element(By.XPATH, './a')
                    
                    # 检查是否有视频
                    media_url = None
                    media_type = None
                        
                    try:
                        video_element = media_link_element.find_element(By.XPATH, './video')
                        media_url = video_element.get_attribute('src')
                        media_type = 'video'
                    except NoSuchElementException:
                        # 如果没有视频，查找图片
                        try:
                            img_element = media_link_element.find_element(By.XPATH, './img')
                            media_url = img_element.get_attribute('src')
                            media_type = 'image'
                        except NoSuchElementException:
                            media_url = None
                            media_type = None
                        
                    if media_url:
                        # 下载并上传媒体文件
                        safe_paper_title = safe_title_func(paper_info['title'])
                        cover_dir = os.path.join(save_dir, f'{i+1}_{safe_paper_title}/covers')
                        local_path, upload_url = self.download_and_upload_media(
                            media_url, 
                            media_type,
                            paper_info['title'], 
                            cover_dir,
                            paper_info['hf_url']
                        )
                        paper_info['cover_url'] = media_url
                        paper_info['cover_local_path'] = local_path
                        paper_info['cover_upload_url'] = upload_url
                        paper_info['cover_type'] = media_type
                    else:
                        paper_info['cover_url'] = None
                        paper_info['cover_local_path'] = None
                        paper_info['cover_upload_url'] = None
                        paper_info['cover_type'] = None
                            
                    # 添加索引
                    paper_info['index'] = i + 1
                    
                    papers_data.append(paper_info)
                    print(f"已处理第 {i+1} 篇论文: {paper_info['title'][:50]}...")
                    
                except Exception as e:
                    print(f"处理第 {i+1} 篇论文时出错: {e}")
                    continue
            
            # 保存数据到JSON文件
            output_file = os.path.join(save_dir, f"paper_list_{week_url.split('/')[-1]}.json")
            os.makedirs(save_dir, exist_ok=True)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(papers_data, f, ensure_ascii=False, indent=2)
            
            print(f"爬取完成！共获取 {len(papers_data)} 篇论文信息")
            print(f"数据已保存到: {output_file}")
            
            return papers_data
            
        except Exception as e:
            print(f"爬取过程中出错: {e}")
            return []
            
        finally:
            self.close_browser()
    

    def crawl_specific_week(self, year, week, topk=10):
        """
        爬取指定年份和周的论文
        
        Args:
            year: 年份，如 2025
            week: 周数，如 W26
            topk: 获取前k篇论文
            
        Returns:
            list: 论文信息列表
        """
        week_url = f"https://huggingface.co/papers/week/{year}-{week}"
        return self.crawl_weekly_paper_list(week_url, os.path.join(PAPER_EXPRESS_ROOT_PATH, f"{year}_{week}"), topk)




if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("--topk", type=int, default=10, help="Top k papers")
    args = arg_parser.parse_args()
    topk = args.topk

    crawler = HFWeeklyPapersCrawler()

    # 获取上一周
    prev_year, prev_week = get_previous_week()
    print(f"上一周: {prev_year}年 {prev_week}")
    # prev_week = 'W25'
    # 爬取上一周的论文
    papers = crawler.crawl_specific_week(prev_year, prev_week, topk)
    
    # 打印结果
    for paper in papers:
        print(f"\n论文 {paper['index']}: {paper['title']}")
        print(f"  点赞数: {paper['likes']}")
        print(f"  作者数: {paper['author_count']}")
        print(f"  GitHub Stars: {paper['github_stars']}")
        print(f"  HF URL: {paper['hf_url']}")
        print(f"  封面类型: {paper['cover_type']}")
        print(f"  封面本地路径: {paper['cover_local_path']}")
        print(f"  封面上传URL: {paper['cover_upload_url']}")