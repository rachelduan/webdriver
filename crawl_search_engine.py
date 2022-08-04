#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import random
import time
import urllib
import logging

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import requests
import pandas as pd
from bs4 import BeautifulSoup as bs
import bs4

from utils import load_text

logging.getLogger().setLevel(logging.INFO)


def load_queries(query_path, dedup=True, shuffle=False):
    queries = load_text(query_path, dedup, shuffle)
    return queries


class SpiderBoy(object):
    def __init__(self, start_url):
        op = webdriver.ChromeOptions()
        op.add_argument('--headless')
        self.driver = webdriver.Chrome(options=op)
        self.start_url = start_url
        self.driver.get(start_url)
    
    def reinit_homepage(self):
        self.driver.get(self.start_url)
    
    def search(self, query):
        # self.driver.find_element_by_id("kw").send_keys(query)
        # self.driver.find_element_by_id("su").click()
        input_element = self.driver.find_element(by=By.ID, value="kw")
        input_element.send_keys(query)
        input_element.submit()

    def next_page(self, ec_element):
        self.driver.find_element(by=By.XPATH, value="//a[@class='n']").click()
        WebDriverWait(self.driver, 10).until(EC.staleness_of(ec_element))

    def get_text_by_tag(self, element, tag):
        elem = element.find_elements(by=By.TAG_NAME, value=tag)
        if not len(elem):
            return None
        return elem[0].text
    
    def get_text_by_classname(self, element, classname):
        elem = element.find_elements(by=By.CLASS_NAME, value=classname)
        if not len(elem):
            return None
        return elem[0].text

    def find_name_by_xpath(self, xpath, classname):
        try:
            _ = WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.CLASS_NAME, classname))
            )
        except Exception as e:
            print('error when finding element by name: {}'.format(str(e)))
        elements = self.driver.find_elements_by_xpath(xpath)
        return elements
    
    def find_name_by_classname(self, classname):
        try:
            _ = WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.CLASS_NAME, classname))
            )
        except Exception as e:
            print('error when finding element by name: {}'.format(str(e)))
        elements = self.driver.find_elements(by=By.CLASS_NAME, value=classname)
        return elements
    
    def run_one_query(self, query, pages=1):
        self.reinit_homepage()
        logging.info('running on query: {}'.format(query))
        self.search(query)
        headlines, contents = [], []
        page = 1
        while True:
            logging.info('\trunning on page {}'.format(page))
            elements = self.find_name_by_classname("c-container")
            for element in elements:
                headlines.append(self.get_text_by_tag(element, "a"))
                contents.append(self.get_text_by_classname(element, "content-right_8Zs40"))
            
            if page >= pages:
                logging.info('\tfinish page {}'.format(page))
                break
            self.next_page(elements.pop())
            logging.info('\tfinish page {}'.format(page))

            page += 1
        return headlines, contents
    
    def run_queries(self, query_path, pages_per_query=2):
        crawled_items = []
        self.reinit_homepage()
        processed = 0
        for query in load_queries(query_path):
            spider_obj = {}
            spider_obj['query'] = query
            try:
                headlines, contents = self.run_one_query(query, pages_per_query)
                spider_obj['headlines'] = headlines
                spider_obj['contents'] = contents
            except Exception as e:
                print('error: {}'.format(str(e)))
                continue
            
            crawled_items.append(spider_obj)
            if processed % 10 == 0:
                print('processed {} items'.format(processed))
            processed += 1

            time.sleep(random.randint(3, 7))
        self.driver.quit()
        return crawled_items


class StaticCrawler:
	def __init__(self):
        self.params = { 
	        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36' 
        }
	
	def _get_page(self, content):
		url = 'https://baike.baidu.com/item/' + urllib.parse.quote(content)
		req = requests.get(url, headers=self.params)
		return bs(req.text, "html.parser")

	def _parse_summary(self, html_obj):
		summary = html_obj.find("div", class_="lemma-summary")
		if not summary:
			return ""
		summary_components = summary.find("div", class_="para")
		if not summary_components:
			return ""
		summary_component_text = []
		for component in summary_components:
			if isinstance(component, bs4.element.NavigableString) \
				or component.get("class") == "_blank" \
				or component.get("target") == "_blank":
				summary_component_text.append(component.get_text().strip())
		return "".join(summary_component_text)
	
	def _parse_basic_info(self, html_obj):
		basic_info = [
			html_obj.find("dl", class_="basicInfo-block basicInfo-left"),
			html_obj.find("dl", class_="basicInfo-block basicInfo-right")
		]
		basic_info_obj = {}
		for info in basic_info:
			if not info:
				continue
			dts = info.find_all("dt", class_="basicInfo-item name")
			dds = info.find_all("dd", class_="basicInfo-item value")
			for dt, dd in zip(dts, dds):
				basic_info_obj[dt.text.strip().replace(u'\xa0', '')] = ''.join(dd.find_all(text=True, recursive=False)).strip()
		return basic_info_obj
	
	def fetch_info(self, kw):
		soup_obj = self._get_page(kw)
		summary = self._parse_summary(soup_obj)
		basic_info = self._parse_basic_info(soup_obj)
		return summary, basic_info

