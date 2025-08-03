"""
Function: 对软件详情进行中文翻译，生成中文版本的软件详情

CreateDay: 20250702
Author: HongfengAi
History:
20250702    HongfengAi  第一版
"""
import json
import argparse
import os
import sys
from datetime import datetime
import requests
from bs4 import BeautifulSoup

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from configs import OUTPUT_ROOT_PATH, SOFTWARE_EXPRESS_ROOT_PATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import set_proxy, unset_proxy, init_llm, safe_title_func, format_json_block


class AppSummarizer:
    def __init__(self):
        # 初始化llm
        self.llm = init_llm(temperature=0.15)
        self.software_express_root_path = SOFTWARE_EXPRESS_ROOT_PATH

    def fetch_website_text(self, url):
        try:
            headers = {"User-Agent": "Mozilla/5.0"}
            resp = requests.get(url, headers=headers, timeout=15)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")
            texts = [p.get_text() for p in soup.find_all('p')]
            return "\n".join(texts)
        except Exception as e:
            print(f"抓取网页失败: {e}")
            return ""

    def build_summary_prompt(self, 
                             title: str, 
                             sentence_description: str, 
                             content_discription: str, 
                             website_text: str):
        prompt = f"""请根据以下软件信息和官网内容，生成中文总结，分3个段落，格式如下：

<格式要求>
目标用户是xxx (不超过100字)

xx产品的亮点功能包括xxx（可以分点，也可以分句描述。不超过150字）

差异化优势在于xxx（不超过100字）
</格式要求>

<参考输出的例子>
目标用户主要是中大型企业团队、项目经理以及需要跨部门协作的专业人士，解决了信息碎片化、工具繁杂切换和工作流断裂等痛点，抓住了日益增长的远程办公和数字化转型市场机遇。

ClickUp 的亮点功能包括其新推出的 Brain MAX AI 桌面应用，集成多款顶级大语言模型（如 GPT-4.1、Claude、Gemini 等），实现跨平台、跨应用的智能搜索和自动化任务执行；支持语音转文本和语音指令，适配多样化办公方式；以及基于上下文的精准 AI 响应，提升信息处理的关联性和效率。

差异化优势在于侧重“故事叙事”而非单次图像生成，实现视觉内容的连贯叙事和多样风格融合。
</参考输出的例子>

现在请根据以下软件信息和官网内容，生成其对应的中文总结：

【软件标题】{title}
【一句话描述】{sentence_description}
【详细描述】{content_discription}
【官网主要内容】{website_text[:5000]}

要求：
- 先总结目标用户
- 再总结亮点功能（不少于2点）
- 最后总结差异化优势
- 语言精炼、专业、有条理
- 不要编造内容，无法判断的可不写
"""
        return prompt

    def summarize_with_website(self, app_data):
        title = app_data.get('title', '')
        sentence_description = app_data.get('sentence_description', '')
        content_discription = app_data.get('content_discription', '')
        website = app_data.get('product_website', '')
        website_text = self.fetch_website_text(website) if website else ""
        prompt = self.build_summary_prompt(title, sentence_description, content_discription, website_text)
        try:
            response = self.llm.invoke(prompt).content.strip()
            return response
        except Exception as e:
            print(f'大模型总结失败: {e}')
            return ""

    def translate_app_content(self, app_data: dict) -> dict:
        """
        翻译软件的相关内容
        Args:
            app_data: 包含需要翻译字段的软件数据字典
        Returns:
            翻译后的字典
        """
        # 构建输入JSON
        input_json = {
            "sentence_description": app_data.get('sentence_description', ''),
            "tags": app_data.get('tags', []),
            "content_description": app_data.get('content_discription', '')  # 注意原字段名有拼写错误
        }
        
        prompt = f"""
        请将以下软件信息翻译成中文，保持JSON格式：

        {json.dumps(input_json, ensure_ascii=False, indent=2)}

        翻译要求：
        - 直接输出翻译后的JSON格式，不要输出任何其他内容
        - sentence_description: 翻译成自然流畅的中文描述
        - tags: 每个标签都翻译成中文，保持数组格式
        - content_description: 翻译成完整的中文描述
        - 对于sentence_description和content_description中的专业术语，可以保留英文并在后面加中文解释，格式为"中文解释(English Term)"
        - 对于公司名、产品名、技术名称等专有名词，建议保留英文原文
        - 禁止编造内容，如果原文为空则保持为空

        输出格式示例：
        {{
          "sentence_description": "翻译后的一句话描述",
          "tags": ["翻译后标签1", "翻译后标签2"],
          "content_description": "翻译后的详细描述"
        }}
        """
        
        try:
            response = self.llm.invoke(prompt).content.strip()
            # 提取JSON内容
            translated_data = format_json_block(response)
            return translated_data
        except Exception as e:
            print(f"翻译失败: {e}")
            # 返回空的翻译结果
            return {
                "sentence_description": "",
                "tags": [],
                "content_description": ""
            }


    def summarize_apps_from_json(self, input_file: str, output_file: str):
        """
        从JSON文件读取软件详情并生成中文版本
        Args:
            input_file: 输入的英文软件详情JSON文件路径
            output_file: 输出的中文软件详情JSON文件路径
        """
        # 设置代理
        set_proxy()

        print(f"正在读取软件详情文件: {input_file}")
        
        # 读取软件详情
        with open(input_file, "r", encoding="utf-8") as f:
            apps_list = json.load(f)
        
        print(f"找到 {len(apps_list)} 款软件，开始处理...")
        
        zh_apps_list = []
        
        for i, app in enumerate(apps_list):
            print(f"\n正在处理第 {i+1}/{len(apps_list)} 款软件: {app.get('title', 'Unknown')}")
            
            # 复制原始软件信息
            zh_app = app.copy()
            
            # 翻译软件内容
            print("  正在翻译软件描述...")
            translated_content = self.translate_app_content(app)
            
            # 将翻译结果追加到原数据中
            translated_content = json.loads(translated_content)
            zh_app['zh_sentence_description'] = translated_content.get('sentence_description', '')
            zh_app['zh_tags'] = translated_content.get('tags', [])
            zh_app['zh_content_description'] = translated_content.get('content_description', '')
            zh_app['zh_summary'] = self.summarize_with_website(zh_app)

            zh_apps_list.append(zh_app)
            print(f"  ✓ 完成处理软件: {app.get('title', 'Unknown')}")
        
        # 确保输出目录存在
        output_dir = os.path.dirname(output_file)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
        
        # 保存中文版本
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(zh_apps_list, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ 处理完成！")
        print(f"总共处理 {len(zh_apps_list)} 款软件")
        print(f"中文版本已保存到: {output_file}")

        # 取消代理
        unset_proxy()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='软件内容翻译器')
    parser.add_argument('--input_file', type=str, default=os.path.join(SOFTWARE_EXPRESS_ROOT_PATH,'2025_29/all_software_details.json'), help='输入的英文软件详情JSON文件路径')
    parser.add_argument('--output_file', type=str, default=os.path.join(SOFTWARE_EXPRESS_ROOT_PATH, '2025_29/zh_all_software_details.json'), help='输出的中文软件详情JSON文件路径')
    
    args = parser.parse_args()
    
    summarizer = AppSummarizer()
    summarizer.summarize_apps_from_json(args.input_file, args.output_file)
