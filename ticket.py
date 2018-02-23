# coding: utf-8

"""Train ticket query via command-line.


Usage:
    tickets [-gdtkz] <from> <to> <date>
    
    
Options:
    -h,--help       显示帮助菜单
    -g              高铁
    -d              动车
    -t              特快
    -k              快速
    -z              直达
    
"""

from docopt import docopt
from stations import cities, stations, sit
from time import sleep
from prettytable import PrettyTable
import requests
import threading
from apscheduler.schedulers.background import BackgroundScheduler
import traceback

import time, sys, os
import sentEmail
import re
from splinter.browser import Browser


class get_ticket(object):
    login_status = False
    driver_name = ''
    executable_path = ''
    # 用户名，密码
    username = u""
    passwd = u""
    # cookies
    starts = u"%u4E0A%u6D77%2CSHH"
    ends = u"%u592A%u539F%2CTYV"
    # 时间格式2018-01-19
    dtime = u"2018-01-19"
    # type
    type = ''
    # 车次，0则从上之下依次点击
    order = 0
    ###乘客名
    users = []
    ##席位
    xb = u"二等座"
    pz = u"成人票"
    #抢票失败，则重新开启抢票
    is_fail = True
    #默认选择时间范围
    starttime = 8
    endtime = 24
    #默认抢票时间间隔
    duration = 1.5

    info = ''

    count = 0

    """网址"""
    ticket_url = "https://kyfw.12306.cn/otn/leftTicket/init"
    login_url = "https://kyfw.12306.cn/otn/login/init"
    initmy_url = "https://kyfw.12306.cn/otn/index/initMy12306"
    buy = "https://kyfw.12306.cn/otn/confirmPassenger/initDc"
    login_url = 'https://kyfw.12306.cn/otn/login/init'

    def cli(self):
        arguments = docopt(__doc__)
        from_station = stations.get(arguments['<from>'])
        to_station = stations.get(arguments['<to>'])
        date = arguments['<date>']
        url = 'https://kyfw.12306.cn/otn/leftTicket/queryZ?leftTicketDTO.train_date={}' \
              '&leftTicketDTO.from_station={}' \
              '&leftTicketDTO.to_station={}' \
              '&purpose_codes=ADULT'.format(
            date, from_station, to_station
        )

        r = requests.get(url, verify=False)
        rows = r.json()['data']['result']
        station_map = r.json()['data']['map']

        headers = '车次 车站 时间 历时 商务 一等 二等 软卧 硬卧 软座 硬座 无座'.split()
        pt = PrettyTable()
        pt._set_field_names(headers)
        for row in rows:
            fields = row.split('|')
            pretty_row = []
            # checi
            pretty_row.append(fields[3])
            # chezhan
            pretty_row.append(station_map[fields[6]] + '-' + station_map[fields[7]])
            # time
            pretty_row.append(fields[8] + '-' + fields[9])
            # duration
            pretty_row.append(fields[10])
            # business
            pretty_row.append(fields[30])
            # first_class
            pretty_row.append(fields[31])
            # second_class
            pretty_row.append(fields[32])
            # ruan wo
            pretty_row.append(fields[23])
            # ruan zuo
            pretty_row.append(fields[24])
            # ying wo
            pretty_row.append(fields[28])
            # ying zuo
            pretty_row.append(fields[29])
            # wuzuo
            pretty_row.append(fields[26])

            pt.add_row(pretty_row)

        print(pt)

    def __init__(self):
        self.driver_name = 'chrome'
        self.executable_path = '/usr/local/bin/chromedriver'

    def login(self):
        self.driver.visit(self.login_url)
        sleep(1)
        # 填充密码
        fill_success = True
        while fill_success:
            try:
                self.driver.fill("loginUserDTO.user_name", self.username)
                # sleep(1)
                self.driver.fill("userDTO.password", self.passwd)
                fill_success = False
                print(u"等待验证码，自行输入...")
            except:
                print("无法填入账号密码！")

        while True:
            if self.driver.url != self.initmy_url:
                sleep(1)
            else:
                self.login_status = True
                break

    def working(self):
        try:
            self.driver.visit(self.ticket_url)
            print(u"购票页面开始...")
            # 加载查询信息
            self.driver.cookies.add({"_jc_save_fromStation": self.starts})
            self.driver.cookies.add({"_jc_save_toStation": self.ends})
            self.driver.cookies.add({"_jc_save_fromDate": self.dtime})
            self.driver.cookies.add({"_jc_save_wfdc_flag": "dc"})
            self.driver.reload()

            # 选择车次类型
            for i in self.type:
                self.driver.find_by_xpath("//input[@value='%s']" % i).click()

            # 只显示可购买车次
            self.driver.find_by_xpath("//input[@id='%s']" % 'avail_ticket').click()

            sleep(1)

            while self.driver.url == self.ticket_url:

                if not self.login_status:
                    return

                self.driver.find_by_text(u"查询").click()
                self.count += 1
                print(u"已抢票... 第 %s 次" % self.count)
                try:
                    # SWZ－特等座，ZY－一等座， ZE－二等座
                    # class_type = self.driver.find_by_xpath("//tbody[@id = 'queryLeftTable']/tr/td[starts-with(@id,%s)]/div" % 'ZE')
                    # 商务座=2，一等座=3， 二等座=4
                    # class_type = self.driver.find_by_xpath("//tbody[@id = 'queryLeftTable']/tr/td[%d]/div" % 4)
                    enable_buttons = self.driver.find_by_xpath("//tbody[@id = 'queryLeftTable']/tr/td/a[contains(text(),'预订')]")
                    self.qulifier(enable_buttons)

                except Exception as e:
                    print(e)
                    print(u"界面出错，重新开始抢票 %s" % self.count)
                    continue

            # print(u"开始预订...")
            # self.driver.reload()
            print(u'开始选择用户...')
            for user in self.users:
                self.driver.find_by_text(user).last.click()

            print(u"提交订单...")
            self.driver.find_by_id('submitOrder_id').click()
            sleep(0.5)

            #判断是否票已被抢
            if self.driver.find_by_xpath("//p[@id = 'sy_ticket_num_id']/font[starts-with(text(),'目前排队人数已经超过余票张数')]").__len__() > 0:
                return
            elif int(re.sub("\D", "", self.driver.find_by_xpath("//p[@id = 'sy_ticket_num_id']").text)) == 0:
                return

            #发送邮件
            _thread = threading.Thread(target=self.play_sound)
            _thread.setDaemon(True)
            _thread.start()  # 启动线程

            #可能需要验证码
            self.driver.find_by_id('qr_submit_id').click()
            sleep(2)
            if self.driver.find_by_xpath("//div[@class = 'tit'][contains(text(),'失败')]").__len__() > 0:
                return
            else:
                self.is_fail = False

        except Exception as e:
            print(e)

    def qulifier(self, check_buttons):
        tr_obj = self.driver.find_by_xpath("//tbody[@id = 'queryLeftTable']/tr/td/a[contains(text(),'预订')]/../..")
        for index, value in enumerate(check_buttons):
            # tr_info = tr_obj[index].text.split('\n')
            tr_info = re.split(' |\n', tr_obj[index].text)
            timehour = int(tr_info[3].split(':')[0])
            train_num = tr_info[0]

            is_class_qulify = False
            for i in self.type:
                for j in sit[i]:
                    if tr_info[j] != '无' and tr_info[j] != '--':
                        is_class_qulify = True
                        print(" ".join(tr_info))
                        break

            if not is_class_qulify:
                continue

            # 判断时间是否符合要求
            if self.starttime <= timehour <= self.endtime:
                print(train_num)
                find_button = self.driver.find_by_xpath(
                    "//tbody[@id = 'queryLeftTable']/tr[starts-with(@id,'ticket')][contains(@id,'%s')]/td/a[contains(text(),'预订')]" % train_num)
                if find_button.__len__() > 0:
                    find_button.click()
                else:
                    self.driver.find_by_xpath(
                        "//tbody[@id = 'queryLeftTable']/tr[starts-with(@id,'ticket')]/td/a[contains(text(),'预订')]")[0].click()

                self.info = tr_info
                sleep(0.5)
                return True
                # break

        sleep(self.duration)
        return False

    def start(self):
        self.driver = Browser(driver_name=self.driver_name)
        self.driver.driver.set_window_size(1400, 1000)
        # self.login()

        # 开启定时任务监听是否退出登陆
        scheduler = BackgroundScheduler()
        scheduler.add_job(self.watch_login, 'interval', minutes=3)
        scheduler.start()

        while self.is_fail:
            # 判断是否为登陆状态
            if self.login_status:
                self.working()
            else:
                self.login()
                self.working()

        print(u"确认选座...")


    def play_sound(self):
        sender_obj = sentEmail.Sender()
        result = sender_obj.mail(self.users[0] + " ".join(self.info))
        # os.system("say bingo. come to get your ticket!")

    # 监听是否为登陆状态
    def watch_login(self):
        print("start mission")
        start_watch = True
        while start_watch:
            try:
                if self.driver._cookie_manager.all().__contains__('tk'):
                    print("----------登陆-----------")
                    self.login_status = True
                else:
                    if self.driver.find_by_xpath("//a[@id = 'login_user'][contains(text(),'登录')]").__len__() > 0:
                        print("----------未登录---------")
                        self.login_status = False
                        # 发邮件通知登录状态以退出
                        sender_obj = sentEmail.Sender()
                        result = sender_obj.mail("登录状态以退出")

                start_watch = False
            except Exception as e:
                print(e)
                start_watch = True

        print("end mission")


if __name__ == '__main__':
    ticket = get_ticket()

    try:
        if (sys.argv[1][0] == '-'):
            ticket.type = sys.argv[1][1:].upper()
            ticket.starts = cities[sys.argv[2]]
            ticket.ends = cities[sys.argv[3]]

            argv_time = sys.argv[4].split(',')
            ticket.dtime = argv_time[0]
            if len(argv_time) > 1:
                ticket.duration = float(argv_time[1])

            ticket.users.append(sys.argv[5])
            if len(sys.argv) > 6:
                ticket.starttime = int(sys.argv[6])
                ticket.endtime = int(sys.argv[7])
        else:
            ticket.starts = cities[sys.argv[1]]
            ticket.ends = cities[sys.argv[2]]

            argv_time = sys.argv[3].split(',')
            ticket.dtime = argv_time[0]
            if len(argv_time) > 1:
                ticket.duration = float(argv_time[1])

            ticket.users.append(sys.argv[4])
            if len(sys.argv) > 5:
                ticket.starttime = int(sys.argv[5])
                ticket.endtime = int(sys.argv[6])

    except Exception as e:
        print(e)
        print('输入参数不正确！')

    ticket.start()
    # ticket.cli()
