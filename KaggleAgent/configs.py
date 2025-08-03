import os


##################
# 爬虫配置
##################
# 浏览器输入about://version，获取用户代理
# 下载跟chrome版本适配的chromedriver: https://googlechromelabs.github.io/chrome-for-testing/
# Windows将chromedriver.exe放置C:\Program Files (x86)\Google\Chrome\Application
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36"


##################
# 路径配置
##################
# 输出根保存路径
OUTPUT_ROOT_PATH = "C:/Users/alvin/Downloads" # "E:/kaggle_agent/output" # 
os.makedirs(OUTPUT_ROOT_PATH, exist_ok=True)

# 竞赛速递的数据保存路径
COMP_EXPRESS_ROOT_PATH = os.path.join(OUTPUT_ROOT_PATH, "comp_express")
os.makedirs(COMP_EXPRESS_ROOT_PATH, exist_ok=True)

# 竞赛复盘的数据保存路径
COMP_REVIEW_ROOT_PATH = os.path.join(OUTPUT_ROOT_PATH, "comp_review")
os.makedirs(COMP_REVIEW_ROOT_PATH, exist_ok=True)


##################
# LLM配置
##################
OPENAI_API_KEY = ""


##################
# Wechat配置
##################
WECHAT_APP_ID = ""
WECHAT_APP_SECRET = ""