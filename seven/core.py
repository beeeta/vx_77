import datetime
import os
from concurrent.futures import ProcessPoolExecutor
from hashlib import md5
import time
from multiprocessing import cpu_count
import traceback
import linecache

from selenium import webdriver
from selenium.webdriver import ChromeOptions
import requests
from bs4 import BeautifulSoup
import itchat
import configparser
import schedule

PIC_SEARCH_BASE_URL = 'https://cn.bing.com/images/search?q=%E6%83%85%E4%BE%A3'
PIC_DIR = 'pic_dir'
TEXT_TEMPLATE='第:{}天\n{}'


config = configparser.ConfigParser()
_curdir = os.path.dirname(__file__)
config.read_file(open(os.path.join(_curdir,'config.ini'), encoding='utf-8'))

def crawl_words():
    res = requests.get('http://www.binzz.com/yulu2/3588.html')
    soup = BeautifulSoup(res.content.decode('gbk'),'lxml')
    content = soup.find(id='content')
    ps = content.find_all('p')
    text_path = os.path.join(os.path.join(_curdir,os.pardir),'words.txt')
    with open(text_path,'w',encoding='utf-8') as f:
        for pp in ps:
            ptext = pp.text.strip()
            if ptext == '':
                continue
            try:
                ptext = ptext[ptext.index('：')+1:]
                ptext = ptext.strip()
            except ValueError:
                traceback.print_exc()
            f.write(ptext+'\n')
    print('reload love words from web finished...')


def save_pic(img_url):
    r = requests.get(img_url)
    filename = md5(img_url.encode('utf-8')).hexdigest()+'.jpg'
    pic_dir = os.path.join(os.path.join(_curdir,os.pardir),PIC_DIR)
    with open(os.path.join(pic_dir,filename),'wb') as f:
        f.write(r.content)

def crawl_pic():
    chrome_options = ChromeOptions()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-gpu')
    driver = webdriver.Chrome(chrome_options=chrome_options)
    driver.get(PIC_SEARCH_BASE_URL)
    while True:
        bef_height = driver.execute_script('return document.body.scrollHeight')
        driver.execute_script("window.scrollTo(0,document.body.scrollHeight)")
        time.sleep(1)
        aft_height = driver.execute_script('return document.body.scrollHeight')
        if aft_height == bef_height:
            break
    soup = BeautifulSoup(driver.page_source,'lxml')
    div = soup.find(id='mmComponent_images_1')
    imgs = div.find_all('img')
    img_urls = []
    for img in imgs:
        img_url = img.attrs.get('src', None) or img.attrs.get('data-src', None)
        if img_url:
            img_urls.append(img_url)

    print('image urls crawl finished,begin to download ...')
    pool = ProcessPoolExecutor(max_workers = cpu_count())
    pool.map(save_pic, img_urls)
    print('download pictures finished ...')

def prepare_msg():
    day_count = int(config['common']['DAY_COUNT'])
    wordsfile_path = os.path.join(os.path.join(_curdir, os.pardir), 'words.txt')
    pic_dir = os.path.join(os.path.join(_curdir, os.pardir),PIC_DIR)
    if not os.path.exists(wordsfile_path):
        raise Exception('words have not crawled,please run the words crawler first')
    if not os.path.exists(pic_dir):
        os.mkdir(pic_dir)

    for i in range(5):
        text = linecache.getline(wordsfile_path, day_count).strip()
        if text:
            break
    pic_filenames = os.listdir(pic_dir)
    pic_filename = pic_filenames[day_count]
    pic_uri = os.path.join(pic_dir, pic_filename)
    if day_count >= len(linecache.getlines(wordsfile_path)):
        # 说完了所有的情话，还是没反应就放弃
        return 'I quit...',None
    else:
        config['common']['DAY_COUNT'] = str(day_count + 1)
    config.write(open(os.path.join(_curdir, 'config.ini'), 'w',encoding='utf-8'))
    return text, pic_uri

def send_msg(coolcat):
    text, pic = prepare_msg()
    firt_date = datetime.datetime.strptime('%Y-%m-%d')
    cur_date = datetime.datetime.now()
    text = TEXT_TEMPLATE.format((cur_date - firt_date).days+1, text)
    coolcat.send_msg(text)
    if pic:
        coolcat.send_image(pic)

def vx():
    itchat.auto_login()
    try:
        coolcats = itchat.search_friends(name=config['common']['nick_name'])
        if len(coolcats) == 0:
            raise IndexError
        if len(coolcats) > 1:
            raise ValueError
        coolcat = coolcats[0]
        schedule.every().day.at("7:30").do(send_msg,coolcat)
        while True:
            schedule.run_pending()
            time.sleep(30)

    except IndexError:
        print('找不到该好友，请检查昵称是否设置正确!')
    except ValueError:
        print('找到多个好友，请使用具有唯一性的昵称或备注名称')
    except Exception:
        traceback.print_exc()
        print('send message error!')
    finally:
        itchat.logout()








