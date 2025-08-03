# App Agent 宅小A
### Author: HongfengAi

[ProductHunt](https://www.producthunt.com/leaderboard/weekly/2025/26)每周一会更新上周一到上周日的热门软件榜单，所以建议在 这周一-这周日之间，爬取上周软件榜单，进行周级热门软件速递。

爬虫内容包括：
- Weekly维度下的产品列表（包括：producthunt_url、标题、一句话描述、标签、comments数量、upvotes数量）
- 每个产品的详情内容（包括：内容描述、图片、星级评分、粉丝数、产品网站）

## 启动服务
```
# 指定周数
python .\code\app_express\pipeline.py --topk 10 --year 2025 --week 25

# 默认上周
python .\code\app_express\pipeline.py
```