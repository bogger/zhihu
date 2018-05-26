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


 
def crawl_person_profile(last_upvotes, last_answers, last_follower_list,last_followee_list, url=None, driver=None,
            save_page = True):

    assert url != None
    assert driver != None

    success=False
    try_limit=3
    sleep_time_limit=10
    voter_page_limit=10
    follower_page_limit=30
    followee_page_limit=100

    try_current=0
    
    while not success:
        try:
            soup = driver.get_soup_until_success(url, save_page=True)
            if not soup: return None 
            user_info={}
            
            #basic info   
            if soup.select('span.ProfileHeader-name'):
                name=soup.select('span.ProfileHeader-name')[0].text
                print(name)
                sys.stdout.flush()
            else:
                user_info['is_blocked']=True
                print "the user is blocked"
                sys.stdout.flush()
                return user_info  
            user_info['is_blocked']=False  
            user_info['user_name']=name
            if len(soup.select('span.RichText.ProfileHeader-headline'))>0:
                headline=soup.select('span.RichText.ProfileHeader-headline')[0].text
            else:
                headline=''    
            print headline
            sys.stdout.flush()
            user_info['headline']=headline

            if len(soup.select('div.ProfileHeader-infoItem'))==0:
                sex=''
            else:
                for item in soup.select('div.ProfileHeader-infoItem'): #users may have several header-inforitems
                    if len(item.select('svg.Icon.Icon--male'))==1:
                        sex='male'
                    elif len(item.select('svg.Icon.Icon--female'))==1:
                        sex='female'
                    else:
                        sex=''
            print sex
            sys.stdout.flush()
            user_info['gender']=sex
            
            #detail background
            detail_content={}
            if soup.select('button.Button.ProfileHeader-expandButton.Button--plain'):
                soup = driver.get_soup_click('Button.ProfileHeader-expandButton.Button--plain', save_page=True)
                detail_list=soup.select('div.ProfileHeader-detailItem')
                for item in detail_list:
                    key=item.span.text
                    print key
                    sys.stdout.flush()
                    if item.div.div is None:
                        value=item.div.text
                    else:
                        value=[x.text for x in item.div.find_all('div')]
                    print value
                    sys.stdout.flush()

                    detail_content[key]=value
            user_info['detail_background']=detail_content
            
            #badges and achievements
            achieve_items=soup.select('div.Profile-sideColumnItem')
            achieve_content={}
            for achieve_item in achieve_items:
                key=achieve_item.select('div.IconGraf')[0].text
                if key[-4:]==u'\u8ba4\u8bc1\u4fe1\u606f': #认证信息
                    key=key[-4:]
                    value=achieve_item.select('div.Profile-sideColumnItemValue')[0].text
                elif key[-5:]==u'\u4f18\u79c0\u56de\u7b54\u8005': #优秀回答者
                    key=key[-5:]
                    value=[x.text for x in achieve_item.select('div.Profile-sideColumnItemValue a')] 
                elif key[:4]==u'\u77e5\u4e4e\u6536\u5f55': #知乎收录
                    key= key[:4]
                    value={}
                    for x in achieve_item.select('div.IconGraf a'):
                        sub_key= x.text[-2:]
                        sub_value=[int(s.replace(',', '')) for s in (x.text).split() if (s.replace(',', '')).isdigit()][0]
                        value[sub_key]=sub_value
                    value[u'\u6536\u5f55detail']=achieve_item.select('div.Profile-sideColumnItemValue')[0].text
                elif key[-2:]==u'\u8d5e\u540c': #赞同
                    key=key[-2:]
                    value=[int(s.replace(',', '')) for s in (achieve_item.select('div.IconGraf')[0].text).split() if (s.replace(',', '')).isdigit()][0]
                    if achieve_item.select('div.Profile-sideColumnItemValue'):
                        achieve_content['thanks_collected']=achieve_item.select('div.Profile-sideColumnItemValue')[0].text
                    else:
                        achieve_content['thanks_collected']=''
                elif key[-4:]==u'\u516c\u5171\u7f16\u8f91': #公共编辑
                    key=key[-4:]
                    value=[int(s.replace(',', '')) for s in (achieve_item.select('div.IconGraf')[0].text).split() if (s.replace(',', '')).isdigit()][0]          
                achieve_content[key]=value
            for k, v in achieve_content.iteritems():
                print k
                if isinstance(v, dict):
                    for sk,sv in v.iteritems():
                        print sk
                        print sv
                elif isinstance(v, list):               
                    for x in v:
                        print x
                else:
                    print v
            print "badge_achive done"       
            sys.stdout.flush()
            user_info['badge_achieve']=achieve_content
            
            #privacy
            privacy=soup.find('span',{'class':'ProfileMainPrivacy-mainContentText'})
            if privacy is None:
                privacy=False
                user_info['set_privacy']=privacy
            else:       
                privacy=True
                user_info['set_privacy']=privacy
                return user_info
            print privacy
            sys.stdout.flush()

            #warning
            if soup.select('span.UserStatus-warnText'):
                user_info['warned']=True
                user_info['warning']=soup.select('span.UserStatus-warnText')[0].text
            else:
                user_info['warned']=False
                user_info['warning']=''
            print user_info['warned']
            sys.stdout.flush()

            #accumulated activities
            acts=soup.select('li.Tabs-item')
            print len(acts)
            sys.stdout.flush()
            act_content={}
            for act_type in acts:
                    temp=act_type.select('a')
                    if len(temp)==0:
                        continue
                    for element in temp[0](text=lambda text: isinstance(text, Comment)):
                        element.extract()
                    act_key=temp[0].find(text=True)
                    temp=act_type.select('span')
                    act_value= '' if len(temp)==0 else temp[0].text
                    act_content[act_key]=act_value
            
            collection_button_try=0
            collection_button_success=False
            while collection_button_try<try_limit and not collection_button_success:
                try:
                    collection_button_try+=1
                    soup = driver.get_soup_click_xpath("//div[contains(@class,'Popover')]/button[contains(@class, 'ProfileMain-menuToggler') and @id]", click_type='popover')
                    print "before"
                    sys.stdout.flush()
                    temp=soup.select('a.Button.Menu-item.Profile-popoverMenuItem.Button--plain')[0]
                    print "after"
                    sys.stdout.flush()
                    for element in temp(text=lambda text: isinstance(text, Comment)):
                        element.extract()#remove comments
                    collection_key=temp.find(text=True)
                    print collection_key
                    sys.stdout.flush()
                    collection_value=temp.span.text
                    print collection_value
                    sys.stdout.flush()
                    act_content[collection_key]=collection_value
                    collection_button_success=True
                except IndexError as e:
                    print "collection button error"
                    print e
                    sys.stdout.flush()
                    driver.change_proxy()
                    soup = driver.get_soup_until_success(url, save_page=True)
                    if not soup: return None
            user_info['accum_act_count']=act_content 
            print "accum_act done"
            sys.stdout.flush()

            #network_count
            networks=soup.select('div.Card.FollowshipCard a.Button.NumberBoard-item.Button--plain')
            network_content={}
            for item in networks:
                key=item.select('div.NumberBoard-itemName')[0].text
                print key
                value=item.select('strong.NumberBoard-itemValue')[0].text
                print value
                sys.stdout.flush()
                network_content[key]=value
            user_info['network_count']=network_content
            sys.stdout.flush()
            
            #interest
            ints=soup.select('a.Profile-lightItem')
            ints_content={}    
            for item in ints:
                key=item.select('span.Profile-lightItemName')[0].text
                value=item.select('span.Profile-lightItemValue')[0].text
                ints_content[key]=value
            user_info['interests']=ints_content

            success = True
        except IndexError as e:
                print "basic info, background, badge_achieve, privacy, accum act"
                print e
                try_current+=1
                if try_current>try_limit:
                    driver.change_proxy()
                    try_current=0
                time.sleep(1)   
    
    ########### #all new upvotes since data scraping (each time check until 7 days ago)
    #get last_upvote_answer_ids from last_upvotes
    last_upvote_answer_ids=[item['answer_id'] for item in last_upvotes]
    print last_upvote_answer_ids
    success = False
    upvote_sleep_time=3
    
    while not success:
        try:
            # scroll down to get enought activities
            scroll_time = 0   
            last_height = driver.driver.execute_script("return document.body.scrollHeight")
            while scroll_time < 6: # the page got a problem when scroll the 7th time
                scroll_time += 1
                # Scroll down to bottom
                driver.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                # Wait to load page
                time.sleep(upvote_sleep_time)
                # get act list
                page = driver.driver.page_source
                soup = BeautifulSoup(page,'lxml')
                recent_acts=soup.find('div',{'class':'List ProfileActivities'}).select('div.List-item')
                # Calculate new scroll height and compare with last scroll height
                new_height = driver.driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    print 'reach bottom of acts'
                    break
                last_height = new_height        
                oldest_act_time=recent_acts[-1].select('div.List-itemMeta span')[1].text
                if oldest_act_time[-2:] in [u'\u6708\u524d', u'\u5e74\u524d']: #月前 or 年前
                    print 'oldest act beyond 1 month'
                    break
                if oldest_act_time[-2:]==u'\u5929\u524d': # until 7 天前
                    oldest_nday=int(oldest_act_time[:-3])
                    if oldest_nday>7:
                        print "oldest act beyond 7 days"
                        break

            if save_page:
                filename = driver.get_filename() + '_scroll_upvote'
                driver.save_page(filename)
            new_upvotes=last_upvotes #all upvotes since data scraping
            for act in recent_acts:
                act_type=act.find('span',{'class':'ActivityItem-metaTitle'}).text
                if act_type!=u'\u8d5e\u540c\u4e86\u56de\u7b54': #赞同了回答
                    continue
                act_time=act.select('div.List-itemMeta span')[1].text
                print "act_type"
                print act_type
                print 'act_time'
                print act_time
                sys.stdout.flush()
                if act_time[-2:]== u'\u6708\u524d' or act_time[-2:]==u'\u5e74\u524d': #月前 or 年前
                    #new_upvotes.extend(last_upvotes)
                    print 'upvote beyond 1 month'
                    break 
                if act_time[-2:]==u'\u5929\u524d': # until 7 天前
                    act_nday=int(act_time[:-3])
                    print('act_nday', act_nday)
                    if act_nday>7:
                        #new_upvotes.extend(last_upvotes)
                        print 'upvote beyond 7 days'
                        break
                new_upvote={}   
                upvoted_answer=act.find('div',{'class':'ContentItem AnswerItem'})
                answer_meta=json.loads(upvoted_answer['data-zop'])
                new_upvote['answer_id']=answer_meta['itemId']                
                if new_upvote['answer_id'] in last_upvote_answer_ids:
                    #new_upvotes.extend(last_upvotes) #last_upvotes is a list
                    print('last upvote reached')
                    break
                else:
                    new_upvote['author_name']=answer_meta['authorName']
                    new_upvote['question_title']=answer_meta['title']
                    print('question_title',new_upvote['question_title'])
                    sys.stdout.flush()
                    new_upvote['answer_meta']=json.loads(upvoted_answer['data-za-extra-module'])
                    beijing_now=datetime.utcnow()+timedelta(hours=8)
                    if act_time[-2:]==u'\u5929\u524d':#天前
                        nday=int(act_time[:-3])
                        beijing_upvote=beijing_now+timedelta(days=-nday)
                        beijing_upvote=beijing_upvote.replace(hour=0, minute=0,second=0, microsecond=0)
                        upvote_time_secs=(beijing_upvote - datetime(1970, 1, 1)).total_seconds()
                    elif act_time[-3:]==u'\u5c0f\u65f6\u524d':#小时前
                        nhour=int(act_time[:-4])
                        beijing_upvote=beijing_now+timedelta(hours=-nhour)
                        beijing_upvote=beijing_upvote.replace(hour=0, minute=0,second=0, microsecond=0)
                        upvote_time_secs=(beijing_upvote - datetime(1970, 1, 1)).total_seconds()
                    elif act_time[-3:]==u'\u5206\u949f\u524d': #分钟前
                        nminutes=int(act_time[:-4])
                        beijing_upvote=beijing_now+timedelta(minutes=-nminutes)
                        beijing_upvote=beijing_upvote.replace(hour=0, minute=0,second=0, microsecond=0)
                        upvote_time_secs=(beijing_upvote - datetime(1970, 1, 1)).total_seconds()
                    elif act_time[-2:]==u'\u521a\u521a': #刚刚
                        beijing_upvote=beijing_now.replace(hour=0, minute=0,second=0, microsecond=0)
                        upvote_time_secs=(beijing_upvote - datetime(1970, 1, 1)).total_seconds()
                    new_upvote['upvote_time_secs']=upvote_time_secs
                    #new_upvotes.append(new_upvote)
                    new_upvotes=[new_upvote]+new_upvotes #append recent upvotes in front
            user_info['new_upvotes']=new_upvotes
            print('len_last_upvotes',len(last_upvotes))
            print('len_new_upvotes',len(new_upvotes))
            success = True
        except (IndexError, AttributeError, KeyError, selenium.common.exceptions.UnexpectedAlertPresentException) as e:
                print "new upvotes"
                print e
                upvote_sleep_time+=2
                if upvote_sleep_time>10:
                    driver.change_proxy()
                    soup = driver.get_soup_until_success(url, save_page=True)
                    if not soup: return None
                    upvote_sleep_time=3
                time.sleep(1)
     
    #following topics (top20)
    success = False
    try_current=0
    while not success:
        try:
            url_topics=url+"/following/topics"
            #print('topics_url', url_topics)
            soup_topics = driver.get_soup_until_success(url_topics, save_page=True)
            if not soup_topics: return None
            topic_list=soup_topics.find('div',{'id':'Profile-following'})
            topics_content=[]
            if topic_list is not None:       
                topics=topic_list.select('div.List-item')        
                for item in topics:
                    key=item.select('h2.ContentItem-title')[0].text
                    value=item.select('div.ContentItem-meta')[0].text
                    topics_content.append({key:value})
                    print key
                    print value
                    sys.stdout.flush()
            user_info['following_topics']=topics_content
            success = True
        except IndexError as e:
            print "following topics"
            print e
            try_current+=1
            if try_current>try_limit:
                driver.change_proxy()
                try_current=0
            time.sleep(1)
        
    
    #new answers since day 0, 2017-12-22, during observation window ; or recent 10 answers
    last_answer_ids=[item['answer_id'] for item in last_answers]
    print last_answer_ids
    sys.stdout.flush()
    answer_time_cut=(datetime(2017, 12, 22) - datetime(1970, 1, 1)).total_seconds()                  
    url_answers=url+"/answers"
    soup_answers=driver.get_soup_until_success(url_answers, save_page=True)
    answer_n = int(user_info['accum_act_count'].get(u'\u56de\u7b54','0').replace(',',''))
    max_page_try = 5
    if not soup_answers:
        return None
    if soup_answers.body.text!='Gone':
        if soup_answers.find('button',{'class':'Button PaginationButton Button--plain'}) is None:
            num_total_pages=1
        else:
            num_total_pages=int(soup_answers.find_all('button',{'class':'Button PaginationButton Button--plain'})[-1].text)
        print('num_total_pages',num_total_pages)
        sys.stdout.flush()  
        new_answers=[]# should be before for loop; before period 6 this was inside for loop
        new_answers_reached = False            
        for i in range(num_total_pages):
            success=False
            voter_sleep_time=3
            page_try = 0
            curr_answer_id = 0  
            voter_try=0 
            while not success and page_try < max_page_try:
                try:
                    page_try += 1
                    url_answers=url+"/answers?page="+str(i+1)
                    soup_answers=driver.get_soup_until_success(url_answers, save_page=True)
                    if not soup_answers:
                        return None
                    soup_answers=driver.get_soup_click_all('div.List-item div.RichContent div.RichContent-inner', save_page=True) #save page
                    answer_list=soup_answers.find('div',{'class':'List Profile-answers'}) 
                    if answer_list is not None:
                        answers=answer_list.select('div.List-item')
                        print('#answers',len(answers))
                        sys.stdout.flush()

                        while curr_answer_id<len(answers): 
                            print("curr_answer_id",curr_answer_id)
                            sys.stdout.flush()
                            item = answers[curr_answer_id]
                            answer={} 
                            if item.select('div.ContentItem-time a'):
                                answer_time=item.select('div.ContentItem-time a')[0].text[-10:] # blocked answers don't have time stamp
                            else: 
                                curr_answer_id+=1
                                continue
                            print 'answer_time'
                            print answer_time
                            sys.stdout.flush()
                            beijing_now=datetime.utcnow()+timedelta(hours=8)
                            if answer_time[:4]==u'\u4e8e \u6628\u5929':#于昨天    
                                beijing_answer=beijing_now+timedelta(hours=-24)
                                beijing_answer=beijing_answer.replace(hour=0, minute=0,second=0, microsecond=0)
                                answer_time_secs=(beijing_answer - datetime(1970, 1, 1)).total_seconds()
                            elif answer_time[-3]==u':':#于今天:
                                beijing_answer=beijing_now.replace(hour=0, minute=0,second=0, microsecond=0)
                                answer_time_secs=(beijing_answer - datetime(1970, 1, 1)).total_seconds()
                            else:       
                                answer_time_secs=(datetime.strptime(answer_time,"%Y-%m-%d") - datetime(1970, 1, 1)).total_seconds()
                            if answer_time_secs<answer_time_cut and len(new_answers)>9: #get new answers after 2017-12-22 and recent 10 answers
                                success = True
                                new_answers_reached = True
                                break

                            temp=item.select('div.ContentItem.AnswerItem')[0]
                            answer_meta=json.loads(temp['data-zop'])
                            answer['answer_id']=answer_meta['itemId']
                            answer['author_name']=answer_meta['authorName']
                            answer['question_title']=answer_meta['title']
                            answer_meta_extra=json.loads(temp['data-za-extra-module'])
                            answer['answer_meta']=answer_meta_extra                    
                            answer['content']=item.select('div.RichContent-inner')[0].text
                            answer['answer_time']=answer_time
                            answer['answer_time_secs']=answer_time_secs
                            upvote_num=answer_meta_extra['card']['content']['upvote_num']
                            answer['upvote_num']=upvote_num
                            print('upvote_num',upvote_num)
                           
                            upvote_num_equal=False
                            if answer['answer_id'] in last_answer_ids:
                                answer_index=last_answer_ids.index(answer['answer_id'])
                                if last_answers[answer_index]['upvote_num']==upvote_num:
                                    upvote_num_equal=True #if upvote_num does not change from last time, won't get the voter list again
                                if "voter_list" in last_answers[answer_index]:
                                    voter_list_last=last_answers[answer_index]['voter_list']
                                    voter_list_ids_last=[item_voter['voter_id'] for item_voter in voter_list_last]  
                                else:  
                                    voter_list_last=[]
                                    voter_list_ids_last=[]
                            else:
                                voter_list_last=[]
                                voter_list_ids_last=[]
                            voter_list=voter_list_last
                            #voter_detail
                            voter_success=False
                            while not upvote_num_equal and not voter_success and voter_try<try_limit:
                                try:
                                    voter_try+=1
                                    print('voter_try',voter_try)
                                    voter_list=voter_list_last #refresh the list while try again
                                    if item.select('span.Voters button'):
                                        soup_voters = driver.click_xpath("//div[contains(@class, 'Profile-answers')]/div/div[@class='List-item'][%d]//span[@class='Voters']/button" % (curr_answer_id+1))
                                        popup = driver.driver.find_element_by_xpath("//div[@class='VoterList-content']")                        
                                        scroll_h = int(popup.get_attribute("scrollHeight")) 
                                        print scroll_h                       
                                        prev_scroll_h = 0
                                        current_voter=0
                                        last_voter_reached=False
                                        voter_page_current=0
                                        while (scroll_h > prev_scroll_h and not last_voter_reached and voter_page_current<voter_page_limit):
                                            prev_scroll_h = scroll_h
                                            driver.driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", popup)   
                                            voter_page_current+=1                                                
                                            time.sleep(voter_sleep_time)
                                            scroll_h = int(popup.get_attribute("scrollHeight"))
                                            print scroll_h
                                            sys.stdout.flush()
                                            page = driver.driver.page_source
                                            soup_voters = BeautifulSoup(page,'lxml') 
                                            temp=soup_voters.select('div.VoterList-content')[0]
                                            if temp.select('div.List-item'):
                                                for voter_node in temp.select('div.List-item')[current_voter:]:
                                                    voter={}
                                                    voter_info=json.loads(voter_node.select('div.ContentItem')[0]['data-za-extra-module'])
                                                    voter['voter_id']=voter_info['card']['content']['member_hash_id']
                                                    if voter['voter_id'] in voter_list_ids_last:
                                                        #voter_list.extend(voter_list_last)
                                                        last_voter_reached=True
                                                        print "last_voter_reached"
                                                        break
                                                    else:
                                                        voter['voter_num_follower']=voter_info['card']['content']['follower_num']
                                                        voter['voter_name']=voter_node.select('span.UserLink.UserItem-name')[0].text
                                                        voter['status']=[]
                                                        for status in voter_node.select('span.ContentItem-statusItem'):
                                                            voter['status'].append(status.text)
                                                        voter_list=[voter]+voter_list
                                                current_voter=len(temp.select('div.List-item'))
                                            else:
                                                print 'problematic voters'
                                                sys.stdout.flush()                                               
                                        if save_page:
                                            filename = driver.get_filename() + "_answer" + str(curr_answer_id) \
                                                    + "_voter_list"
                                            driver.save_page(filename)
                                        driver.click('Button.Modal-closeButton.Button--plain') # close the popup after collecting data
                                    else:
                                        print 'no voters'
                                    voter_success=True
                                except IndexError as e:
                                    if soup_voters.find('Button',{'class':'Modal-closeButton.Button--plain'}) is not None:
                                        driver.click('Button.Modal-closeButton.Button--plain')
                                    print e
                            voter_try=0 # reset to 0 when while loop finish
                            answer['voter_list']=voter_list
                            print('len last voter list', len(voter_list_last))
                            print('len voter list', len(voter_list))
                            sys.stdout.flush()
                            new_answers.append(answer)
                            curr_answer_id+=1
                    if not(answer_list is None and answer_n > 0): 
                        success = True
                except (IndexError, KeyError, selenium.common.exceptions.NoSuchElementException, selenium.common.exceptions.ElementNotInteractableException, selenium.common.exceptions.ElementClickInterceptedException) as e:
                    print e
                    sys.stdout.flush()
                    # voter_sleep_time+=10
                    # if voter_sleep_time>sleep_time_limit:
                    driver.change_proxy()
                    page_try = 0
                    # voter_sleep_time=3
                    time.sleep(1)
            if new_answers_reached: break
        user_info['new_answers']=new_answers 
        print('last answers len', len(last_answers))
        print('new answers len', len(new_answers))
    else:
        print "the page is gone"        
        
    
    #network_detail
    follower_user_ids_last=[item['follower_user_id'] for item in last_follower_list]
    follower_list=last_follower_list
    if int(user_info['network_count'][u'\u5173\u6ce8\u8005'].replace(',',''))>0:#关注者
        url_follower=url+"/followers"
        soup_followers=driver.get_soup_until_success(url_follower, save_page=True)
        if not soup_followers:
            return None
        if soup_followers.find('button',{'class':'Button PaginationButton Button--plain'}) is None:
            num_total_pages=1
        else:
            num_total_pages=int(soup_followers.find_all('button',{'class':'Button PaginationButton Button--plain'})[-1].text)
        print('pages of followers',num_total_pages)

        last_follower_reached=False #follower list in last period
        for i in range(min(num_total_pages,follower_page_limit)): #np.nanpercentile(d_df0_notorg.follower_count,96)=2007 
            success = False
            while not success:
                try:
                    print('follower_page',i) 

                    url_follower=url+"/followers?page="+str(i+1)
                    soup_followers=driver.get_soup_until_success(url_follower, save_page=True)
                    if not soup_followers:
                        return None
                    followers=soup_followers.find('div',{'id':'Profile-following'}).select('div.List-item')   
                    print('#follower',len(followers))
                    sys.stdout.flush()
                    for follower in followers:
                        meta=follower.find('div',{'class','ContentItem'})['data-za-extra-module']
                        meta_dict=json.loads(meta)
                        follower_user_id=meta_dict['card']['content']['member_hash_id']
                        if follower_user_id in follower_user_ids_last:
                            #follower_list.extend(last_follower_list)
                            last_follower_reached=True
                            print "last_follower_reached"
                            sys.stdout.flush()
                            break
                        else:
                            follower_follower_num=meta_dict['card']['content']['follower_num']
                            follower_name=follower.select('span.UserLink.UserItem-name div.Popover div a')[0].text
                            follower_badge=''
                            badge_info=''
                            if follower.find('a',{'class':'UserLink-badge'}) is not None:
                                follower_badge=follower.select('span.UserLink.UserItem-name a.UserLink-badge')[0]['data-tooltip']
                                badge_info=follower.select('div.ContentItem-meta div div')[0].text
                            follower_intro=''
                            if follower.find('div',{'class':'RichText'}) is not None:
                                follower_intro=follower.find('div',{'class':'RichText'}).text
                            follower_status=[]
                            if len(follower.find_all('span',{'class':'ContentItem-statusItem'}))>0:
                                #print 'follower_status'
                                for item in follower.find_all('span',{'class':'ContentItem-statusItem'}):                       
                                    #print item.text
                                    follower_status.append(item.text)
                            follower_list=[{'follower_user_id':follower_user_id,'follower_name':follower_name,\
                                'follower_badge':{follower_badge:badge_info},\
                                'follower_follower_num':follower_follower_num,'follower_intro':follower_intro,'follower_status':follower_status}]+follower_list
                    success = True
                except (KeyError,AttributeError) as e:
                    print e
                    sys.stdout.flush()
                    driver.change_proxy()
                    time.sleep(1)
            if last_follower_reached:
                break

    print ('last_follower_list_len',len(last_follower_list))
    print ('follower_list_len', len(follower_list))
    user_info['follower_list']=follower_list
    
    followee_user_ids_last=[item['followee_user_id'] for item in last_followee_list]
    followee_list=last_followee_list
    if int(user_info['network_count'][u'\u5173\u6ce8\u4e86'].replace(',',''))>0:#关注了
        url_followee=url+"/following"
        soup_followees=driver.get_soup_until_success(url_followee, save_page=True)
        if not soup_followees:
            return None
        if soup_followees.find('button',{'class':'Button PaginationButton Button--plain'}) is None:
            num_total_pages=1
        else:
            num_total_pages=int(soup_followees.find_all('button',{'class':'Button PaginationButton Button--plain'})[-1].text)
        print('pages of followees',num_total_pages)

        last_followee_reached=False
        for i in range(min(num_total_pages,followee_page_limit)): 
            success = False
            while not success:
                try:
                    print('followee_page',i)           
                    url_followee=url+"/following?page="+str(i+1)
                    soup_followees=driver.get_soup_until_success(url_followee, save_page=True)
                    if not soup_followees:
                        return None
                    followees=soup_followees.find('div',{'id':'Profile-following'}).select('div.List-item')   
                    print('#followee',len(followees))
                    sys.stdout.flush()
                    for followee in followees:
                        meta=followee.find('div',{'class','ContentItem'})['data-za-extra-module']
                        meta_dict=json.loads(meta)
                        followee_user_id=meta_dict['card']['content']['member_hash_id']
                        if followee_user_id in followee_user_ids_last:
                            #followee_list.extend(last_followee_list)
                            last_followee_reached=True
                            print "last_followee_reached"
                            sys.stdout.flush()
                            break
                        else:
                            followee_follower_num=meta_dict['card']['content']['follower_num']
                            followee_name=followee.select('span.UserLink.UserItem-name div.Popover div a')[0].text
                            followee_badge=''
                            badge_info=''
                            if followee.find('a',{'class':'UserLink-badge'}) is not None:
                                followee_badge=followee.select('span.UserLink.UserItem-name a.UserLink-badge')[0]['data-tooltip']
                                badge_info=followee.select('div.ContentItem-meta div div')[0].text
                            followee_intro=''
                            if followee.find('div',{'class':'RichText'}) is not None:
                                followee_intro=followee.find('div',{'class':'RichText'}).text
                            followee_status=[]
                            if len(followee.find_all('span',{'class':'ContentItem-statusItem'}))>0:
                                for item in followee.find_all('span',{'class':'ContentItem-statusItem'}):
                                    followee_status.append(item.text)
                            followee_list=[{'followee_user_id':followee_user_id,'followee_name':followee_name,\
                                'followee_badge':{followee_badge:badge_info},\
                                'followee_follower_num':followee_follower_num,'followee_intro':followee_intro,'followee_status':followee_status}]+followee_list
                    success = True 
                except (KeyError,AttributeError) as e:
                    print e
                    sys.stdout.flush()
                    driver.change_proxy()
                    time.sleep(1)
            if last_followee_reached:
                break
    print ('last_followee_list_len',len(last_followee_list))
    print ('followee_list_len', len(followee_list))
    user_info['followee_list']=followee_list
    
    
    #for next period
    #recent upvotes
    #recent anwers (including voters), and new voters for old anwsers
    #recent followers
    #recent followees

    return user_info

if __name__ =="__main__":
    period=int(sys.argv[1])
    task_id=int(sys.argv[2])
    start_id=int(sys.argv[3])
    end_id=int(sys.argv[4])
    if len(sys.argv) > 5:
        proxy_source = sys.argv[5]
    else:
        proxy_source = 'cloak'
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
    save_path = "ego_nodes_period" +str(period)+"_"+str(task_id)
    todo_ids = []
    for i in range(len(start_urls))[start_id:end_id]:
        url=start_urls[i]
        user_id = user_id_dict[url]
        json_file = glob.glob(save_path+'/*'+user_id+'.json')
        if not json_file:
            todo_ids.append(i)
    driver = crawl_utils.soupDriver(period,task_id, proxy_source = proxy_source)
    change_proxy_every = 10
    cur_steps = 0
    while len(todo_ids)>0:
        #i=1
        i = random.choice(todo_ids)
        cur_steps+=1
        if  (cur_steps) % change_proxy_every == 0:
            driver.change_proxy(new_list=True)
        url=start_urls[i]
        #url='https://www.zhihu.com/people/huang-xiong-wei-45'
        print(i,url)
        sys.stdout.flush()
        user_id=user_id_dict[url]
        json_file_last=glob.glob(path_to_last_period+'/*'+user_id+'.json')[0]
        #json_file_last=[pos_json for pos_json in os.listdir(path_to_last_period) if pos_json.endswith(user_id+'.json')][0]
        with open(json_file_last) as json_data:
            d_last = json.load(json_data)
        if d_last["is_blocked"] or d_last["set_privacy"]:
            last_upvotes=[]
            last_answers=[]
            last_follower_list=[]
            last_followee_list=[]
        else:
            if period==1:
                if d_last['last_upvote']:
                    last_upvotes=[d_last['last_upvote']]
                else:
                    last_upvotes=[]
            if period>1:
                last_upvotes=d_last['new_upvotes']
            last_follower_list=d_last['follower_list']
            last_followee_list=d_last['followee_list']
            if 'new_answers' in d_last:
                last_answers=d_last['new_answers']
            else:
                last_answers=[]
            
            
            



        user_info=crawl_person_profile(last_upvotes,last_answers,last_follower_list,last_followee_list, url, driver)
        if user_info:
            # update todo ids
            todo_ids.remove(i)
            current_time_insec=int(calendar.timegm((datetime.now()).timetuple())) #UTC seconds
            #user_id='000000000000000003'
            user_info['user_id']=user_id
            user_info['period']=period
            user_info['current_time_insec']=current_time_insec
            user_info['user_url']=url
            file_name="ego_nodes_period"+str(period)+"_"+str(task_id)+"/"+str(period)+"_"+str(current_time_insec)+"_"+user_id+".json"
            print file_name
            with io.open(file_name,"w",encoding="utf-8") as outfile:
                outfile.write(unicode(json.dumps(user_info, outfile, ensure_ascii=False)))
    driver.quit()
