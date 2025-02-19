#scrapy crawl wiki_spider1
# WikiSpider1 - Scrapy 爬虫脚本
# 该爬虫从维基百科（中文）抓取指定的文章页面，提取文章内容并将其存储到 MongoDB 中。
# 为了避免存储过长的文章内容，内容会被分割成多个小段，每段不超过500个字符，并且将标题与每段内容一起存储。
# 本爬虫还会将抓取的文本内容转换为简体字存储，确保处理过的文本适用于后续的自然语言处理。
# 爬虫工作流程包括：抓取指定 URL、清理文本内容、分段存储到数据库。

import scrapy
from tech_crawler.items1 import TechCrawlerItem
from pymongo import MongoClient
import re
from opencc import OpenCC


class WikiSpider(scrapy.Spider):
    # 爬虫名称
    name = "wiki_spider1"

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
        self.db = self.client["tech_data1"]
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

    def split_and_store_content(self, title, content):
        """每500字分割一次内容，并存储每一段"""
        content_len = len(content)
        chunks = []
        prev_end = 0

        # 每500字分割一次，保证每次多截取50个字以避免语义冲突
        while prev_end < content_len:
            end = min(prev_end + 500, content_len)
            chunk = content[prev_end:end]
            if prev_end > 0:
                # 保证保留上次截取的最后50个字
                chunk = content[prev_end - 50:end]
            chunks.append(chunk)
            prev_end = end

        # 存储每个片段
        for chunk in chunks:
            item = TechCrawlerItem()
            item["content"] = title + "\n" + self.cc.convert(chunk)  # 标题和内容合并存储
            item["author"] = None
            item["date"] = None

            # 将每一片段存入数据库
            try:
                self.collection.insert_one(dict(item))
                self.log(f"数据已插入: {item['content'][:30]}...")  # 打印部分内容
            except Exception as e:
                self.log(f"数据插入失败: {e}")

    def parse_article(self, response):
        """解析单篇文章并将数据存储到 MongoDB"""
        self.log(f"正在处理页面: {response.url}")

        # 提取页面标题并移除“ - 维基百科，自由的百科全书”后缀
        title = response.css('title::text').get()
        if title:
            title = title.replace(' - 维基百科，自由的百科全书', '')  # 去掉Wikipedia后缀

        # 使用自定义的内容提取方法提取文章内容
        content = self.extract_content(response)

        # 确保内容有效
        if content:
            # 将标题与内容合并存储在 "content" 字段中
            self.split_and_store_content(title, content)  # 分割并存储内容
        else:
            self.log(f"无法提取正文内容: {response.url}")

    def closed(self, reason):
        """爬虫关闭时关闭 MongoDB 连接"""
        self.client.close()


