#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import random
import time
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from utils import load_text

logging.getLogger().setLevel(logging.INFO)

data_dir = './data'
query_path = os.path.join(data_dir, 'test')


def load_queries(dedup=True, shuffle=False):
    queries = load_text(query_path, dedup, shuffle)
    return queries


class SpiderBoy(object):
    def __init__(self, start_url):
        op = webdriver.ChromeOptions()
        # op.add_argument('--headless')
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
            print(elements)
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
    
    def run_queries(self, pages_per_query=2):
        crawled_items = []
        self.reinit_homepage()
        processed = 0
        for query in load_queries():
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


if __name__ == "__main__":
    spider = SpiderBoy('http://www.baidu.com')
    crawled_items = spider.run_queries()

