# -*- coding: utf-8 -*-
from urllib.parse import quote
from urllib.request import urlopen
from urllib.error import HTTPError
import json
import math
import time

x_pi = 3.14159265358979324 * 3000.0 / 180.0
pi = 3.1415926535897932384626
a = 6378245.0
ee = 0.00669342162296594323

def transformlat(lng, lat):
    ret = -100.0 + 2.0 * lng + 3.0 * lat + 0.2 * lat * lat + \
        0.1 * lng * lat + 0.2 * math.sqrt(math.fabs(lng))
    ret += (20.0 * math.sin(6.0 * lng * pi) + 20.0 *
            math.sin(2.0 * lng * pi)) * 2.0 / 3.0
    ret += (20.0 * math.sin(lat * pi) + 40.0 *
            math.sin(lat / 3.0 * pi)) * 2.0 / 3.0
    ret += (160.0 * math.sin(lat / 12.0 * pi) + 320 *
            math.sin(lat * pi / 30.0)) * 2.0 / 3.0
    return ret

def transformlng(lng, lat):
    ret = 300.0 + lng + 2.0 * lat + 0.1 * lng * lng + \
        0.1 * lng * lat + 0.1 * math.sqrt(math.fabs(lng))
    ret += (20.0 * math.sin(6.0 * lng * pi) + 20.0 *
            math.sin(2.0 * lng * pi)) * 2.0 / 3.0
    ret += (20.0 * math.sin(lng * pi) + 40.0 *
            math.sin(lng / 3.0 * pi)) * 2.0 / 3.0
    ret += (150.0 * math.sin(lng / 12.0 * pi) + 300.0 *
            math.sin(lng / 30.0 * pi)) * 2.0 / 3.0
    return ret
	
def bd09togcj02(bd_lon, bd_lat):
    x = bd_lon - 0.0065
    y = bd_lat - 0.006
    z = math.sqrt(x * x + y * y) - 0.00002 * math.sin(y * x_pi)
    theta = math.atan2(y, x) - 0.000003 * math.cos(x * x_pi)
    gg_lng = z * math.cos(theta)
    gg_lat = z * math.sin(theta)
    return [gg_lng, gg_lat]

def gcj02towgs84(lng, lat):
    dlat = transformlat(lng - 105.0, lat - 35.0)
    dlng = transformlng(lng - 105.0, lat - 35.0)
    radlat = lat / 180.0 * pi
    magic = math.sin(radlat)
    magic = 1 - ee * magic * magic
    sqrtmagic = math.sqrt(magic)
    dlat = (dlat * 180.0) / ((a * (1 - ee)) / (magic * sqrtmagic) * pi)
    dlng = (dlng * 180.0) / (a / sqrtmagic * math.cos(radlat) * pi)
    mglat = lat + dlat
    mglng = lng + dlng
    return [lng * 2 - mglng, lat * 2 - mglat]	

def gengeo(lattice_num, orig_lat1, orig_lng1, orig_lat2, orig_lng2):
    dataset = []
    for i_lat in range(0,int(lattice_num)):
        lat1 = orig_lat1 + ((orig_lat2 - orig_lat1) / int(lattice_num)) * i_lat
        lat2 = orig_lat1 + ((orig_lat2 - orig_lat1) / int(lattice_num)) * (i_lat + 1)
        for i_lng in range(0, int(lattice_num)):
            lng1 = orig_lng1 + ((orig_lng2 - orig_lng1) / int(lattice_num)) * i_lng
            lng2 = orig_lng1 + ((orig_lng2 - orig_lng1) / int(lattice_num)) * (i_lng + 1)
            lettice = [lat1, lng1, lat2, lng2]
            dataset.append(lettice)
    return dataset

def getinfo(query, lat1, lng1, lat2, lng2):
    global start_time
    global Your_App_Key
    url = 'http://api.map.baidu.com/place/v2/search?q=%s&bounds=%s,%s,%s,%s&page_size=20&page_num=0&output=json&' % (query, lat1, lng1, lat2, lng2) + 'ak=%s' % Your_App_Key
#    print(url)
    infos = json.loads(urlopen(url).read().decode('utf-8'))
#    print(infos)
    if infos["total"] == 400:
        is_go_on = 0
    elif infos["total"] == 0:
        print("There is nothing here.")
        is_go_on = 1
    else:
        for info in infos["results"]:
            true_location = gcj02towgs84(bd09togcj02(info["location"]["lng"], info["location"]["lat"])[0], bd09togcj02(info["location"]["lng"], info["location"]["lat"])[1])
            with open("D:\output%s.txt" % start_time, "at") as f:
                f.write("%s,%s,%s\n" % (info["name"],true_location[0],true_location[1]))
            print("Done with %s" % info["name"])
        page_num = 1
        while len(infos["results"]) == 20:
            url = 'http://api.map.baidu.com/place/v2/search?q=%s&bounds=%s,%s,%s,%s&page_size=20&page_num=%s&output=json&' % (query, lat1, lng1, lat2, lng2, page_num) + 'ak=%s' % Your_App_Key
#            print(url)
            infos = json.loads(urlopen(url).read().decode('utf-8'))
            for info in infos["results"]:
                true_location = gcj02towgs84(bd09togcj02(info["location"]["lng"], info["location"]["lat"])[0], bd09togcj02(info["location"]["lng"], info["location"]["lat"])[1])
                with open("D:\output%s.txt" % start_time, "at") as f:
                    f.write("%s,%s,%s\n" % (info["name"],true_location[0],true_location[1]))
                print("Done with %s" % info["name"])
            page_num = page_num +1
        is_go_on = 1
    return is_go_on

def get_poi(query, lattice_num, orig_lat1, orig_lng1, orig_lat2, orig_lng2):
    global start_time
    global Your_App_Key
    geos = gengeo(lattice_num, orig_lat1, orig_lng1, orig_lat2, orig_lng2)
    for geo in geos:
        try:
            go_on = getinfo(query, geo[0], geo[1], geo[2], geo[3])
            iter_num = 1
            if go_on == 0:
                go_on = get_poi(query, iter_num*3, geo[0], geo[1], geo[2], geo[3])
                iter_num = iter_num+1
        except HTTPError:
            print("Something went wrong, trying again in 10 seconds...")
            time.sleep(10)
            go_on = getinfo(query, geo[0], geo[1], geo[2], geo[3])
            iter_num = 1
            if go_on == 0:
                go_on = get_poi(query, iter_num*3, geo[0], geo[1], geo[2], geo[3])
                iter_num = iter_num+1
            continue

lattice_num = int(input('请输入分片数值：'))
#百度地图坐标拾取系统
#http://api.map.baidu.com/lbsapi/getpoint/index.html?c=
point1 = input('请输入左下角点坐标，经纬度以逗号隔开：')
point2 = input('请输入右上角点坐标，经纬度以逗号隔开：')
bound1 = point1.split(',') + (point2.split(','))
bound = [float(i) for i in bound1]
start_time = time.time()
Your_App_Key = "PutKeyHere"

with open("D:\output%s.txt" % start_time, "wt") as f:
    f.write('PLACE,LNG,LAT\n')

get_poi(quote(input("请输入查询关键字:"), safe='/:?=&'), lattice_num, bound[1], bound[0], bound[3], bound[2])