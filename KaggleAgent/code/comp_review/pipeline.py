"""
Function: 竞赛复盘的pipeline
Competition List -> Competition Overview -> Competition Discussion List -> Competition Discussion Details -> 生成竞赛复盘文章 -> 填充HTML模板 -> 制作封面图 -> 上传封面图至公众号平台 -> 创建草稿至公众号平台

CreateDay: 20250603
Author: HongfengAi
History:
20250603    HongfengAi  第一版
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
    CompDisListCrawler,
    CompDisDetailsCrawler,
)
from comp_express.overview_summarizer import OverviewSummarizer
from comp_review.find_top_solution import FindTopSolution
from comp_review.solution_summarizer import SolutionSummarizer
from comp_review.summary_template_fill import SummaryTemplateFiller
from wechat_utils.ppt_to_image import PPTToImage
from wechat_utils.upload_material import WeChatPermanentMaterialUploader
from wechat_utils.create_draft import WeChatDraftCreator

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from configs import OUTPUT_ROOT_PATH, COMP_EXPRESS_ROOT_PATH, COMP_REVIEW_ROOT_PATH
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

    # 筛选出leave_time包含"ago"且comp_reward包含"$"的比赛
    filtered_comp_list = []
    for comp in all_comp_list:
        # 检查筛选条件
        if 'ago' in comp['leave_time'] and '$' in comp['comp_reward']:
            filtered_comp_list.append(comp)
    print(f'筛选条件：leave_time包含"ago"且comp_reward包含"$"')
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
    # 4、爬取比赛讨论列表
    ############################
    print("\n" + "="*60)
    print("比赛讨论帖列表爬取")
    print("="*60)
    
    dis_list_file_path = f'{COMP_REVIEW_ROOT_PATH}/{safe_title}/comp_dis_list.json'
    if os.path.exists(dis_list_file_path):
        print(f"发现已存在的讨论列表数据: {dis_list_file_path}")
        user_input = input(f"是否需要重新爬取 '{selected_comp['name']}' 的讨论列表？(y/N): ").strip().lower()
        
        if user_input not in ['y', 'yes']:
            print(f"[讨论列表] ✓ 跳过: {selected_comp['name']} (使用现有数据)")
        else:
            crawl_page = int(input("请输入每个比赛要爬取的讨论页数 (默认: 5): ").strip() or "5")
            stime = time.time()
            discussion_crawler = CompDisListCrawler()
            comp_discussions = discussion_crawler.parse_page(url=selected_comp['link'],
                                                            page_limit=crawl_page)
            etime = time.time()
            print(f"[讨论列表] ✓ 完成: {selected_comp['name']}，耗时 {etime-stime} 秒")
    else:
        crawl_page = int(input("请输入每个比赛要爬取的讨论页数 (默认: 5): ").strip() or "5")
        stime = time.time()
        discussion_crawler = CompDisListCrawler()
        comp_discussions = discussion_crawler.parse_page(url=selected_comp['link'],
                                                        page_limit=crawl_page)
        etime = time.time()
        print(f"[讨论列表] ✓ 完成: {selected_comp['name']}，耗时 {etime-stime} 秒")


    ############################
    # 5、爬取讨论详情
    ############################
    print("\n" + "="*60)
    print("讨论帖正文内容爬取")
    print("="*60)
    
    user_input = input(f"是否需要爬取讨论贴正文内容的？(y/N): ").strip().lower()
    if user_input not in ['y', 'yes']:
        print(f"[讨论列表] ✓ 跳过所有讨论贴正文内容的爬取 (使用现有数据)")

    else:
        # 读取讨论列表
        with open(dis_list_file_path, 'r', encoding='utf-8') as f:
            comp_discussions = json.load(f)

        crawl_details_num = int(input("请输入每个比赛要爬取多少条讨论详情 (默认: 30): ").strip() or "30")
        crawl_details_num = min(crawl_details_num, len(comp_discussions))

        # 遍历讨论列表中每个讨论帖，然后依次爬取其正文内容
        stime = time.time()
        details_crawler = CompDisDetailsCrawler()
        for i in range(1, crawl_details_num+1):
            comp_dis = comp_discussions[i-1]
            print(f"[讨论详情] 正在处理（{i}/{crawl_details_num}）: {comp_dis['title']}")
            
            # 检查是否已存在讨论详情文件
            safe_discussion_title = safe_title_func(comp_dis['title'])
            detail_file_path = f'{COMP_REVIEW_ROOT_PATH}/{safe_title}/discussion_details/{safe_discussion_title}/discussion_content.md'
            if os.path.exists(detail_file_path):
                skip_existing = input(f"    现已存在的详情文件: {detail_file_path}，是否重复爬取？(Y/n): ").strip().lower()
                
                if skip_existing not in ['y', 'yes']:
                    print(f"    ✓ 跳过: {comp_dis['title']} (使用现有数据)")
                    continue
                
            detail_content = details_crawler.parse_page(url=comp_dis['link'])
            print(f"[讨论详情] ✓ 完成: {comp_dis['title']}")

        etime = time.time()
        print(f"[讨论详情] ✓ 完成: {selected_comp['name']}，耗时 {etime-stime} 秒")

    ############################
    # 6、找出TOP Solution
    ############################
    print("\n" + "="*60)
    print("TOP Solution寻找")
    print("="*60)

    user_input = input(f"是否需要找出TOP Solution？(y/N): ").strip().lower()
    if user_input not in ['y', 'yes']:
        print(f"[TOP Solution] ✓ 跳过所有TOP Solution的寻找 (使用现有数据)")

    else:
        top_k_disussion_name2rank_file_path = f'{COMP_REVIEW_ROOT_PATH}/{safe_title}/top_k_disussion_name2rank.json'
        top_k_disussion_name2url_file_path = f'{COMP_REVIEW_ROOT_PATH}/{safe_title}/top_k_disussion_name2url.json'
        if os.path.exists(top_k_disussion_name2rank_file_path) and os.path.exists(top_k_disussion_name2url_file_path):
            print(f"发现已存在的TOP Solution数据: {top_k_disussion_name2rank_file_path} 和 {top_k_disussion_name2url_file_path}")
            user_input = input(f"是否需要重新找出TOP Solution？(y/N): ").strip().lower()
            
            if user_input not in ['y', 'yes']:
                print(f"[TOP Solution] ✓ 跳过: {selected_comp['name']} (使用现有数据)")
                top_k_disussion_name2rank = json.load(open(top_k_disussion_name2rank_file_path, 'r', encoding='utf-8'))
                top_k_disussion_name2url = json.load(open(top_k_disussion_name2url_file_path, 'r', encoding='utf-8'))
            else:
                top_k = int(input("请输入要找出多少个TOP Solution (默认: 100): ").strip() or "100")
                find_top_solution = FindTopSolution()
                top_k_disussion_name2rank, top_k_disussion_name2url = find_top_solution.find_top_solution(safe_title, top_k=top_k)
                print(f"[TOP Solution] ✓ 完成: {selected_comp['name']}")
        else:
            top_k = int(input("请输入要找出多少个TOP Solution (默认: 100): ").strip() or "100")
            find_top_solution = FindTopSolution()
            top_k_disussion_name2rank, top_k_disussion_name2url = find_top_solution.find_top_solution(safe_title, top_k=top_k)
            print(f"[TOP Solution] ✓ 完成: {selected_comp['name']}")

        # 打印TOP Solution
        print(f"\n[TOP Solution] 找到的TOP Solution:")
        for i, (name, rank) in enumerate(top_k_disussion_name2rank.items(), 1):
            print(f"{i}. {name} - 排名: {rank}")
            print(f"   链接: {top_k_disussion_name2url[name]}")
            print("-" * 50)

        # 请选择你想要的TOP Solution
        print(f"\n请选择你想要的TOP Solution:")
        print(f"输入格式：")
        print(f"  - 多个选择：输入数字 (如: 1,2,3)")
        print(f"  - 退出程序：输入 'exit' 或 'q'")
        
        # 用户输入选择哪些游戏
        user_input = input(f"\n请输入您的选择 (1-{len(top_k_disussion_name2rank)}): ").strip()

        if user_input.lower() in ['exit', 'q']:
            print("程序已退出。")
            exit() 
            
        # 修改top_k_disussion_name2rank/url，只保留选择后的讨论帖的名称
        selected_dis_names = [list(top_k_disussion_name2rank.keys())[int(i)-1] for i in user_input.split(',')]
        top_k_disussion_name2rank = {k: v for k, v in top_k_disussion_name2rank.items() if k in selected_dis_names}
        top_k_disussion_name2url = {k: v for k, v in top_k_disussion_name2url.items() if k in selected_dis_names}

        # 将top_k_disussion_name2rank/url保存到文件
        with open(top_k_disussion_name2rank_file_path, 'w', encoding='utf-8') as f:
            json.dump(top_k_disussion_name2rank, f, ensure_ascii=False, indent=4)
        with open(top_k_disussion_name2url_file_path, 'w', encoding='utf-8') as f:
            json.dump(top_k_disussion_name2url, f, ensure_ascii=False, indent=4)

        # 打印top结果
        print(f"\n[TOP Solution] 选择后的TOP Solution:")
        for i, (name, rank) in enumerate(top_k_disussion_name2rank.items(), 1):
            print(f"{i}. {name} - 排名: {rank}")
            print(f"   链接: {top_k_disussion_name2url[name]}")
            print("-" * 50)


    ############################
    # 7、总结TOP Solution
    ############################    
    print("\n" + "="*60)
    print("TOP Solution总结")
    print("="*60)

    stime = time.time()
    discussion_summarys_file_path = f'{COMP_REVIEW_ROOT_PATH}/{safe_title}/top_solution_summarys.json'
    if os.path.exists(discussion_summarys_file_path):
        print(f"发现已存在的TOP Solution总结数据: {discussion_summarys_file_path}")
        user_input = input(f"是否需要重新总结TOP Solution？(y/N): ").strip().lower()
        
        if user_input not in ['y', 'yes']:
            print(f"[TOP Solution] ✓ 跳过: {selected_comp['name']} (使用现有数据)")
        
        else:
            solution_summarizer = SolutionSummarizer()
            solution_summarizer.summarize_solution(safe_title, 
                                                top_k_disussion_name2rank, 
                                                top_k_disussion_name2url)
            print(f"[TOP Solution] ✓ 完成: {selected_comp['name']}")
    else:
        solution_summarizer = SolutionSummarizer()
        solution_summarizer.summarize_solution(safe_title, 
                                            top_k_disussion_name2rank, 
                                            top_k_disussion_name2url)
        print(f"[TOP Solution] ✓ 完成: {selected_comp['name']}")

    etime = time.time()
    print(f"\n[TOP Solution] 总结TOP Solution完成，耗时 {etime-stime} 秒")
    
    
    ############################
    # 8、填充竞赛复盘模版
    ############################ 
    print("\n" + "="*60)
    print("竞赛复盘模版填充")
    print("="*60)

    solution_summary_file_path = f'{COMP_REVIEW_ROOT_PATH}/{safe_title}/solution_summary.html'
    if os.path.exists(solution_summary_file_path):
        print(f"发现已存在的竞赛复盘模版填充数据: {solution_summary_file_path}")
        user_input = input(f"是否需要重新填充竞赛复盘模版？(y/N): ").strip().lower()
        
        if user_input not in ['y', 'yes']:
            print(f"[竞赛复盘模版] ✓ 跳过: {selected_comp['name']} (使用现有数据)")
        else:
            summary_template_filler = SummaryTemplateFiller()
            summary_template_filler.solution_template_fill(safe_title)
            print(f"[竞赛复盘模版] ✓ 填充完成")
    else:
        summary_template_filler = SummaryTemplateFiller()
        summary_template_filler.solution_template_fill(safe_title)
        print(f"[竞赛复盘模版] ✓ 填充完成")


    ############################
    # 9、制作封面图
    ############################
    print("\n" + "="*60)
    print("制作封面图")
    print("="*60)

    # 检查是否已存在封面图文件
    cover_image_file_path = f'{COMP_REVIEW_ROOT_PATH}/{safe_title}/cover/cover.png'
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
            ppt_to_image.main(comp_type="comp_review",
                              title=zh_comp_overview['竞赛名称'],
                              host=zh_comp_overview['组织者'],
                              keywords=keywords)
            print(f"[封面图] ✓ 制作完成: {selected_comp['name']}")
    else:
        with open(f'{COMP_EXPRESS_ROOT_PATH}/{safe_title}/zh_comp_overview.json', 'r', encoding='utf-8') as f:
            zh_comp_overview = json.load(f)

        keywords = zh_comp_overview['竞赛关键词'][1:-1].replace("'", "").replace(", ", "、").replace(" ", "")
        ppt_to_image = PPTToImage()
        ppt_to_image.main(comp_type="comp_review",
                          title=zh_comp_overview['竞赛名称'],
                          host=zh_comp_overview['组织者'],
                          keywords=keywords)
        print(f"[封面图] ✓ 制作完成: {selected_comp['name']}")


    ############################
    # 10、上传封面图至公众号平台
    ############################
    print("\n" + "="*60)
    print("上传封面图至公众号平台")
    print("="*60)

    # 检查是否已存在封面图文件
    cover_image_file_path = f'{COMP_REVIEW_ROOT_PATH}/{safe_title}/cover/cover.png'
    wechat_uploader = WeChatPermanentMaterialUploader()
    upload_result= wechat_uploader.upload_specific_file(cover_image_file_path)
    print(f"[封面图] ✓ 上传完成: {selected_comp['name']}")


    ############################
    # 11、创建草稿至公众号平台
    ############################
    print("\n" + "="*60)
    print("创建草稿至公众号平台")
    print("="*60)

    wechat_draft_creator = WeChatDraftCreator()
    wechat_draft_creator.create_draft(comp_type="comp_review",
                                      title=selected_comp['name'])
    print(f"[草稿] ✓ 创建完成: {selected_comp['name']}")
