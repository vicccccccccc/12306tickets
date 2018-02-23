#!/usr/bin/python
# -*- coding:utf-8 -*-
# Python Mail for chenglee
# if fileformat=dos, update fileformat=unix
# code:set fileformat=unix
# check:set ff ?
import smtplib
from email.mime.text import MIMEText
from email.utils import formataddr

class Sender(object):
    my_name = ''
    my_sender = ''  # 发件人邮箱账号
    my_pass = ''  # 发件人邮箱密码(当时申请smtp给的口令)
    my_user = ''  # 收件人邮箱账号

    def mail(self, user):
        ret = True

        msg=MIMEText('抢票成功！%s' % user,'plain','utf-8')
        msg['From']=formataddr([self.my_name,self.my_sender])  # 括号里的对应发件人邮箱昵称、发件人邮箱账号
        msg['To']=formataddr(["收件人昵称",self.my_user])              # 括号里的对应收件人邮箱昵称、收件人邮箱账号
        msg['Subject']="抢票成功！" + user               # 邮件的主题，也可以说是标题
        try:
            smtpObj = smtplib.SMTP_SSL("smtp.qq.com", 465)
            smtpObj.login(self.my_sender, self.my_pass)
            smtpObj.sendmail(self.my_sender, self.my_user, msg.as_string())
            smtpObj.quit()
            print("Successfully sent email")
        except Exception:
            print ("Error: unable to send email")
            ret = False

        return ret

if __name__ == '__main__':
    sender_obj = Sender()
    result = sender_obj.mail('chendanjie')
    if result:
        print(u"邮件发送成功")
    else:
        print(u"邮件发送失败")
