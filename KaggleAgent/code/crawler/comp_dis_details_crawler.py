"""
Function: 爬取比赛的给定discussion的内容

CreateDay: 20250602
Author: HongfengAi
History:
20250602    HongfengAi  第一版
"""
import re
import json
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning) # 禁用SSL警告

import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.append("D:/KaggleAgent/code")
from crawler.crawler_utils import open_browser
from configs import COMP_REVIEW_ROOT_PATH, USER_AGENT
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import safe_title_func


class CompDisDetailsCrawler():
    def __init__(self):
        pass
        
    def open_browser(self):
        self.browser, self.wait = open_browser()   
    
    def parse_page(self, url):
        self.url = url
        # 打开模拟浏览器
        self.open_browser()
        # 进入点击进入Competitions详细列表网页
        self.browser.get(self.url)
        time.sleep(8)  # 等待页面加载
        # 下拉到最低，保证页面完整加载
        self.browser.execute_script("window.scrollTo(0, document.body.scrollHeight)")
        time.sleep(4)  # 等待页面加载

        # 提取比赛标题
        # comp_title = self.browser.find_element(By.XPATH, '//*[@id="site-content"]/div[2]/div/div/div[2]/div[2]/div[1]/h1').text
        comp_title = WebDriverWait(self.browser, 20).until(
                        EC.presence_of_element_located((By.XPATH, '//*[@id="site-content"]/div[2]/div/div/div[2]/div[2]/div[1]/h1'))
                    ).text
        
        # 提取讨论帖的标题
        title = self.browser.find_element(By.XPATH, '//*[@id="site-content"]/div[2]/div/div/div[6]/div/div/div[1]/div[1]/h3').text

        # 智能提取作者排名和发布时间
        author_rank, post_time = self.extract_author_and_time()
        # 若没有排名，超级极大概率不是高分方案，可以直接跳过爬取
        if author_rank == "未知":
            print(f"讨论帖：{title} 不存在排名，已跳过。")
            self.browser.quit()
            return None
        
        author_rank_no = re.search(r'(\d+)(?:TH|RD|ST|ND)', author_rank)
        if author_rank_no:
            author_rank_no = author_rank_no.group(1)
            if int(author_rank_no) > 100:
                print(f"讨论帖：{title} 排名{author_rank_no} > 100，已跳过。")
                self.browser.quit()
                return None
        
        # 提取主要内容
        content_div = self.browser.find_element(By.XPATH, '//*[@id="site-content"]/div[2]/div/div/div[6]/div/div/div[1]/div[1]/div[3]/div/div')

        # 合规化标题
        comp_safe_title = safe_title_func(comp_title)
        dis_safe_title = safe_title_func(title)

        # 创建以比赛title命名的文件夹
        folder_path = f'{COMP_REVIEW_ROOT_PATH}/{comp_safe_title}/discussion_details/{dis_safe_title}'
        os.makedirs(folder_path, exist_ok=True)
        
        # 转换为markdown格式，传入文件夹路径
        markdown_content = self.convert_to_markdown(content_div, comp_safe_title, dis_safe_title)
        
        # 组合完整的markdown内容
        full_markdown = f"""# {title}

**Author Rank**: {author_rank}

**Publish Time**: {post_time}

**Link**: {self.url}

---

{markdown_content}
"""
        
        # 保存为markdown文件到对应的文件夹下
        file_path = f'{folder_path}/discussion_content.md'
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(full_markdown)
            
        print(f'内容已保存到: {file_path}')
        self.browser.quit()
        return full_markdown
            
            
    def convert_to_markdown(self, element, comp_safe_title, dis_safe_title):
        """将HTML元素转换为markdown格式"""
        markdown = ""
        img_no = 1
        img_name2scr_dict = {}

        # 处理所有子元素
        for child in element.find_elements(By.XPATH, './/*'):
            tag_name = child.tag_name
            
            if tag_name == 'p':
                # 处理段落，包括段落内的链接
                paragraph_text = self.process_element_with_links(child)
                if paragraph_text.strip():
                    markdown += paragraph_text + "\n\n"
                
            elif tag_name == 'h1':
                heading_text = self.process_element_with_links(child)
                markdown += f"# {heading_text}\n\n"
            elif tag_name == 'h2':
                heading_text = self.process_element_with_links(child)
                markdown += f"## {heading_text}\n\n"
            elif tag_name == 'h3':
                heading_text = self.process_element_with_links(child)
                markdown += f"### {heading_text}\n\n"
            
            # elif tag_name == 'a':
            #     # 处理独立的链接
            #     link_text = child.text
            #     link_url = child.get_attribute('href')
            #     if link_text and link_url:
            #         markdown += f"[{link_text}]({link_url})"
            #     elif link_url:
            #         markdown += f"[{link_url}]({link_url})"
            #     else:
            #         markdown += link_text or ""
            
            elif tag_name == 'ul':
                # 处理无序列表
                items = child.find_elements(By.TAG_NAME, 'li')
                for item in items:
                    item_text = self.process_element_with_links(item)
                    markdown += f"- {item_text}\n"
                markdown += "\n"
                
            elif tag_name == 'ol':
                # 处理有序列表
                items = child.find_elements(By.TAG_NAME, 'li')
                for i, item in enumerate(items, 1):
                    item_text = self.process_element_with_links(item)
                    markdown += f"{i}. {item_text}\n"
                markdown += "\n"
                
            elif tag_name == 'table':
                # 处理表格
                # 获取表头
                headers = child.find_elements(By.TAG_NAME, 'th')
                # markdown += '<table>\n'
                if headers:
                    header_row = "| " + " | ".join([h.text for h in headers]) + " |"
                    separator = "| " + " | ".join(["---" for _ in headers]) + " |"
                    markdown += header_row + "\n" + separator + "\n"
                
                # 获取表格内容
                rows = child.find_elements(By.TAG_NAME, 'tr')
                for row in rows:
                    cells = row.find_elements(By.TAG_NAME, 'td')
                    if cells:
                        row_text = "| " + " | ".join([cell.text for cell in cells]) + " |"
                        markdown += row_text + "\n"
                # markdown += '\n</table>'
                markdown += "\n"
                
            elif tag_name == 'img':
                # 处理图片
                alt_text = child.get_attribute('alt')
                src = child.get_attribute('src')
                # 创建图片保存目录到对应的title文件夹下
                image_dir = f'{COMP_REVIEW_ROOT_PATH}/{comp_safe_title}/discussion_details/{dis_safe_title}/images'
                if not os.path.exists(image_dir):
                    os.makedirs(image_dir)
                
                # 完整的保存路径
                file_name = f"image_{img_no}.png"  # 默认使用png格式
                save_path = os.path.join(image_dir, file_name)
                img_name2scr_dict[file_name] = save_path

                try:
                    # 使用requests直接下载图片内容到指定的images文件夹
                    # 禁用代理以避免代理连接问题
                    proxies = {
                        'http': 'http://127.0.0.1:7890',
                        'https': 'http://127.0.0.1:7890'
                    }
                    response = requests.get(
                        src, 
                        headers={'User-Agent': USER_AGENT}, 
                        timeout=30,  # 增加超时时间
                        proxies=proxies,  # 使用代理
                        verify=False  # 忽略SSL证书验证
                    )
                    if response.status_code == 200:
                        with open(save_path, 'wb') as f:
                            f.write(response.content)
                            img_no += 1
                        markdown += f"![{file_name}](images/{file_name})\n\n"
                        print(f'图片已保存: {save_path}')
                    else:
                        print(f'图片下载失败，状态码: {response.status_code}，URL: {src}')
                        # 即使下载失败，也保留markdown引用
                        markdown += f"![{file_name}]({src})\n\n"
                        
                except Exception as e:
                    print(f'下载图片时出错: {e}，URL: {src}')
                    # 保留原始URL作为备选
                    markdown += f"![{file_name}]({src})\n\n"
                
            elif tag_name == 'blockquote':
                # 处理引用
                quote_text = self.process_element_with_links(child)
                markdown += f"> {quote_text}\n\n"
                
            elif tag_name == 'pre':
                # 处理代码块
                code_text = child.text.strip()
                if code_text:
                    markdown += f"```\n{code_text}\n```\n\n"
                
            # elif tag_name == 'code':
            #     # 处理独立的代码标签（通常被pre包围，这里作为备用）
            #     code_text = child.text.strip()
            #     if code_text:
            #         markdown += f"`{code_text}`\n\n"
        # 保存图片来源
        img_name2scr_dict_file_path = f'{COMP_REVIEW_ROOT_PATH}/{comp_safe_title}/discussion_details/{dis_safe_title}/img_name2scr_dict.json'
        with open(img_name2scr_dict_file_path, 'w', encoding='utf-8') as f:
            json.dump(img_name2scr_dict, f, ensure_ascii=False, indent=4)

        return markdown.strip()

    def process_element_with_links(self, element):
        """处理包含链接和代码的元素，将链接和代码转换为markdown格式"""
        try:
            # 获取元素的HTML内容
            html_content = element.get_attribute('innerHTML')
            if not html_content:
                return element.text or ""
            
            # 使用正则表达式查找链接
            import re
            
            # 首先处理代码标签，避免被后续的HTML标签清理影响
            # 匹配 <code>text</code> 格式
            code_pattern = r'<code[^>]*>([^<]*)</code>'
            
            def replace_code(match):
                code_text = match.group(1).strip()
                return f"`{code_text}`"
            
            # 替换HTML中的代码为markdown格式
            processed_content = re.sub(code_pattern, replace_code, html_content)
            
            # 匹配 <a href="..." ...>text</a> 格式
            link_pattern = r'<a[^>]*href=["\']([^"\']*)["\'][^>]*>([^<]*)</a>'
            
            def replace_link(match):
                url = match.group(1)
                text = match.group(2).strip()
                if text:
                    return f"[{text}]({url})"
                else:
                    return f"[{url}]({url})"
            
            # 替换HTML中的链接为markdown格式
            processed_content = re.sub(link_pattern, replace_link, processed_content)
            
            # 移除剩余的HTML标签，保留文本和已处理的markdown格式
            # 但保留已处理的代码和链接格式
            text_content = re.sub(r'<[^>]+>', '', processed_content)
            
            return text_content.strip()
            
        except Exception as e:
            print(f"处理元素链接和代码时出错: {e}")
            return element.text or ""

    def extract_author_and_time(self):
        """智能提取作者排名和发布时间"""
        try:
            # 获取包含span的父级div
            parent_div = self.browser.find_element(By.XPATH, '//*[@id="site-content"]/div[2]/div/div/div[6]/div/div/div[1]/div[1]/div[1]/div')
            
            # 获取所有span元素
            span_elements = parent_div.find_elements(By.XPATH, './/span/span')
            
            print(f"找到 {len(span_elements)} 个span元素")
            
            author_rank = "未知"
            post_time = "未知"
            
            if len(span_elements) == 1:
                # 只有1个span，它是发布时间
                post_time_element = span_elements[0]
                post_time = post_time_element.get_attribute('title') or post_time_element.text
                print("情况1：只有发布时间，无作者排名")
                
            elif len(span_elements) >= 2:
                # 有2个或更多span，第一个是作者排名，第二个是发布时间
                author_rank_element = span_elements[0]
                post_time_element = span_elements[1]
                
                author_rank = author_rank_element.text or "未知"
                post_time = post_time_element.get_attribute('title') or post_time_element.text
                print("情况2：有作者排名和发布时间")
                
            else:
                print("情况3：未找到任何span元素")
                
            print(f"提取结果 - 作者排名: {author_rank}, 发布时间: {post_time}")
            return author_rank, post_time
            
        except Exception as e:
            print(f"提取作者和时间信息时出错: {e}")
            return "提取失败", "提取失败"


if __name__ == '__main__':
    # 执行爬虫并显示结果
    clspider = CompDisDetailsCrawler()
    result = clspider.parse_page(url = "https://www.kaggle.com/competitions/image-matching-challenge-2025/discussion/583401")  # 替换为实际的讨论帖URL
    print(f'爬取完成')

