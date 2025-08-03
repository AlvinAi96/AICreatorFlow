"""
Function: 论文速递的pipeline
Paper List -> Paper Details -> 翻译和总结 -> 填充HTML模板 -> 创建草稿至公众号平台

CreateDay: 20250129
Author: HongfengAi
History:
20250129    HongfengAi  第一版
"""

import sys, os
import re
import json
import time
import argparse

# 添加项目根目录到系统路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from configs import PAPER_EXPRESS_ROOT_PATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from crawler.paper_list_crawler import HFWeeklyPapersCrawler
from crawler.paper_details_crawler import PaperDetailsCrawler
from paper_express.paper_summarizer import PaperSummarizer
from paper_express.paper_template_fill import PaperTemplateFiller
from utils import get_previous_week
from wechat_utils.upload_material import WeChatPermanentMaterialUploader
from wechat_utils.create_draft import WeChatDraftCreator
from wechat_utils.ppt_to_image import PPTToImage


if __name__ == '__main__':
    print("="*80)
    print("论文速递 Pipeline")
    print("="*80)
    
    # 获取命令行参数
    parser = argparse.ArgumentParser(description='论文速递Pipeline')
    parser.add_argument('--topk', type=int, default=10, help='获取前k篇论文')
    parser.add_argument('--year', type=int, help='指定年份')
    parser.add_argument('--week', type=str, help='指定周数，如W25')
    args = parser.parse_args()
    
    # 确定要处理的年份和周数
    if args.year and args.week:
        year, week = args.year, args.week
    else:
        year, week = get_previous_week()
        print(f"自动获取上一周: {year}年 {week}")
    
    topk = args.topk
    data_dir = f'{PAPER_EXPRESS_ROOT_PATH}/{year}_{week}'
    
    print(f"处理时间: {year}年 {week}")
    print(f"获取论文数量: {topk}")
    print(f"数据目录: {data_dir}")
    
    ############################
    # 1、爬取论文列表
    ############################
    print("\n" + "="*60)
    print("步骤1: 爬取论文列表")
    print("="*60)
    
    paper_list_file = f'{data_dir}/paper_list_{year}-{week}.json'
    
    if os.path.exists(paper_list_file):
        print(f"发现已存在的论文列表: {paper_list_file}")
        user_input = input("是否需要重新爬取论文列表? (y/N): ").strip().lower()
        
        if user_input not in ['y', 'yes']:
            print(f"[论文列表] ✓ 跳过爬取 (使用现有数据)")
            with open(paper_list_file, 'r', encoding='utf-8') as f:
                papers_list = json.load(f)
        else:
            stime = time.time()
            crawler = HFWeeklyPapersCrawler()
            papers_list = crawler.crawl_specific_week(year, week, topk)
            etime = time.time()
            print(f"[论文列表] ✓ 爬取完成，共获取 {len(papers_list)} 篇论文，耗时 {etime-stime:.2f} 秒")
    else:
        stime = time.time()
        crawler = HFWeeklyPapersCrawler()
        papers_list = crawler.crawl_specific_week(year, week, topk)
        etime = time.time()
        print(f"[论文列表] ✓ 爬取完成，共获取 {len(papers_list)} 篇论文，耗时 {etime-stime:.2f} 秒")
    
    if not papers_list:
        print("[论文列表] ❌ 没有获取到论文数据，程序结束。")
        exit()
    
    ############################
    # 2、爬取论文详情
    ############################
    print("\n" + "="*60)
    print("步骤2: 爬取论文详情")
    print("="*60)
    
    all_papers_details_file = f'{data_dir}/all_papers_details.json'
    
    if os.path.exists(all_papers_details_file):
        print(f"发现已存在的论文详情: {all_papers_details_file}")
        user_input = input("是否需要重新爬取论文详情? (y/N): ").strip().lower()
        
        if user_input not in ['y', 'yes']:
            print(f"[论文详情] ✓ 跳过爬取 (使用现有数据)")
            with open(all_papers_details_file, 'r', encoding='utf-8') as f:
                papers_details = json.load(f)
        else:
            stime = time.time()
            details_crawler = PaperDetailsCrawler()
            details_crawler.crawl_papers_details_from_list(paper_list_file, data_dir, topk)
            etime = time.time()
            print(f"[论文详情] ✓ 爬取完成，耗时 {etime-stime:.2f} 秒")
    else:
        stime = time.time()
        details_crawler = PaperDetailsCrawler()
        details_crawler.crawl_papers_details_from_list(paper_list_file, data_dir, topk)
        etime = time.time()
        print(f"[论文详情] ✓ 爬取完成，耗时 {etime-stime:.2f} 秒")
    
    
    ############################
    # 3、翻译和总结论文
    ############################
    print("\n" + "="*60)
    print("步骤3: 翻译和总结论文")
    print("="*60)
    
    zh_papers_details_file = f'{data_dir}/zh_all_papers_details.json'
    
    if os.path.exists(zh_papers_details_file):
        print(f"发现已存在的中文论文详情: {zh_papers_details_file}")
        user_input = input("是否需要重新翻译和总结论文? (y/N): ").strip().lower()
        
        if user_input not in ['y', 'yes']:
            print(f"[论文翻译] ✓ 跳过翻译 (使用现有数据)")
        else:
            stime = time.time()
            summarizer = PaperSummarizer()
            summarizer.summarize_papers_from_json(all_papers_details_file, zh_papers_details_file)
            etime = time.time()
            print(f"[论文翻译] ✓ 翻译完成，耗时 {etime-stime:.2f} 秒")
    else:
        stime = time.time()
        summarizer = PaperSummarizer()
        summarizer.summarize_papers_from_json(all_papers_details_file, zh_papers_details_file)
        etime = time.time()
        print(f"[论文翻译] ✓ 翻译完成，耗时 {etime-stime:.2f} 秒")

    ############################
    # 4、制作封面图
    ############################
    print("\n" + "="*60)
    print("制作封面图")
    print("="*60)

    # 检查是否已存在封面图文件
    cover_image_file_path = f'{PAPER_EXPRESS_ROOT_PATH}/{year}_{week}/cover/cover.png'
    if os.path.exists(cover_image_file_path):
        print(f"发现已存在的封面图: {cover_image_file_path}")
        user_input = input(f"是否需要重新制作封面图？(y/N): ").strip().lower()

        if user_input not in ['y', 'yes']:
            print(f"[封面图] ✓ 跳过: {year}_{week} (使用现有数据)")
        else:
            ppt_to_image = PPTToImage()
            ppt_to_image.main(year=year,
                              week=week)
            print(f"[封面图] ✓ 制作完成: {year}_{week}")
    else:    
        ppt_to_image = PPTToImage()
        ppt_to_image.main(year=year,
                          week=week)
        print(f"[封面图] ✓ 制作完成: {year}_{week}")

    ############################
    # 5、填充HTML模板
    ############################
    print("\n" + "="*60)
    print("步骤4: 填充HTML模板")
    print("="*60)
    
    html_file = f'{data_dir}/zh_all_papers_express.html'
    
    if os.path.exists(html_file):
        print(f"发现已存在的HTML文件: {html_file}")
        user_input = input("是否需要重新填充HTML模板? (y/N): ").strip().lower()
        
        if user_input not in ['y', 'yes']:
            print(f"[HTML模板] ✓ 跳过填充 (使用现有数据)")
        else:
            template_filler = PaperTemplateFiller()
            template_filler.paper_template_fill(year, week)
            print(f"[HTML模板] ✓ 填充完成")
    else:
        template_filler = PaperTemplateFiller()
        template_filler.paper_template_fill(year, week)
        print(f"[HTML模板] ✓ 填充完成")



    ############################
    # 5、上传封面图至公众号平台
    ############################
    print("\n" + "="*60)
    print("上传封面图至公众号平台")
    print("="*60)

    # 检查是否已存在封面图文件
    cover_image_file_path = f'{PAPER_EXPRESS_ROOT_PATH}/{year}_{week}/cover/cover.png'
    wechat_uploader = WeChatPermanentMaterialUploader()
    upload_result= wechat_uploader.upload_specific_file(cover_image_file_path)
    print(f"[封面图] ✓ 上传完成！")


    ############################
    # 6、创建草稿至公众号平台
    ############################
    print("\n" + "="*60)
    print("创建草稿至公众号平台")
    print("="*60)

    wechat_draft_creator = WeChatDraftCreator()
    wechat_draft_creator.create_draft(comp_type="paper_express",
                                      title=f"HF论文速递 | {year}年第{week[1:]}周AI精选热门论文",
                                      year=year,
                                      week=week)
    print(f"[草稿] ✓ 创建完成！")

