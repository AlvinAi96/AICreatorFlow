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

    def upload_permanent_video(self, video_path: str, title: str, introduction: str = "") -> Dict:
        """
        上传视频到永久素材库
        
        Args:
            video_path: 视频文件路径
            title: 视频标题，不超过30个字
            introduction: 视频介绍
        """
        if not Path(video_path).exists():
            return {
                "success": False,
                "error": f"文件不存在: {video_path}"
            }

        # 检查标题长度
        if len(title) > 30:
            title = title[:30]
            print(f"警告: 视频标题过长，已截取为: {title}")

        # 构建请求URL
        url = f"https://api.weixin.qq.com/cgi-bin/material/add_material?access_token={self.access_token}&type=video"
        
        # 创建不使用代理的session
        session = requests.Session()
        session.trust_env = False  # 禁用环境变量中的代理设置
        
        # 准备视频描述信息
        description = {
            "title": title,
            "introduction": introduction
        }
        description_json = json.dumps(description, ensure_ascii=False)
        
        # 准备文件上传
        with open(video_path, 'rb') as f:
            # 确定content-type
            file_ext = Path(video_path).suffix.lower()
            if file_ext == '.mp4':
                content_type = 'video/mp4'
            elif file_ext == '.avi':
                content_type = 'video/avi'
            elif file_ext == '.mov':
                content_type = 'video/quicktime'
            elif file_ext == '.wmv':
                content_type = 'video/x-ms-wmv'
            else:
                content_type = 'video/mp4'  # 默认
            
            files = {'media': (Path(video_path).name, f, content_type)}
            data = {'description': description_json}
            
            print(f"正在上传视频到永久素材库: {Path(video_path).name}")
            print(f"视频标题: {title}")
            print(f"视频介绍: {introduction}")
            
            # 发送请求
            response = session.post(url, files=files, data=data, timeout=300)  # 视频上传时间较长
            
            # 解析响应
            result = response.json()
            
            if response.status_code == 200:
                if 'media_id' in result:
                    return {
                        "success": True,
                        "media_id": result['media_id'],
                        "url": result.get('url', ''),
                        "file_path": video_path,
                        "file_name": Path(video_path).name,
                        "title": title,
                        "introduction": introduction
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

    def upload_permanent_media(self, media_path: str, media_type: str = "auto", 
                              title: str = "", introduction: str = "") -> Dict:
        """
        上传媒体文件到永久素材库（自动识别类型）
        
        Args:
            media_path: 媒体文件路径
            media_type: 媒体类型，可选值: auto, image, video, voice, thumb
            title: 视频标题（仅视频需要）
            introduction: 视频介绍（仅视频需要）
        """
        if not Path(media_path).exists():
            return {
                "success": False,
                "error": f"文件不存在: {media_path}"
            }

        # 自动识别媒体类型
        if media_type == "auto":
            file_ext = Path(media_path).suffix.lower()
            if file_ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp']:
                media_type = "image"
            elif file_ext in ['.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm']:
                media_type = "video"
            else:
                media_type = "image"  # 默认当作图片处理
        
        # 根据类型调用相应的上传方法
        if media_type == "video":
            # 如果没有提供标题，使用文件名作为标题
            if not title:
                title = Path(media_path).stem[:30]  # 限制30个字符
            return self.upload_permanent_video(media_path, title, introduction)
        elif media_type == "image":
            return self.upload_permanent_image(media_path)
    

    def upload_specific_file(self, file_path: str, title: str = "", introduction: str = "") -> Dict:
        """
        上传指定文件（自动识别类型）
        
        Args:
            file_path: 文件路径
            title: 视频标题（仅视频需要）
            introduction: 视频介绍（仅视频需要）
            
        Returns:
            上传结果
        """
        print(f"准备上传文件: {file_path}")
        print("=" * 50)

        # 使用自动识别上传方法
        result = self.upload_permanent_media(file_path, "auto", title, introduction)
        
        if result.get("success"):
            print(f"✅ 上传成功!")
            print(f"📁 文件: {result['file_name']}")
            print(f"🆔 Media ID: {result['media_id']}")
            if result.get('url'):
                print(f"🔗 媒体URL: {result['url']}")
            if result.get('title'):
                print(f"📺 视频标题: {result['title']}")
            if result.get('introduction'):
                print(f"📝 视频介绍: {result['introduction']}")
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
    parser.add_argument("--file_path", type=str, default="C:/Users/alvin/Downloads/comp_express/cmi__detect_behavior_with_sensor_data/cover/cover.png", help="要上传的媒体文件路径")
    parser.add_argument("--title", type=str, default="", help="视频标题（仅视频文件需要，不超过30个字）")
    parser.add_argument("--introduction", type=str, default="", help="视频介绍（仅视频文件需要）")
    args = parser.parse_args()
    
    # 上传素材
    uploader = WeChatPermanentMaterialUploader()
    
    result = uploader.upload_specific_file(args.file_path, args.title, args.introduction)
