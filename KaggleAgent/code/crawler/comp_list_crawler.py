"""
Function: 爬取比赛列表信息

CreateDay: 20250525
Author: HongfengAi
History:
20250525    HongfengAi  第一版
"""
import selenium
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import time
from datetime import datetime
import argparse
import json

import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from configs import OUTPUT_ROOT_PATH
from crawler.crawler_utils import open_browser


class CompListCrawler():
    def __init__(self):
        self.url = "https://www.kaggle.com/competitions"
        
    def open_browser(self):
        """打开浏览器"""
        self.browser, self.wait = open_browser()

    def parse_page(self, page_limit=10):
        """解析页面"""
        self.page_limit = int(page_limit)  # 确保page_limit是整数类型
        # 打开模拟浏览器
        self.open_browser()
        # 进入点击进入Competitions详细列表网页
        self.browser.get(self.url)
        button = self.browser.find_element(By.XPATH,
                                           '//*[@id="site-content"]/div[2]/div/div[4]/div/div[2]/div/div[1]/button[1]')
        button.click()  # 直接点击按钮
        
        # 获取当前页面的所有比赛信息
        all_competitions = []  # 存储所有比赛信息
        page = 1
        current_date = datetime.now().strftime('%Y%m%d')
        
        while True:
            try:
                # 下拉到最低，保证页面完整加载
                self.browser.execute_script("window.scrollTo(0, document.body.scrollHeight)")
                time.sleep(5)  # 等待页面加载

                competitions = self.wait.until(EC.presence_of_all_elements_located(
                    (By.XPATH, '//*[@id="site-content"]/div[2]/div/div[5]/div/div/div/ul[1]/li/div')))
                
                # 遍历每个比赛元素
                for i, comp in enumerate(competitions):
                    try:
                        # 获取比赛名称
                        name = comp.find_element(By.XPATH, './/a/div/div[2]/div').text
                        # 获取比赛链接
                        link = comp.find_element(By.XPATH, './/a').get_attribute('href')
                        # 获取比赛描述
                        description = comp.find_element(By.XPATH, './/a/div/div[2]/span[1]').text
                        # 获取比赛meta
                        comp_type_team = comp.find_element(By.XPATH, './/a/div/div[2]/span[2]/span').text.split('·')
                        comp_type_team = [v.lstrip() for v in comp_type_team]
                        comp_type_team = [v.rstrip() for v in comp_type_team]
                        # 获取比赛剩余时间
                        leave_time = comp_type_team[-1]
                        # 获取比赛当前队伍
                        team_number = comp_type_team[-2].split(' ')[0]
                        # 获取比赛类型
                        comp_type = ' · '.join(comp_type_team[:-2])
                        # 获取奖金
                        comp_reward = comp.find_element(By.XPATH,
                                                        f'//*[@id="site-content"]/div[2]/div/div[5]/div/div/div/ul[1]/li[{i + 1}]/div/div/div[1]/div').text

                        
                        all_competitions.append({'name': name,
                                                'link': link,
                                                'description': description,
                                                'comp_type': comp_type,
                                                'team_number': team_number,
                                                'leave_time': leave_time,
                                                'comp_reward': comp_reward,
                                                'current_date': current_date
                                                })
                        
                    except selenium.common.exceptions.StaleElementReferenceException as e:
                        print(f'元素已过期，跳过第{i+1}个比赛: {e}')
                        continue
                    
                    except Exception as e:
                        print(f'解析第{i+1}个比赛信息时出错: {e}')
                        continue
                
                print(f'第 {page} 页爬取完成，当前共累积获取 {len(all_competitions)} 个比赛信息')
                
                # 尝试点击下一页按钮
                try:
                    next_button = self.browser.find_element(By.XPATH,
                                                            '//*[@id="site-content"]/div[2]/div/div[5]/div/div/div/ul[2]/li[11]/button')

                    if not next_button.is_enabled():
                        print('已到达最后一页')
                        break
                    # next_button.click()
                    # 因为点击按钮时被其他元素（Cookie确认）遮挡了，所以使用 JavaScript 点击
                    self.browser.execute_script("arguments[0].click();", next_button)
                    page += 1
                    # 确保类型一致性，添加调试信息
                    if page > self.page_limit:
                        print(f'已达到页数爬取上限 {self.page_limit}')
                        break
                    time.sleep(5)  # 等待新页面加载
                except Exception as e:
                    print('没有找到下一页按钮或已到达最后一页, e:', e)
                    break
                
            except selenium.common.exceptions.TimeoutException:
                print('parse_page: TimeoutException 网页超时')
                continue
            
            except selenium.common.exceptions.StaleElementReferenceException:
                print('turn_page: StaleElementReferenceException 某元素因JS刷新已过时没出现在页面中')
                print('刷新并重新解析网页...')
                self.browser.refresh()
                time.sleep(1)
                continue
            
            except Exception as e:
                print(f'发生错误: {e}')
                break
        
        # 将结果保存为JSON文件
        if all_competitions:
            # 保存为JSON格式
            json_file_path = os.path.join(OUTPUT_ROOT_PATH, 'kaggle_competitions_list.json')
            with open(json_file_path, 'w', encoding='utf-8') as f:
                json.dump(all_competitions, f, ensure_ascii=False, indent=4)
            print(f'数据已保存到 {json_file_path}，共 {len(all_competitions)} 条记录')
            
        # 关闭浏览器
        self.browser.quit()
        
        return all_competitions


if __name__ == '__main__':
    # 创建命令行参数解析器
    parser = argparse.ArgumentParser(description='爬取Kaggle比赛列表信息')
    parser.add_argument('--pages', '-p', type=int, default=1, 
                       help='要爬取的页数上限 (默认: 2)')
    
    # 解析命令行参数
    args = parser.parse_args()
    print(f'开始爬取，页数上限: {args.pages}')
    
    # 执行爬虫并显示结果
    clspider = CompListCrawler()
    result = clspider.parse_page(page_limit=args.pages)
    print(f'爬取完成，共获取 {len(result)} 个比赛信息')
    
    # 开始爬取，页数上限: 3
    # DevTools listening on ws://127.0.0.1:54359/devtools/browser/9842122b-33fa-429e-832d-35580025ec24
    # WARNING: All log messages before absl::InitializeLog() is called are written to STDERR
    # I0000 00:00:1749994529.809319    8560 voice_transcription.cc:58] Registering VoiceTranscriptionCapability
    # 第 1 页爬取完成，当前共累积获取 20 个比赛信息
    # 第 2 页爬取完成，当前共累积获取 40 个比赛信息
    # 第 3 页爬取完成，当前共累积获取 60 个比赛信息
    # 已达到页数爬取上限 3
    # 数据已保存到 E:/kaggle_agent/output\kaggle_competitions_list.json，共 60 条记录
    # 爬取完成，共获取 60 个比赛信息