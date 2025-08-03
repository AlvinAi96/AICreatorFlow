"""
Function: 从比赛discussion中找到top solution

CreateDay: 20250611
Author: HongfengAi
History:
20250611    HongfengAi  第一版
"""
import re
import json
import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from configs import COMP_REVIEW_ROOT_PATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import safe_title_func

class FindTopSolution():
    def __init__(self):
        pass

    def find_top_solution(self, comp_name:str, top_k:int=50):
        """找到高分方案"""
        # 读取给定comp_name下discussion_detail下的帖子名称和md文件
        safe_comp_name = safe_title_func(comp_name)
        discussion_detail_dir = f'{COMP_REVIEW_ROOT_PATH}/{safe_comp_name}/discussion_details/'
        discussion_detail_files = os.listdir(discussion_detail_dir)

        disussion_name2rank = {}
        disussion_name2url = {}
        for file in discussion_detail_files:
            with open(os.path.join(discussion_detail_dir, f"{file}/discussion_content.md"), 'r', encoding='utf-8') as f:
                discussion_detail = f.read()
                # 获取帖子名称
                discussion_name = file

                # 获取帖子排名，用正则匹配的方式获取，**作者比赛排名**: 8TH，提取出8
                discussion_rank = re.search(r'\*\*Author Rank\*\*: (\d+)(?:TH|RD|ST|ND)', discussion_detail)
                if discussion_rank:
                    discussion_rank = discussion_rank.group(1)
                    disussion_name2rank[discussion_name] = int(discussion_rank)

                # 获取帖子链接
                discussion_url = re.search(r'\*\*Link\*\*: (https://www\.kaggle\.com/competitions/[\w-]+/discussion/\d+)', discussion_detail)
                if discussion_url:
                    discussion_url = discussion_url.group(1)
                    disussion_name2url[discussion_name] = discussion_url

        # 对disussion_name2rank进行排序，按照排名升序
        disussion_name2rank = sorted(disussion_name2rank.items(), key=lambda x: int(x[1]))

        print(f"==========disussion_name2rank==========")
        for name, rank in disussion_name2rank:
            print(f"{name}: {rank}")
        print("\n\n")

        print(f"==========disussion_name2url==========")
        for name, url in disussion_name2url.items():
            print(f"{name}: {url}")

        # 按rank，获取排名前top_k的帖子（注意会有相同top_k的帖子，都保留，而不是直接选择top_k）
        top_k_disussion_name2rank = {}
        top_k_disussion_name2url = {}
        for i, (name, rank) in enumerate(disussion_name2rank):
            if rank <= top_k:
                top_k_disussion_name2rank[name] = rank
                top_k_disussion_name2url[name] = disussion_name2url[name]
            else:
                break

        # 将top_k结果保存
        with open(f'{COMP_REVIEW_ROOT_PATH}/{safe_comp_name}/top_k_disussion_name2rank.json', 'w', encoding='utf-8') as f:
            json.dump(top_k_disussion_name2rank, f, ensure_ascii=False, indent=4)
        with open(f'{COMP_REVIEW_ROOT_PATH}/{safe_comp_name}/top_k_disussion_name2url.json', 'w', encoding='utf-8') as f:
            json.dump(top_k_disussion_name2url, f, ensure_ascii=False, indent=4)

        return top_k_disussion_name2rank, top_k_disussion_name2url

if __name__ == '__main__':
    find_top_solution = FindTopSolution()
    top_k = 20
    top_k_disussion_name2rank, top_k_disussion_name2url = find_top_solution.find_top_solution('Drawing with LLMs', top_k=top_k)
    print(f"\n==========top_k={top_k}==========")
    print(top_k_disussion_name2rank)
    print(top_k_disussion_name2url)