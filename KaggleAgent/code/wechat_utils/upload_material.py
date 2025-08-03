#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
微信公众号永久素材上传工具
将图片上传到微信公众号永久素材库并返回media_id和URL
"""

import os
import sys
import json
import requests
from pathlib import Path
from typing import Dict, Optional, Any
import argparse

import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from configs import WECHAT_APP_ID, WECHAT_APP_SECRET


class WeChatPermanentMaterialUploader:
    """微信公众号永久素材上传器"""
    
    def __init__(self):
        self.appid = WECHAT_APP_ID
        self.secret = WECHAT_APP_SECRET
        self.access_token = ""

        token_result = self.get_access_token(self.appid, self.secret)
        if token_result['success']:
            self.access_token = token_result['access_token']

        if not self.access_token:
            print("警告: 未提供access_token，请确保已配置")
    

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
        print(result)
        print(f"✅ Access Token获取成功")
        print(f"⏰ 有效期: {result.get('expires_in', 0)}秒 ({result.get('expires_in', 0) // 60}分钟)")
        return {
            'success': True,
            'access_token': result['access_token'],
            'expires_in': result.get('expires_in', 7200)
        }
    
    def upload_permanent_image(self, image_path: str) -> Dict:
        """
        上传图片到永久素材库
        
        Args:
            image_path: 图片文件路径
        """
        if not Path(image_path).exists():
            return {
                "success": False,
                "error": f"文件不存在: {image_path}"
            }

        # 构建请求URL
        url = f"https://api.weixin.qq.com/cgi-bin/material/add_material?access_token={self.access_token}&type=image"
        
        # 创建不使用代理的session
        session = requests.Session()
        session.trust_env = False  # 禁用环境变量中的代理设置
        
        # 准备文件上传
        with open(image_path, 'rb') as f:
            files = {'media': (Path(image_path).name, f, 'image/png')}
            print(f"正在上传到永久素材库: {Path(image_path).name}")
            
            # 发送请求
            response = session.post(url, files=files, timeout=60)
            
            # 解析响应
            result = response.json()
            
            if response.status_code == 200:
                if 'media_id' in result:
                    return {
                        "success": True,
                        "media_id": result['media_id'],
                        "url": result.get('url', ''),
                        "file_path": image_path,
                        "file_name": Path(image_path).name,
                    }
                else:
                    return {
                        "success": False,
                        "error": f"API错误: {result.get('errmsg', '未知错误')} (错误码: {result.get('errcode', 'N/A')})",
                        "errcode": result.get('errcode'),
                        "errmsg": result.get('errmsg')
                    }
            else:
                return {
                    "success": False,
                    "error": f"HTTP错误: {response.status_code}"
                    }
    

    def upload_specific_file(self, file_path: str) -> Dict:
        """
        上传指定文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            上传结果
        """
        print(f"准备上传文件: {file_path}")
        print("=" * 50)

        result = self.upload_permanent_image(file_path)
        
        if result.get("success"):
            print(f"✅ 上传成功!")
            print(f"📁 文件: {result['file_name']}")
            print(f"🆔 Media ID: {result['media_id']}")
            if result.get('url'):
                print(f"🔗 图片URL: {result['url']}")
        else:
            print(f"\n❌ 上传失败: {result.get('error', '未知错误')}")
        
        # 在file_path文件的同级目录下进行保存
        file_name = Path(file_path).name.split(".")[0]
        file_dir = Path(file_path).parent
        output_file = file_dir / f"{file_name}.json"
        self.save_result(result, output_file)

        return result
    

    def save_result(self, result: Dict, 
                    output_file: str):
        """保存上传结果到JSON文件"""
        try:
            # 保存到文件
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            print(f"结果已保存到: {output_file}")
        except Exception as e:
            print(f"保存结果失败: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="微信公众号永久素材上传工具")
    parser.add_argument("--file_path", type=str, default="C:/Users/alvin/Downloads/comp_express/cmi__detect_behavior_with_sensor_data/cover/cover.png", help="要上传的图片文件路径")
    args = parser.parse_args()
    
    # 上传素材
    uploader = WeChatPermanentMaterialUploader()
    result = uploader.upload_specific_file(args.file_path)