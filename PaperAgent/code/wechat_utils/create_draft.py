import requests
import json
import os
import argparse
from typing import Dict, Any, Optional, List

import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from configs import PAPER_EXPRESS_ROOT_PATH, WECHAT_APP_ID, WECHAT_APP_SECRET
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import safe_title_func, get_previous_week


class WeChatDraftCreator:
    """微信公众号草稿箱创建工具"""
    
    def __init__(self):
        self.appid = WECHAT_APP_ID
        self.secret = WECHAT_APP_SECRET
        self.access_token = ""

        token_result = self.get_access_token(self.appid, self.secret)
        if token_result['success']:
            self.access_token = token_result['access_token']

        if not self.access_token:
            print("警告: 未提供access_token，请确保已配置")
        
        self.api_url = f"https://api.weixin.qq.com/cgi-bin/draft/add?access_token={self.access_token}"


    def get_access_token(self, appid: str, appsecret: str) -> Dict[str, Any]:
        """
        获取微信公众号Access Token
        """
        url = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={appid}&secret={appsecret}"
        
        # 创建不使用代理的session
        session = requests.Session()
        session.trust_env = False  # 禁用环境变量中的代理设置
        
        response = session.get(url)
        result = response.json()

        print(f"✅ Access Token获取成功")
        print(f"⏰ 有效期: {result.get('expires_in', 0)}秒 ({result.get('expires_in', 0) // 60}分钟)")
        return {
            'success': True,
            'access_token': result['access_token'],
            'expires_in': result.get('expires_in', 7200)
        }

    
    def create_draft(self, 
                     comp_type: str,
                     title: str,
                     year: str,
                     week: str) -> Dict[str, Any]:
        """
        创建微信公众号草稿
        
        Args:
            comp_type: 推文类型（comp_express or comp_review）
            title: 标题
            thumb_media_id: 封面图片媒体ID（直接传入的media_id）
        """
        if comp_type == "paper_express":
            # 论文速递类型
            # year, week = get_previous_week()
            data_dir = f"{PAPER_EXPRESS_ROOT_PATH}/{year}_{week}"
            
            # 读取封面图片ID
            cover_file_path = f"{data_dir}/cover/cover.json"
            with open(cover_file_path, 'r', encoding='utf-8') as f:
                cover_data = json.load(f)
            thumb_media_id = cover_data.get('media_id', '')
            
            # 读取HTML内容
            html_file_path = f"{data_dir}/zh_all_papers_express.html"
            with open(html_file_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            # 设置关键词
            article_title = title
        else:
            # 其他类型暂不支持
            return {"errcode": -1, "errmsg": f"不支持的类型: {comp_type}"}



        payload = {
            "articles": [{
                "article_type": "news",
                "title": article_title,
                "author": "宅小P",
                "digest": f"Hugging Face论文速递 | {year}年第{week[1:]}周AI精选热门论文",
                "content": html_content,
                "thumb_media_id": thumb_media_id,
                "need_open_comment": 1,
                "only_fans_can_comment": 0
            }]
        }
    
        # 发送请求
        headers = {
            'Content-Type': 'application/json; charset=utf-8'
        }
        # 创建不使用代理的session
        session = requests.Session()
        session.trust_env = False  # 禁用环境变量中的代理设置

        response = session.post(
            self.api_url,
            data=json.dumps(payload, ensure_ascii=False).encode('utf-8'),
            headers=headers
        )
        
        # 解析响应
        result = response.json()
        
        if 'errcode' not in result:
            print(f"草稿创建成功！")
            print(f"媒体ID: {result.get('media_id')}")
            return result
        else:
            print(f"草稿创建失败: {result.get('errcode')}: {result.get('errmsg')}")
            return result
    

if __name__ == "__main__":
    args = argparse.ArgumentParser()
    args.add_argument("--comp_type", type=str, default="paper_express", help="推文类型")
    args.add_argument("--title", type=str, default="HF论文速递 | 2025年第25周AI精选热门论文", help="标题")
    args.add_argument("--year", type=str, default="2025", help="年份")
    args.add_argument("--week", type=str, default="W25", help="周数")
    args = args.parse_args()
    
    print("🚀 微信公众号草稿创建工具")
    creator = WeChatDraftCreator()
    result = creator.create_draft(
        comp_type=args.comp_type,
        title=args.title,
        year=args.year,
        week=args.week
    )
