# -*- coding: utf-8 -*-
"""
Created on Sun Feb 11 15:30:01 2018

@author: mengxia_zhang
"""

import urllib2
import pandas as pd
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
import random
import glob
import selenium
base_zhihu_url = 'https://www.zhihu.com'



def crawl_answer_rank(answer_id, question_id, driver=None, save_page = True):
    sleep_time=5
    question_url=base_zhihu_url+'/question/'+question_id # answers belong to the same question overlap
    soup = driver.get_soup_until_success(question_url, save_page=True)#save page using folder name "html_answer_rank_period"
    if not soup: return None
    question_info={}
    question_info['question_id']=question_id
    if not soup.find('meta', {'itemprop':'name'}):
        return {'answer_id':answer_id,'answer_rank':'', 'answer_meta': {}, 'question_info':'unavailable'}
    question_info['title']=soup.find('meta', {'itemprop':'name'})['content']
    question_info['key_words']=soup.find('meta', {'itemprop':'keywords'})['content']
    question_info['answer_count']=soup.find('meta', {'itemprop':'answerCount'})['content']
    question_info['comment_count']=soup.find('meta', {'itemprop':'commentCount'})['content']
    question_info['date_created']=soup.find('meta', {'itemprop':'dateCreated'})['content']
    question_info['date_modified']=soup.find('meta', {'itemprop':'dateModified'})['content']
    question_info['follower_count']=soup.find('meta', {'itemprop':'zhihu:followerCount'})['content']
    question_info['views_count']=soup.find('div',{'class':'QuestionFollowStatus'}).findAll('strong',{'class':'NumberBoard-itemValue'})[1].text
    info = soup.find('div',{'class':'QuestionPage'}).findAll('div')[0]['data-zop-question']
    info = json.loads(info)
    question_info['topics']=info['topics']
    question_info['is_editable']=info['isEditable']
    success=False
    proxy_limit = 5
    scroll_limit = 5
    try_num = 0
    try_proxy_num = 0
    while not success:
        try:
            answer_box=soup.find('div',{'class':'QuestionAnswers-answers'})
            if not answer_box: #if no answers shown (some answers can be folded)     
                answer_rank='not_in_first_2_scrolls_no_answer_box'
                answer_meta_extra={}
                success=True
            else: # if there are some answers shown
                scroll_success=False
                

                last_height = driver.driver.execute_script("return document.body.scrollHeight")
                #scroll once
                # scroll slowly
                scroll_times = 10
                for i in xrange(1, scroll_times+1):
                    driver.driver.execute_script("window.scrollTo(0, %d);" % (last_height * i / scroll_times))
                    time.sleep(0.1)

                # wait to load page
                time.sleep(sleep_time)
                new_height = driver.driver.execute_script("return document.body.scrollHeight")
                print "previous height", last_height, "new height", new_height
                # get answer list
                page = driver.driver.page_source
                soup_answer_list= BeautifulSoup(page,'lxml')
                
                answer_box_new=soup_answer_list.find('div',{'class':'QuestionAnswers-answers'})
                if not answer_box_new:
                    answer_rank='not_in_first_2_scrolls_no_answer_box'
                    answer_meta_extra={}
                    success=True
                else:
                    answers=soup_answer_list.find('div',{'class':'QuestionAnswers-answers'}).select('div.ContentItem.AnswerItem')
                    print('#answers total',question_info['answer_count'])
                    print('#answers got', len(answers))
                    sys.stdout.flush()
                    if len(answers)>=min(int(question_info['answer_count']),10):#originally 40, changed on Feb 28, 2018
                        print('2 scrolls got')
                        sys.stdout.flush()
                        scroll_success=True
                    elif soup_answer_list.select('button.Button.QuestionAnswers-answerButton.Button--blue.Button--spread'):
                        print('reach bottom')
                        sys.stdout.flush()
                        scroll_success=True
                    print('scroll_success',scroll_success)
                    sys.stdout.flush()

                    if scroll_success:
                        if save_page:
                            filename = driver.get_filename() + '_answer_2scroll_'+str(answer_id)
                            driver.save_page(filename)
                        answer_ids=[json.loads(item['data-zop'])['itemId'] for item in answers]
                        if answer_id in answer_ids:
                            answer_rank=answer_ids.index(answer_id)
                            answer_meta_extra=json.loads(answers[answer_rank]['data-za-extra-module'])#include #upvotes and #comments
                        elif len(answers)==question_info['answer_count']:
                            answer_rank='deleted'
                            answer_meta_extra = {}
                        else:
                            answer_rank='not_in_first_2_scrolls_num_answer_got'+str(len(answers))
                            answer_meta_extra = {}
                        print('answer_rank',answer_rank)
                        print('answer_meta',answer_meta_extra)
                        sys.stdout.flush()
                        success=True
                        print('success',success)
                        sys.stdout.flush()
                    else:
                        try_num += 1
                        if try_num == scroll_limit:
                            if try_proxy_num == proxy_limit:
                                
                                answer_ids=[json.loads(item['data-zop'])['itemId'] for item in answers]
                                if answer_id in answer_ids:
                                    answer_rank=answer_ids.index(answer_id)
                                    answer_meta_extra=json.loads(answers[answer_rank]['data-za-extra-module'])#include #upvotes and #comments
                                
                                else:
                                    answer_rank='not_in_first_scroll_num_answer_got'+str(len(answers))
                                    answer_meta_extra = {}
                                print('answer_rank',answer_rank)
                                print('answer_meta',answer_meta_extra)
                                sys.stdout.flush()
                                success=True
                                print('success',success)
                                sys.stdout.flush()
                            else:
                                try_proxy_num += 1
                                try_num = 0
                                print 'scoll limit reached'
                                sys.stdout.flush()
                                driver.change_proxy()
                                soup = driver.get_soup_until_success(question_url, save_page=True)
                                if not soup: return None
        except (KeyError, IndexError) as e:
            print e
            sys.stdout.flush()
            driver.change_proxy()
            soup = driver.get_soup_until_success(question_url, save_page=True)
            if not soup: return None
    return {'answer_id':answer_id,'answer_rank':answer_rank, 'answer_meta': answer_meta_extra, 'question_info':question_info}

if __name__ =="__main__":  
    period=int(sys.argv[1])
    if len(sys.argv) > 2:
        proxy_source = sys.argv[2]
    else:
        proxy_source = 'cloak'
    #num_engine_ego=1
    #base_url='/Users/mengxia_zhang/Dropbox/Lan_Mengxia/project_quora_zhihu/zhihu/scrape_weekly_data_without_api/'
    base_url = './'
    driver = crawl_utils.soupDriver(period, 0, proxy_source = proxy_source, 
            save_folder='html_answer_rank_period_%d')
    path_to_json = base_url+'ego_nodes_period'+str(period)#+'_'+str(engine)
    json_files_ego=[pos_json for pos_json in os.listdir(path_to_json) if pos_json.endswith('.json')]
    print len(json_files_ego), 'nodes in total'
    save_path = "ranks_of_answers_in_period"+str(period)
    todo_user_id_answer_ids = []
    for json_file in json_files_ego:
        with open(path_to_json+'/'+json_file) as json_data:
            d = json.load(json_data)         
            if 'new_answers' in d:
                user_id=d['user_id']
                new_answers=d['new_answers']
                for answer in new_answers:
                    answer_id=answer['answer_id']

                    question_id=answer['answer_meta']['card']['content']['parent_token']
                    file_name="ranks_of_answers_in_period"+str(period)+"/"+str(period)+"_"+str(user_id)+"_"+str(answer_id)+".json"
                    
                    if not os.path.exists(file_name):
                        todo_user_id_answer_ids.append((user_id, answer_id, question_id))
    change_proxy_every = 100
    curr_steps = 0
    while len(todo_user_id_answer_ids) > 0:
        curr_steps += 1


        if curr_steps % change_proxy_every == 0:
            driver.change_proxy(new_list=True)
        user_id, answer_id, question_id = random.choice(todo_user_id_answer_ids)
        answer_info=crawl_answer_rank(answer_id, question_id, driver=driver, save_page = True)
        if answer_info:
            todo_user_id_answer_ids.remove((user_id, answer_id, question_id))
            current_time_insec=int(calendar.timegm((datetime.now()).timetuple()))
            answer_info['current_time']=current_time_insec
            answer_info['user_id']=user_id
            fd_name = 'ranks_of_answers_in_period' + str(period)
            if not os.path.exists(fd_name):
                os.makedirs(fd_name)
            file_name="ranks_of_answers_in_period"+str(period)+"/"+str(period)+"_"+str(user_id)+"_"+str(answer_id)+".json"
            print file_name
            with io.open(file_name,"w",encoding="utf-8") as outfile:
                outfile.write(unicode(json.dumps(answer_info, outfile, ensure_ascii=False)))
            
