from flask import Flask, render_template, request

import datetime, time

from captcha import Captcha
from utils import Utils
from code_info import CodeInfo, CodeType
from code_email import CodeEmail
from data_manager import DataManager

app = Flask(__name__)
code_cache = [CodeInfo]
code_email = CodeEmail()
valid_tokens = {'leever': int(time.time()) * 2}
requesting_emails = False

@app.route('/') # 访问首页
def get():
    request_id = request.args.get('token')
    expired_time = valid_tokens.get(request_id, 0)
    if (expired_time > int(time.time())):
        error = update_emails()
        if error != None:
            return str(error)
        return get_index_page()
    return get_captcha_page()

@app.route('/captcha-request', methods=['POST']) # 人机验证接口
def captcha_request():
    captchaVerifyParam = request.json["captchaVerifyParam"]
    (response, error) = Captcha.verify(captchaVerifyParam)
    request_id = response.body.request_id
    if response == None:
        return 'NO'
    if response.body.result.verify_result:
        valid_tokens[request_id] = int(time.time()) + 60
        now = int(time.time())
        toekns_copied = valid_tokens.copy()
        tokens = toekns_copied.keys()
        del toekns_copied
        for token in tokens:
            expired_time = valid_tokens.get(token, 0)
            if (expired_time <= now):
                if (token in valid_tokens.keys()):
                    del valid_tokens[token]
        return request_id
    else:
        return 'NO'

def update_emails(): # 请求更新邮件
    
    global requesting_emails
    if requesting_emails:
        return None
    requesting_emails = True
    
    ex = code_email.login_if_not(False)
    if (ex != None):
        requesting_emails = False
        return str(ex)
    
    global code_cache
    if code_cache != None and len(code_cache) >= 1:
        typ, new_code_list = code_email.get_emails(code_cache)
    else:
        typ, new_code_list = code_email.get_emails(None)
    if (typ != 'OK'):
        code_email.login_if_not(True)
        requesting_emails = False
        return typ
    
    unique_code_list = CodeEmail.update_emails_cache(code_cache, new_code_list)
    if code_cache:
        formal_code_num = len(code_cache)
    else:
        formal_code_num = 0
    delta = len(unique_code_list) - formal_code_num
    code_cache = unique_code_list.copy()
    del unique_code_list

    print("===========================================")
    print("获取新邮件数量：", len(new_code_list))
    print("相较于缓存变化：", delta)
    print("当前总缓存数量：", len(code_cache))
    print("===========================================")

    DataManager.save_to_file(code_cache)
    requesting_emails = False
    return None

def get_index_page(): # 为用户展示验证码获取页面
    login_codes = CodeInfo.get_in_type(code_cache, CodeType.LOGIN)
    if login_codes is None or len(login_codes) < 1:
        return "邮件数据处理失败，请联系管理员。"
    
    def get_code_time(code): return code.time
    login_codes.sort(key=get_code_time, reverse=True)
    latest_code = login_codes[0].code
    latest_code_region = login_codes[0].region
    latest_code_time = Utils.convert_time_delta_to_relative_time(datetime.datetime.now() - datetime.datetime.fromtimestamp(login_codes[0].time))

    return render_template('index.html', latest_code_area=latest_code, latest_code_time_area=latest_code_time, latest_code_region_area=latest_code_region, count_login=CodeInfo.count_type(code_cache, CodeType.LOGIN), count_recovery=CodeInfo.count_type(code_cache, CodeType.RECOVERY), count_support=CodeInfo.count_type(code_cache, CodeType.SUPPORT), count_game_purchase=CodeInfo.count_type(code_cache, CodeType.GAME_PURCHASE), count_refund_request=CodeInfo.count_type(code_cache, CodeType.REFUND_REQUEST), count_refunded=CodeInfo.count_type(code_cache, CodeType.REFUNDED), count_market_purchase=CodeInfo.count_type(code_cache, CodeType.MARKET_PURCHASE), count_market_sold=CodeInfo.count_type(code_cache, CodeType.MARKET_SOLD))

def get_captcha_page(): # 为用户展示人机验证页面
    return render_template('captcha.html')

if __name__ == '__main__':

    code_cache = DataManager.read_from_file()

    print("===========================================")
    if code_cache:
        cache_num = len(code_cache)
    else:
        cache_num = 0
    print("当前总缓存数量：", cache_num)
    print("===========================================")

    app.run(host='127.0.0.1', port=1244)
    requesting_emails = False