#!/usr/bin/env python
# -*- coding: utf-8 -*-


import sys
import json

from .craw_search_engine import StaticCrawler, SpiderBoy
from .utils import load_csv


def crawl_info(line, crawler, wf):
	index = line["index"]
	brand = line["brand"]
	description = line["description"]
	try:
		summary, basic_info = crawler.fetch_info(brand)
		basic_info = json.dumps(basic_info, ensure_ascii=False)
	except Exception as e:
		print('error: {}'.format(str(e)))
		wf.close()
		sys.exit()
	summary = summary if summary else "NO_SUMMARY"
	wf.write('\t'.join([brand, description, summary, basic_info]))
	wf.write('\n')
	if index % 10 == 0:
		print("processed {} items.".format(index))
	time.sleep(0.5)


def run_crawler():
	filename = "./data/brand_base.csv"
	out_file = "./data/out"
	df = load_csv(filename)
	crawler = StaticCrawler()
	with open(out_file, 'w') as wf:
		df.apply(lambda line: crawl_info(line, crawler, wf), axis=1)


def run_spider():
	data_dir = './data'
	query_path = os.path.join(data_dir, 'test')
	spider = SpiderBoy('http://www.baidu.com')
    crawled_items = spider.run_queries(query_path)
	print(crawled_items)


if __name__ == "__main__":
	run()
