from __future__ import annotations
import datetime, imaplib, logging, re
from email import header
from email.parser import BytesParser
from email.utils import parsedate_to_datetime
from typing import Optional, Tuple

from code_info import CodeInfo, CodeType
from utils import Utils
from data_manager import normalize_region  # 用统一的清洗逻辑

log = logging.getLogger("code_email")

class CodeEmail:
    def __init__(
            self,
            host: str,
            port: int,
            username: str,
            password: str,
            sender_filter: str,
    ):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.sender = sender_filter
        self.imap: Optional[imaplib.IMAP4_SSL] = None
        self.initialized = False
        imaplib.Commands["ID"] = "AUTH"

    def ensure_login(self) -> Optional[Exception]:
        if not self.initialized or self.imap is None or not self._noop_ok():
            return self._login()
        return None

    def force_relogin(self) -> Optional[Exception]:
        self._logout_silent()
        return self._login()

    def _login(self) -> Optional[Exception]:
        try:
            self.imap = imaplib.IMAP4_SSL(host=self.host, port=int(self.port))
            typ, _ = self.imap.login(self.username, self.password)
            if typ != "OK":
                raise RuntimeError("IMAP 登录失败")
            try:
                args = (
                    "name",
                    "IMAPClient",
                    "contact",
                    "support@example.com",
                    "version",
                    "1.0.0",
                    "vendor",
                    "myclient",
                )
                self.imap._simple_command("ID", '("' + '" "'.join(args) + '")')
            except Exception:
                pass
            self.initialized = True
            return None
        except Exception as e:
            log.exception("IMAP 登录异常")
            return e

    def _noop_ok(self) -> bool:
        try:
            if self.imap is None:
                return False
            typ, _ = self.imap.noop()
            return typ == "OK"
        except Exception:
            return False

    def _logout_silent(self):
        try:
            if self.imap is not None:
                self.imap.logout()
        except Exception:
            pass
        finally:
            self.imap = None
            self.initialized = False

    @staticmethod
    def update_emails_cache(code_cache: Optional[list[CodeInfo]], new_code_list: list[CodeInfo]) -> list[CodeInfo]:
        if not code_cache:
            return new_code_list.copy()
        unique_code_set = set(code_cache) | set(new_code_list)
        return list(unique_code_set)

    def get_emails(self, code_cache: Optional[list[CodeInfo]]) -> Tuple[str, list[CodeInfo]]:
        if self.imap is None:
            return "接入邮箱失败，请联系管理员。", []

        try:
            typ, _ = self.imap.select("inbox", readonly=True)
            if typ != "OK":
                return "选择收件箱失败。", []

            if code_cache:
                latest_time = max(code_cache, key=lambda x: x.time).time
                latest_date = datetime.datetime.fromtimestamp(latest_time).strftime("%d-%b-%Y")
                query = f'(FROM "{self.sender}" SINCE {latest_date})'
            else:
                query = f'(FROM "{self.sender}")'

            typ_search, data = self.imap.search(None, query)
            log.info("===========================================")
            log.info("开始读取邮件：%s", query)
            if typ_search != "OK":
                return "读取邮件失败，请联系管理员。", []

            new_code_list: list[CodeInfo] = []
            code_times_set = {c.time for c in code_cache} if code_cache else set()

            for num in data[0].split():
                uid = int(num)
                typ_fetch, content = self.imap.fetch(num, "(RFC822)")
                if typ_fetch != "OK" or not content or not content[0]:
                    log.warning("ID%s：邮件读取失败被跳过...", uid)
                    continue

                msg = BytesParser().parsebytes(content[0][1])
                time_ts = self._parse_email_date(msg.get("Date"))
                if time_ts is None:
                    log.warning("ID%s：无法解析时间，跳过", uid)
                    continue

                if time_ts in code_times_set:
                    continue  # 跳过已缓存

                html_text, plain_text = self._extract_payloads(msg)
                content_flat_html = (html_text or "").replace("\n", "").replace("\r", "")
                content_plain = plain_text or ""

                code = self._extract_code_html(content_flat_html) or self._extract_code_plain(content_plain)
                region = (
                        self._extract_region_from_request_block(content_flat_html)
                        or self._extract_region_html_loose(content_flat_html)
                        or self._extract_region_plain(content_plain)
                )
                region = normalize_region(region) or "未知"

                code_type = self._classify_type(content_flat_html or content_plain)

                # 只有 LOGIN 类型保留 code，其他清空
                if code_type != CodeType.LOGIN:
                    code = ""

                if not (content_flat_html or content_plain):
                    log.warning("ID%s：无有效正文，跳过", uid)
                    continue

                new_code = CodeInfo(uid=uid, time=time_ts, code=code, code_type=code_type, region=region)
                new_code_list.append(new_code)
                log.info("ID%s：邮件成功添加至缓存，类型为：%s", uid, code_type)

            if not new_code_list:
                log.info("没有任何新邮件")
            return "OK", new_code_list

        except Exception as e:
            log.exception("读取邮件时异常")
            return f"读取邮件异常：{e}", []

    def _parse_email_date(self, date_header: Optional[str]) -> Optional[float]:
        if not date_header:
            return None
        try:
            decoded = header.decode_header(date_header)
            val = decoded[0][0]
            if isinstance(val, bytes):
                val = val.decode(errors="ignore")
            val = Utils.remove_brackets(val).strip()

            dt = parsedate_to_datetime(val)
            if dt is None:
                log.warning("无法通过 parsedate_to_datetime 解析：%s", val)
                return None

            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=datetime.timezone.utc)
            dt_cst8 = dt.astimezone(datetime.timezone(datetime.timedelta(hours=8)))
            return dt_cst8.timestamp()
        except Exception:
            log.exception("解析日期头异常：%s", date_header)
            return None

    def _extract_payloads(self, msg) -> tuple[str | None, str | None]:
        html_text = None
        plain_text = None
        for part in msg.walk():
            if part.is_multipart():
                continue
            if part.get_param("name"):
                continue
            ctype = (part.get_content_type() or "").lower()
            if ctype == "text/html" and html_text is None:
                html_text = Utils.auto_decode(part)
            elif ctype == "text/plain" and plain_text is None:
                plain_text = Utils.auto_decode(part)
        return html_text, plain_text

    # 验证码（HTML）
    def _extract_code_html(self, html: str) -> str:
        if not html:
            return ""
        code_pat = r"\b[A-Z0-9]{5}\b"

        m = re.search(
            r'(?is)<(td|div|span)[^>]*?(?:font-weight\s*:\s*bold[^;>]*;)[^>]*?(?:text-align\s*:\s*center)[^>]*>(.*?)</\1>',
            html,
        )
        if m:
            inner = re.sub(r"(?is)<[^>]+>", "", m.group(2))
            mcode = re.search(code_pat, inner)
            if mcode:
                return mcode.group(0)

        m = re.search(r'(?is)<(td|div|span)[^>]*class="[^"]*(title|code|guard)[^"]*"[^>]*>(.*?)</\1>', html)
        if m:
            inner = re.sub(r"(?is)<[^>]+>", "", m.group(3))
            mcode = re.search(code_pat, inner)
            if mcode:
                return mcode.group(0)

        around = re.search(r"(?is)Steam\s+Guard\s+code.*?([A-Z0-9]{5})", html)
        if around:
            return around.group(1)
        return ""

    # 验证码（纯文本）
    def _extract_code_plain(self, text: str) -> str:
        if not text:
            return ""
        norm = text.replace("=\r\n", "").replace("=\n", "").replace("\r", "")
        m = re.search(r"(?im)^Login\s+Code\s*\n\s*([A-Z0-9]{5})\b", norm)
        if m:
            return m.group(1)
        m = re.search(r"\b[A-Z0-9]{5}\b", norm)
        return m.group(0) if m else ""

    # Region 首选：从“Request made from / 请求来自”块紧邻的下一个单元格提取纯文本
    def _extract_region_from_request_block(self, html: str) -> str:
        if not html:
            return ""
        # 英文模板
        m1 = re.search(
            r'(?is)(Request\s+made\s+from.*?</(?:td|div|span)>)\s*<(?:td|div|span)[^>]*>(.*?)</(?:td|div|span)>',
            html,
        )
        if m1:
            inner = re.sub(r"(?is)<[^>]+>", "", m1.group(2)).strip()
            if inner:
                return inner
        # 中文模板（“请求来自”）
        m2 = re.search(
            r'(?is)(请求来自.*?</(?:td|div|span)>)\s*<(?:td|div|span)[^>]*>(.*?)</(?:td|div|span)>',
            html,
        )
        if m2:
            inner = re.sub(r"(?is)<[^>]+>", "", m2.group(2)).strip()
            if inner:
                return inner
        return ""

    # Region 次选：样式定位但只取元素内部纯文本
    def _extract_region_html_loose(self, html: str) -> str:
        if not html:
            return ""
        m = re.search(
            r'(?is)<(td|div|span)[^>]*?style="[^"]*(color\s*:\s*#f1f1f1)[^"]*(text-align\s*:\s*center)[^"]*(letter-spacing\s*:\s*1px)[^"]*"[^>]*>(.*?)</\1>',
            html,
        )
        if m:
            inner = re.sub(r"(?is)<[^>]+>", "", m.group(5)).strip()
            return inner
        return ""

    # Region（纯文本）
    def _extract_region_plain(self, text: str) -> str:
        if not text:
            return ""
        norm = text.replace("=\r\n", "").replace("=\n", "").replace("\r", "")
        # 英文
        m = re.search(r"(?im)^Request\s+made\s+from\s*\n\s*([^\n\r]+)", norm)
        if m:
            return m.group(1).strip()
        # 中文
        m2 = re.search(r"(?im)^请求来自\s*\n\s*([^\n\r]+)", norm)
        if m2:
            return m2.group(1).strip()
        return ""

    def _classify_type(self, content: str) -> CodeType:
        patt = re.findall
        if patt(r'It looks like you are trying to log in from a new device', content) or \
                patt(r'Here is the Steam Guard code you need to login to account', content) or \
                patt(r'Here is the Steam Guard code you need to access your account', content) or \
                patt(r'Access from new web or mobile device', content) or \
                patt(r'新的?网页或移动设备', content) or \
                patt(r'看起来您正在尝试使用新设备登录', content):
            return CodeType.LOGIN

        if patt(r'We received a request to add a phone number', content) or \
                patt(r'Here is the code you need to change your Steam login credentials', content) or \
                patt(r'Please click the link below to recover your Steam login credentials', content) or \
                patt(r'手机号码', content) or \
                patt(r'以下是您更', content) or \
                patt(r'恢复您的 Steam 登录凭据', content):
            return CodeType.RECOVERY

        if patt(r'You have a new message from Steam Support', content) or \
                patt(r'您有一条来自 Steam 客服的新信息', content):
            return CodeType.SUPPORT

        if patt(r'Thank you for your recent transaction on Steam', content) or \
                patt(r'感谢您近期在 Steam 上的交易', content):
            return CodeType.GAME_PURCHASE

        if patt(r'Your recent Community Market purchases have been processed', content) or \
                patt(r'处购买社区市场物品的请求已被处理', content):
            return CodeType.MARKET_PURCHASE

        if patt(r'An item you listed in the Community Market has been sold', content) or \
                patt(r'您在社区市场中上架的一件物品已售给了', content):
            return CodeType.MARKET_SOLD

        if patt(r'Your refund request has been received', content) or \
                patt(r'已收到您的退款申请', content):
            return CodeType.REFUND_REQUEST

        if patt(r'We’ve issued the refund', content) or \
                patt(r'我们已将款项退还到您的 Steam 钱包', content):
            return CodeType.REFUNDED

        return CodeType.UNKNOWN