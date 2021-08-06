import requests
import time
import json
import pandas as pd
import datetime
import sys
import base64
from random import *


# 调用dingtalk hook发出通知
def getDingMes(dingtalk_url, name_today, mobile_today, name_tomorrow,
               mobile_tomorrow):

    baseUrl = dingtalk_url

    HEADERS = {"Content-Type": "application/json ;charset=utf-8 "}

    message_today = "上海A股交易市场韭菜管理员王阿姨提醒您，今日值班人员：" + name_today + "，"
    message_tomorrow = "次交易日值班人员：" + name_tomorrow + "。"
    # 使用手机号@指定人员，若isAtAll为true，则@指定人员配置失效
    stringBody = {
        "msgtype": "text",
        "text": {
            "content": message_today + message_tomorrow
        },
        "at": {
            "atMobiles": [mobile_today, mobile_tomorrow],
            "isAtAll": False
        }
    }

    print(stringBody)

    MessageBody = json.dumps(stringBody)
    result = requests.post(url=baseUrl, data=MessageBody, headers=HEADERS)
    print(result.text)


# 若day为0，则返回当天值班人员id，若day为1，则返回下一日值班人员id
def get_person_id_on_duty(duty_csv, day):

    data = pd.read_csv(duty_csv)
    count = len(data)

    if not day:
        # 查找当前值班人员，on_duty=1
        person_on_duty = data.loc[data.on_duty == 1]

        return person_on_duty['id'].values[0]
    else:
        # 查找下一日值班人员，on_duty=2
        person_on_duty = data.loc[data.on_duty == 2]

        return person_on_duty['id'].values[0]


def get_csv_len(duty_csv):
    data = pd.read_csv(duty_csv)
    return len(data)


# 判断是否为交易日
def is_trade_day(holiday_url, key):
    today = datetime.date.today().strftime('%Y-%m-%d')
    url = holiday_url + "?key=" + key + "&date=" + today
    result = requests.get(url)

    data = json.loads(result.text)

    print(data)

    if (data["newslist"][0]["isnotwork"] == 0
            and data["newslist"][0]["weekday"] != 6
            and data["newslist"][0]["weekday"] != 0):
        return True
    else:
        return False


def get_weekday(holiday_url, key):
    today = datetime.date.today().strftime('%Y-%m-%d')
    url = holiday_url + "?key=" + key + "&date=" + today
    result = requests.get(url)

    data = json.loads(result.text)

    print(data)

    return data["newslist"][0]["weekday"]


# 轮转csv文件内容
# 旧版
def rotate_person_on_duty(duty_csv):
    data = pd.read_csv(duty_csv)
    current_id = get_person_on_duty(duty_csv, 0)[1]
    next_id = get_person_on_duty(duty_csv, 1)[1]

    data.loc[data.id == current_id, "on_duty"] = 0
    data.loc[data.id == next_id, "on_duty"] = 1

    data.to_csv("duty.csv", index=False)


# 轮转csv文件内容
# on_duty=0，本周未值班
# on_duty=1，当日值班
# on_duty=2，下日值班
# on_duty=3，本周已值过班
# on_duty=4，本周刚值过班
def rotate_person_on_duty_random(duty_csv):
    data = pd.read_csv(duty_csv)

    data.loc[data.on_duty == 4, "on_duty"] = 3
    data.loc[data.on_duty == 1, "on_duty"] = 4
    data.loc[data.on_duty == 2, "on_duty"] = 1

    # 将周五状态为5的值重新置为1
    data.loc[data.on_duty == 5, "on_duty"] = 1

    if len(data.loc[data.on_duty > 0]) == len(data):
        data.loc[data.on_duty == 3, "on_duty"] = 0
        data.to_csv("duty.csv", index=False)

    id_tomorrow = get_person_id_on_duty_random(duty_csv)

    data.loc[data.id == id_tomorrow, "on_duty"] = 2

    data.to_csv("duty.csv", index=False)


# 获取cst时区小时，用于轮转csv文件内容，大于14点返回true
def get_cst_time(time_url, key):
    url = time_url + "?key=" + key + "&city=上海"
    result = requests.get(url)

    data = json.loads(result.text)

    date_time = time.strptime(data["newslist"][0]["strtime"],
                              "%Y-%m-%d %H:%M:%S")
    if date_time.tm_hour > 14:
        return True
    else:
        return False


# 随机返回当前未值班人员id，若无未值班人员，则将所有已值班人员 on_duty=3 修改为 on_duty=0
def get_person_id_on_duty_random(duty_csv):
    data = pd.read_csv(duty_csv)
    count = len(data)

    # 查找当前未值班人员

    person_not_on_duty = data.loc[data.on_duty == 0]

    # 随机选择当前未值班人数的id
    index_nextday = randint(0, len(person_not_on_duty) - 1)

    person_on_duty = person_not_on_duty.iloc[index_nextday]

    return (person_on_duty['id'])


# 返回用户名，手机号
def get_person_info_by_id(id):
    data = pd.read_csv(duty_csv)
    return data.loc[data.id == id]['name'].values[0], base64.b64decode(
        data.loc[data.id == id]['mobile'].values[0]).decode()


# 将on_duty非1全清零
def init_csv(duty_csv):
    data = pd.read_csv(duty_csv)

    # 周五清除状态前，先将当日值班==1，暂时修改为5，防止被rotate置为4
    # 在rotate中重新修改为1，即值班池中去除周五当日值班人员
    data.loc[data.on_duty == 1, "on_duty"] = 5

    # 此处将非5的状态全清空，用于在rotate中提供值班池随机生成下周一值班
    data.loc[data.on_duty != 5, "on_duty"] = 0
    data.to_csv("duty.csv", index=False)


# 将on_duty非2的值清零
def init_csv_2(duty_csv):
    data = pd.read_csv(duty_csv)

    data.loc[data.on_duty != 2, "on_duty"] = 0
    data.to_csv(duty_csv, index=False)


# 获取偏移量
def get_offset(offset):
    with open(offset, 'r') as fp:
        value = fp.read()
        value_offset = int(value)
        return value_offset


def rotate_offset(offset):
    with open(offset, "r+") as fp:
        value = fp.read()
        new_offset = int(value) + 1
        fp.seek(0)
        fp.truncate()
        fp.write(str(new_offset))


if __name__ == '__main__':

    # 钉钉webhook地址
    dingtalk_url = "https://oapi.dingtalk.com/robot/send?access_token="

    # 钉钉webhook接口key
    dingtalk_key = sys.argv[1]

    # 节假日API
    holiday_url = "http://api.tianapi.com/txapi/jiejiari/index"

    # 世界时间API
    time_url = "http://api.tianapi.com/txapi/worldtime/index"

    # API接口key
    tianapi_key = sys.argv[2]

    # csv文件路径
    duty_csv = "duty.csv"
    offset_file = 'offset'

    WEEKDAY = get_weekday(holiday_url, tianapi_key)
    OFFSET = get_offset(offset_file)
    CSV_LEN = get_csv_len(duty_csv)

    # 周五早上，更新偏移值
    if (WEEKDAY == 5 and not get_cst_time(time_url, tianapi_key)):
        rotate_offset(offset_file)

    # 若为周五，取今日值班时，因早上offset已更新，所以取今日值班人员id时需减1，即使用本周的offset获取
    # 周五取下个值班人员id时需加1
    if (is_trade_day(holiday_url, tianapi_key)):

        id_today = (WEEKDAY + OFFSET) % CSV_LEN
        id_nextday = (WEEKDAY + 1 + OFFSET) % CSV_LEN
        if (WEEKDAY == 5):
            OFFSET = get_offset(offset_file)
            id_today = (WEEKDAY + OFFSET - 1) % CSV_LEN
            id_nextday = (1 + OFFSET) % CSV_LEN

        # 取余时处理余数可能为0，存在id越界的情况，此处对id加1获取真实id
        id_today = id_today + 1
        id_nextday = id_nextday + 1
        print("weekday: %d, offset: %d, csv_len: %d" %
              (WEEKDAY, OFFSET, CSV_LEN))
        print("id today: %d,id nextday: %d" % (id_today, id_nextday))

        # 获取今日和次交易日值班人员信息
        name_today, mobile_today = get_person_info_by_id(id_today)
        name_tomorrow, mobile_tomorrow = get_person_info_by_id(id_nextday)

        # 钉钉提醒
        getDingMes(dingtalk_url + dingtalk_key, name_today, mobile_today,
                   name_tomorrow, mobile_tomorrow)

    else:
        print("today is not a trade day")
