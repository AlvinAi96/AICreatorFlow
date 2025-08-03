"""
Function: 软件速递的pipeline
Software List -> Software Details -> 翻译和总结 -> 填充HTML模板 -> 创建草稿至公众号平台

CreateDay: 20250702
Author: HongfengAi
History:
20250702    HongfengAi  第一版
"""

import sys, os
import re
import json
import time
import argparse

# 添加项目根目录到系统路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from configs import SOFTWARE_EXPRESS_ROOT_PATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from crawler.software_list_crawler import ProductHuntWeeklyProductsCrawler
from crawler.software_details_crawler import SoftwareDetailsCrawler
from app_express.app_summarizer import AppSummarizer
from app_express.app_template_fill import AppTemplateFiller
from utils import get_previous_week
from wechat_utils.upload_material import WeChatPermanentMaterialUploader
from wechat_utils.create_draft import WeChatDraftCreator
from wechat_utils.ppt_to_image import PPTToImage


if __name__ == '__main__':
    print("="*80)
    print("软件速递 Pipeline")
    print("="*80)
    
    # 获取命令行参数
    parser = argparse.ArgumentParser(description='软件速递Pipeline')
    parser.add_argument('--topk', type=int, default=10, help='获取前k款软件')
    parser.add_argument('--year', type=int, help='指定年份')
    parser.add_argument('--week', type=str, help='指定周数，如26')
    args = parser.parse_args()
    
    # 确定要处理的年份和周数
    if args.year and args.week:
        year, week = args.year, args.week
    else:
        year, week = get_previous_week()
        print(f"自动获取上一周: {year}年 {week}")
    
    topk = args.topk
    data_dir = f'{SOFTWARE_EXPRESS_ROOT_PATH}/{year}_{week}'
    
    print(f"处理时间: {year}年 {week}")
    print(f"获取软件数量: {topk}")
    print(f"数据目录: {data_dir}")
    
    ############################
    # 1、爬取软件列表
    ############################
    print("\n" + "="*60)
    print("步骤1: 爬取软件列表")
    print("="*60)
    
    software_list_file = f'{data_dir}/software_list_{week}.json'
    
    if os.path.exists(software_list_file):
        print(f"发现已存在的软件列表: {software_list_file}")
        user_input = input("是否需要重新爬取软件列表? (y/N): ").strip().lower()
        
        if user_input not in ['y', 'yes']:
            print(f"[软件列表] ✓ 跳过爬取 (使用现有数据)")
            with open(software_list_file, 'r', encoding='utf-8') as f:
                software_list = json.load(f)
        else:
            stime = time.time()
            crawler = ProductHuntWeeklyProductsCrawler()
            software_list = crawler.crawl_specific_week(year, week, topk)
            etime = time.time()
            print(f"[软件列表] ✓ 爬取完成，共获取 {len(software_list)} 款软件，耗时 {etime-stime:.2f} 秒")
    else:
        stime = time.time()
        crawler = ProductHuntWeeklyProductsCrawler()
        software_list = crawler.crawl_specific_week(year, week, topk)
        etime = time.time()
        print(f"[软件列表] ✓ 爬取完成，共获取 {len(software_list)} 款软件，耗时 {etime-stime:.2f} 秒")
    
    if not software_list:
        print("[软件列表] ❌ 没有获取到软件数据，程序结束。")
        exit()
    
    ############################
    # 2、爬取软件详情
    ############################
    print("\n" + "="*60)
    print("步骤2: 爬取软件详情")
    print("="*60)
    
    all_software_details_file = f'{data_dir}/all_software_details.json'
    
    if os.path.exists(all_software_details_file):
        print(f"发现已存在的软件详情: {all_software_details_file}")
        user_input = input("是否需要重新爬取软件详情? (y/N): ").strip().lower()
        
        if user_input not in ['y', 'yes']:
            print(f"[软件详情] ✓ 跳过爬取 (使用现有数据)")
            with open(all_software_details_file, 'r', encoding='utf-8') as f:
                software_details = json.load(f)
        else:
            stime = time.time()
            details_crawler = SoftwareDetailsCrawler()
            details_crawler.crawl_software_details_from_list(software_list_file, data_dir, topk)
            etime = time.time()
            print(f"[软件详情] ✓ 爬取完成，耗时 {etime-stime:.2f} 秒")
    else:
        stime = time.time()
        details_crawler = SoftwareDetailsCrawler()
        details_crawler.crawl_software_details_from_list(software_list_file, data_dir, topk)
        etime = time.time()
        print(f"[软件详情] ✓ 爬取完成，耗时 {etime-stime:.2f} 秒")
    
    
    ############################
    # 3、翻译和总结软件
    ############################
    print("\n" + "="*60)
    print("步骤3: 翻译和总结软件")
    print("="*60)
    
    zh_software_details_file = f'{data_dir}/zh_all_software_details.json'
    
    if os.path.exists(zh_software_details_file):
        print(f"发现已存在的中文软件详情: {zh_software_details_file}")
        user_input = input("是否需要重新翻译和总结软件? (y/N): ").strip().lower()
        
        if user_input not in ['y', 'yes']:
            print(f"[软件翻译] ✓ 跳过翻译 (使用现有数据)")
        else:
            stime = time.time()
            summarizer = AppSummarizer()
            summarizer.summarize_apps_from_json(all_software_details_file, zh_software_details_file)
            etime = time.time()
            print(f"[软件翻译] ✓ 翻译完成，耗时 {etime-stime:.2f} 秒")
    else:
        stime = time.time()
        summarizer = AppSummarizer()
        summarizer.summarize_apps_from_json(all_software_details_file, zh_software_details_file)
        etime = time.time()
        print(f"[软件翻译] ✓ 翻译完成，耗时 {etime-stime:.2f} 秒")

    ############################
    # 4、制作封面图
    ############################
    print("\n" + "="*60)
    print("制作封面图")
    print("="*60)

    # 检查是否已存在封面图文件
    cover_image_file_path = f'{SOFTWARE_EXPRESS_ROOT_PATH}/{year}_{week}/cover/cover.png'
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
    
    html_file = f'{data_dir}/zh_all_software_express.html'
    
    if os.path.exists(html_file):
        print(f"发现已存在的HTML文件: {html_file}")
        user_input = input("是否需要重新填充HTML模板? (y/N): ").strip().lower()
        
        if user_input not in ['y', 'yes']:
            print(f"[HTML模板] ✓ 跳过填充 (使用现有数据)")
        else:
            template_filler = AppTemplateFiller()
            template_filler.app_template_fill(year, week)
            print(f"[HTML模板] ✓ 填充完成")
    else:
        template_filler = AppTemplateFiller()
        template_filler.app_template_fill(year, week)
        print(f"[HTML模板] ✓ 填充完成")



    ############################
    # 5、上传封面图至公众号平台
    ############################
    print("\n" + "="*60)
    print("上传封面图至公众号平台")
    print("="*60)

    # 检查是否已存在封面图文件
    cover_image_file_path = f'{SOFTWARE_EXPRESS_ROOT_PATH}/{year}_{week}/cover/cover.png'
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
    wechat_draft_creator.create_draft(comp_type="app_express",
                                      title=f"ProductHunt产品速递 | {year}年第{week}周热门创新产品精选",
                                      year=year,
                                      week=week)
    print(f"[草稿] ✓ 创建完成！")

