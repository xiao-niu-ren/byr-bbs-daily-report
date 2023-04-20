#!/usr/bin/python
# @Time ：2023.04.19
# @Author : Xie zy
# @File : auto.py
import logging
import os
from datetime import time, datetime, timezone, timedelta
import time
import requests
from lxml import etree

# 爬取板块url
PART_TIME_JOB_URL = 'https://bbs.byr.cn/board/ParttimeJob'

# 模拟浏览器信息
USER_AGENT = 'User-Agent: Mozilla/5.0 (X11; Linux x86_64; rv:91.0) Gecko/20100101 Firefox/91.0'
# Cookie模板
COOKIE_TEMP = "nforum[UTMPUSERID]={username}; nforum[PASSWORD]={password_session}"

# 环境变量获取
USERNAME = os.environ['USERNAME']
PASSWORD_SESSION = os.environ['PASSWORD_SESSION']
try:
    CALLBACK_URL = os.environ['CALLBACK_URL']
except Exception as e:
    pass
try:
    ROOM_ID = os.environ['ROOM_ID']
except Exception as e:
    pass

# CN时间获取
BJ_TIME_NOW = datetime.utcnow().replace(tzinfo=timezone.utc).astimezone(timezone(timedelta(hours=8)))
TODAY = BJ_TIME_NOW.strftime('%Y-%m-%d')
YESTERDAY = (BJ_TIME_NOW.now() - timedelta(days=1)).strftime('%Y-%m-%d')


def fetch_one_page(idx):
    res = []
    fetch_flag = True
    cookie = COOKIE_TEMP.format(username=USERNAME, password_session=PASSWORD_SESSION)
    session = requests.Session()
    headers = {
        "User-Agent": USER_AGENT,
        "cookie": cookie,
        "x-requested-with": "XMLHttpRequest"
    }
    params = {
        "_uid": USERNAME,
        "p": str(index)
    }
    response = session.get(url=PART_TIME_JOB_URL, headers=headers, params=params)
    html = etree.HTML(response.text)
    len_trs = len(html.xpath('/html/body/div[3]/table/tbody//tr'))
    for i in range(len_trs):
        num = str(i + 1)
        base_url = "https://bbs.byr.cn"
        link = base_url + html.xpath('/html/body/div[3]/table/tbody/tr[' + num + ']/td[2]/a/@href')[0]
        title = html.xpath('/html/body/div[3]/table/tbody/tr[' + num + ']/td[2]/a/text()')[0]
        create_date = html.xpath('/html/body/div[3]/table/tbody/tr[' + num + ']/td[3]/text()')[0]
        update_date = html.xpath('/html/body/div[3]/table/tbody/tr[' + num + ']/td[6]/a/text()')[0]
        # 爬取范围：update_time为今天或昨天或第一页的帖子，每天9～10点爬
        # 选择：create_time为昨天的帖子
        # 注意：当天的帖子时间为'%H:%M:%S '，否则为'%Y-%m-%d'
        try:
            time.strptime(create_date, "%Y-%m-%d")
        except Exception as e:
            create_date = TODAY
        try:
            time.strptime(update_date, "%Y-%m-%d")
        except Exception as e:
            update_date = TODAY

        if idx != 1 and update_date != TODAY and update_date != YESTERDAY:
            fetch_flag = False

        if create_date == YESTERDAY:
            dic = {'title': title, 'link': link}
            res.append(dic)

    return res, fetch_flag


list_articles = []
flag = True
index = 1
while flag:
    # byr做了反爬的降级，连续发送请求会直接返空
    time.sleep(20)
    one_page_article, flag = fetch_one_page(index)
    list_articles += one_page_article
    index += 1

# build msg
callback_data = ''
callback_data += '{date} 兼职实习新贴:'.format(date=YESTERDAY) + os.linesep
for idx, article in enumerate(list_articles):
    callback_data += '{no}. {title} {link}'.format(no=str(idx + 1), title=article['title'], link=article['link'])
    callback_data += os.linesep

# send to wechat/xiaoniuren
try:
    requests.post(url=CALLBACK_URL, params={"msg": callback_data})
except Exception as e:
    logging.info("callback error")

# send to wechat/room
try:
    requests.post(url=CALLBACK_URL, json={
        "wxid": ROOM_ID,
        "content": callback_data
    })
except Exception as e:
    logging.info("callback error")
