# -*- coding: utf-8 -*-
"""
Created on Sun Dec 17 16:30:44 2017

@author: mengxia_zhang
"""
import urllib2
import json
from bs4 import BeautifulSoup
import socket
import time
from selenium import webdriver
import selenium
USE_PROXY=True
from get_proxylist_incloack import get_proxies
import random
import io
import os
from email.mime.text import MIMEText
import smtplib
import sys

proxy_type_map = ['httpProxy', 'sslProxy', 'socksProxy', 'socksProxy'] 

import signal

class timeout:
    def __init__(self, seconds=1, error_message='Timeout'):
        self.seconds = seconds
        self.error_message = error_message
    def handle_timeout(self, signum, frame):
        raise RuntimeError(self.error_message)
    def __enter__(self):
        signal.signal(signal.SIGALRM, self.handle_timeout)
        signal.alarm(self.seconds)
    def __exit__(self, type, value, traceback):
        signal.alarm(0)

def send_email():
    text = "Instance got an exception" #+ str(error)
    msg = MIMEText(text)

    # me == the sender's email address
    # you == the recipient's email address
    msg['Subject'] = 'google instance exception'
    msg['From'] = 'evazmx@gmail.com'
    msg['To'] = 'zmxmdzmxmd@gmail.com'
    
    server = smtplib.SMTP('smtp.gmail.com',587) #port 465 or 587
    server.ehlo()
    server.starttls()
    server.ehlo()
    server.login('evazmx@gmail.com','080112021zmxmd')
    server.sendmail('evazmx@gmail.com','zmxmdzmxmd@gmail.com',msg.as_string())
    server.close()

class soupDriver:
    def __init__(self, period, task_id, save_folder='html_period_%d', proxy=None, proxy_type_str = "1000", proxy_source='cloak'):

        self.proxy_file = "current_proxies_%d_%d.txt" %(period,task_id)
        self.html_file="current_html_period_%d_%d.html" %(period,task_id)
        self.html_file_click="current_html_period_%d_%d_click.html" %(period,task_id)
        self.ip_block_file = "ip_block_list.txt"
        self.ip_block_file_out = "ip_block_list_%d_%d.txt" % (period, task_id)
        with open(self.ip_block_file) as f:
            self.ip_block_list = [line.strip() for line in f]   
        self.proxy_source = proxy_source
        self.save_folder = save_folder % period
        if not os.path.exists(self.save_folder):
            os.makedirs(self.save_folder)

        self.opts = webdriver.FirefoxOptions()
        self.opts.add_argument("--headless")
        self.proxy = ''
        self.all_proxies = {}
        if USE_PROXY:
            if proxy is None:
                proxy_param = self.get_proxy()
            else:
                self.proxy = proxy
                proxy_param = self.get_desired_capability(proxy, proxy_type_str)
            self.profile = webdriver.FirefoxProfile()
            self.profile.set_preference("browser.privatebrowsing.autostart", True)
            self.driver = webdriver.Firefox(firefox_options=self.opts, firefox_profile=self.profile,  capabilities=proxy_param)

        else:
            self.driver = webdriver.Firefox(firefox_options=self.opts)

        #self.driver = webdriver.Firefox()
    def get_desired_capability(self, proxy, proxy_type_str):
        proxy_param = webdriver.DesiredCapabilities.FIREFOX
        proxy_param['proxy']={
            "proxyType":"manual"
        }
        for i in range(4):
            if proxy_type_str[i] == '1':
                proxy_param['proxy'][proxy_type_map[i]] = proxy
                if i>=2: # need to set the sock version: 4 or 5
                    proxy_param['proxy']['socksVersion'] = i + 2
        return proxy_param
    def save_block_list(self):
        with open(self.ip_block_file_out,'w') as f:
            f.write('\n'.join(self.ip_block_list))
    def get_proxy(self, new_list=False, delete=False):
        if delete:
            self.all_proxies.pop(self.proxy, 0)
        if len(self.all_proxies.keys()) < 1 or new_list:
            self.all_proxies = get_proxies(self.proxy_file, self.proxy_source)
            for ip in self.ip_block_list:
                if ip in self.all_proxies:
                    del self.all_proxies[ip]
        self.proxy, proxy_type_str = random.choice(list(self.all_proxies.items()))
        
        print 'use proxy ip', self.proxy, 'proxy type', proxy_type_str
        desired_capability = self.get_desired_capability(self.proxy, proxy_type_str)
        return desired_capability

    def change_proxy(self,new_list=False, delete=False):
        succ = False
        while not succ:
            try:
                with timeout(seconds=20):
                    proxy_param = self.get_proxy(new_list=new_list, delete=delete)
                    # accept potential alert
                    try:
                            alert = self.driver.switch_to.alert
                            alert.accept()
                            print "alert accepted"
                    except Exception as e:
                        print e
                        
                    try:
                        self.driver.close()
                    except Exception as e:
                        print e
                    print 'start new webdriver instance'
                    sys.stdout.flush()

                    self.driver = webdriver.Firefox(firefox_options=self.opts, firefox_profile=self.profile,  capabilities=proxy_param)
                    print 'started'
                    sys.stdout.flush()
                    succ = True
            except (RuntimeError,selenium.common.exceptions.WebDriverException) as e:
                print e

    def try_connect(self, url, use_driver=True, timeout = 20):
        if use_driver:
            self.driver.set_page_load_timeout(timeout)
            while True:
                try:

                    print 'fetching', url
                    self.driver.get(url)
                    print 'page opened'
                    time.sleep(6)
                    page = self.driver.page_source
                except (selenium.common.exceptions.TimeoutException, selenium.common.exceptions.WebDriverException) as e:
                    print e
                    if USE_PROXY:
                        self.change_proxy(delete=True)
                    time.sleep(3)
                else:
                    return page
        else:
            while True:
                try:
                    page = urllib2.urlopen(url, timeout=5).read()
                except (urllib2.HTTPError,urllib2.URLError) as e:
                    return 'Page not found'
                except (socket.error) as e:
                    print "socket error: "+e.message
                    time.sleep(5)
                else:
                    return page    
    def save_page(self, filename):
        page = self.driver.page_source

        with io.open(os.path.join(self.save_folder, filename),'w', encoding='utf-8') as f:
           f.write(page)
    def get_filename(self):
        return self.url[22:].replace('/', '<>')
    def get_soup(self, url, use_driver=True, save_page=True):
        #page = try_connect(url)
        self.url = url
        print 'start connecting', url
        sys.stdout.flush()
        page = self.try_connect(url, use_driver=use_driver)
        if save_page:
            filename = self.get_filename()
            self.save_page(filename)
        print 'page fetched'
        sys.stdout.flush()
        soup = BeautifulSoup(page,'lxml')
        #title = soup.find('form',{'name':'captcha_form'})
        #blocked IP
        if (soup.title and (soup.title.text==u"安全验证" or u'Error 400' in soup.title.text)) or (soup.select('title') and soup.select('title')[0].text=='Web Page Blocked'):
            return None, False
        else:
            return soup, True
    def click(self, css):
        self.driver.find_element_by_css_selector(css).click()
        time.sleep(1)

    def click_xpath(self, xpath):
        self.driver.find_element_by_xpath(xpath).click()
        time.sleep(3)
        
    def get_soup_click(self, css, save_page=True):
        self.driver.find_element_by_css_selector(css).click()
        page = self.driver.page_source
        soup = BeautifulSoup(page,'lxml')
        if save_page:
            filename=self.get_filename()+'_click'
            self.save_page(filename)
        return soup
    def get_soup_click_all(self, css, save_page=True):
        elements = self.driver.find_elements_by_css_selector(css)
        for element in elements:
            element.click()
        page = self.driver.page_source
        if save_page:
            filename = self.get_filename() + '_click_all'
            self.save_page(filename)
        soup = BeautifulSoup(page,'lxml')
        return soup
    def get_soup_click_xpath(self, xpath, click_type='', save_page=True, wait=3):
        self.driver.find_element_by_xpath(xpath).click()
        if wait > 0:
            time.sleep(wait)
        page = self.driver.page_source
        if save_page:
            filename = self.get_filename() + '_click_' + click_type
            self.save_page(filename)
        
        soup = BeautifulSoup(page,'lxml')
        return soup
    def get_soup_until_success(self, url, use_driver=True, save_page=False):
        wait_time = 5
        success = False
        #while not success:
        soup, success = self.get_soup(url, use_driver, save_page=save_page)
        if not success:
            print 'page blocked'
            print 'put ip into block list', self.proxy
            self.ip_block_list.append(self.proxy)
            self.save_block_list()
            self.change_proxy(delete=True)
            time.sleep(wait_time)
            return None
        else:
            return soup
    def quit(self):
        self.driver.quit()
