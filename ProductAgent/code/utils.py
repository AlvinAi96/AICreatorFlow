import re
import os
import json
import datetime
from langchain_openai import ChatOpenAI

import sys
# 添加项目根目录到系统路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from configs import OPENAI_API_KEY


def safe_title_func(title):
    """将标题转换为安全标题"""
    # 剔除特殊字符
    safe_title = re.sub(r'[\\/*?:"<>|.,。，-]', "", title)
    # 只保留prefix len=100的字符串
    safe_title = safe_title[:80]
    # 转换为小写
    safe_title = safe_title.lower()
    # 转换为md格式
    safe_title = safe_title.replace(" ", "_")
    return safe_title


def set_proxy():
    """设置proxy"""
    os.environ["http_proxy"] = "http://127.0.0.1:7890"
    os.environ["https_proxy"] = "http://127.0.0.1:7890"
    os.environ["all_proxy"] = "socks5://127.0.0.1:7890"


def unset_proxy():
    """取消proxy"""
    os.environ["http_proxy"] = ""
    os.environ["https_proxy"] = ""
    os.environ["all_proxy"] = ""


def init_llm(model:str="gpt-4o",
             temperature:float=0.7,
             max_tokens:int=8192,
             streaming:bool=True,
             timeout:int=None,
             max_retries:int=2):
    """初始化llm"""
    set_proxy()
    llm = ChatOpenAI(
        api_key=OPENAI_API_KEY,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        streaming=streaming,
        timeout=timeout,
        max_retries=max_retries
    )
    return llm


def format_json_block(json_str: str) -> str:
    """
    处理JSON格式块，清理并格式化JSON字符串
    Args:
        json_str: 包含JSON格式块的字符串，如 "```json\n['传感器数据处理']\n```
    """
    if not json_str:
        return ""

    # 移除 ```json 和 ``` 标记
    json_str = re.sub(r'```json\n|```', '', json_str)
    return json_str.strip()


def parse_llm_json_output(llm_output: str):
    """解析LLM输出的JSON，支持多种格式"""
    try:
        # 方法1: 尝试直接解析JSON
        try:
            return json.loads(llm_output)
        except json.JSONDecodeError:
            pass
        
        # 方法2: 如果有```json```标记，提取其中的JSON内容
        json_pattern = r'```json\s*(.*?)\s*```'
        json_match = re.search(json_pattern, llm_output, re.DOTALL)
        if json_match:
            json_content = json_match.group(1).strip()
            try:
                return json.loads(json_content)
            except json.JSONDecodeError:
                print(f"Failed to parse JSON from ```json``` block: {json_content}")
        
        # 方法3: 如果有```标记（不一定是json），提取其中的内容
        general_pattern = r'```.*?\s*(.*?)\s*```'
        general_match = re.search(general_pattern, llm_output, re.DOTALL)
        if general_match:
            content = general_match.group(1).strip()
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                print(f"Failed to parse JSON from ``` block: {content}")
        
        # 方法4: 尝试从文本中提取JSON对象（查找最外层的{}）
        brace_start = llm_output.find('{')
        brace_end = llm_output.rfind('}')
        if brace_start != -1 and brace_end != -1 and brace_end > brace_start:
            json_candidate = llm_output[brace_start:brace_end+1]
            try:
                return json.loads(json_candidate)
            except json.JSONDecodeError:
                print(f"Failed to parse JSON from extracted braces: {json_candidate}")
        
        print("No valid JSON found in LLM output")
        return None
        
    except Exception as e:
        print(f"Error parsing LLM JSON output: {e}")
        return None
    

def get_previous_week():
    """
    获取上一周的年份和周数

    Returns:
        tuple: (year, week) 上一周的年份和周数
    """
    # 获取当前日期
    current_date = datetime.datetime.now()
    year = current_date.year
    
    # 计算当前是第几周
    # 使用ISO周数计算（周一为每周第一天）
    week_num = current_date.isocalendar()[1]
    
    if week_num == 1:
        # 如果是第一周，上一周是上一年的最后一周
        prev_year = year - 1
        # 计算上一年的最后一周（通常是第52或53周）
        last_day_of_prev_year = datetime.datetime(prev_year, 12, 31)
        prev_week_num = last_day_of_prev_year.isocalendar()[1]
        return prev_year, prev_week_num
    else:
        # 否则就是上一周
        prev_week = week_num-1
        return year, prev_week