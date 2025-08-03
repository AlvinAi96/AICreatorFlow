"""
Function: 将竞赛总结的内容填充到竞赛复盘推文的模板内

CreateDay: 20250612
Author: HongfengAi
History:
20250612    HongfengAi  第一版
"""

import json
import argparse
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from configs import OUTPUT_ROOT_PATH, COMP_REVIEW_ROOT_PATH, COMP_EXPRESS_ROOT_PATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import safe_title_func
from wechat_utils.upload_material import WeChatPermanentMaterialUploader


class SummaryTemplateFiller():
    def __init__(self):
        self.express_data_root_path = COMP_EXPRESS_ROOT_PATH
        self.review_data_root_path = COMP_REVIEW_ROOT_PATH
        self.template_path = "./code/comp_review/wechat_html_template/solution_summary_template.html"
        self.img_uploader = WeChatPermanentMaterialUploader()

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
            '[solution_list]': data.get('solution_list', ''),
        }

        # 替换模板中的关键词
        for key, value in keyword_mapping.items():
            value = value.replace('\n', '')
            template = template.replace(key, value)
        
        return template


    def solution_template_fill(self, comp_name:str):
        safe_comp_name = safe_title_func(comp_name)
        print(f"正在处理比赛: {comp_name}")
        
        # 构建文件路径
        json_file = f'{self.express_data_root_path}/{safe_comp_name}/zh_comp_overview.json'
        summary_file = f'{self.review_data_root_path}/{safe_comp_name}/top_solution_summarys.json'
        output_file = f'{self.review_data_root_path}/{safe_comp_name}/zh_solution_summary.html'
        
        # 加载JSON数据
        data = self.load_json_file(json_file)
        summary_data = self.load_json_file(summary_file)
        
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
                
            elif line['type'] == 'h1' or line['type'] == 'h2':
                # 加粗标题和放大字号
                comp_description_html += "<p style='font-size: 16px;box-sizing: border-box;font-weight: bold;'>"
                comp_description_html += "<span leaf=''>{}</span>".format(line['content'])
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
            
            elif line['type'] == 'h2' or line['type'] == 'h2':
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

        # solution_list
        solution_list = []
        solution_source_list = []
        for i, solution in enumerate(summary_data):
            solution_title = solution.get('title', '')
            solution_rank = solution.get('rank', '')
            solution_url = solution.get('url', '')
            # solution_content = solution.get('discussion_content', '')
            solution_summary = solution.get('summary', {})
            solution_source_list.append([i+1, solution_title, solution_url])

            # 生成solution_html
            solution_no_html = f"""<section
            style="display: flex;flex-flow: row;margin: 10px 0%;text-align: left;justify-content: flex-start;position: static;box-sizing: border-box;">
            <section
                style="display: inline-block;vertical-align: middle;width: auto;flex: 0 0 auto;align-self: center;margin: 0px;min-width: 10%;max-width: 100%;height: auto;padding: 0px;box-sizing: border-box;">
                <section
                    style="--darkreader-inline-color: #ffffff;color: rgb(0, 0, 0);font-size: 18px;text-align: center;box-sizing: border-box;"
                    data-darkreader-inline-color="">
                    <p style="margin: 0px;padding: 0px;box-sizing: border-box;">
                        <b style="box-sizing: border-box;">
                            <span leaf="">{i+1}</span>
                        </b>
                    </p>
                </section>
            </section>
            <section
                style="display: inline-block;vertical-align: middle;width: 16px;flex: 0 0 auto;height: auto;border-width: 0px;border-style: none;border-color: rgb(62, 62, 62);align-self: center;--darkreader-inline-border-top: #948978;--darkreader-inline-border-bottom: #948978;--darkreader-inline-border-left: #948978;--darkreader-inline-border-right: #948978;box-sizing: border-box;"
                data-darkreader-inline-border-top="" data-darkreader-inline-border-right=""
                data-darkreader-inline-border-bottom="" data-darkreader-inline-border-left="">
                <section
                    style="display: flex;flex-flow: row;justify-content: flex-start;position: static;box-sizing: border-box;">
                    <section
                        style="display: inline-block;vertical-align: top;width: auto;flex: 100 100 0%;height: auto;align-self: flex-start;box-sizing: border-box;">
                        <section
                            style="position: static;transform: rotateZ(14deg);-webkit-transform: rotateZ(14deg);-moz-transform: rotateZ(14deg);-o-transform: rotateZ(14deg);box-sizing: border-box;">
                            <section style="text-align: center;position: static;box-sizing: border-box;">
                                <section
                                    style="display: inline-block;width: 3px;height: 26px;vertical-align: top;overflow: hidden;background-color: rgb(0, 0, 0);--darkreader-inline-bgcolor: #000000;box-sizing: border-box;"
                                    data-darkreader-inline-bgcolor="">
                                    <svg viewBox="0 0 1 1" style="float:left;line-height:0;width:0;vertical-align:top;">
                                    </svg>
                                </section>
                            </section>
                        </section>
                    </section>
                    <section
                        style="display: inline-block;vertical-align: top;width: auto;flex: 100 100 0%;height: auto;align-self: flex-start;box-sizing: border-box;">
                        <section
                            style="position: static;transform: rotateZ(14deg);-webkit-transform: rotateZ(14deg);-moz-transform: rotateZ(14deg);-o-transform: rotateZ(14deg);box-sizing: border-box;">
                            <section style="text-align: center;position: static;box-sizing: border-box;">
                                <section
                                    style="display: inline-block;width: 3px;height: 15px;vertical-align: top;overflow: hidden;background-color: rgb(0, 0, 0);--darkreader-inline-bgcolor: #000000;box-sizing: border-box;"
                                    data-darkreader-inline-bgcolor="">
                                    <svg viewBox="0 0 1 1" style="float:left;line-height:0;width:0;vertical-align:top;">
                                    </svg>
                                </section>
                            </section>
                        </section>
                    </section>
                </section>
            </section>
            <section
                style="display: inline-block;vertical-align: middle;width: 100%;align-self: center;box-sizing: border-box;">
                <section style="margin: 0.5em 0px;position: static;box-sizing: border-box;">
                    <section
                        style="background-color: rgb(0, 0, 0);height: 1px;--darkreader-inline-bgcolor: #000000;box-sizing: border-box;"
                        data-darkreader-inline-bgcolor="">
                        <svg viewBox="0 0 1 1" style="float:left;line-height:0;width:0;vertical-align:top;">
                        </svg>
                    </section>
                </section>
            </section>
        </section>"""

            solution_title_html = f"""<section
            style="--darkreader-inline-color: #eee7dd;font-size: 18px;color: rgb(62, 62, 62);padding: 0px 8px;line-height: 1.8;letter-spacing: 0.544px;text-align: left;box-sizing: border-box;width: 100%;">
            <p style="margin: 0px;padding: 0px;box-sizing: border-box;text-align: left;">
                <strong style="box-sizing: border-box;"><span leaf="">{solution_title}</span></strong>
            </p>
        </section>"""

            solution_rank_url_html = f"""    <section
            style="margin: 10px 0% 8px;text-align: left;justify-content: flex-start;display: flex;flex-flow: row;width: 100%;border-left: 3px solid rgb(219, 219, 219);border-bottom-left-radius: 0px;padding: 0px 0px 0px 8px;align-self: flex-start;position: static;box-sizing: border-box;--darkreader-inline-border-left: #474d4f;"
            data-darkreader-inline-border-left="">
            <section
                style="color: rgba(0, 0, 0, 0.5);--darkreader-inline-color: rgba(255, 255, 255, 0.5);width: 100%;box-sizing: border-box;"
                data-darkreader-inline-color="">
                <p style="margin: 0px;padding: 0px;box-sizing: border-box;text-align: left;">
                    <span leaf="">Rank: {solution_rank}</span>
                </p>
                <p style="margin: 0px;padding: 0px;box-sizing: border-box;text-align: left;">
                    <span leaf="">URL: {solution_url}</span>
                </p>
            </section>
        </section>"""
            
            solution_description_html = f"""<p style="white-space: normal;margin: 0px;padding: 0px;box-sizing: border-box;">
            <span leaf=""><br></span>
        </p>
        <section
            style="font-size: 18px;color: rgb(62, 62, 62);padding: 0px 8px;line-height: 1.8;letter-spacing: 0.544px;--darkreader-inline-color: #eee7dd;box-sizing: border-box;width: 100%;"
            data-darkreader-inline-color="">
            <p style="margin: 0px;padding: 0px;box-sizing: border-box;">
                <strong
                    style="letter-spacing: 0.544px;color: rgb(0, 0, 0);--darkreader-inline-color: #ffffff;box-sizing: border-box;"
                    data-darkreader-inline-color=""><span leaf="">1) 方案介绍</span></strong>
            </p>
        </section>
        <section style="letter-spacing: 0.544px;line-height: 1.8;padding: 0px 8px;box-sizing: border-box;width: 100%;">"""
            solution_summary_list = solution_summary.get('solution_description', '').split('\n')
            for line in solution_summary_list:
                solution_description_html += "<p style='text-align: left;margin: 0px;padding: 0px;box-sizing: border-box;width: 100%;'>"
                solution_description_html += "<span style='font-size: 15px;box-sizing: border-box;'><span leaf=''>{}</span></span>".format(line)
                solution_description_html += "</p>"
            solution_description_html += """<p style="text-align: left;margin: 0px;padding: 0px;box-sizing: border-box;">
                <span style="font-size: 15px;box-sizing: border-box;"><br style="box-sizing: border-box;"></span>
            </p>
        </section>"""
            
            solution_core_techniques_html = """<section
            style="font-size: 18px;color: rgb(62, 62, 62);padding: 0px 8px;line-height: 1.8;letter-spacing: 0.544px;--darkreader-inline-color: #eee7dd;box-sizing: border-box;width: 100%;"
            data-darkreader-inline-color="">
            <p style="margin: 0px;padding: 0px;box-sizing: border-box;">
                <strong
                    style="letter-spacing: 0.544px;color: rgb(0, 0, 0);--darkreader-inline-color: #ffffff;box-sizing: border-box;"
                    data-darkreader-inline-color=""><span leaf="">2) 核心技巧</span></strong>
            </p>
        </section>"""
            solution_core_techniques_list = solution_summary.get('core_techniques', [])
            for core_technique in solution_core_techniques_list:
                core_technique_name = core_technique.get('core_technique', '')
                core_technique_description = core_technique.get('core_technique_description', '')
                solution_core_techniques_html += f"""    <section style="letter-spacing: 0.544px;line-height: 1.8;padding: 0px 8px;box-sizing: border-box;width: 100%;">
            <p style="text-align: left;margin: 0px;padding: 0px;box-sizing: border-box;width: 100%;">
                <span style="font-size: 15px;box-sizing: border-box;"><span leaf="">●&nbsp;</span><strong
                        style="box-sizing: border-box;"><span leaf="">{core_technique_name}</span></strong></span>
            </p>
        </section>
        <section style="letter-spacing: 0.544px;line-height: 1.8;padding: 0px 8px;box-sizing: border-box;width: 100%;">
            <p style="text-align: left;margin: 0px;padding: 0px;box-sizing: border-box;width: 100%;">
                <span style="font-size: 15px;box-sizing: border-box;"><span
                        leaf="">{core_technique_description}</span></span>
            </p>
            <p style="text-align: left;margin: 0px;padding: 0px;box-sizing: border-box;">
                <span style="font-size: 15px;box-sizing: border-box;"><br style="box-sizing: border-box;"></span>
            </p>
        </section>"""

            solution_summary_html = """    <section
            style="font-size: 18px;color: rgb(62, 62, 62);padding: 0px 8px;line-height: 1.8;letter-spacing: 0.544px;--darkreader-inline-color: #eee7dd;box-sizing: border-box;width: 100%;"
            data-darkreader-inline-color="">
            <p style="margin: 0px;padding: 0px;box-sizing: border-box;">
                <strong
                    style="letter-spacing: 0.544px;color: rgb(0, 0, 0);--darkreader-inline-color: #ffffff;box-sizing: border-box;"
                    data-darkreader-inline-color=""><span leaf="">3) 方案总结</span></strong>
            </p>
        </section>"""
            solution_summary_list = solution_summary.get('solution_summary', '').split('\n')
            for line in solution_summary_list:
                solution_summary_html += """<section style='letter-spacing: 0.544px;line-height: 1.8;padding: 0px 8px;box-sizing: border-box;width: 100%;'>"""
                solution_summary_html += "<p style='text-align: left;margin: 0px;padding: 0px;box-sizing: border-box;width: 100%;'><span style='font-size: 15px;box-sizing: border-box;'><span leaf=''>{}</span></span></p>".format(line)
            solution_summary_html += """<p style="text-align: left;margin: 0px;padding: 0px;box-sizing: border-box;">
                <span style="font-size: 15px;box-sizing: border-box;"><br style="box-sizing: border-box;"></span>
            </p>
                <p style="text-align: left;margin: 0px;padding: 0px;box-sizing: border-box;">
      <span style="font-size: 15px;box-sizing: border-box;"><span leaf=""><br></span></span>
    </p>
            </section>"""

            # 读取该方案的图片来源
            safe_dis_title = safe_title_func(solution_title)
            img_name2scr_dict_file_path = f'{COMP_REVIEW_ROOT_PATH}/{safe_comp_name}/discussion_details/{safe_dis_title}/img_name2scr_dict.json'
            with open(img_name2scr_dict_file_path, 'r', encoding='utf-8') as f:
                img_name2scr_dict = json.load(f)
            
            if img_name2scr_dict == {}:
                solution_img_html = ""
            else:
                solution_img_html = f"""<section
  style="box-sizing: border-box;font-style: normal;font-weight: 400;text-align: justify;font-size: 16px;color: rgb(62, 62, 62);"
  data-pm-slice="0 0 []">
  <section style="margin: 10px 0px;position: static;box-sizing: border-box;">
    <section style="display: inline-block;width: 100%;vertical-align: top;overflow-x: auto;box-sizing: border-box;">
      <section style="overflow: hidden;width: 500%;max-width: 500% !important;box-sizing: border-box;">"""

                for i, (_, img_scr) in enumerate(img_name2scr_dict.items()):
                    # 将图片上传到微信公众号永久素材号
                    img_upload_result = self.img_uploader.upload_specific_file(img_scr)
                    img_scr = img_upload_result.get('url', '')
                    if img_scr:
                        solution_img_html += f"""<section style="display: inline-block;width: 20%;vertical-align: middle;box-sizing: border-box;">
          <section style="text-align: center;margin: 0px;line-height: 0;position: static;box-sizing: border-box;">
            <section
              style="max-width: 100%;vertical-align: middle;display: inline-block;line-height: 0;width: 100%;box-sizing: border-box;"
              nodeleaf="">
              <img data-ratio="0.66640625" data-s="300,640" data-w="1280"
                style="vertical-align: middle;max-width: 100%;width: 100%;box-sizing: border-box;" data-imgqrcoded="1"
                data-src="{img_scr}"
                src="{img_scr}">
            </section>
          </section>
        </section>"""
                solution_img_html += f"""      </section>
    </section>
  </section>
  <section style="margin: 0px 0px 10px;position: static;box-sizing: border-box;">
    <section style="font-size: 14px;color: rgb(106, 106, 106);box-sizing: border-box;">
      <p style="white-space: normal;margin: 0px;padding: 0px;box-sizing: border-box;text-align: left;">
        <span leaf="">竞赛高分方案《{solution_title}》的图片集（可左右滑动）</span>
      </p>
        <p style="white-space: normal;margin: 0px;padding: 0px;box-sizing: border-box;text-align: left;">
          <span leaf=""><br></span>
        </p>
    </section>
  </section>
</section>
<p style="display: none;">
  <mp-style-type data-value="3">
  </mp-style-type>
</p>"""
        
            solution_html = solution_no_html + solution_title_html + solution_rank_url_html + solution_description_html + solution_img_html + solution_core_techniques_html + solution_summary_html
            solution_list.append(solution_html)

        # solution出处汇总
        solution_source_html = """<section style="position: static;box-sizing: border-box;">
<grammarly-extension style="position: absolute;top: 0px;left: 0px;pointer-events: none;--rem: 16;box-sizing: border-box;">
</grammarly-extension>
<grammarly-extension style="position: absolute;top: 0px;left: 0px;pointer-events: none;--rem: 16;box-sizing: border-box;">
</grammarly-extension>
<section style="line-height: 1.8;letter-spacing: 0.544px;padding: 0px 8px;box-sizing: border-box;">
<p style="margin: 0px;padding: 0px;box-sizing: border-box;">
    <span leaf=""><br></span>
</p>
<p style="margin: 0px;padding: 0px;box-sizing: border-box;">
    <font color="#000000" style="box-sizing: border-box;">
    <span style="font-size: 20px;box-sizing: border-box;"><b style="box-sizing: border-box;">
        <span leaf="">方案出处汇总</span>
        </b></span>
    </font>
</p>
</section>"""
        for val in solution_source_list:
            solution_source_html += f"""
            <section style="line-height: 1.8;letter-spacing: 0.544px;padding: 0px 8px;box-sizing: border-box;">
            <p style="white-space: normal;margin: 0px;padding: 0px;box-sizing: border-box;text-align: left;">
<span leaf="" style="font-size: 15px;color: rgb(100, 100, 100);box-sizing: border-box;">[{val[0]}] {val[1]}: {val[2]}</span>
</p>
</section>"""
        solution_source_html += """</section>
<p style="display: none;">
<mp-style-type data-value="3">
</mp-style-type>
</p>"""
        solution_list.append(solution_source_html)
        data['solution_list'] = ''.join(solution_list)


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

    summary_template_filler = SummaryTemplateFiller()
    summary_template_filler.solution_template_fill(args.comp_name)