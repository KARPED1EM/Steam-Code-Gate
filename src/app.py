import datetime, logging, threading
from typing import Optional
from flask import Flask, jsonify, render_template, request

from code_email import CodeEmail
from code_info import CodeInfo, CodeType
from data_manager import DataManager
from settings import Settings
from utils import Utils

app = Flask(__name__, static_url_path='', static_folder='static')
log = logging.getLogger("app")

# Global state
code_cache: list[CodeInfo] | None = None
requesting_lock = threading.Lock()
email_client = CodeEmail(
    host=Settings.IMAP_HOST,
    port=Settings.IMAP_PORT,
    username=Settings.IMAP_USERNAME,
    password=Settings.IMAP_PASSWORD,
    sender_filter=Settings.SENDER_FILTER,
)

def setup_logging():
    logging.basicConfig(
        level=logging.INFO if not Settings.DEBUG else logging.DEBUG,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

def init_app_once():
    global code_cache
    setup_logging()
    if code_cache is None:
        code_cache = DataManager.read_from_file()
        cleaned = DataManager.clean_cache_on_start(code_cache or [])
        code_cache = cleaned
        DataManager.save_to_file(code_cache)

        cache_num = len(code_cache) if code_cache else 0
        log.info("===========================================")
        log.info("当前总缓存数量：%s", cache_num)
        log.info("===========================================")

@app.route("/")
def index():
    init_app_once()
    err = update_emails_background()
    if err is not None:
        return f"邮箱接入失败：{err}"
    return get_index_page()

def update_emails_background() -> Optional[str]:
    if not requesting_lock.acquire(blocking=False):
        return None
    try:
        ex = email_client.ensure_login()
        if ex is not None:
            return str(ex)

        global code_cache
        typ, new_list = email_client.get_emails(code_cache if code_cache else None)
        if typ != "OK":
            email_client.force_relogin()
            typ2, new_list2 = email_client.get_emails(code_cache if code_cache else None)
            if typ2 != "OK":
                return f"{typ}; 重试后失败：{typ2}"
            typ, new_list = typ2, new_list2

        unique_list = CodeEmail.update_emails_cache(code_cache, new_list)
        unique_list = DataManager.clean_cache_on_start(unique_list)

        formal_num = len(code_cache) if code_cache else 0
        delta = len(unique_list) - formal_num
        code_cache = unique_list.copy()

        log.info("===========================================")
        log.info("获取新邮件数量：%s", len(new_list))
        log.info("相较于缓存变化：%s", delta)
        log.info("当前总缓存数量：%s", len(code_cache))
        log.info("===========================================")

        DataManager.save_to_file(code_cache)
        return None
    finally:
        requesting_lock.release()

def get_index_page():
    if not code_cache:
        return "邮件数据处理失败，请联系管理员。"
    login_codes = CodeInfo.get_in_type(code_cache, CodeType.LOGIN)
    if not login_codes:
        return "邮件数据处理失败，请联系管理员。"

    login_codes.sort(key=lambda c: c.time, reverse=True)
    latest = login_codes[0]
    latest_code = latest.code
    latest_code_region = latest.region
    latest_code_time = Utils.convert_time_delta_to_relative_time(
        datetime.datetime.now() - datetime.datetime.fromtimestamp(latest.time)
    )

    return render_template(
        "index.html",
        latest_code_area=latest_code,
        latest_code_time_area=latest_code_time,
        latest_code_region_area=latest_code_region,
        count_login=CodeInfo.count_type(code_cache, CodeType.LOGIN),
        count_recovery=CodeInfo.count_type(code_cache, CodeType.RECOVERY),
        count_support=CodeInfo.count_type(code_cache, CodeType.SUPPORT),
        count_game_purchase=CodeInfo.count_type(code_cache, CodeType.GAME_PURCHASE),
        count_refund_request=CodeInfo.count_type(code_cache, CodeType.REFUND_REQUEST),
        count_refunded=CodeInfo.count_type(code_cache, CodeType.REFUNDED),
        count_market_purchase=CodeInfo.count_type(code_cache, CodeType.MARKET_PURCHASE),
        count_market_sold=CodeInfo.count_type(code_cache, CodeType.MARKET_SOLD),
    )

@app.route("/api/latest")
def api_latest():
    init_app_once()
    if request.args.get("refresh") == "1":
        update_emails_background()

    if not code_cache:
        return jsonify({"ok": False, "error": "NO_CACHE"}), 200

    login_codes = CodeInfo.get_in_type(code_cache, CodeType.LOGIN)
    if not login_codes:
        return jsonify({"ok": False, "error": "NO_LOGIN_CODES"}), 200

    login_codes.sort(key=lambda c: c.time, reverse=True)
    latest = login_codes[0]
    return jsonify(
        {
            "ok": True,
            "code": latest.code,
            "region": latest.region,
            "time": latest.time,
        }
    )

if __name__ == "__main__":
    init_app_once()
    app.run(host="127.0.0.1", port=1244, debug=Settings.DEBUG)