# -*- coding: utf-8 -*-
"""
Created on Sun Dec 17 16:01:08 2017

@author: mengxia_zhang
"""

import urllib2
import json
from bs4 import BeautifulSoup, Comment
import socket
import time
import os
import cPickle as pickle
from sets import Set
import crawl_utils 
from datetime import datetime, timedelta
import calendar
import io
import ast
import sys
import glob
import selenium
import random
base_zhihu_url = 'https://www.zhihu.com'
#os.chdir(r'/Users/mengxia_zhang/Dropbox/Lan_Mengxia/project_quora_zhihu/zhihu/scrape_weekly_data_without_api')

def process(period):
    period_last=period-1
    path_to_last_period='ego_nodes_period'+str(period_last)#+'_'+str(task_id)
    f = open("ego_urls_nonorganization.txt")
    start_urls = []
    user_id_dict = {}
    for x in f.readlines():
        item = x.strip().split()
        user_id_dict[item[1]] = item[0]
        start_urls.append(item[1])
    f.close()
    # job allocation:
    # 0: basic information, activities, followed topics
    # 1: answers
    # 2: followers and followees
    job_num = 3
    save_path = "ego_nodes_period" +str(period)

    todo_ids = []
    json_files = {}
    answer_bad_list = []
    good_answer_list = []
    for i in range(len(start_urls)):
        url=start_urls[i]
        user_id = user_id_dict[url]
        json_file = glob.glob(save_path+'/*'+user_id+'.json')
        user_info = json.load(open(json_file[0]))
        # note the previous results does not have to_do_list
        
        n_answer = len(user_info.get('new_answers',[]))
        json_file_old = glob.glob(path_to_last_period+'/*'+user_id+'.json')
        user_info_old = json.load(open(json_file_old[0]))
        n_answer_old = len(user_info_old.get('new_answers',[]))
        if n_answer_old > n_answer:
            answer_bad_list.append((url, user_id, json_file[0], json_file_old[0], n_answer, n_answer_old))
        else:
            good_answer_list.append((url, user_id, json_file[0], json_file_old[0], n_answer, n_answer_old))
    with open('bad_answer_list.txt','w') as f:
        for item in answer_bad_list:
            f.write('{} {} {} {} {} {}\n'.format(*item))

    with open('good_answer_list.txt','w') as f:
        for item in good_answer_list:
            f.write('{} {} {} {} {} {}\n'.format(*item))
 

if __name__ =="__main__":
    period=int(sys.argv[1])
    process(period)
