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
base_zhihu_url = 'https://www.zhihu.com'
#os.chdir(r'/Users/mengxia_zhang/Dropbox/Lan_Mengxia/project_quora_zhihu/zhihu/scrape_weekly_data_without_api')


 
def crawl_person_profile(url=None, driver=None):
    
    assert url != None
    assert driver != None
    soup = driver.get_soup_until_success(url)
    
    user_info={}
    
    #basic info   
    if soup.select('span.ProfileHeader-name'):
        name=soup.select('span.ProfileHeader-name')[0].text
    else:
        user_info['is_blocked']=True
        print "the user is blocked"
        return user_info  
    user_info['is_blocked']=False  
    user_info['user_name']=name
    if len(soup.select('span.RichText.ProfileHeader-headline'))>0:
        headline=soup.select('span.RichText.ProfileHeader-headline')[0].text
    else:
        headline=''    
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
    user_info['gender']=sex
    
    #detail background
    detail_content={}
    if soup.select('button.Button.ProfileHeader-expandButton.Button--plain'):
        soup = driver.get_soup_click('Button.ProfileHeader-expandButton.Button--plain')
        detail_list=soup.select('div.ProfileHeader-detailItem')
        for item in detail_list:
            key=item.span.text
            if item.div.div is None:
                value=item.div.text
            else:
                value=[x.text for x in item.div.find_all('div')]
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
            
    #accumulated activities
    acts=soup.select('li.Tabs-item')
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
    #soup = driver.get_soup_click('button.ProfileMain-menuToggler.Button--plain') #get collections number
    soup = driver.get_soup_click_xpath("//div[contains(@class,'Popover')]/button[contains(@class, 'ProfileMain-menuToggler') and @data-reactid]")
    temp=soup.select('a.Button.Menu-item.Profile-popoverMenuItem.Button--plain')[0]
    for element in temp(text=lambda text: isinstance(text, Comment)):
        element.extract()#remove comemnts
    collection_key=temp.find(text=True)
    print collection_key
    collection_value=temp.span.text
    print collection_value
    act_content[collection_key]=collection_value
    user_info['accum_act_count']=act_content    
    
    ########### last upvote within 1 month
    success = False
    while not success:
        try:
            last_upvote={} 
            # scroll down to get enought activities   
            last_height = driver.driver.execute_script("return document.body.scrollHeight")
            while True:
                # Scroll down to bottom
                driver.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                # Wait to load page
                time.sleep(3)
                # get act list
                recent_acts=soup.find('div',{'class':'List ProfileActivities'}).select('div.List-item')
                page = driver.driver.page_source
                soup= BeautifulSoup(page,'lxml') 
                # Calculate new scroll height and compare with last scroll height
                new_height = driver.driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    break
                last_height = new_height        
                oldest_act_time=recent_acts[-1].select('div.List-itemMeta span')[1].text
                if oldest_act_time[-2:] in [u'\u6708\u524d', u'\u5e74\u524d']:
                    break
            for act in recent_acts:
                act_type=act.find('span',{'class':'ActivityItem-metaTitle'}).text
                act_time=act.select('div.List-itemMeta span')[1].text
                print "act_type"
                print act_type
                print 'act_time'
                print act_time
                if act_time[-2:]== u'\u6708\u524d' or act_time[-2:]==u'\u5e74\u524d': #月前 or 年前
                    break    
                if act_type==u'\u8d5e\u540c\u4e86\u56de\u7b54':#赞同了回答
                    upvoted_answer=act.find('div',{'class':'ContentItem AnswerItem'})
                    answer_meta=json.loads(upvoted_answer['data-zop'])
                    last_upvote['answer_id']=answer_meta['itemId']
                    last_upvote['author_name']=answer_meta['authorName']
                    last_upvote['question_title']=answer_meta['title']
                    last_upvote['answer_meta']=json.loads(upvoted_answer['data-za-extra-module'])
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
                    elif act_time[-2]==u'\u521a\u521a': #刚刚
                        beijing_upvote=beijing_now.replace(hour=0, minute=0,second=0, microsecond=0)
                        upvote_time_secs=(beijing_upvote - datetime(1970, 1, 1)).total_seconds()
                    last_upvote['upvote_time_secs']=upvote_time_secs
                    break
            user_info['last_upvote']=last_upvote
            success = True
        except IndexError as e:
                print "last upvote"
                print e
                time.sleep(1)
    
    #network_count
    # success = False
    # while not success:
    #     try:
    networks=soup.select('a.Button.NumberBoard-item.Button--plain')
    network_content={}
    for item in networks:
        key=item.select('div.NumberBoard-itemName')[0].text
        print key
        value=item.select('strong.NumberBoard-itemValue')[0].text
        print value
        network_content[key]=value
    user_info['network_count']=network_content
    success = True
        # except IndexError as e:
        #     print "network count"
        #     print e 
        #     time.sleep(1)
    
    #interest
    ints=soup.select('a.Profile-lightItem')
    ints_content={}    
    for item in ints:
        key=item.select('span.Profile-lightItemName')[0].text
        value=item.select('span.Profile-lightItemValue')[0].text
        ints_content[key]=value
    user_info['interests']=ints_content
    
    #following topics (top20)
    success = False
    while not success:
        try:
            url_topics=url+"/following/topics"
            #print('topics_url', url_topics)
            soup_topics = driver.get_soup_until_success(url_topics)
            topic_list=soup_topics.find('div',{'id':'Profile-following'})
            topics_content=[]
            if topic_list is not None:       
                topics=topic_list.select('div.List-item')        
                for item in topics:
                    key=item.select('h2.ContentItem-title')[0].text
                    value=item.select('div.ContentItem-meta')[0].text
                    topics_content.append({key:value})
            user_info['following_topics']=topics_content
            success = True
        except IndexError as e:
            print e
            time.sleep(1)
        
    
    #new answers since day 0, 2017-12-22, during observation window 
    answer_time_cut=(datetime(2017, 12, 22) - datetime(1970, 1, 1)).total_seconds()                  
    success=False
    while not success:
        try:
            url_answers=url+"/answers"
            soup_answers=driver.get_soup_until_success(url_answers)
            soup_answers=driver.get_soup_click_all('div.List-item div.RichContent div.RichContent-inner') 
            #soup_answers=driver.get_soup_click_all('Button.ContentItem-more.Button--plain')
            if soup_answers.find('button',{'class':'Button PaginationButton Button--plain'}) is None:
                num_total_pages=1
            else:
                num_total_pages=int(soup_answers.find_all('button',{'class':'Button PaginationButton Button--plain'})[-1].text)
            print('num_total_pages',num_total_pages)            
            for i in range(num_total_pages):
                if success:
                    break            
                if i>0:
                    url_answers=url+"/answers?page="+str(i+1)
                    soup_answers=driver.get_soup_until_success(url_answers)
                    soup_answers=driver.get_soup_click_all('div.List-item div.RichContent div.RichContent-inner') 
                answer_list=soup_answers.find('div',{'class':'List Profile-answers'})
                new_answers=[]    
                if answer_list is not None:
                    answers=answer_list.select('div.List-item')
                    print('#answers',len(answers))
                    for k, item in enumerate(answers): 
                        answer={} 
                        #print item
                        #temp_list = item.select('div.ContentItem-time a span')
                        #print 'a span list length', len(temp_list)
                        if item.select('div.ContentItem-time a'):
                            answer_time=item.select('div.ContentItem-time a')[0].text[-10:]
                        else: 
                            continue
                        #answer_time=(item.select('div.ContentItem-time a span')[0]['data-tooltip'])[-10:]
                        print 'answer_time'
                        print answer_time
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
                        if answer_time_secs<answer_time_cut:
                            success = True
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


                        #voter_detail
                        upvote_num=answer_meta_extra['card']['content']['upvote_num']
                        answer['upvote_num']=upvote_num
                        print('upvote_num',upvote_num)
                        voter_list=[]
                        if item.select('span.Voters button'):
                            soup_voters = driver.click_xpath("//div[contains(@class, 'Profile-answers')]/div/div[@class='List-item'][%d]//span[@class='Voters']/button" % (k+1))
                            popup = driver.driver.find_element_by_xpath("//div[@class='VoterList-content']")                        
                            scroll_h = int(popup.get_attribute("scrollHeight")) 
                            print scroll_h                       
                            prev_scroll_h = 0
                            while (scroll_h > prev_scroll_h):
                                prev_scroll_h = scroll_h
                                driver.driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", popup)                                                   
                                time.sleep(3)
                                scroll_h = int(popup.get_attribute("scrollHeight"))
                                print scroll_h
                            page = driver.driver.page_source
                            soup_voters = BeautifulSoup(page,'lxml') 
                            temp=soup_voters.select('div.VoterList-content')[0]
                            if temp.select('div.List-item'):
                                for voter_node in temp.select('div.List-item'):
                                    voter={}
                                    voter_info=json.loads(voter_node.select('div.ContentItem')[0]['data-za-extra-module'])
                                    voter['voter_id']=voter_info['card']['content']['member_hash_id']
                                    voter['voter_num_follower']=voter_info['card']['content']['follower_num']
                                    voter['voter_name']=voter_node.select('span.UserLink.UserItem-name')[0].text
                                    voter['status']=[]
                                    for status in voter_node.select('span.ContentItem-statusItem'):
                                        voter['status'].append(status.text)
                                    voter_list.append(voter)
                            else:
                                print 'problematic voter'    
                            driver.click('Button.Modal-closeButton.Button--plain') # close the popup after collecting data
                        else:
                            print 'no voters'
                        answer['voter_list']=voter_list
                        new_answers.append(answer)
            user_info['new_answers']=new_answers 
            success = True
        except IndexError as e:
            print e
            #print content
            time.sleep(1)
    
    #network_detail
    follower_list_content=[]
    if int(user_info['network_count'][u'\u5173\u6ce8\u8005'].replace(',',''))>0:#关注者
        url_follower=url+"/followers"
        soup_followers=driver.get_soup_until_success(url_follower)
        if soup_followers.find('button',{'class':'Button PaginationButton Button--plain'}) is None:
            num_total_pages=1
        else:
            num_total_pages=int(soup_followers.find_all('button',{'class':'Button PaginationButton Button--plain'})[-1].text)
        print('pages of followers',num_total_pages)
        for i in range(num_total_pages): 
            print('follower_page',i)
            if i>100:
                break #np.nanpercentile(d_df0_notorg.follower_count,96)=2007             
            if i>0:
                url_follower=url+"/followers?page="+str(i+1)
                soup_followers=driver.get_soup_until_success(url_follower)
            follower_list=soup_followers.find('div',{'id':'Profile-following'}).select('div.List-item')   
            print('#follower',len(follower_list))
            for follower in follower_list:
                meta=follower.find('div',{'class','ContentItem'})['data-za-extra-module']
                #print('follower',meta)
                meta_dict=json.loads(meta)
                follower_user_id=meta_dict['card']['content']['member_hash_id']
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
                follower_list_content.append({'follower_user_id':follower_user_id,'follower_name':follower_name,\
                    'follower_badge':{follower_badge:badge_info},\
                    'follower_follower_num':follower_follower_num,'follower_intro':follower_intro,'follower_status':follower_status})
    user_info['follower_list']=follower_list_content
    
    followee_list_content=[]
    if int(user_info['network_count'][u'\u5173\u6ce8\u4e86'].replace(',',''))>0:#关注了
        url_followee=url+"/following"
        soup_followees=driver.get_soup_until_success(url_followee)
        if soup_followees.find('button',{'class':'Button PaginationButton Button--plain'}) is None:
            num_total_pages=1
        else:
            num_total_pages=int(soup_followees.find_all('button',{'class':'Button PaginationButton Button--plain'})[-1].text)
        print('pages of followees',num_total_pages)
        for i in range(num_total_pages): 
            print('followee_page',i) 
            if i>100:
                break #np.nanpercentile(d_df0_notorg.follower_count,96)=2007            
            if i>0:
                url_followee=url+"/following?page="+str(i+1)
                soup_followees=driver.get_soup_until_success(url_followee)
            followee_list=soup_followees.find('div',{'id':'Profile-following'}).select('div.List-item')   
            print('#followee',len(followee_list))
            for followee in followee_list:
                meta=followee.find('div',{'class','ContentItem'})['data-za-extra-module']
                #print('followee',meta)
                meta_dict=json.loads(meta)
                followee_user_id=meta_dict['card']['content']['member_hash_id']
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
                        #print'followee_status' 
                        #print item.text
                        followee_status.append(item.text)
                followee_list_content.append({'followee_user_id':followee_user_id,'followee_name':followee_name,\
                    'followee_badge':{followee_badge:badge_info},\
                    'followee_follower_num':followee_follower_num,'followee_intro':followee_intro,'followee_status':followee_status})
    user_info['followee_list']=followee_list_content
    
    
    #for next period
    #recent upvotes
    #recent followers
    #recent followees

    return user_info

if __name__ =="__main__":
    period=0
    f = open("ego_urls_nonorganization.txt")
    start_urls = []
    user_id_dict = {}
    for x in f.readlines():
        item = x.strip().split()
        user_id_dict[item[1]] = item[0]
        start_urls.append(item[1])
    f.close()
    driver = crawl_utils.soupDriver()
    for i in range(len(start_urls))[1302:]:
        #i=1
        url=start_urls[i]
        #url='https://www.zhihu.com/people/richard-xu-25'
        print(i,url)
        sys.stdout.flush()
        user_info=crawl_person_profile(url, driver)
        current_time_insec=int(calendar.timegm((datetime.now()).timetuple())) #UTC seconds
        user_id=user_id_dict[url]
        #user_id='000000000000000003'
        user_info['user_id']=user_id
        user_info['period']=period
        user_info['current_time_insec']=current_time_insec
        user_info['user_url']=url
        file_name="ego_nodes_period"+str(period)+"/"+str(period)+"_"+str(current_time_insec)+"_"+user_id+".json"
        print file_name
        with io.open(file_name,"w",encoding="utf-8") as outfile:
            outfile.write(unicode(json.dumps(user_info, outfile, ensure_ascii=False)))
    driver.quit()
    #    with open('test_user_profile.json','w') as f:
#        json.dump(achieve_content,f)
