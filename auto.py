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

# 爬取板块list，后续可以动态添加
FETCH_LIST = {
    'PART_TIME_JOB': {'name': '兼职实习', 'url': 'https://bbs.byr.cn/board/ParttimeJob'},
    'JOB_INFO': {'name': '招聘信息', 'url': 'https://bbs.byr.cn/board/JobInfo', 'title_keywords': ['实习', '麦吉太文']},
    # add here...
}

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
    WeChat_ID_LIST = os.environ['WeChat_ID_LIST'].split(',', -1)
except Exception as e:
    pass

# CN时间获取
BJ_TIME_NOW = datetime.utcnow().replace(tzinfo=timezone.utc).astimezone(timezone(timedelta(hours=8)))
TODAY = BJ_TIME_NOW.strftime('%Y-%m-%d')
YESTERDAY = (BJ_TIME_NOW.now() - timedelta(days=1)).strftime('%Y-%m-%d')


def is_hit_keyword(title, title_keywords):
    """
        判断title是否包含任意keyword
        :param title: 帖子标题
        :param title_keywords: keyword的list 为空表示所有标题都可
        :return: bool
    """
    if not title_keywords:
        return True
    else:
        for keyword in title_keywords:
            if keyword in title:
                return True
        return False


def fetch_one_page(url, page_num, title_keywords=[]):
    """
        目前只查昨天的文章
        :param url: 爬取url
        :param page_num: 第几页
        :param title_keywords:  默认[]表示获取所有帖子, 不为空list表示只获取标题包含该特定关键词的帖子
        :return: res-结果list, last_flag-当前page是否是是最后一页
    """
    res = []
    last_flag = False
    cookie = COOKIE_TEMP.format(username=USERNAME, password_session=PASSWORD_SESSION)
    session = requests.Session()
    params = {
        "_uid": USERNAME,
        "p": str(page_num)
    }
    headers = {
        "User-Agent": USER_AGENT,
        "cookie": cookie,
        "x-requested-with": "XMLHttpRequest"
    }
    response = session.get(url=url, headers=headers, params=params)
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

        if page_num != 1 and update_date != TODAY and update_date != YESTERDAY:
            last_flag = True

        if create_date == YESTERDAY:
            if is_hit_keyword(title, title_keywords):
                dic = {'title': title, 'link': link}
                res.append(dic)

    return res, last_flag


def fetch_one_module(module_url, title_keywords=[]):
    res = []
    end_flag = False
    idx = 1
    start_time = time.time()
    while not end_flag:
        # byr做了反爬的降级，连续发送请求会直接返空
        time.sleep(20)

        # 防止死循环
        current_time = time.time()
        if current_time - start_time > 10 * 60:
            break

        # 获取单页数据并拼接
        one_page_article, end_flag = fetch_one_page(module_url, idx, title_keywords)
        res += one_page_article
        idx += 1
    return res


def build_msg_one_module(list_articles, module_name, title_keywords=[]):
    res = '{date} {module_name}新帖:'.format(date=YESTERDAY, module_name=module_name) + os.linesep
    if title_keywords:
        res += '标题中包含关键词'
        for keyword in title_keywords:
            res += '"' + keyword + '"'
        res += os.linesep
    for idx, article in enumerate(list_articles):
        res += '{no}. {title} {link}'.format(no=str(idx + 1), title=article['title'], link=article['link'])
        res += os.linesep
    return res


###############################################################################
# 执行
###############################################################################
# 设置log
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(filename)s:%(lineno)s - %(message)s')

for key in FETCH_LIST.keys():
    # get meta_info
    name = FETCH_LIST[key]['name']
    url = FETCH_LIST[key]['url']
    title_keywords = FETCH_LIST[key].get('title_keywords', [])

    # 爬取 & 构造数据
    list_articles = fetch_one_module(url, title_keywords)
    msg = build_msg_one_module(list_articles, name, title_keywords)

    # send to wechat
    try:
        for room_id in WeChat_ID_LIST:
            requests.post(url=CALLBACK_URL, json={
                "wxid": room_id,
                "content": msg
            })
    except Exception as e:
        logging.info(name + "板块 callback error")

    logging.info(name + "板块 callback success")
