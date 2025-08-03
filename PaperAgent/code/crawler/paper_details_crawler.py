"""
Function: 从paper_list爬取每篇论文的详细信息

CreateDay: 20250625
Author: HongfengAi
History:
20250625    HongfengAi  第一版
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
from datetime import datetime
# 添加PDF处理相关导入
import PyPDF2 # pip install PyPDF2
import fitz  # pip install pymupdf
from PIL import Image
import io
from pdf2image import convert_from_path
from transformers import AutoProcessor, AutoModelForCausalLM
import torch


sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from configs import USER_AGENT, PAPER_EXPRESS_ROOT_PATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from crawler.crawler_utils import open_browser
from utils import set_proxy, unset_proxy, safe_title_func
from wechat_utils.upload_material import WeChatPermanentMaterialUploader


class PaperDetailsCrawler:
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
    

    def extract_github_url_from_pdf(self, pdf_url):
        """
        从PDF第一页提取GitHub URL
        
        Args:
            pdf_url: PDF文件的URL
            
        Returns:
            str or None: 找到的GitHub URL，如果没找到则返回None
        """
            
        try:
            print(f"🔍 正在从PDF第一页提取GitHub URL: {pdf_url}")
            
            # 下载PDF文件
            headers = {
                'User-Agent': USER_AGENT
            }
            response = requests.get(pdf_url, headers=headers, timeout=30, stream=True)
            response.raise_for_status()
            
            # 将PDF内容写入临时文件
            temp_pdf_path = "temp_paper.pdf"
            with open(temp_pdf_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            text_content = ""
            
            # 尝试使用PyPDF2
            try:
                with open(temp_pdf_path, 'rb') as pdf_file:
                    pdf_reader = PyPDF2.PdfReader(pdf_file)
                    if len(pdf_reader.pages) > 0:
                        text_content = pdf_reader.pages[0].extract_text()
            except Exception as e:
                print(f"❌ PDF文本提取失败: {e}")
                # 清理临时文件
                if os.path.exists(temp_pdf_path):
                    os.remove(temp_pdf_path)
                return None
            
            # 清理临时文件
            if os.path.exists(temp_pdf_path):
                os.remove(temp_pdf_path)
            
            if not text_content:
                print("❌ 无法从PDF第一页提取文本内容")
                return None
            
            # 使用正则表达式查找GitHub URL
            github_patterns = [
                r'https?://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+',
                r'github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+',
                r'https?://www\.github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+'
            ]
            
            for pattern in github_patterns:
                matches = re.findall(pattern, text_content, re.IGNORECASE)
                if matches:
                    # 确保URL是完整的
                    github_url = matches[0]
                    if not github_url.startswith('http'):
                        github_url = 'https://' + github_url
                    
                    print(f"✅ 从PDF第一页成功提取GitHub URL: {github_url}")
                    return github_url
            
            print("❌ PDF第一页中未找到GitHub URL")
            return None
            
        except requests.RequestException as e:
            print(f"❌ 下载PDF文件失败: {e}")
            return None
        except Exception as e:
            print(f"❌ 从PDF提取GitHub URL时发生错误: {e}")
            return None

    def extract_images_from_pdf(self, pdf_url, save_dir, max_images=5):
        """
        使用TF-ID模型从PDF中抽取表格/图片，只抽取max_images张，上传到微信素材库，返回image url列表。
        """
        try:
            print(f"🔍 正在从PDF中抽取表格/图片: {pdf_url}")
            set_proxy()
            headers = {'User-Agent': USER_AGENT}
            response = requests.get(pdf_url, headers=headers, timeout=60)
            response.raise_for_status()
            # 保存临时PDF文件
            os.makedirs(save_dir, exist_ok=True)
            temp_pdf_path = os.path.join(save_dir, "temp_paper.pdf")
            with open(temp_pdf_path, 'wb') as f:
                f.write(response.content)

            # ===== TF-ID模型推理部分 =====
            model_id = "yifeihu/TF-ID-base"
            images = convert_from_path(temp_pdf_path)
            model = AutoModelForCausalLM.from_pretrained(model_id, trust_remote_code=True)
            processor = AutoProcessor.from_pretrained(model_id, trust_remote_code=True)
            print("Model loaded: ", model_id)
            unset_proxy()
            
            img_urls = []
            img_count = 0
            for i, image in enumerate(images):
                # 推理
                prompt = "<OD>"
                inputs = processor(text=prompt, images=image, return_tensors="pt")
                with torch.no_grad():
                    generated_ids = model.generate(
                        input_ids=inputs["input_ids"],
                        pixel_values=inputs["pixel_values"],
                        max_new_tokens=1024,
                        do_sample=False,
                        num_beams=3
                    )
                generated_text = processor.batch_decode(generated_ids, skip_special_tokens=False)[0]
                annotation = processor.post_process_generation(generated_text, task="<OD>", image_size=(image.width, image.height))["<OD>"]
                # 裁剪并保存图片
                for j, bbox in enumerate(annotation['bboxes']):
                    label = annotation['labels'][j]
                    x1, y1, x2, y2 = bbox
                    cropped_image = image.crop((x1, y1, x2, y2))
                    img_path = os.path.join(save_dir, f"page_{i}_{label}_{j}.png")
                    cropped_image.save(img_path)
                    # 上传到微信
                    upload_result = self.media_uploader.upload_specific_file(img_path)
                    if upload_result and upload_result.get('success') and upload_result.get('url'):
                        img_urls.append(upload_result['url'])
                    img_count += 1
                    if img_count >= max_images:
                        break
                if img_count >= max_images:
                    break
            # 清理临时PDF
            if os.path.exists(temp_pdf_path):
                os.remove(temp_pdf_path)
            print(f"✓ 成功抽取并上传 {len(img_urls)} 张图片")
            return img_urls
        except Exception as e:
            print(f"❌ PDF图片抽取失败: {e}")
            return []

    def extract_paper_details(self, hf_url):
        """
        从Hugging Face论文页面提取详细信息
        
        Args:
            hf_url: 论文在HF上的URL
            
        Returns:
            dict: 论文详细信息
        """
        # 访问论文页面
        print(f"正在访问论文页面: {hf_url}")
        self.browser.get(hf_url)
        
        # 等待页面加载
        time.sleep(3)
        
        paper_details = {}
        
        # 提取论文发表时间
        date_element = self.browser.find_element(By.XPATH, "/html/body/div[1]/main/div/section[1]/div/div[1]/div[2]/div[1]")
        paper_details['published_date'] = date_element.text

        # 提取作者列表
        author_elements = self.browser.find_elements(By.XPATH, "/html/body/div[1]/main/div/section[1]/div/div[1]/div[4]/*")
        authors = []
        for author_element in author_elements:
            if author_element.text == 'Authors:':
                pass
            else:
                authors.append(author_element.text.replace("\n,", ''))
        paper_details['authors'] = authors
        
        # 提取AI生成总结
        try:
            ai_summary_element = self.browser.find_element(By.XPATH, "/html/body/div/main/div/section[1]/div/div[2]/div/div/p")
            paper_details['ai_summary'] = ai_summary_element.text
        except NoSuchElementException:
            paper_details['ai_summary'] = ""
            pass
        

        # 提取摘要
        abstract_element = self.browser.find_element(By.XPATH, "/html/body/div/main/div/section[1]/div/div[2]/div/p")
        paper_details['abstract'] = abstract_element.text

        # 提取PDF链接和arXiv信息
        link_elements = self.browser.find_elements(By.XPATH, "/html/body/div[1]/main/div/section[1]/div/div[3]/*")
        paper_details['pdf_url'] = None
        paper_details['github_url'] = None
        for link_element in link_elements:
            if link_element.text == 'View PDF' or link_element.text == 'View arXiv page':
                paper_details['pdf_url'] = link_element.get_attribute('href')
            elif 'GitHub' in link_element.text:
                paper_details['github_url'] = link_element.get_attribute('href')
        
        # 如果没有找到GitHub URL但有PDF URL，尝试从PDF第一页提取
        if paper_details['github_url'] is None and paper_details['pdf_url'] is not None:
            print("🔍 Hugging Face页面未找到GitHub URL，尝试从PDF第一页提取...")
            pdf_github_url = self.extract_github_url_from_pdf(paper_details['pdf_url'])
            if pdf_github_url:
                paper_details['github_url'] = pdf_github_url
            else:
                print("❌ PDF第一页也未找到GitHub URL")
        
        return paper_details


    def crawl_papers_details_from_list(self, paper_list_file, output_dir, max_papers=None):
        """
        从论文列表文件中读取论文信息并爬取详情
        
        Args:
            paper_list_file: 论文列表JSON文件路径
            output_dir: 输出目录
            max_papers: 最大爬取论文数量，None表示爬取所有
            
        Returns:
            None
        """
        # 读取论文列表
        with open(paper_list_file, 'r', encoding='utf-8') as f:
            papers_list = json.load(f)
        
        print(f"找到 {len(papers_list)} 篇论文")
        
        # 限制爬取数量
        if max_papers:
            papers_list = papers_list[:max_papers]
            print(f"限制爬取前 {max_papers} 篇论文")
        
        # 创建输出目录
        os.makedirs(output_dir, exist_ok=True)
        
        crawled_papers = []
        
        for i, paper in enumerate(papers_list):
            print(f"\n正在处理第 {i+1}/{len(papers_list)} 篇论文: {paper.get('title', 'Unknown')}")

            # 打开浏览器
            self.open_browser()

            # 爬取论文详情
            paper_details = self.extract_paper_details(paper['hf_url'])

            # 关闭浏览器
            self.close_browser()
            
            # 合并基本信息和详细信息
            combined_paper_info = {
                **paper,  # 原有的基本信息
                **paper_details  # 新爬取的详细信息
            }
            
            # 新增：抽取论文图片并上传
            paper_img_urls = []
            if combined_paper_info.get('pdf_url'):
                safe_title = safe_title_func(paper.get('title', f'{i+1}_paper'))
                paper_img_dir = os.path.join(output_dir, f"{i+1}_{safe_title}", "paper_imgs")
                paper_img_urls = self.extract_images_from_pdf(combined_paper_info['pdf_url'], paper_img_dir, max_images=5)
            combined_paper_info['paper_img_urls'] = paper_img_urls
            crawled_papers.append(combined_paper_info)
            
            # 为每篇论文创建单独的文件
            safe_title = safe_title_func(paper.get('title', f'{i+1}_paper'))
            paper_path = os.path.join(output_dir, f"{i+1}_{safe_title}")
            paper_file = os.path.join(paper_path, f"paper_details.json")
            
            with open(paper_file, 'w', encoding='utf-8') as f:
                json.dump(combined_paper_info, f, ensure_ascii=False, indent=2)
            
            print(f"已保存论文详情到: {paper_file}")
            
            # 避免请求过快
            time.sleep(2)
        
        # 保存所有论文的详细信息汇总
        summary_file = os.path.join(output_dir, "all_papers_details.json")
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(crawled_papers, f, ensure_ascii=False, indent=2)
        
        print(f"\n爬取完成！共处理 {len(crawled_papers)} 篇论文")
        print(f"详细信息已保存到: {summary_file}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='论文详情爬虫')
    parser.add_argument('--paper_list', type=str, required=True, default='C:/Users/alvin/Downloads/paper_express/2025_W25/paper_list_2025-W25.json', help='论文列表JSON文件路径')
    parser.add_argument('--output_dir', type=str, required=True, default='C:/Users/alvin/Downloads/paper_express/2025_W25', help='输出目录')
    parser.add_argument('--max_papers', type=int, required=True, default=10, help='最大爬取论文数量')
    
    args = parser.parse_args()
    
    crawler = PaperDetailsCrawler()
    crawler.crawl_papers_details_from_list(
        paper_list_file=args.paper_list,
        output_dir=args.output_dir,
        max_papers=args.max_papers
    )

