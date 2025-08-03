"""
Function: 将软件速递的内容填充到软件速递推文的模板内

CreateDay: 20250702
Author: HongfengAi
History:
20250702    HongfengAi  第一版
"""

import json
import argparse
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from configs import SOFTWARE_EXPRESS_ROOT_PATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import safe_title_func, get_previous_week
from wechat_utils.upload_material import WeChatPermanentMaterialUploader


class AppTemplateFiller():
    def __init__(self):
        self.express_data_root_path = SOFTWARE_EXPRESS_ROOT_PATH
        self.template_path = "./code/app_express/wechat_html_template/app_express_template.html"
        self.img_uploader = WeChatPermanentMaterialUploader()

    def load_json_file(self, file_path):
        """加载JSON文件"""
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
        

    def app_template_fill(self, year:int, week:int):

        # 构建文件路径
        json_file = f'{self.express_data_root_path}/{year}_{week}/zh_all_software_details.json'
        output_file = f'{self.express_data_root_path}/{year}_{week}/zh_all_software_express.html'
        
        cover_image_file_path = f'{self.express_data_root_path}/{year}_{week}/cover/cover.json'
        with open(cover_image_file_path, 'r', encoding='utf-8') as f:
            cover_image_data = json.load(f)
        cover_image_url = cover_image_data.get('url', '')

        # 加载JSON数据
        data_list = self.load_json_file(json_file)

        app_html_list = []
        for i, data in enumerate(data_list):
            # 预处理下相关元素
           title_html = f"""  <section
    style="display: flex;flex-flow: row;text-align: left;justify-content: flex-start;position: static;box-sizing: border-box;">
    <section
      style="display: inline-block;vertical-align: middle;width: 60px;flex: 0 0 auto;align-self: center;height: auto;margin: 0px 0px 0px 20px;box-sizing: border-box;">
      <section
        style="text-align: center;margin-top: 10px;margin-bottom: 10px;line-height: 0;position: static;box-sizing: border-box;">
        <section
          style="max-width: 100%;vertical-align: middle;display: inline-block;line-height: 0;border-width: 0px;border-radius: 50%;border-style: none;border-color: rgb(62, 62, 62);overflow: hidden;box-sizing: border-box;"
          nodeleaf="">
          <img data-ratio="1" data-s="300,640" data-type="jpeg" data-w="815"
            style="vertical-align: middle;max-width: 100%;width: 100%;box-sizing: border-box;"
            data-imgfileid="100007468"
            data-src="{data.get('app_icon_upload_url', '')}"
            src="{data.get('app_icon_upload_url', '')}">
        </section>
      </section>
    </section>
    <section
      style="display: inline-block;vertical-align: middle;width: auto;flex: 100 100 0%;height: auto;align-self: center;border-left: 1px solid rgba(84, 103, 239, 0.57);border-bottom-left-radius: 0px;margin: 0px 0px 0px 10px;box-sizing: border-box;">
      <section
        style="text-align: justify;justify-content: flex-start;display: flex;flex-flow: row;position: static;box-sizing: border-box;">
        <section
          style="display: inline-block;vertical-align: bottom;width: auto;min-width: 10%;max-width: 100%;flex: 0 0 auto;height: auto;align-self: flex-end;box-sizing: border-box;">
          <section
            style="color: rgb(84, 103, 239);font-size: 21px;line-height: 1;letter-spacing: 0px;padding: 0px 10px;text-align: left;box-sizing: border-box;">
            <p style="margin: 0px;padding: 0px;box-sizing: border-box;">
              <strong style="box-sizing: border-box;"><span leaf="">TOP{i+1}: {data.get('title', '')}</span></strong>
            </p>
          </section>
        </section>
        <section
          style="display: inline-block;vertical-align: bottom;width: auto;min-width: 10%;max-width: 100%;flex: 0 0 auto;height: auto;line-height: 0;padding: 0px;align-self: flex-end;box-sizing: border-box;">
          <p style="white-space: normal;margin: 0px;padding: 0px;box-sizing: border-box;">
            <span leaf=""><br></span>
          </p>
        </section>
      </section>
    </section>
  </section>"""
           
           keywords_html = f"""<section
    style="margin: 10px 0% 8px;text-align: left;justify-content: flex-start;display: flex;flex-flow: row;position: static;box-sizing: border-box;">
    <section
      style="display: inline-block;width: 100%;border-left: 3px solid rgba(84, 103, 239, 0.57);border-bottom-left-radius: 0px;padding: 0px 0px 0px 8px;vertical-align: top;align-self: flex-start;flex: 0 0 auto;margin: 0px 0px 0px 10px;box-sizing: border-box;">
      <section style="color: rgba(0, 0, 0, 0.5);font-size: 15px;box-sizing: border-box;">
        <p style="margin: 0px;padding: 0px;box-sizing: border-box;">
          <span style="color: rgba(84, 103, 239, 0.57);box-sizing: border-box;"><strong
              style="box-sizing: border-box;"><span leaf="">评分：</span></strong></span>
          <strong style="box-sizing: border-box;"><span style="color: rgb(84, 103, 239);box-sizing: border-box;"><span
                leaf="">{data.get('rating', '')} &nbsp;</span><span style="color: rgba(84, 103, 239, 0.57);box-sizing: border-box;"><span
                  leaf="">粉丝数：</span></span><span leaf="">{data.get('fans', '')}</span></span></strong>
        </p>
        <p style="margin: 0px;padding: 0px;box-sizing: border-box;">
          <strong style="color: rgba(84, 103, 239, 0.57);box-sizing: border-box;"><span leaf="">评论数：</span><span
              style="color: rgb(84, 103, 239);box-sizing: border-box;"><span leaf="">{data.get('comments', '')}</span></span><span
              leaf="">&nbsp; 点赞数：</span><span style="color: rgb(84, 103, 239);box-sizing: border-box;"><span
                leaf="">{data.get('upvotes', '')}&nbsp;</span></span></strong>
        </p>
        <p style="margin: 0px;padding: 0px;box-sizing: border-box;">
          <strong style="color: rgba(84, 103, 239, 0.57);box-sizing: border-box;"><span leaf="">关键词：</span></strong>
          <strong style="color: rgba(84, 103, 239, 0.57);box-sizing: border-box;"><span
              style="color: rgb(84, 103, 239);box-sizing: border-box;"><span leaf="">{', '.join(data.get('zh_tags', ''))}</span></span></strong>
        </p>
        <p style="margin: 0px;padding: 0px;box-sizing: border-box;">
          <strong style="color: rgba(84, 103, 239, 0.57);box-sizing: border-box;"><span leaf="">产品链接：</span></strong>
          <strong style="color: rgba(84, 103, 239, 0.57);box-sizing: border-box;"><span
              style="color: rgb(84, 103, 239);box-sizing: border-box;"><span leaf="">{data.get('product_website', '')}</span></span></strong>
        </p>
      </section>
    </section>
  </section>"""
           
           sentence_description_html = f"""  <p style="white-space: normal;margin: 0px;padding: 0px;box-sizing: border-box;">
    <span leaf=""><br></span>
  </p>
  <section style="letter-spacing: 0.544px;line-height: 1.8;padding: 0px 8px;text-align: left;box-sizing: border-box;">
    <p style="margin: 0px;padding: 0px;box-sizing: border-box;">
      <strong style="letter-spacing: 0.544px;box-sizing: border-box;"><span
          style="color: rgb(51, 51, 51);font-size: 15px;box-sizing: border-box;"><span
            leaf="">一句话描述：</span></span></strong>
      <span style="letter-spacing: 0.544px;color: rgb(51, 51, 51);font-size: 15px;box-sizing: border-box;"><span
          leaf="">{data.get('zh_sentence_description', '')}</span></span>
    </p>
    <p style="margin: 0px;padding: 0px;box-sizing: border-box;">
      <span leaf=""><br></span>
    </p>
  </section>"""
           if data.get('images_upload_url', []) == []:
               solution_img_html = ""
           else:
              #  img_num = len(data.get('images_upload_url', [])) 
               solution_img_html = f"""<section
    style="box-sizing: border-box;font-style: normal;font-weight: 400;text-align: justify;font-size: 16px;color: rgb(62, 62, 62);"
    data-pm-slice="0 0 []">
    <section style="margin: 10px 0px;position: static;box-sizing: border-box;">
    <section style="display: inline-block;width: 100%;vertical-align: top;overflow-x: auto;box-sizing: border-box;">
        <section style="overflow: hidden;width: 500%;max-width: 500% !important;box-sizing: border-box;">"""

           for i, img_scr in enumerate(data.get('images_upload_url', [])[:5]):
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
        <span leaf="">产品介绍图片集（可左右滑动）</span>
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

          
    #        description_text = data.get('zh_content_description', '') + '\n' + data.get('zh_summary', '')
    #        description_text = description_text.replace('\n', '<br>')
    #        description_html = f"""    <section style="letter-spacing: 0.544px;line-height: 1.8;padding: 0px 8px;text-align: left;box-sizing: border-box;">
    #   <p style="margin: 0px;padding: 0px;box-sizing: border-box;">
    #     <strong style="letter-spacing: 0.544px;box-sizing: border-box;"><span
    #         style="color: rgb(51, 51, 51);font-size: 15px;box-sizing: border-box;"><span
    #           leaf="">简介：</span></span></strong>
    #     <span style="letter-spacing: 0.544px;color: rgb(51, 51, 51);font-size: 15px;box-sizing: border-box;"><span
    #         leaf="">{description_text}</span></span>
    #   </p>
    #   <p style="white-space: normal;margin: 0px;padding: 0px;box-sizing: border-box;">
    #     <span leaf=""><br></span>
    # </p>
    # </section>"""
           
           # 获取描述文本并合并
           description_text = data.get('zh_content_description', '') + '\n' + data.get('zh_summary', '')

           # 按换行符分割文本为段落列表
           paragraphs = [p.strip() for p in description_text.split('\n') if p.strip()]

            # 构建HTML内容
           if paragraphs:
                # 开始构建section
                description_html = '    <section style="letter-spacing: 0.544px;line-height: 1.8;padding: 0px 8px;text-align: left;box-sizing: border-box;">\n'
                description_html += '      <p style="margin: 0px;padding: 0px 0px 10px;box-sizing: border-box;">\n'
                description_html += '        <strong style="letter-spacing: 0.544px;box-sizing: border-box;"><span style="color: rgb(51, 51, 51);font-size: 15px;box-sizing: border-box;">简介：</span></strong>\n'
                
                # 添加各个段落，每个段落用单独的span并添加换行
                for i, para in enumerate(paragraphs):
                    description_html += f'        <span style="letter-spacing: 0.544px;color: rgb(51, 51, 51);font-size: 15px;box-sizing: border-box;">{para}</span>\n'
                    # 不是最后一段则添加换行
                    if i != len(paragraphs) - 1:
                        description_html += '        <br/><br/>\n'
                
                description_html += '        <br/>\n'  # 结尾再加一个换行
                description_html += '      </p>\n'
                description_html += '    </section>'
           else:
                # 如果没有内容，生成空的section
                description_html = '    <section style="letter-spacing: 0.544px;line-height: 1.8;padding: 0px 8px;text-align: left;box-sizing: border-box;">\n'
                description_html += '      <p style="margin: 0px;padding: 0px;box-sizing: border-box;">\n'
                description_html += '        <strong style="letter-spacing: 0.544px;box-sizing: border-box;"><span style="color: rgb(51, 51, 51);font-size: 15px;box-sizing: border-box;">简介：</span></strong>\n'
                description_html += '        <span style="letter-spacing: 0.544px;color: rgb(51, 51, 51);font-size: 15px;box-sizing: border-box;">无内容</span>\n'
                description_html += '      </p>\n'
                description_html += '    </section>'


           app_html = title_html + keywords_html + sentence_description_html + solution_img_html + description_html
           app_html_list.append(app_html)

        # 读取模板文件
        with open(self.template_path, 'r', encoding='utf-8') as f:
            template = f.read()

        filled_template = template.replace('[app_html_list]', ''.join(app_html_list))
        filled_template = filled_template.replace('[cover_image_url]', cover_image_url)
        
        # 保存结果
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(filled_template)
        
        print(f"模板已成功填充并保存到: {output_file}")



if __name__ == "__main__":
    year, week = get_previous_week()
    app_template_filler = AppTemplateFiller()
    app_template_filler.app_template_fill(year, week)