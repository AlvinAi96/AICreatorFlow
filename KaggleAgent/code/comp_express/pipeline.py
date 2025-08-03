"""
Function: 竞赛速递的pipeline
Competition List -> Competition Overview -> 翻译Overview -> 填充HTML模板 -> 制作封面图 -> 上传封面图至公众号平台 -> 创建草稿至公众号平台

CreateDay: 20250603
Author: HongfengAi
History:
20250610    HongfengAi  第一版
20250617    HongfengAi  第二版 支持自动化制作封面图和上传草稿至公众号平台
"""

import sys, os
import re
import json
import time
# 添加项目根目录到系统路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from crawler import (
    CompListCrawler,
    CompOverviewCrawler,        
)
from comp_express.overview_summarizer import OverviewSummarizer
from comp_express.overview_template_fill import OverviewTemplateFiller
from wechat_utils.ppt_to_image import PPTToImage
from wechat_utils.upload_material import WeChatPermanentMaterialUploader
from wechat_utils.create_draft import WeChatDraftCreator

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from configs import OUTPUT_ROOT_PATH, COMP_EXPRESS_ROOT_PATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import safe_title_func


if __name__ == '__main__':
    ############################
    # 1、爬取比赛列表 并 过滤
    ############################
    print("="*60)
    print("比赛列表爬取")
    print("="*60)
    user_input = input("是否需要重新爬取比赛列表: (y/N): ").strip().lower()
    if user_input not in ['y', 'yes']:
        with open(f'{OUTPUT_ROOT_PATH}/kaggle_competitions_list.json', 'r', encoding='utf-8') as f:
            all_comp_list = json.load(f)
    else:
        page_limit = input("请输入要爬取的页数: ")
        stime = time.time()
        cl_crawler = CompListCrawler()
        all_comp_list = cl_crawler.parse_page(page_limit=page_limit)
        etime = time.time()
        print(f'爬取完成，共获取 {len(all_comp_list)} 个比赛信息，耗时 {etime-stime} 秒')

    # 筛选出leave_time包含"to go"且comp_reward包含"$"的比赛
    filtered_comp_list = []
    for comp in all_comp_list:
        # 检查筛选条件
        if 'to go' in comp['leave_time'] and '$' in comp['comp_reward']:
            filtered_comp_list.append(comp)
    print(f'筛选条件：leave_time包含"to go"且comp_reward包含"$"')
    print(f'[比赛列表] 原始比赛数量: {len(all_comp_list)}')
    print(f'[比赛列表] 筛选后比赛数量: {len(filtered_comp_list)}')

    # 用户输入选择哪些游戏
    if not filtered_comp_list:
        print("[比赛列表] 没有找到符合条件的比赛，程序结束。")
        exit()
    
    print("\n" + "="*60)
    print("[比赛列表] 筛选后的比赛列表：")
    print("="*60)
    
    for i, comp in enumerate(filtered_comp_list, 1):
        print(f"{i}. {comp['name']}")
        print(f"   奖金: {comp['comp_reward']}")
        print(f"   剩余时间: {comp['leave_time']}")
        print(f"   类型: {comp['comp_type']}")
        print(f"   参与队伍: {comp['team_number']}")
        print(f"   链接: {comp['link']}")
        print("-" * 50)
    
    print(f"\n请选择要进一步处理的比赛：")
    print(f"输入格式：")
    print(f"  - 单个选择：输入数字 (如: 1)")
    print(f"  - 退出程序：输入 'exit' 或 'q'")
    
    while True:
        try:
            user_input = input(f"\n请输入您的选择 (1-{len(filtered_comp_list)}): ").strip()
            
            if user_input.lower() in ['exit', 'q']:
                print("程序已退出。")
                exit()
            
            # 解析用户输入的数字
            indices = []
            for item in user_input.split(','):
                index = int(item.strip())
                if 1 <= index <= len(filtered_comp_list):
                    indices.append(index)
                else:
                    print(f"错误：索引 {index} 超出范围 (1-{len(filtered_comp_list)})")
                    raise ValueError()
            
            if not indices:
                print("请至少选择一个比赛。")
                continue
            
            # 获取选中的比赛
            selected_indice = indices[0]
            selected_comp = filtered_comp_list[selected_indice-1]
            break
            
        except ValueError:
            print("输入格式错误，请重新输入。")
            continue
        except KeyboardInterrupt:
            print("\n程序已被中断。")
            exit()
    
    print(f"\n您选择了比赛：[{selected_indice}] {selected_comp['name']}")


    ############################
    # 2、爬取选中比赛的Overview信息
    ############################
    print("\n" + "="*60)
    print("比赛Overview爬取")
    print("="*60)

    # 检查是否已存在概览数据文件
    safe_title = safe_title_func(selected_comp['name'])
    overview_file_path = f'{COMP_EXPRESS_ROOT_PATH}/{safe_title}/comp_overview.json'
    if os.path.exists(overview_file_path):
        print(f"发现已存在的概览数据: {overview_file_path}")
        user_input = input(f"是否需要重新爬取 '{selected_comp['name']}' 的概览信息？(y/N): ").strip().lower()
        
        if user_input not in ['y', 'yes']:
            print(f"[比赛概览] ✓ 跳过: {selected_comp['name']} (使用现有数据)")
        else:
            # 爬取比赛概览信息
            stime = time.time()
            overview_crawler = CompOverviewCrawler()
            comp_overview = overview_crawler.parse_page(selected_comp['link'])
            etime = time.time()
            print(f"[比赛概览] ✓ 完成: {selected_comp['name']}，耗时 {etime-stime} 秒")
    else:
        # 爬取比赛概览信息
        stime = time.time()
        overview_crawler = CompOverviewCrawler()
        comp_overview = overview_crawler.parse_page(selected_comp['link'])
        etime = time.time()
        print(f"[比赛概览] ✓ 完成: {selected_comp['name']}，耗时 {etime-stime} 秒")


    ############################
    # 3、用中文翻译比赛速览
    ############################
    print("\n" + "="*60)
    print("比赛Overview翻译")
    print("="*60)

    # 检查是否已存在翻译数据文件
    zh_comp_overview_file_path = f'{COMP_EXPRESS_ROOT_PATH}/{safe_title}/zh_comp_overview.json'
    if os.path.exists(zh_comp_overview_file_path):
        print(f"发现已存在的翻译数据: {zh_comp_overview_file_path}")
        user_input = input(f"是否需要重新翻译 '{selected_comp['name']}' 的概览信息？(y/N): ").strip().lower()
        
        if user_input not in ['y', 'yes']:
            print(f"[比赛速览] ✓ 跳过: {selected_comp['name']} (使用现有数据)")
        else:
            stime = time.time()
            overview_summarizer = OverviewSummarizer()
            overview_summarizer.overview_summarizer(selected_comp['name'])
            etime = time.time()
            print(f"[比赛速览] ✓ 翻译完成: {selected_comp['name']}，耗时 {etime-stime} 秒")
    else:
        stime = time.time()
        overview_summarizer = OverviewSummarizer()
        overview_summarizer.overview_summarizer(selected_comp['name'])
        etime = time.time()
        print(f"[比赛速览] ✓ 翻译完成: {selected_comp['name']}，耗时 {etime-stime} 秒")
        
        
    ############################
    # 4、填充竞赛速览HTML模版
    ############################        
    print("\n" + "="*60)
    print("填充竞赛速递的HTML模板")
    print("="*60)

    # 检查是否已存在填充数据文件
    zh_comp_overview_html_file_path = f'{COMP_EXPRESS_ROOT_PATH}/{safe_title}/zh_comp_overview.html'
    if os.path.exists(zh_comp_overview_html_file_path):
        print(f"发现已存在的填充数据: {zh_comp_overview_html_file_path}")
        user_input = input(f"是否需要重新填充 '{selected_comp['name']}' 的竞赛速览HTML模板？(y/N): ").strip().lower()
        
        if user_input not in ['y', 'yes']:
            print(f"[比赛速览] ✓ 跳过: {selected_comp['name']} (使用现有数据)")
        else:
            overview_template_filler = OverviewTemplateFiller()
            overview_template_filler.overview_template_fill(selected_comp['name'])
            print(f"[比赛速览] ✓ 填充完成: {selected_comp['name']}")
    else:
        overview_template_filler = OverviewTemplateFiller()
        overview_template_filler.overview_template_fill(selected_comp['name'])
        print(f"[比赛速览] ✓ 填充完成: {selected_comp['name']}")


    ############################
    # 5、制作封面图
    ############################
    print("\n" + "="*60)
    print("制作封面图")
    print("="*60)

    # 检查是否已存在封面图文件
    cover_image_file_path = f'{COMP_EXPRESS_ROOT_PATH}/{safe_title}/cover/cover.png'
    if os.path.exists(cover_image_file_path):
        print(f"发现已存在的封面图: {cover_image_file_path}")
        user_input = input(f"是否需要重新制作封面图？(y/N): ").strip().lower()

        if user_input not in ['y', 'yes']:
            print(f"[封面图] ✓ 跳过: {selected_comp['name']} (使用现有数据)")
        else:

            with open(f'{COMP_EXPRESS_ROOT_PATH}/{safe_title}/zh_comp_overview.json', 'r', encoding='utf-8') as f:
                zh_comp_overview = json.load(f)

            keywords = zh_comp_overview['竞赛关键词'][1:-1].replace("'", "").replace(", ", "、").replace(" ", "")
            ppt_to_image = PPTToImage()
            ppt_to_image.main(comp_type="comp_express",
                              title=zh_comp_overview['竞赛名称'],
                              host=zh_comp_overview['组织者'],
                              keywords=keywords)
            print(f"[封面图] ✓ 制作完成: {selected_comp['name']}")
    else:
        with open(f'{COMP_EXPRESS_ROOT_PATH}/{safe_title}/zh_comp_overview.json', 'r', encoding='utf-8') as f:
            zh_comp_overview = json.load(f)

        keywords = zh_comp_overview['竞赛关键词'][1:-1].replace("'", "").replace(", ", "、").replace(" ", "")
        ppt_to_image = PPTToImage()
        ppt_to_image.main(comp_type="comp_express",
                          title=zh_comp_overview['竞赛名称'],
                          host=zh_comp_overview['组织者'],
                          keywords=keywords)
        print(f"[封面图] ✓ 制作完成: {selected_comp['name']}")


    ############################
    # 6、上传封面图至公众号平台
    ############################
    print("\n" + "="*60)
    print("上传封面图至公众号平台")
    print("="*60)

    # 检查是否已存在封面图文件
    cover_image_file_path = f'{COMP_EXPRESS_ROOT_PATH}/{safe_title}/cover/cover.png'
    wechat_uploader = WeChatPermanentMaterialUploader()
    upload_result= wechat_uploader.upload_specific_file(cover_image_file_path)
    print(f"[封面图] ✓ 上传完成: {selected_comp['name']}")


    ############################
    # 7、创建草稿至公众号平台
    ############################
    print("\n" + "="*60)
    print("创建草稿至公众号平台")
    print("="*60)

    wechat_draft_creator = WeChatDraftCreator()
    wechat_draft_creator.create_draft(comp_type="comp_express",
                                      title=selected_comp['name'])
    print(f"[草稿] ✓ 创建完成: {selected_comp['name']}")
