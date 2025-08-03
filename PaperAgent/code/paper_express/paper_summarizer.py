"""
Function: 对论文详情进行中文翻译，生成中文版本的论文摘要

CreateDay: 20250626
Author: HongfengAi
History:
20250626    HongfengAi  第一版
"""
import json
import argparse
import os
import sys
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from configs import OUTPUT_ROOT_PATH, PAPER_EXPRESS_ROOT_PATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import set_proxy, unset_proxy, init_llm, safe_title_func, format_json_block


class PaperSummarizer:
    def __init__(self):
        # 初始化llm
        self.llm = init_llm(temperature=0.15)
        self.paper_express_root_path = PAPER_EXPRESS_ROOT_PATH


    def translate_abstract(self, abstract: str) -> str:
        """
        翻译论文摘要
        Args:
            abstract: 原始英文摘要
        Returns:
            翻译后的中文摘要
        """
        if not abstract or abstract.strip() == "":
            return abstract

        prompt = f"""
        请将以下学术论文的摘要内容专业地翻译成中文：

        {abstract}

        注意：
        - 直接输出中文翻译后的结果，不要输出任何其他无关内容。
        - 禁止编造内容。
        - 保持学术性和专业性。
        - 对于专业英文术语，请保留该英文术语，可以在后面加上中文解释，格式为"英文术语(中文解释)"。
        - 对于模型名称、算法名称、数据集名称、公司名称等专有名词，请保留英文原文。
        - 对于数学公式和技术参数，请原封不动保留其格式。
        - 翻译要准确、流畅、符合中文学术写作习惯。
        """
        translated_abstract = self.llm.invoke(prompt).content.strip()
        return translated_abstract


    def generate_paper_keywords(self, title: str, ai_summary: str, abstract: str) -> list:
        """
        根据论文信息生成技术关键词
        Args:
            title: 论文标题
            ai_summary: AI总结
            abstract: 摘要
        Returns:
            技术关键词列表
        """
        prompt = f"""
        请根据以下学术论文信息，生成该论文的核心技术关键词（不超过5个）：

        # 论文标题：
        {title}

        # AI总结：
        {ai_summary}

        # 摘要：
        {abstract}

        注意：
        1. 输出格式为JSON列表，列表中每个元素为技术关键词；
        2. 关键词应该是具体的技术术语，避免使用"机器学习"、"深度学习"等过于泛化的词汇；
        3. 关键词数量不能超过5个；
        4. 优先使用中文，但对于专有名词可以保留英文；
        5. 关键词应该能够准确反映论文的技术贡献和创新点。

        输出示例：["VLA", "Agent", "多模态学习", "强化学习", "大语言模型"]
        """
        keywords_response = self.llm.invoke(prompt).content.strip()
        keywords = format_json_block(keywords_response)
        return keywords


    def convert_date_to_chinese(self, date_str: str) -> str:
        """
        将英文日期转换为中文格式
        Args:
            date_str: 原始日期字符串，如 "Published on Jun 16"
        Returns:
            转换后的中文日期字符串
        """
        if not date_str:
            return date_str
            
        try:
            # 移除"Published on"前缀
            date_part = date_str.replace("Published on ", "").strip()
            
            # 月份映射
            month_mapping = {
                "Jan": "1月", "Feb": "2月", "Mar": "3月", "Apr": "4月",
                "May": "5月", "Jun": "6月", "Jul": "7月", "Aug": "8月", 
                "Sep": "9月", "Oct": "10月", "Nov": "11月", "Dec": "12月"
            }
            
            # 处理格式如 "Jun 16" 或 "Jun 16, 2024"
            parts = date_part.split()
            if len(parts) >= 2:
                month = parts[0]
                day = parts[1].replace(",", "")
                
                if month in month_mapping:
                    chinese_date = f"{month_mapping[month]}{day}日"
                    if len(parts) > 2:  # 包含年份
                        year = parts[2]
                        chinese_date = f"{year}年{chinese_date}"
                    return f"发布于{chinese_date}"
            
            return date_str
        except Exception as e:
            print(f"转换日期格式时出错: {str(e)}")
            return date_str


    def summarize_papers_from_json(self, input_file: str, output_file: str):
        """
        从JSON文件读取论文详情并生成中文版本
        Args:
            input_file: 输入的英文论文详情JSON文件路径
            output_file: 输出的中文论文详情JSON文件路径
        """
        # 设置代理
        set_proxy()

        print(f"正在读取论文详情文件: {input_file}")
        
        # 读取论文详情
        with open(input_file, "r", encoding="utf-8") as f:
            papers_list = json.load(f)
        
        print(f"找到 {len(papers_list)} 篇论文，开始处理...")
        
        zh_papers_list = []
        
        for i, paper in enumerate(papers_list):
            print(f"\n正在处理第 {i+1}/{len(papers_list)} 篇论文: {paper.get('title', 'Unknown')}")
            
            # 复制原始论文信息
            zh_paper = paper.copy()
            
            # 翻译AI总结
            if paper['ai_summary']:
                zh_paper['zh_ai_summary'] = self.translate_abstract(paper['ai_summary'])
            else:
                zh_paper['zh_ai_summary'] = ""

            # 翻译摘要
            zh_paper['zh_abstract'] = self.translate_abstract(paper['abstract'])

            # 生成技术关键词
            zh_paper['keywords'] = self.generate_paper_keywords(
                paper.get('title', ''),
                paper.get('ai_summary', ''),
                paper.get('abstract', '')
            )

            # 转换发布日期为中文
            zh_paper['zh_published_date'] = self.convert_date_to_chinese(paper['published_date'])

            zh_papers_list.append(zh_paper)
            print(f"  ✓ 完成处理论文: {paper.get('title', 'Unknown')}")
        
        # 确保输出目录存在
        output_dir = os.path.dirname(output_file)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
        
        # 保存中文版本
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(zh_papers_list, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ 处理完成！")
        print(f"总共处理 {len(zh_papers_list)} 篇论文")
        print(f"中文版本已保存到: {output_file}")

        # 取消代理
        unset_proxy()



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='论文摘要翻译器')
    parser.add_argument('--input_file', type=str, default=os.path.join(PAPER_EXPRESS_ROOT_PATH,'2025_W25/all_papers_details.json'), help='输入的英文论文详情JSON文件路径')
    parser.add_argument('--output_file', type=str, default=os.path.join(PAPER_EXPRESS_ROOT_PATH, '2025_W25/zh_all_papers_details.json'), help='输出的中文论文详情JSON文件路径')
    
    args = parser.parse_args()
    
    summarizer = PaperSummarizer()
    summarizer.summarize_papers_from_json(args.input_file, args.output_file)
