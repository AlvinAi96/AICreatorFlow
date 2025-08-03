# Paper Agent 宅小P
### Author: HongfengAi

[Huggingface](https://huggingface.co/papers/week)每周日会更新 上周日-这周六 之间的热门论文榜单。所以建议在 这周日-下周六 之间爬取上周论文榜单，进行周级热门论文速递。

爬虫内容包括：
- Weekly维度下的论文列表（包括：点赞数、论文封面、论文标题、论文作者数量，github点赞数、论文hf_url）;
- 每篇论文的详情内容（包括：论文发表时间、作者列表、AI生成总结、摘要、view pdf的链接、github地址）


爬虫完后，需要做的事情：
- 选择top k热门论文
- 根据点赞数进行归一化，形成本周热度，提供火苗 1-5个；
- 作者列表只提供top k个作者，过多则省略加显示论文作者数量；
- LLM翻译 AI生成总结 和 摘要总结；
- 准备html文章模板，并填充；
- 准备封面图片模板，并填充；
- 上传素材；
- 创建草稿。

## 环境依赖
使用了``https://github.com/ai8hyf/TF-ID``用于提取论文pdf中的图表。
```
pip install pdf2image transformers==4.51.3 pymupdf fitz torch einops timm
```
pdf2image需要poppler，请根据教程下载并配置[教程](https://blog.csdn.net/qq_38486203/article/details/143983252)。

## 启动服务
```
# 指定周数
python .\code\paper_express\pipeline.py --topk 10 --year 2025 --week W25

# 默认上周
python .\code\paper_express\pipeline.py
```