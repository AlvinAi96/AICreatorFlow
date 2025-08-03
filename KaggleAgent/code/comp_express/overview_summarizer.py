"""
Function: 对给定进行中的比赛，生成比赛速览

CreateDay: 20250604
Author: HongfengAi
History:
20250604    HongfengAi  第一版
"""
import json
import argparse
from datetime import datetime

import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from configs import OUTPUT_ROOT_PATH, COMP_EXPRESS_ROOT_PATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import set_proxy, unset_proxy, init_llm, safe_title_func, format_json_block

class OverviewSummarizer:
    def __init__(self):
        # 初始化llm
        self.llm = init_llm(temperature=0.15)
        self.data_root_path = OUTPUT_ROOT_PATH
        self.comp_express_root_path = COMP_EXPRESS_ROOT_PATH

    def convert_time_to_chinese(self, time_str: str) -> str:
        """
        将时间字符串转换为中文格式
        Args:
            time_str: 原始时间字符串
        Returns:
            转换后的中文时间字符串
        """
        try:
            if time_str:
                # 移除(中国标准时间)部分
                time_str = time_str.split(" (")[0]
                # 解析时间字符串
                dt = datetime.strptime(time_str, "%a %b %d %Y %H:%M:%S GMT%z")
                # 转换为中文格式
                return dt.strftime("%Y年%m月%d日 %H:%M")
            else:
                return time_str
        except:
            return time_str

    def translate_diff_type_elements(self, elements:list):
        """
        翻译不同类型的元素
        """
        # 由于description可能包含多种类型的元素，因此需要分别翻译
        # 若遇到type为table，则直接输出table内容，不用翻译它
        translate_elements = []
        for item in elements:
            if item.get("type") == "table":
                translate_elements.append({"type": "table", "content": item.get("content", "")})
            
            elif item.get("type") == "image":
                translate_elements.append({"type": "image", "content": item.get("content", "")})
            
            elif item.get("type") == "pre": # 代码
                translate_elements.append({"type": "pre", "content": item.get("content", "")})

            elif item.get("type") == "ul":
                prompt = f"""
                请将专业地中文翻译出以下Kaggle比赛Overview中的有序列表，并输出：

                {item.get("content", "")}

                注意：
                - 直接输出中文翻译后的结果，不要输出任何其他无关内容。
                - 禁止编造内容。
                - 若存在专业英文术语，请保留该英文术语，可以不用将该英文术语翻译成中文。
                - 对于$$包括的数学latex公式，请原封不动保留其$数据公式$的样式，不需要翻译它且不要删除$符号。
                - 翻译结果请保留输入的原始无序列表符号，即● 。
                """
                translate_elements.append({"type": "ul", "content": self.llm.invoke(prompt).content.strip()})   

            elif item.get("type") == "ol":
                prompt = f"""
                请将专业地中文翻译出以下Kaggle比赛Overview中的无序列表，并输出：

                {item.get("content", "")}

                注意：
                - 直接输出中文翻译后的结果，不要输出任何其他无关内容。
                - 禁止编造内容。
                - 若存在专业英文术语，请保留该英文术语，可以不用将该英文术语翻译成中文。
                - 对于$$包括的数学latex公式，请原封不动保留其$数据公式$的样式，不需要翻译它且不要删除$符号。
                - 翻译结果请保留输入的原始有序列表符号，如1. 2. 3. 等。
                """
                translate_elements.append({"type": "ol", "content": self.llm.invoke(prompt).content.strip()})  

            elif item.get("type") == "h2" or item.get("type") == "h1":
                translate_elements.append({"type": item.get("type"), "content": item.get("content", "")})
                
            else:
                # 若为行间公式，即整个item的content是一个$$包围的公式,然后中间没有$，则不需要翻译
                if item.get("content", "").startswith("$") and item.get("content", "").endswith("$") and "$" not in item.get("content", "")[1:-1]:
                    translate_elements.append({"type": item.get("type"), "content": item.get("content", "")})
                else:
                    prompt = f"""
                    请将专业地中文翻译出以下Kaggle比赛Overview中的段落，并输出：

                    {item.get("content", "")}

                    注意：
                    - 直接输出中文翻译后的结果，不要输出任何其他无关内容。
                    - 禁止编造内容。
                    - 若存在专业英文术语，请保留该英文术语，可以不用将该英文术语翻译成中文。
                    - 对于$$包围的数学latex公式，请原封不动保留其$数据公式$的样式内容，不需要翻译它且不要删除$符号。
                    """
                    translate_elements.append({"type": item.get("type"), "content": self.llm.invoke(prompt).content.strip()})   

        return translate_elements
    
    def overview_summarizer(self, comp_name:str):
        """
        对给定进行中的比赛，生成比赛速览
        Args:
            comp_name: 比赛名称（完整）
        """
        # 设置代理
        set_proxy()

        print(f"正在处理比赛: {comp_name}")
        print(f"数据根目录: {self.data_root_path}")

        # 获取比赛metadata
        comp_metadata_path = f"{self.data_root_path}/kaggle_competitions_list.json"
        with open(comp_metadata_path, "r", encoding="utf-8") as f:
            comp_metadata_list = json.load(f)

        # 查找指定比赛的metadata
        comp_metadata = {}
        for item in comp_metadata_list:
            if item["name"] == comp_name:
                comp_metadata = item
                break
        
        # 合规划标题
        safe_comp_title = safe_title_func(comp_name)

        # 获取比赛详情
        comp_detail_path = f"{self.comp_express_root_path}/{safe_comp_title}/comp_overview.json"
        with open(comp_detail_path, "r", encoding="utf-8") as f:
            comp_details = json.load(f)


        # 生成竞赛类型
        # 用llm根据overview, description和evaluation判断竞赛类型
        prompt = f"""
        请根据以下Kaggle比赛信息，给出关于该比赛类型的几个核心技术关键词（不超过4个）：

        # 比赛标题：
        {comp_details.get("title", comp_name)}

        # 比赛总览：
        {comp_details.get("overview", "暂无详细比赛总览")}

        # 比赛描述：
        {comp_details.get("description", "暂无比赛描述")}

        # 评估指标：
        {comp_details.get("evaluation", "暂无评估指标")}

        注意：
        1. 输出格式为列表，列表中每个元素为技术关键词，不要用"机器学习"、"深度学习"等通用且过于泛化的词汇；
        2. 关于该比赛类型的技术关键词数量不能超过4个;
        3. 用中文输出。

        输出示例：['图像识别', '目标检测']
        """
        comp_type_keywords = self.llm.invoke(prompt).content.strip()
        comp_type_keywords = format_json_block(comp_type_keywords)
        print("comp_type_keywords:", comp_type_keywords)

        
        # Kaggle有时没有overview或description，所以这里需要额外处理
        # 当有overview但无description时，需要把overview放到description内，然后overview需要根据description进行llm总结
        # 当overview只有一个p时，则正常翻译，否则需要对overview做总结
        # 当没有overview时，需要根据description进行llm总结
        
        original_overview = comp_details.get("overview", [])
        original_description = comp_details.get("description", [])
        
        # 根据不同情况处理overview和description
        if len(original_overview) > 0 and len(original_description) == 0:
            # 情况1：有overview但无description - 把overview移到description，用LLM生成新的overview总结
            print("处理情况：有overview但无description")
            comp_details["description"] = original_overview
            
            # 基于overview内容生成简短的overview总结
            overview_content_for_summary = ""
            for item in original_overview:
                if item.get("content"):
                    overview_content_for_summary += item.get("content", "") + "\n"
            
            summary_prompt = f"""
            请根据以下Kaggle比赛的详细描述，生成一个简洁的比赛总览（不超过200字）：

            {overview_content_for_summary}

            注意：
            - 用中文输出
            - 总结要简洁明了，突出比赛的核心目标和任务
            - 不要编造内容，只基于给定信息进行总结
            - 保留专业术语的英文原文
            """
            overview_summary = self.llm.invoke(summary_prompt).content.strip()
            comp_details["overview"] = [{"type": "p", "content": overview_summary}]
            
        elif len(original_overview) > 1:
            # 情况2：overview有多个元素 - 对overview做总结
            print("处理情况：overview有多个元素，需要总结")
            overview_content_for_summary = ""
            for item in original_overview:
                if item.get("content"):
                    overview_content_for_summary += item.get("content", "") + "\n"
            
            summary_prompt = f"""
            请将以下Kaggle比赛的多段overview总结为一个简洁的总览（不超过200字）：

            {overview_content_for_summary}

            注意：
            - 用中文输出
            - 总结要简洁明了，突出比赛的核心目标和任务
            - 不要编造内容，只基于给定信息进行总结
            - 保留专业术语的英文原文
            """
            overview_summary = self.llm.invoke(summary_prompt).content.strip()
            comp_details["overview"] = [{"type": "p", "content": overview_summary}]
            
        elif len(original_overview) == 0 and len(original_description) > 0:
            # 情况3：没有overview但有description - 根据description生成overview总结
            print("处理情况：没有overview但有description")
            description_content_for_summary = ""
            for item in original_description:
                if item.get("content"):
                    description_content_for_summary += item.get("content", "") + "\n"
            
            summary_prompt = f"""
            请根据以下Kaggle比赛的详细描述，生成一个简洁的比赛总览（不超过200字）：

            {description_content_for_summary}

            注意：
            - 用中文输出
            - 总结要简洁明了，突出比赛的核心目标和任务
            - 不要编造内容，只基于给定信息进行总结
            - 保留专业术语的英文原文
            """
            overview_summary = self.llm.invoke(summary_prompt).content.strip()
            comp_details["overview"] = [{"type": "p", "content": overview_summary}]
        
        # 生成竞赛目标 (overview) - 翻译处理后的overview
        comp_overview_list = comp_details.get("overview", [])
        if len(comp_overview_list) > 0:
            comp_overview_list = self.translate_diff_type_elements(comp_overview_list)
        print("comp_overview_list:", comp_overview_list)

        # 获取竞赛网站
        comp_website = comp_metadata.get("link", "")
        print("comp_website:", comp_website)

        # 获取竞赛的组织者
        comp_host = comp_details.get("host", "")
        print("comp_host:", comp_host)

        # 生成竞赛描述（description）
        # 由于description可能包含多种类型的元素，因此需要分别翻译
        # 若遇到type为table，则直接输出table内容，不用翻译它
        comp_description_list = comp_details.get("description", [])
        if len(comp_description_list) > 0:
            comp_description_list = self.translate_diff_type_elements(comp_description_list)   
        print("comp_description_list:", comp_description_list)

        # 生成竞赛评估指标
        comp_evaluation_list = comp_details.get("evaluation", [])
        if len(comp_evaluation_list) > 0:
            comp_evaluation_list = self.translate_diff_type_elements(comp_evaluation_list)   
        print("comp_evaluation_list:", comp_evaluation_list)

        # 生成竞赛时间线
        comp_timeline_list = comp_details.get("timeline", [])
        if len(comp_timeline_list) > 0:
            comp_timeline_list = self.translate_diff_type_elements(comp_timeline_list)   
        print("comp_timeline_list:", comp_timeline_list)

        # 生成竞赛奖金
        comp_prize_list = comp_details.get("prize", [])
        if len(comp_prize_list) > 0:
            comp_prize_list = self.translate_diff_type_elements(comp_prize_list)   
        print("comp_prize_list:", comp_prize_list)

        # 保存概览信息到文件
        overview_data = {
            "竞赛名称": comp_details.get("title", comp_name),
            "竞赛副标题": comp_metadata.get("description", ""),
            "竞赛类型": comp_metadata.get("comp_type", ""),
            "竞赛关键词": comp_type_keywords,
            "组织者": comp_host,
            "开始时间": self.convert_time_to_chinese(comp_details.get("start_time", "")),
            "结束时间": self.convert_time_to_chinese(comp_details.get("end_time", "")),
            "竞赛参与人数": comp_details.get("participation", []),
            "竞赛网站": comp_website,
            "竞赛总览": comp_overview_list,
            "详细描述": comp_description_list,
            "评估指标": comp_evaluation_list,
            "时间线": comp_timeline_list,
            "奖金": comp_prize_list,
        }

        output_path = f"{self.comp_express_root_path}/{safe_comp_title}/zh_comp_overview.json"
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(overview_data, f, ensure_ascii=False, indent=2)

        print(f"\n概览信息已保存到: {output_path}")

        # 取消代理
        unset_proxy()


if __name__ == "__main__":
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="对给定进行中的比赛，生成比赛速览")
    parser.add_argument(
        "--comp_name", 
        type=str, 
        default="DRW - Crypto Market Prediction",
        help="比赛名称 (完整名称)"
    )
    args = parser.parse_args()

    overview_summarizer = OverviewSummarizer()
    overview_summarizer.overview_summarizer(args.comp_name)  