# Kaggle Agent 宅小K
### Author: HongfengAi

# 数据爬取
### 1、爬取竞赛列表
```
python code/crawler/comp_list_crawler.py
```
数据保存至: ``kaggle_competitions_list.csv``。

### 2、爬取指定竞赛的总览
```
python code/crawler/comp_overview_crawler.py
```
数据保存至: ``comp_express/[comp_title]/comp_overview.json``。

### 3、爬取指定竞赛的讨论帖列表
```
python code/crawler/comp_dis_list_crawler.py
```
数据保存至: ``comp_review/[comp_title]/comp_dis_list.json``。

### 4、爬取指定竞赛的指定讨论帖的详情
```
python code/crawler/comp_dis_details_crawler.py
```
数据保存至: ``comp_review/[comp_title]/discussion_details/[dis_title]/discussion_content.md``。


# Agent主流程

## 1. 竞赛速览
```
python .\code\comp_express\pipeline.py
```

## 2. 竞赛复盘
```
python .\code\comp_review\pipeline.py
```

## 3. 其它
（1）MpMath有人优化后能支持将公式一键转换，Chrome插件下载链接：[MpMath](https://github.com/latentcat/mpmath/tree/bce3a5d0d96dc34be597d125b3994766dc0eef48), 配合Console控制台+HidvaMpMathGo()命令，可以一键转换公式。


（2）对微信公众号新建草稿的接口来说，图文消息的具体内容CONTENT，支持HTML标签，必须少于2万字符，小于1M，且此处会去除JS,涉及图片url必须来源 "上传图文消息内的图片获取URL"接口获取。外部图片url将被过滤。 所以我做了优化，就是把图片上传到微信公众号平台的永久素材库内，用平台的素材url即可。


## TODO
- Awesome Kaggle

进度：
- (20250616) 完成爬虫重构
- (20250617) 完成竞赛速递的v2重构
- (20250620) 完成竞赛复盘的v2重构


