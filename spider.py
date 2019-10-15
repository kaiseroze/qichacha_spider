# encoding:utf-8
# requests库用于爬取HTML页面，提交网络抓取
import requests
# xlwt模块针对Excel文件的创建、设置、保存
import xlwt
# 正则表达式模块
import re
import time
import random
from lxml import etree

from basic_info import export_basic_inf
from config import base_url, base_url1, enterprise_search_file, spider_timeout, spider_retry_num
from error_data import export_error_data
from proxy_ip import _proxy, is_internet
from headers import get_headers, get_proxy_headers
from partners import export_partners
from key_personnel import export_key_personnel


def export_excel(data,error_data):
    # 创建输出excel文件
    workbook = xlwt.Workbook(encoding="utf-8")
    # 导出企业基本信息
    if len(data) > 0:
        print("=======================================企业基本信息======================================")
        export_basic_inf(data, workbook)
        # 导出企业股东信息
        print("=======================================企业股东信息======================================")
        export_partners(data, workbook)
        # 导出企业主要人员
        print("=======================================企业主要人员======================================")
        export_key_personnel(data, workbook)
    # 导出抓取失败企业名称
    if len(error_data) > 0:
        print("=======================================导出抓取失败企业======================================")
        export_error_data(error_data, workbook)
    export_excel_name = '企业信息_' + str(int(time.time())) + '.xls'
    workbook.save(export_excel_name)

# 爬取目标页面重试
def get_retry(url,isProxy):
    response = None
    for i in range(spider_retry_num):
        print('请求{}超时，第{}次重复请求'.format(start_url, i + 1))
        if isProxy:
            proxy = _proxy()
            response = requests.get(url, headers=get_proxy_headers(proxy), proxies=proxy, timeout=spider_timeout)
        else:
            response = requests.get(url, headers=get_headers(), timeout=spider_timeout)
        if response.status_code == 200:
            break
    return response


# 去除重复的名称
def remove_repeat(list):
    list2 = []
    for i in list:
        name = i.replace('\n', '').replace(')', '）').replace('(', '（').strip()
        if '' != name and not name.isspace() and name not in list2:
            list2.append(name)
        elif '' != name and not name.isspace():
            print('存在重复企业名称==========={}'.format(name))
    # print(list2)
    return list2


if __name__ == '__main__':
    print('>>>>>>>>>>>>>>>>>>>启动企查查爬虫程序>>>>>>>>>>>>>>>>>>>')
    print('********************************************************')
    print('本程序运行条件：')
    print('1、请先确保本程序处于外网环境！')
    print('2、为防止企查查网站反爬，每次程序运行间隔不少于30分钟！')
    print('3、一次爬取企业数量建议不大于50条！')
    print('4、程序执行过程中请勿关闭！')
    print('********************************************************')

    if is_internet():
        is_proxy = 'n'
        # is_proxy = input("是否启用ip代理y/n？：")
        # 打开企业搜索文件
        f = open(enterprise_search_file, encoding='utf-8')
        enterprise_list = f.readlines()
        print('开始对文件进行重复检查......')
        _enterprise_list = remove_repeat(enterprise_list)
        print('企业总数============={}'.format(len(_enterprise_list)))
        # 定义查询结果集
        data_list = []
        # 定义查询结果异常集
        error_data_list = []
        # 增加重试连接次数
        requests.adapters.DEFAULT_RETRIES = 5
        # 关闭多余的连接
        s = requests.session()
        s.keep_alive = False
        for name in _enterprise_list:
            start_url = base_url + str(name)
            # print(start_url)
            try:
                print("正在抓取公司==========================={}".format(name))
                if is_proxy == 'y':
                    try:
                        proxy = _proxy()
                    except Exception as e:
                        print('========================请先启动ip代理程序=======================')
                        break
                    print('正在使用代理{}，抓取页面 {}'.format(proxy, start_url))
                    try:
                        response = requests.get(start_url, headers=get_proxy_headers(proxy), proxies=proxy, timeout=spider_timeout)
                    except requests.exceptions.Timeout as e:
                        response = get_retry(start_url,True)
                else:
                    try:
                        response = requests.get(start_url, headers=get_headers(), timeout=spider_timeout)
                    except requests.exceptions.Timeout as e:
                        response = get_retry(start_url, False)
                if response.status_code != 200:
                    error_data_list.append(name)
                    print("抓取页面 {}，异常 {} 可能被企查查网站反爬拦截了！".format(start_url, response.status_code))
                    continue
                _response = response.text
                # print("========================返回信息===========================")
                # print(_response)
                # content = etree.HTML(_response)
                # print(content)
                # 获取筛选信息链接
                search_url = re.findall('</div> <a href="(.*?)" class="a-decoration"> <div class="list-item"> <div class="list-item-top">',_response)
                if len(search_url) < 1:
                    print('该cookie被企查查网站反爬拦截了，需重新生成，请稍后再试！')
                    error_data_list.append(name)
                    continue
                print("获取筛选信息链接=============={}".format(search_url))
                url = base_url1 + search_url[0]
                # print(url)
                # print('*' * 100)
                time.sleep(random.randint(3, 10))  # 每隔3到10秒
                if is_proxy == 'y':
                    proxy = _proxy()
                    print('正在使用代理{}，抓取页面 {}'.format(proxy, url))
                    try:
                        response1 = requests.get(url, headers=get_proxy_headers(proxy), proxies=proxy, timeout=spider_timeout)
                    except requests.exceptions.Timeout as e:
                        response1 = get_retry(url, True)
                else:
                    try:
                        response1 = requests.get(url, headers=get_headers(), timeout=spider_timeout)
                    except requests.exceptions.Timeout as e:
                        response1 = get_retry(url, False)
                if response1.status_code != 200:
                    print("抓取页面 {}，异常 {} 可能被企查查网站反爬拦截了！".format(url, response1.status_code))
                    error_data_list.append(name)
                    continue
                _response1 = response1.text
                # print("========================返回信息===========================")
                # print(_response1)
                # content = etree.HTML(_response1)
                # print(content)
                data_list.append(_response1)
                print("{}=============抓取成功！".format(name))
            except Exception as e:
                print(name+'=========================抓取该公司的信息异常')
                error_data_list.append(name)
                print(str(e))
                continue
            time.sleep(random.randint(5, 20))   # 每隔5到20秒
        # 导出excel
        if len(data_list) > 0 or len(error_data_list) > 0:
            print('==================正在写入excel文件，请勿关闭程序！==================')
            export_excel(data_list,error_data_list)
        f.close()
    else:
        print('====================本程序只能在外网环境下运行====================')
    input('按任意键回车退出：')