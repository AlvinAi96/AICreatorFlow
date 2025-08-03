"""
Function: 生成top solution的复盘
根据top_k_disussion_name2rank，
获取{COMP_REVIEW_ROOT_PATH}/{comp_name}/discussion_details/{name}下的md文件，
并使用llm生成top solution的复盘

CreateDay: 20250611
Author: HongfengAi
History:
20250611    HongfengAi  第一版
"""
import json

import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from configs import COMP_REVIEW_ROOT_PATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import set_proxy, unset_proxy, init_llm, safe_title_func, parse_llm_json_output


class SolutionSummarizer():
    def __init__(self):
        set_proxy()
        # 初始化llm
        self.llm = init_llm(temperature=0.7)
        self.comp_review_root_path = COMP_REVIEW_ROOT_PATH

    def summarize_solution(self, comp_name:str, 
                           top_k_disussion_name2rank:dict,
                           top_k_disussion_name2url:dict):
        """总结top solution的复盘"""
        # 设置代理
        set_proxy()
        safe_comp_name = safe_title_func(comp_name)

        # 根据top_k_disussion_name2rank，获
        # 取data/{comp_name}/discussion_details/{name}下的md文件，
        # 并使用llm生成top solution的复盘
        discussion_summarys = []
        total_len = len(top_k_disussion_name2rank)
        i = 0
        for name, rank in top_k_disussion_name2rank.items():
            i += 1
            print(f"=========={i}/{total_len}==========")
            print(f"Summary Discussion | {name} | {top_k_disussion_name2url[name]} (rank: {rank})...")
            discussion_summary = {}
            discussion_summary['title'] = name
            discussion_summary['rank'] = rank
            discussion_summary['url'] = top_k_disussion_name2url[name]
            
            with open(f'{self.comp_review_root_path}/{safe_comp_name}/discussion_details/{name}/discussion_content.md', 'r', encoding='utf-8') as f:
                discussion_detail = f.read()
                discussion_summary['discussion_content'] = discussion_detail

            # 调用大模型生成总结
            prompt = f"""
            您是一个Kaggle专家，擅长将Kaggle Discussion内的获奖方案进行总结。 

            具体解决方案全文如下： 
            {discussion_detail}

            请帮我对以上给定的方案进行总结，总结格式要求如下json格式：

            {{{{
                "solution_description": "...",
                "core_techniques": [
                    {{
                        "core_technique": "...",
                        "core_technique_description": "..."
                    }},
                    ...
                ],
                "solution_summary": "..."
            }}}}
            
            关于各字段的说明：
            - solution_description：解决方案描述。分点描述本解决方案的总体方法，包括数据处理、模型结构、训练，效果等，字数控制在150-300字以内；
            - core_techniques：核心技术点。按内容分点整理出多个核心点，但不能超过5个，且每个核心点的描述内容的字数控制在150-500字以内，核心点包括：核心提高评估分数的技巧、花较重篇幅介绍的核心技术内容，尽量详细描述各核心技术点的一些技术细节，比如如何实现的？出于什么考虑使用该技术？最好能让没了解过该比赛的人也能通过这些细节知道该核心技术点的思路和实现方法。如果作者有解释为什么使用该技术，请在核心技术点中体现出来。
            - solution_summary：解决方案总结。总结该解决方案，字数控制在150-500字以内。

            注意：json内给字段下的内容都请中文，但在对方案总结过程中，如果遇到一些AI领域或业务领域的专有名词，请保留对应词的英文表述。请不要使用**来强调任何内容。
            """
            set_proxy()
            llm_output = self.llm.invoke(prompt).content.strip()
            print(f"LLM Raw Output: \n{llm_output}")
            
            # 解析LLM输出的JSON
            parsed_summary = parse_llm_json_output(llm_output)
            if parsed_summary:
                discussion_summary['summary'] = parsed_summary
                print(f"Parsed Summary: \n{parsed_summary}")
            else:
                # 如果解析失败，保留原始输出
                discussion_summary['summary'] = llm_output
                print(f"Failed to parse JSON, using raw output")
                
            discussion_summarys.append(discussion_summary)
            print('\n\n')

        with open(f'{self.comp_review_root_path}/{safe_comp_name}/top_solution_summarys.json', 'w', encoding='utf-8') as f:
            json.dump(discussion_summarys, f, ensure_ascii=False, indent=4)

        # 取消代理
        unset_proxy()            



if __name__ == '__main__':
    solution_summarizer = SolutionSummarizer()
    comp_name = 'March Machine Learning Mania 2025'
    safe_comp_name = safe_title_func(comp_name)
    top_k_disussion_name2rank = json.load(open(f'{COMP_REVIEW_ROOT_PATH}/{safe_comp_name}/top_k_disussion_name2rank.json', 'r', encoding='utf-8'))
    top_k_disussion_name2url = json.load(open(f'{COMP_REVIEW_ROOT_PATH}/{safe_comp_name}/top_k_disussion_name2url.json', 'r', encoding='utf-8'))
    solution_summarizer.summarize_solution(comp_name, top_k_disussion_name2rank, top_k_disussion_name2url)
    