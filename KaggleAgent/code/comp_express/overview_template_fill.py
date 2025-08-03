"""
Function: 将竞赛概览的内容填充到竞赛概览推文的模板内

CreateDay: 20250612
Author: HongfengAi
History:
20250612    HongfengAi  第一版
"""

import json
import os
import argparse
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from configs import OUTPUT_ROOT_PATH, COMP_EXPRESS_ROOT_PATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import safe_title_func


class OverviewTemplateFiller():
    def __init__(self):
        self.data_root_path = COMP_EXPRESS_ROOT_PATH
        self.template_path = "./code/comp_express/wechat_html_template/overview_template.html"
    

    def load_json_file(self, file_path):
        """加载JSON文件"""
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)


    def fill_template(self, template, data):
        """填充模板中的关键词"""
        # 定义关键词映射
        keyword_mapping = {
            '[竞赛主标题]': data.get('竞赛名称', ''),
            '[竞赛副标题]': data.get('竞赛副标题', ''),
            '[竞赛关键词]': data.get('竞赛关键词', '')[1:-1].replace("'", '').replace(',', '、'),
            '[竞赛类型]': data.get('竞赛类型', ''),
            '[竞赛组织者]': data.get('组织者', ''),
            '[起始时间]': data.get('开始时间', '') + ' - ' + data.get('结束时间', ''),
            '[竞赛网址]': data.get('竞赛网站', ''),
            '[竞赛总览]': data.get('竞赛总览', ''),
            '[竞赛描述]': data.get('详细描述', ''),
            '[评估指标]': data.get('评估指标', ''),
            '[时间线]': data.get('时间线', ''),
            '[奖金]': data.get('奖金', ''),
        }
        
        # 替换模板中的关键词
        for key, value in keyword_mapping.items():
            value = value.replace('\n', '')
            template = template.replace(key, value)
        
        return template


    def overview_template_fill(self, comp_name:str):
        print(f"正在处理比赛: {comp_name}")
        safe_comp_name = safe_title_func(comp_name)

        # 构建文件路径
        json_file = f'{self.data_root_path}/{safe_comp_name}/zh_comp_overview.json'
        output_file = f'{self.data_root_path}/{safe_comp_name}/zh_comp_overview.html'
        
        # 加载JSON数据
        data = self.load_json_file(json_file)

        # 若data内竞赛总览存在\n，需要按html p标签处理
        comp_overview = data.get('竞赛总览', '')[0]['content']
        comp_overview_list = comp_overview.split('\n')
        comp_overview_html = ""
        for line in comp_overview_list:
            comp_overview_html += "<p style='white-space: normal;margin: 0px;padding: 0px;box-sizing: border-box;'>"
            comp_overview_html += "<span leaf=''>{}</span>".format(line)
            comp_overview_html += "</p>"
        data['竞赛总览'] = comp_overview_html

        # 若data内详细描述存在\n，需要按html p标签处理
        comp_description_list = data.get('详细描述', '')
        comp_description_html = ""
        for line in comp_description_list:
            if line['type'] == 'table':
                comp_description_html += line['content'].replace('<br>', '')
                
            elif line['type'] == 'p':
                comp_description_html += "<p style='margin: 0px;padding: 0px;box-sizing: border-box;'>"
                comp_description_html += "<span leaf=''>{}</span>".format(line['content'])
                comp_description_html += "</p>"
            
            elif line['type'] == 'image':
                # 改为居中显示
                comp_description_html += "<p style='margin: 0px;padding: 0px;box-sizing: border-box;text-align: center;'>"
                comp_description_html += "<img style='display: block;margin: 0 auto;max-width: 100%;width: 50%;box-sizing: border-box;'src='{}'>".format(line['content'])
                comp_description_html += "</p>"    

            else:
                sub_content = line['content'].split('\n')
                for sub_line in sub_content:
                    comp_description_html += "<p style='margin: 0px;padding: 0px;box-sizing: border-box;'>"
                    comp_description_html += "<span leaf=''>{}</span>".format(sub_line)
                    comp_description_html += "</p>"

            # 添加换行符
            comp_description_html += "<p style='margin: 0px;padding: 0px;box-sizing: border-box;'>"
            comp_description_html += "<span leaf=''><br></span>"
            comp_description_html += "</p>"
        data['详细描述'] = comp_description_html

        # 若data内评估指标存在\n，需要按html p标签处理
        comp_evaluation_list = data.get('评估指标', '')
        comp_evaluation_html = ""
        for line in comp_evaluation_list:
            if line['type'] == 'table':
                comp_evaluation_html += line['content'].replace('<br>', '')   
                 
            elif line['type'] == 'p':
                comp_evaluation_html += "<p style='font-size: 15px;box-sizing: border-box;'>"
                comp_evaluation_html += "<span leaf=''>{}<br></span>".format(line['content'])
                comp_evaluation_html += "</p>"
            
            
            elif line['type'] == 'pre':
                comp_evaluation_html += "<section class='code-snippet__fix code-snippet__js'>"
                comp_evaluation_html += "<pre class='code-snippet__js' data-lang='python'>"
                sub_content = line['content'].split('\n')
                for sub_line in sub_content:
                    comp_evaluation_html += "<code><span leaf=''>{}</span></code>".format(sub_line)
                comp_evaluation_html += "</pre>"
                comp_evaluation_html += "</section>"
            
            elif line['type'] == 'h2':
                # 加粗标题和放大字号
                comp_evaluation_html += "<p style='font-size: 16px;box-sizing: border-box;font-weight: bold;'>"
                comp_evaluation_html += "<span leaf=''>{}</span>".format(line['content'])
                comp_evaluation_html += "</p>"

            else:
                sub_content = line['content'].split('\n')
                for sub_line in sub_content:
                    comp_evaluation_html += "<p style='font-size: 15px;box-sizing: border-box;'>"
                    comp_evaluation_html += "<span leaf=''>{}</span>".format(sub_line)
                    comp_evaluation_html += "</p>"

            # 添加换行符
            comp_evaluation_html += "<p style='font-size: 15px;box-sizing: border-box;'>"
            comp_evaluation_html += "<span leaf=''><br></span>"
            comp_evaluation_html += "</p>"
                
        data['评估指标'] = comp_evaluation_html

        # 若data内时间线存在\n，需要按html p标签处理
        comp_timeline_list = data.get('时间线', '')
        comp_timeline_html = ""
        for line in comp_timeline_list:
            if line['type'] == 'table':
                comp_timeline_html += line['content'].replace('<br>', '')
                
            elif line['type'] == 'p':
                comp_timeline_html += "<p style='font-size: 15px;box-sizing: border-box;'>"
                comp_timeline_html += "<span leaf=''>{}<br></span>".format(line['content'])
                comp_timeline_html += "</p>"

            else:
                sub_content = line['content'].split('\n')
                for sub_line in sub_content:
                    comp_timeline_html += "<p style='font-size: 15px;box-sizing: border-box;'>"
                    comp_timeline_html += "<span leaf=''>{}</span>".format(sub_line)
                    comp_timeline_html += "</p>"

            # 添加换行符
            comp_timeline_html += "<p style='font-size: 15px;box-sizing: border-box;'>"
            comp_timeline_html += "<span leaf=''><br></span>"
            comp_timeline_html += "</p>"
        data['时间线'] = comp_timeline_html

        # 若data内奖金存在\n，需要按html p标签处理
        comp_prize_list = data.get('奖金', '')
        comp_prize_html = ""
        for line in comp_prize_list:
            if line['type'] == 'table':
                comp_prize_html += line['content'].replace('<br>', '')
                
            elif line['type'] == 'p':
                comp_prize_html += "<p style='font-size: 15px;box-sizing: border-box;'>"
                comp_prize_html += "<span leaf=''>{}<br></span>".format(line['content'])
                comp_prize_html += "</p>"
                
            else:
                sub_content = line['content'].split('\n')
                for sub_line in sub_content:
                    comp_prize_html += "<p style='font-size: 15px;box-sizing: border-box;'>"
                    comp_prize_html += "<span leaf=''>{}</span>".format(sub_line)
                    comp_prize_html += "</p>"

            # 添加换行符
            comp_prize_html += "<p style='font-size: 15px;box-sizing: border-box;'>"
            comp_prize_html += "<span leaf=''><br></span>"
            comp_prize_html += "</p>"
        data['奖金'] = comp_prize_html

        # 读取模板文件
        with open(self.template_path, 'r', encoding='utf-8') as f:
            template = f.read()
        
        # 填充模板
        filled_template = self.fill_template(template, data)
        
        # 保存结果
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(filled_template)
        
        print(f"模板已成功填充并保存到: {output_file}")


if __name__ == "__main__":
        # 解析命令行参数
    parser = argparse.ArgumentParser(description="填充竞赛概览HTML模板")
    parser.add_argument(
        "--comp_name", 
        type=str, 
        default="CMI - Detect Behavior with Sensor Data",
        help="比赛名称 (默认: CMI - Detect Behavior with Sensor Data)"
    )

    args = parser.parse_args()
    comp_name = args.comp_name
    
    overview_template_filler = OverviewTemplateFiller()
    overview_template_filler.overview_template_fill(comp_name)
