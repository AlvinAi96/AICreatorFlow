"""
Function: 将论文速递的内容填充到论文速递推文的模板内

CreateDay: 20250626
Author: HongfengAi
History:
20250626    HongfengAi  第一版
"""

import json
import argparse
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from configs import PAPER_EXPRESS_ROOT_PATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import safe_title_func, get_previous_week


class PaperTemplateFiller():
    def __init__(self):
        self.express_data_root_path = PAPER_EXPRESS_ROOT_PATH
        self.template_path = "./code/paper_express/wechat_html_template/paper_express_template.html"

    def load_json_file(self, file_path):
        """加载JSON文件"""
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
        

    def paper_template_fill(self, year:int, week:str):

        # 构建文件路径
        json_file = f'{self.express_data_root_path}/{year}_{week}/zh_all_papers_details.json'
        output_file = f'{self.express_data_root_path}/{year}_{week}/zh_all_papers_express.html'
        
        cover_image_file_path = f'{self.express_data_root_path}/{year}_{week}/cover/cover.json'
        with open(cover_image_file_path, 'r', encoding='utf-8') as f:
            cover_image_data = json.load(f)
        cover_image_url = cover_image_data.get('url', '')

        # 加载JSON数据
        data_list = self.load_json_file(json_file)


        paper_html_list = []
        for data in data_list:
            # 预处理下相关元素
            data['keywords'] = eval(data['keywords'])
            data['keywords'] = ', '.join(data['keywords'])
            data['authors'] = ', '.join(data['authors'])

            # 准备标题html
            title_html = f"""    <section style="position: static;box-sizing: border-box;">
        <grammarly-extension
            style="position: absolute;top: 0px;left: 0px;pointer-events: none;--rem: 16;box-sizing: border-box;">
        </grammarly-extension>
        <grammarly-extension
            style="position: absolute;top: 0px;left: 0px;pointer-events: none;--rem: 16;box-sizing: border-box;">
        </grammarly-extension>
        <section style="line-height: 1.8;letter-spacing: 0.544px;padding: 0px 8px;text-align: left;box-sizing: border-box;">
            <p style="margin: 0px;padding: 0px;box-sizing: border-box;">
                <span leaf=""><br></span>
            </p>
            <p style="margin: 0px;padding: 0px;text-align: left;box-sizing: border-box;">
                <span style="font-size: 19px;color: rgb(0, 0, 0);box-sizing: border-box;"><strong
                        style="box-sizing: border-box;"><span leaf="">{data.get('index', '')}. {data.get('title', '')}</span></strong></span>
            </p>
        </section>
    </section>
    <p style="white-space: normal;margin: 0px;padding: 0px;box-sizing: border-box;">
        <span leaf=""><br></span>
    </p>"""
            # 准备封面图片
            cover_html = f"""<section
        style="text-align: center;margin-top: 10px;margin-bottom: 10px;line-height: 0;position: static;box-sizing: border-box;">
        <section
            style="max-width: 100%;vertical-align: middle;display: inline-block;line-height: 0;box-sizing: border-box;"
            nodeleaf="">
            <img data-s="300,640" data-type="png"
                style="vertical-align: middle;max-width: 100%;width: 100%;box-sizing: border-box;"
                data-imgfileid="100007161" data-imgqrcoded="1" data-src="{data.get('cover_upload_url', '')}" src="{data.get('cover_upload_url', '')}">
        </section>
    </section>
    <p style="white-space: normal;margin: 0px;padding: 0px;box-sizing: border-box;">
        <span leaf=""><br></span>
    </p>"""
            
            # 准备paper概览信息
            paper_overview_html = f"""    <section
        style="display: inline-block;width: 100%;border-style: solid;border-width: 0px 0px 0px 3px;padding: 10px;border-left-color: rgb(178, 178, 178);border-right-color: rgb(178, 178, 178);position: static;box-sizing: border-box;">
        <section
            style="font-size: 14px;text-align: left;line-height: 1.8;letter-spacing: 0.544px;width: 100%;box-sizing: border-box;">
            <p style="margin: 0px;padding: 0px;box-sizing: border-box;">
                <strong style="box-sizing: border-box;"><span leaf="">论文发表时间：</span></strong>
                <span leaf="">{data.get('zh_published_date', '')}</span>
            </p>
            <p style="margin: 0px;padding: 0px;box-sizing: border-box;">
                <strong style="box-sizing: border-box;"><span leaf="">论文关键词:&nbsp;</span></strong>
                <span leaf="">{data.get('keywords', '')}</span>
            </p>
            <p style="margin: 0px;padding: 0px;box-sizing: border-box;">
                <strong style="box-sizing: border-box;"><span leaf="">作者：</span></strong>
                <span leaf="">{data.get('authors', '')}</span>
            </p>
            <p style="margin: 0px;padding: 0px;box-sizing: border-box;">
                <strong style="box-sizing: border-box;"><span leaf="">HuggingFace热度:</span></strong>
                <span leaf="">&nbsp;{data.get('likes', '')}</span>
            </p>
            <p style="margin: 0px;padding: 0px;box-sizing: border-box;">
                <strong style="box-sizing: border-box;"><span leaf="">PDF地址:&nbsp;</span></strong>
                <span leaf="">{data.get('pdf_url', '')}</span>
            </p>
            <p style="margin: 0px;padding: 0px;box-sizing: border-box;">
                <strong style="box-sizing: border-box;"><span leaf="">Github地址:&nbsp;</span></strong>
                <span leaf="">{data.get('github_url', '')}</span>
            </p>
        </section>
    </section>
    <p style="white-space: normal;margin: 0px;padding: 0px;box-sizing: border-box;">
        <span leaf=""><br></span>
    </p>
    <section
        style="text-align: right;margin: 10px 0% 0px;justify-content: flex-end;display: flex;flex-flow: row;position: static;box-sizing: border-box;">
        <section
            style="display: inline-block;vertical-align: middle;width: 10%;align-self: center;flex: 0 0 auto;box-sizing: border-box;">
            <section style="text-align: left;margin: 0px 0%;line-height: 0;position: static;box-sizing: border-box;">
                <section
                    style="max-width: 100%;vertical-align: middle;display: inline-block;line-height: 0;width: 80%;border-width: 0px;box-sizing: border-box;"
                    nodeleaf="">
                    <img class="rich_pages wxw-img" data-ratio="0.7731959" data-s="300,640" data-type="svg" data-w="194"
                        style="vertical-align: middle;max-width: 100%;width: 100%;height: 100%;box-sizing: border-box;"
                        data-imgfileid="100007160"
                        data-src="https://mmbiz.qlogo.cn/mmbiz_svg/jRoggJ2RF3D6LCmTKZsbfcjHyYia2dbnr0WPSjClib3vQuq6ic6Qjh6icn7pfpoYwE4OeOjuzmkJe41wojCMLclkMZ8JvOyCynEQ/0?wx_fmt=svg&amp;from=appmsg"
                        src="https://mmbiz.qlogo.cn/mmbiz_svg/jRoggJ2RF3D6LCmTKZsbfcjHyYia2dbnr0WPSjClib3vQuq6ic6Qjh6icn7pfpoYwE4OeOjuzmkJe41wojCMLclkMZ8JvOyCynEQ/0?wx_fmt=svg&amp;from=appmsg">
                </section>
            </section>
        </section>
        <section
            style="display: inline-block;vertical-align: middle;width: 50%;border-bottom: 2px dashed rgb(182, 182, 182);border-bottom-right-radius: 0px;align-self: center;flex: 0 0 auto;box-sizing: border-box;">
            <section style="margin: 0px 0%;position: static;box-sizing: border-box;">
                <section style="border-top: 1px dashed rgba(0, 0, 0, 0);box-sizing: border-box;">
                    <svg viewBox="0 0 1 1" style="float:left;line-height:0;width:0;vertical-align:top;">
                    </svg>
                </section>
            </section>
        </section>
    </section>"""

            # 准备paper table和figures
            if data.get('paper_img_urls', []) == []:
                        paper_img_html = ""
            else:
                paper_img_html = f"""<section
        style="box-sizing: border-box;font-style: normal;font-weight: 400;text-align: justify;font-size: 16px;color: rgb(62, 62, 62);"
        data-pm-slice="0 0 []">
        <section style="margin: 10px 0px;position: static;box-sizing: border-box;">
        <section style="display: inline-block;width: 100%;vertical-align: top;overflow-x: auto;box-sizing: border-box;">
            <section style="overflow: hidden;width: 500%;max-width: 500% !important;box-sizing: border-box;">"""

            for i, img_scr in enumerate(data.get('paper_img_urls', [])[:5]):
                    if img_scr:
                        paper_img_html += f"""<section style="display: inline-block;width: 20%;vertical-align: middle;box-sizing: border-box;">
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
            paper_img_html += f"""      </section>
                </section>
            </section>
            <section style="margin: 0px 0px 10px;position: static;box-sizing: border-box;">
                <section style="font-size: 14px;color: rgb(106, 106, 106);box-sizing: border-box;">
                <p style="white-space: normal;margin: 0px;padding: 0px;box-sizing: border-box;text-align: left;">
                    <span leaf="">论文图表集（可左右滑动）</span>
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

            # 准备paper AI summary和摘要
            paper_abstract_html = f"""    <section style="margin: 10px 0%;position: static;box-sizing: border-box;">
        <section
            style="color: rgb(29, 29, 29);line-height: 1.8;letter-spacing: 0.544px;padding: 0px 8px;font-size: 15px;box-sizing: border-box;">
            <p style="white-space: normal;margin: 0px;padding: 0px;box-sizing: border-box;">
                <span style="color: rgba(51, 51, 51, 0.8);box-sizing: border-box;"><span
                        leaf="">{data.get('zh_ai_summary', '')}&nbsp;</span></span>
            </p>
            <p style="text-align: right;white-space: normal;margin: 0px;padding: 0px;box-sizing: border-box;">
                <span style="color: rgb(182, 182, 182);box-sizing: border-box;"><span leaf="">HF AI Summary</span></span>
            </p>
        </section>
    </section>
    <p style="white-space: normal;margin: 0px;padding: 0px;box-sizing: border-box;">
        <span leaf=""><br></span>
    </p>
    <section style="letter-spacing: 0.544px;line-height: 1.8;padding: 0px 8px;box-sizing: border-box;">
        <p style="margin: 0px;padding: 0px;box-sizing: border-box;">
            <span style="font-size: 15px;color: rgb(51, 51, 51);letter-spacing: 0.544px;box-sizing: border-box;"><span
                    leaf="">{data.get('zh_abstract', '')}</span></span>
        </p>
    </section>"""

            paper_html = title_html + cover_html + paper_overview_html + paper_img_html + paper_abstract_html
            paper_html_list.append(paper_html)

        # 读取模板文件
        with open(self.template_path, 'r', encoding='utf-8') as f:
            template = f.read()

        filled_template = template.replace('[paper_html_list]', ''.join(paper_html_list))
        filled_template = filled_template.replace('[cover_image_url]', cover_image_url)
        
        # 保存结果
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(filled_template)
        
        print(f"模板已成功填充并保存到: {output_file}")



if __name__ == "__main__":
    year, week = get_previous_week()
    week = 'W29'
    paper_template_filler = PaperTemplateFiller()
    paper_template_filler.paper_template_fill(year, week)