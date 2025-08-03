"""
Function: 爬虫通用函数

CreateDay: 20250615
Author: HongfengAi
History:
20250615    HongfengAi  第一版
"""
from selenium import webdriver
from selenium.webdriver.support.wait import WebDriverWait

import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))))
from configs import USER_AGENT


def open_browser():
    """打开浏览器"""
    
    # 配置 Chrome 选项
    options = webdriver.ChromeOptions()
    options.add_argument(f'--user-agent={USER_AGENT}')
    
    # 创建 Chrome 浏览器实例
    browser = webdriver.Chrome(options=options)
    
    # 添加反检测代码
    browser.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
                        "source": """
                        Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined
                        })
                    """
                    })

    # 隐式等待：等待页面全部元素加载完成（即页面加载圆圈不再转后），才会执行下一句，如果超过设置时间则抛出异常
    try:
        browser.implicitly_wait(10)
    except:
        print("页面无法加载完成，无法开启爬虫操作！")
        
    # 显式等待：设置浏览器最长允许超时的时间
    wait = WebDriverWait(browser, 10)
    return browser, wait