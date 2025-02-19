#使用爬虫的代码是scrapy crawl wiki_spider 在使用爬虫前记得将终端的路径更改为文件tech_crawler文件的目录，
# 即和src同级党的目录，使用cd 路径即可
# WikiSpider - Scrapy 爬虫脚本
# 该爬虫从维基百科（中文）抓取指定的文章页面，提取文章内容并将其存储到 MongoDB 中。
# 其中，文章内容经过清理，移除无用的引用、特殊字符等，还会将繁体字转换为简体字存储。
# 本脚本使用 Scrapy 框架，MongoDB 数据库用于存储抓取到的文章数据。

import scrapy
from tech_crawler.items import TechCrawlerItem
from pymongo import MongoClient
import re
from opencc import OpenCC


class WikiSpider(scrapy.Spider):
    # 爬虫名称
    name = "wiki_spider"

    # 允许爬取的域名
    allowed_domains = ["zh.wikipedia.org"]

    # 自定义需要抓取的 URL 列表
    custom_urls = [
        "https://zh.wikipedia.org/wiki/%E7%A7%91%E5%AD%A6",
        "https://zh.wikipedia.org/wiki/%E6%9C%BA%E5%99%A8%E5%AD%A6%E4%B9%A0",
        "https://zh.wikipedia.org/wiki/%E6%B7%B1%E5%BA%A6%E5%AD%A6%E4%B9%A0",
        "https://zh.wikipedia.org/wiki/%E8%AE%A1%E7%AE%97%E6%9C%BA%E7%A7%91%E5%AD%A6",
        "https://zh.wikipedia.org/wiki/%E6%87%89%E7%94%A8%E7%A7%91%E5%AD%B8",
        "https://zh.wikipedia.org/wiki/%E8%87%AA%E7%84%B6%E7%A7%91%E5%AD%A6",
        "https://zh.wikipedia.org/wiki/%E7%A4%BE%E4%BC%9A%E7%A7%91%E5%AD%A6",
        "https://zh.wikipedia.org/wiki/%E4%BA%BA%E5%B7%A5%E6%99%BA%E8%83%BD",
        "https://zh.wikipedia.org/wiki/6G",
        "https://zh.wikipedia.org/wiki/5G",
        "https://zh.wikipedia.org/wiki/%E7%89%A9%E8%81%94%E7%BD%91",
        "https://zh.wikipedia.org/wiki/%E8%97%8D%E7%89%99",
        "https://zh.wikipedia.org/wiki/Wi-Fi",
    ]
    # 可以修改为需要爬取的其他维基百科 URL

    def __init__(self, *args, **kwargs):
        """初始化 MongoDB 连接及 OpenCC（用于繁体转简体）"""
        super(WikiSpider, self).__init__(*args, **kwargs)
        # 连接 MongoDB
        self.client = MongoClient("mongodb://localhost:27017")
        self.db = self.client["tech_data"]
        self.collection = self.db["articles"]
        # 初始化 OpenCC，用于繁体字转换为简体字
        self.cc = OpenCC('t2s')

    def start_requests(self):
        """开始请求，发送自定义的 URL 列表进行抓取"""
        for url in self.custom_urls:
            yield scrapy.Request(url, callback=self.parse_article)

    def clean_text(self, text):
        """清理文本，移除特殊字符（如引用标记）、多余空格和换行"""
        if text:
            # 移除引用标记 [1], [2] 等
            text = re.sub(r'\[\d+\]', '', text)
            # 移除多余空格和换行
            text = ' '.join(text.split())
            return text.strip()
        return ''  # 若文本为空，返回空字符串

    def extract_content(self, response):
        """提取文章的主体内容"""
        content_parts = []  # 存储清理后的文本部分

        # 获取页面中的主要内容区域
        main_content = response.css('div.mw-parser-output')

        # 遍历所有子元素进行内容提取
        for element in main_content.xpath('./*'):
            # 跳过目录、参考文献等无关部分
            if element.xpath('@class').get() in ['toc', 'reflist']:
                continue

            # 处理普通段落（<p>标签）
            if element.root.tag == 'p':
                # 提取段落的文本内容
                text = ''.join(element.xpath('.//text()').getall())
                cleaned_text = self.clean_text(text)
                if cleaned_text:
                    content_parts.append(cleaned_text)

            # 处理标题（<h2>, <h3>, <h4>标签）
            elif element.root.tag in ['h2', 'h3', 'h4']:
                header_text = ''.join(element.xpath('.//text()').getall())
                if '[edit]' in header_text:  # 移除维基百科特有的[edit]标记
                    header_text = header_text.replace('[edit]', '')
                cleaned_header = self.clean_text(header_text)
                if cleaned_header:
                    content_parts.append(f"\n{cleaned_header}\n")

            # 处理列表（<ul>, <ol>标签）
            elif element.root.tag in ['ul', 'ol']:
                for li in element.xpath('.//li'):
                    list_text = ''.join(li.xpath('.//text()').getall())
                    cleaned_list_text = self.clean_text(list_text)
                    if cleaned_list_text:
                        content_parts.append(f"- {cleaned_list_text}")

        # 返回拼接后的所有内容部分
        return '\n'.join(content_parts)

    def parse_article(self, response):
        """解析单篇文章并将数据存储到 MongoDB 中"""
        self.log(f"正在处理页面: {response.url}")

        # 创建 TechCrawlerItem 实例
        item = TechCrawlerItem()

        # 提取页面标题并移除“ - Wikipedia”后缀
        title = response.css('title::text').get()
        if title:
            title = title.replace(' - Wikipedia', '')
        item["title"] = title

        item["url"] = response.url

        # 使用自定义的内容提取方法提取文章内容
        content = self.extract_content(response)
        # 将内容从繁体字转换为简体字
        item["content"] = self.cc.convert(content)
        item["author"] = None
        item["date"] = None

        # 如果内容有效，则将数据存储到 MongoDB
        if item["content"]:
            try:
                # 检查 MongoDB 中是否已有相同 URL 的文档
                existing_doc = self.collection.find_one({"url": item["url"]})
                if existing_doc:
                    # 更新已有文档
                    self.collection.update_one(
                        {"url": item["url"]},
                        {"$set": dict(item)}
                    )
                    self.log(f"数据已更新: {item['title']}")
                else:
                    # 插入新文档
                    self.collection.insert_one(dict(item))
                    self.log(f"数据已插入: {item['title']}")
            except Exception as e:
                self.log(f"数据操作失败: {e}")
        else:
            self.log(f"无法提取正文内容: {response.url}")

    def closed(self, reason):
        """爬虫关闭时关闭 MongoDB 连接"""
        self.client.close()
