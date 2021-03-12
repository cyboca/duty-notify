import requests
import sqlite3
import json

def getDingMes(msg,dingtalk_url,mobile):

    baseUrl = dingtalk_url

    HEADERS = {
        "Content-Type": "application/json ;charset=utf-8 "
    }

    message = msg
    stringBody ={
        "msgtype": "text",
        "text": {"content": message},
        "at": {
            "atMobiles": [mobile],
               "isAtAll": False
        }
    }

    MessageBody = json.dumps(stringBody)
    result = requests.post(url=baseUrl, data=MessageBody, headers=HEADERS)
    print(result.text)

def get_dutyer(db):
    conn=sqlite3.connect(db)
    cur=conn.execute("select id from duty where on_duty=1")
    id=cur.fetchone()[0]
    print(id)


if __name__ == '__main__':
    dingtalk_url = "https://oapi.dingtalk.com/robot/send?access_token=17fdba4f02b202d42f93bd02ec6f40eeefa94fa0ac6d69887df26d56f8b551ca"
    db="F:\duty.db"
    hello_msg="上海A股交易所"
    manager="韭菜管理员王阿姨"
    person_on_duty="张三"
    mobile="+86-17826837146"


    msg=hello_msg+manager+"提醒您，今日值班人员："+person_on_duty
    # getDingMes(msg,dingtalk_url,mobile)
    get_dutyer(db)
