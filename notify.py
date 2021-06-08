import requests
import time
import json
import pandas as pd
import datetime
from pyDes import *
import sys
import base64


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


# 若day为0，则返回当天值班，否则返回下一天值班
def get_person_on_duty(duty_csv, day):

    data = pd.read_csv(duty_csv)
    count = len(data)

    # 查找当前值班人员，on_duty=1
    person_on_duty = data.loc[data.on_duty == 1]

    # 获取人员信息
    name = person_on_duty["name"].values[0]
    id = person_on_duty["id"].values[0]
    mobile = person_on_duty["mobile"].values[0]

    if (day):
        if (id + 1 > count):
            next_id = 1
        else:
            next_id = id + 1

        next_person_on_duty = data.loc[data.id == next_id]

        name = next_person_on_duty["name"].values[0]
        id = next_person_on_duty["id"].values[0]
        mobile = next_person_on_duty["mobile"].values[0]
        return name, id, mobile
    else:
        return name, id, mobile


def is_trade_day(holiday_url, key):
    today = datetime.date.today().strftime('%Y-%m-%d')
    url = holiday_url + "?key=" + key + "&date=" + today
    result = requests.get(url)

    data = json.loads(result.text)

    print(data)

    if (data["newslist"][0]["isnotwork"] == 0
            and data["newslist"][0]["weekday"] != 6
            and data["newslist"][0]["weekday"] != 0):
        return 1
    else:
        return 0


def rotate_person_on_duty(duty_csv):
    data = pd.read_csv(duty_csv)
    current_id = get_person_on_duty(duty_csv, 0)[1]
    next_id = get_person_on_duty(duty_csv, 1)[1]

    data.loc[data.id == current_id, "on_duty"] = 0
    data.loc[data.id == next_id, "on_duty"] = 1

    data.to_csv("duty.csv", index=False)


def get_cst_time(time_url, key):
    url = time_url + "?key=" + key + "&city=上海"
    result = requests.get(url)

    data = json.loads(result.text)

    date_time = time.strptime(data["newslist"][0]["strtime"],
                              "%Y-%m-%d %H:%M:%S")
    if date_time.tm_hour > 15:
        return True
    else:
        return False


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

    if (is_trade_day(holiday_url, tianapi_key)):
        # 获取今日和次交易日值班人员信息
        name_today, id_today, mobile_today = get_person_on_duty(duty_csv, 0)
        name_tomorrow, id_tomorrow, mobile_tomorrow = get_person_on_duty(
            duty_csv, 1)

        # 解码手机号用于@指定人员

        mobile_today = base64.b64decode(mobile_today).decode()
        mobile_tomorrow = base64.b64decode(mobile_tomorrow).decode()

        # 钉钉提醒
        getDingMes(dingtalk_url + dingtalk_key, name_today, mobile_today,
                   name_tomorrow, mobile_tomorrow)

        if (get_cst_time(time_url, tianapi_key)):
            # 更新值班人员csv
            rotate_person_on_duty(duty_csv)
    else:
        print("today is not a trade day")
