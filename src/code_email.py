from email.parser import BytesParser

import imaplib, email, datetime, re

from code_info import CodeInfo, CodeType
from utils import Utils

class CodeEmail:
    host = 'imap.xxx.net' # 目标邮箱服务器
    port = '993' # 目标邮箱端口
    username = '' # 你的邮箱账号
    password = '' # 你的邮箱密码或访问密钥
    sender = '' # 只获取指定发件人的邮件
    imap = None
    initially = True

    def __init__(self):
        imaplib.Commands['ID'] = ('AUTH')

    def login_if_not(self, force):
        if (self.initially or self.imap == None or force or self.noop() == False):
            try:
                self.imap = imaplib.IMAP4_SSL(host=self.host, port=int(self.port))
                self.imap.login(user=self.username, password=self.password)
                args = ("name","IMAPClient","contact","leever.zzz@gmail.com","version","1.0.0","vendor","myclient")
                self.imap._simple_command('ID', '("' + '" "'.join(args) + '")')
                self.initially = False
            except Exception as e:
                return e

    def noop(self):
        try:
            response, _ = self.imap.noop()
            return response == 'OK'
        except:
            return False

    @staticmethod
    def update_emails_cache(code_cache, new_code_list):
        if code_cache == None or len(code_cache) < 1:
            return new_code_list.copy()
        unique_code_list = set(code_cache) | set(new_code_list)
        return list(unique_code_list)
        
    def get_emails(self, code_cache):
        if self.imap is None:
            return ("接入邮箱失败，请联系管理员。", None)
        self.imap.select('inbox')

        if code_cache:
            latest_time = max(code_cache, key=lambda x:x.time).time
            latest_date = datetime.datetime.fromtimestamp(latest_time).strftime('%d-%b-%Y')
            query = f'(FROM "{self.sender}" SINCE "{latest_date}")'
        else:
            query = f'(FROM "{self.sender}")'
        typ_search, data = self.imap.search(None, query)
        print("===========================================")
        print("开始读取邮件：{}".format(query))
        #  数据格式 data =  [b'1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18']
        if typ_search != 'OK':
            return ("读取邮件失败，请联系管理员。", None)
        
        new_code_list = []
        if code_cache:
            code_times_set = {code.time for code in code_cache}

        for num in data[0].split():
            id = int(num)
            typ_fetch, content = self.imap.fetch(num, '(RFC822)')
            if typ_fetch != 'OK':
                print("ID{}：邮件读取失败被跳过...".format(id))
                continue

            msg = BytesParser().parsebytes(content[0][1])
            time = self.get_email_date(email.header.decode_header(msg.get('Date')))

            if code_cache:
                if time in code_times_set:
                    continue # 跳过已缓存邮件

            for part in msg.walk():
                if part.is_multipart():
                    print("ID{}：邮件的会话部分被跳过...".format(id))
                    continue # 跳过往来邮件
                if part.get_param('name'):
                    print("ID{}：邮件的附件部分被跳过...".format(id))
                    continue # 跳过附件
                content_raw = Utils.auto_decode(part)
            
            content = content_raw.replace('\n', '').replace('\r', '')
            
            re_code_list = re.findall(r'bold; text-align:center">(.*?)</td>', content)
            if len(re_code_list) == 1:
                code = re_code_list[0]
            else:
                code = ""
            re_region_list = re.findall(r'#f1f1f1; text-align:center; letter-spacing:1px">(.*?)</td>', content)
            if len(re_region_list) == 1:
                region = re_region_list[0]
            else:
                region = "未知"

            if len(re.findall('It looks like you are trying to log in from a new device', content)) > 0:
                type = CodeType.LOGIN
            elif len(re.findall('Here is the Steam Guard code you need to login to account', content)) > 0:
                type = CodeType.LOGIN
            elif len(re.findall('看起来您正在尝试使用新设备登录', content)) > 0:
                type = CodeType.LOGIN

            elif len(re.findall('We received a request to add a phone number', content)) > 0:
                type = CodeType.RECOVERY
            elif len(re.findall('Here is the code you need to change your Steam login credentials', content)) > 0:
                type = CodeType.RECOVERY
            elif len(re.findall('Please click the link below to recover your Steam login credentials', content)) > 0:
                type = CodeType.RECOVERY
            elif len(re.findall('手机号码', content)) > 0:
                type = CodeType.RECOVERY
            elif len(re.findall('以下是您更改 Steam 登录凭据时所需的代码', content)) > 0:
                type = CodeType.RECOVERY
            elif len(re.findall('恢复您的 Steam 登录凭据', content)) > 0:
                type = CodeType.RECOVERY

            elif len(re.findall('You have a new message from Steam Support', content)) > 0:
                type = CodeType.SUPPORT
            elif len(re.findall('您有一条来自 Steam 客服的新信息', content)) > 0:
                type = CodeType.SUPPORT

            elif len(re.findall('Thank you for your recent transaction on Steam', content)) > 0:
                type = CodeType.GAME_PURCHASE
            elif len(re.findall('感谢您近期在 Steam 上的交易', content)) > 0:
                type = CodeType.GAME_PURCHASE
            
            elif len(re.findall('Your recent Community Market purchases have been processed', content)) > 0:
                type = CodeType.MARKET_PURCHASE
            elif len(re.findall('处购买社区市场物品的请求已被处理', content)) > 0:
                type = CodeType.MARKET_PURCHASE

            elif len(re.findall('An item you listed in the Community Market has been sold', content)) > 0:
                type = CodeType.MARKET_SOLD
            elif len(re.findall('您在社区市场中上架的一件物品已售给了', content)) > 0:
                type = CodeType.MARKET_SOLD

            elif len(re.findall('Your refund request has been received', content)) > 0:
                type = CodeType.REFUND_REQUEST
            elif len(re.findall('已收到您的退款申请', content)) > 0:
                type = CodeType.REFUND_REQUEST

            elif len(re.findall('We’ve issued the refund', content)) > 0:
                type = CodeType.REFUNDED
            elif len(re.findall('我们已将款项退还到您的 Steam 钱包', content)) > 0:
                type = CodeType.REFUNDED
                
            else:
                type = CodeType.UNKNOWN

            new_code_list.append(CodeInfo(id=id, time=time, code=code, type=type, region=region))
            print("ID{}：邮件成功添加至缓存，类型为：".format(id), type)

        if len(new_code_list) < 1:
            print("没有任何新邮件")
        return ('OK', new_code_list)

    def get_email_date(self, date):
        utcstr = date[0][0].replace('+00:00', '')
        utcstr = Utils.remove_brackets(utcstr).strip()
        utcdatetime = None
        localtimestamp = None
        try:
            utcdatetime = datetime.datetime.strptime(utcstr, '%a, %d %b %Y %H:%M:%S +0000')
            localdatetime = utcdatetime + datetime.timedelta(hours=+8)
            localtimestamp = localdatetime.timestamp()
        except:
            try:
                utcdatetime = datetime.datetime.strptime(utcstr, '%a, %d %b %Y %H:%M:%S +0800')
                localtimestamp = utcdatetime.timestamp()
            except:
                try:
                    utcdatetime = datetime.datetime.strptime(utcstr, '%a, %d %b %Y %H:%M:%S +0800')
                    localtimestamp = utcdatetime.timestamp()
                except:
                    print("错误：未能处理收件时间格式：", str(utcstr))
                    raise
        return localtimestamp