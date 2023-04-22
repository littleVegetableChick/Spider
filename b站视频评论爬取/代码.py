#-*-coding:utf-8-*-

import urllib
import requests
import json
import xlwt
import time
import re
from multiprocessing.dummy import Pool

#视频链接列表
video_url_list=[]
#视频链接和标题字典
title_dic={}
#第几个视频
c=0
#行
k=0
headers={
        'cookie': "nostalgia_conf=-1; _uuid=B71D4975-83E6-86F8-6C68-4118DC43A87A72641infoc; buvid4=A7A0D047-8EAA-F4DB-A270-90086CA701BD76321-022092917-aXhbnnGQBgDZEwAADzV9wA==; b_nut=1664442775; buvid3=AAA14238-D475-CA4A-6205-8DFE95B01E7D76321infoc; CURRENT_FNVAL=4048; i-wanna-go-back=-1; rpdid=|(JJmY)YRuYR0J'uYYm|~)~J|; buvid_fp_plain=undefined; fingerprint=27c45b61e890f8003b75a370dd6d8ca3; header_theme_version=CLOSE; buvid_fp=27c45b61e890f8003b75a370dd6d8ca3; home_feed_column=5; bsource=search_baidu; FEED_LIVE_VERSION=V8; CURRENT_PID=b66a9200-de79-11ed-a2a9-c1654fb07034; bp_video_offset_302217057=785549424155689000; b_ut=5; SESSDATA=89d8709c,1697456691,89d1e*42; bili_jct=2d801615e352b7cd8eac946da2ff3eae; DedeUserID=302217057; DedeUserID__ckMd5=62fe74e5334df5d7; sid=5ixbiimf; innersign=1; b_lsid=861031247_1879D294699; Hm_lvt_d7c7037093938390bc160fc28becc542=1681969065; PVID=3; Hm_lpvt_d7c7037093938390bc160fc28becc542=1681970151",
        'origin': 'https://search.bilibili.com',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36'
    }
#搜索页面视频信息的模板
s_url = "https://api.bilibili.com/x/web-interface/wbi/search/type?__refresh__=true&_extra=&context=&page=%d&page_size=42&from_source=&from_spmid=333.337&platform=pc&highlight=1&single_column=0&keyword=%s&qv_id=O4ABtuSQIcLMoKc8KgXhUTxNol68tSzh&ad_resource=5654&source_tag=3&gaia_vtoken=&category_id=&search_type=video&dynamic_offset=%d"
#excel保存地址
savepath = ".\\bilibli.xls"
#创建Excel
book = xlwt.Workbook(encoding='utf-8', style_compression=0)
#创建工作簿
sheet = book.add_sheet('bilibli_comment', cell_overwrite_ok=True)
#写入标题
col = ['视频名称','视频链接','用户名', '用户评论']
for i in range(4):
    sheet.write(0, i, col[i])

#获取请求评论链接的oid
def getAid(url):
    response = requests.get(url)
    t = response.text
    a = re.compile(r'.*window.__INITIAL_STATE__={"aid":(\d*?),"bvid":.*')
    aid = a.findall(t)[0]
    r_c=r'.*?"aid":'+aid+'.*?"reply":(\d*?),"favorite":\d*?,"coin".*'
    total_reply=re.compile(r_c)
    total_comment=int(total_reply.findall(t)[0])
    # print("成功获得Aid！")
    return aid,total_comment

#获得评论
def getComment(url):
    global c
    global k
    i=1
    c = c + 1
    count = c
    flag=True
    print("正在爬取第%d个视频"%count)
    oid,total_comment = getAid(url)
    #第二级别评论的请求链接模板
    reply_url_template="https://api.bilibili.com/x/v2/reply/reply?csrf=ade864a738201b7d655c4dc80fd25b01&oid=%s&pn=%d&ps=10&root=%s&type=1"
    # print("总评论数：%d"%total_comment)
    while True:
        try:
            # 第一级别评论的请求链接模板，模板的root的值可以用rpid的值替换
            comment_url = "https://api.bilibili.com/x/v2/reply/main?csrf=2d801615e352b7cd8eac946da2ff3eae&mode=3&next=%d&oid=%s&plat=1&seek_rpid=&type=1"
            comment_url=format(comment_url%(i,oid))
            #请求的第一级别评论链接
            response=requests.get(url=comment_url,headers=headers)
            json_data=response.json()
            if flag:
                # 爬取置顶一级评论
                if json_data['data']['top']['upper']:
                    k=k+1
                    sheet.write(k,0,title_dic[url])
                    sheet.write(k, 1, url)
                    sheet.write(k, 2, json_data['data']['top']['upper']['member']['uname'])
                    sheet.write(k, 3, json_data['data']['top']['upper']['content']['message'])
                    # print("爬取第%d条评论" % k)
                    pn=1
                    # 爬取置顶二级评论
                    while 1:
                        root = json_data['data']['top']['upper']['rpid']
                        reply_url=format(reply_url_template%(oid,pn,root))
                        r_response = requests.get(reply_url)
                        r_json_data = r_response.json()
                        if r_json_data['data']['replies'] is None:
                            break
                        for g in range(len(r_json_data['data']['replies'])):
                            k = k + 1
                            sheet.write(k, 0, title_dic[url])
                            sheet.write(k, 1, url)
                            sheet.write(k, 2, r_json_data['data']['replies'][g]['member']['uname'])
                            sheet.write(k, 3, r_json_data['data']['replies'][g]['content']['message'])
                            # print("爬取第%d条评论" % k)
                        flag=False
                        if not len(r_json_data['data']['replies']):
                            break
                        pn=pn+1
            #爬取非置顶的一级评论
            n=len(json_data['data']['replies'])
            if n==0:
                book.save(savepath)
                print("爬取第%d视频成功!"%count)
                break
            for j in range(n):
                k=k+1
                sheet.write(k, 0, title_dic[url])
                sheet.write(k, 1, url)
                sheet.write(k,2,json_data['data']['replies'][j]['member']['uname'])
                sheet.write(k,3,json_data['data']['replies'][j]['content']['message'])
                # 爬取非置顶的二级评论
                root = json_data['data']['replies'][j]['rpid']
                pn = 1
                while 1:
                    reply_url = format(reply_url_template % (oid, pn, root))
                    r_response = requests.get(reply_url)
                    r_json_data = r_response.json()
                    if r_json_data['data']is not None and r_json_data['data']['replies'] is not None:
                        for g in range(len(r_json_data['data']['replies'])):
                            k = k + 1
                            sheet.write(k, 0, title_dic[url])
                            sheet.write(k, 1, url)
                            sheet.write(k, 2, r_json_data['data']['replies'][g]['member']['uname'])
                            sheet.write(k, 3, r_json_data['data']['replies'][g]['content']['message'])
                            # print("爬取第%d条评论" % k)
                    else:
                        break
                    pn = pn + 1
            i=i+1
            time.sleep(0.5)
        except TimeoutError:
            print("请求超时！")
            book.save(savepath)
            break

#获取搜索页面所有视频的链接
def search(url):
    k = 0
    page = 0
    print("输入你要爬取视频的关键字：")
    keyword = input()
    while page <= 0 or page >= 43:
        print("输入你要爬取的搜索页总数：")
        page = int(input())
    #将获取搜索页视频链接的api补充完整
    for p in range(1, page + 1):
        url = s_url
        url = format(url % (p, keyword, (p - 1) * 24))
        url_list = []
        try:
            response = requests.get(url=url, headers=headers)
            jason_data = response.json()
            for j in range(24):
                video_url=jason_data['data']['result'][j]['arcurl']
                video_url_list.append(video_url)
                title = jason_data['data']['result'][j]['title'].replace('<em class="keyword">', '')
                title = title.replace('</em>', '')
                title = title.strip()
                title_dic[video_url]=title
                print(title)
                k = k + 1
            time.sleep(1)
        except TimeoutError:
            print("爬取失败！")

if __name__=='__main__':
    start_time=time.time()
    search(s_url)
    #创建多线程
    pool=Pool(5)
    print("获取视频链接成功!")
    print("进入爬取评论")
    pool.map(getComment,video_url_list)
    end_time=time.time()
    print("爬取完毕!")
    print("用时：%d秒"%(end_time-start_time))
