import email
import imaplib
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Optional, Tuple

from src.services.code_provider.base import CodeProvider


@dataclass
class EmailCodeResult:
    code: Optional[str]
    code_timestamp: Optional[datetime]


class EmailProvider(CodeProvider):
    def __init__(self, imap_server: str, imap_port: int, email_address: str,
                 email_password: str, use_ssl: bool = True):
        self.imap_server = imap_server
        self.imap_port = imap_port
        self.email_address = email_address
        self.email_password = email_password
        self.use_ssl = use_ssl

    def get_code(self) -> Optional[str]:
        result = self.fetch_latest_code_since(None)
        return result.code if result else None

    def get_remaining_seconds(self) -> Optional[int]:
        return None

    def fetch_latest_code_since(self, last_code_at: Optional[datetime]) -> Optional[EmailCodeResult]:
        last_code_at_utc = self._normalize_timestamp(last_code_at)

        try:
            if self.use_ssl:
                mail = imaplib.IMAP4_SSL(self.imap_server, self.imap_port)
            else:
                mail = imaplib.IMAP4(self.imap_server, self.imap_port)

            mail.login(self.email_address, self.email_password)
            mail.select('inbox')

            search_criteria = ['FROM', '"noreply@steampowered.com"']
            if last_code_at_utc:
                search_criteria = ['SINCE', last_code_at_utc.strftime('%d-%b-%Y')] + search_criteria

            status, messages = mail.search(None, *search_criteria)
            if status != 'OK' or not messages[0]:
                mail.logout()
                return EmailCodeResult(code=None, code_timestamp=None)

            email_ids = messages[0].split()
            for email_id in reversed(email_ids):
                message_date = self._fetch_message_date(mail, email_id)
                if message_date and last_code_at_utc and message_date <= last_code_at_utc:
                    break
                if not message_date:
                    continue

                msg = self._fetch_message(mail, email_id)
                if not msg:
                    continue

                code = self._extract_code_from_email(msg)
                if code:
                    mail.logout()
                    return EmailCodeResult(code=code, code_timestamp=message_date)

            mail.logout()
            return EmailCodeResult(code=None, code_timestamp=None)

        except Exception:
            return EmailCodeResult(code=None, code_timestamp=None)

    def check_health(self) -> Tuple[bool, Optional[str]]:
        try:
            if self.use_ssl:
                mail = imaplib.IMAP4_SSL(self.imap_server, self.imap_port)
            else:
                mail = imaplib.IMAP4(self.imap_server, self.imap_port)

            mail.login(self.email_address, self.email_password)
            status, _ = mail.select('inbox')
            mail.logout()

            if status != 'OK':
                return False, '无法打开收件箱'
            return True, None
        except Exception as exc:
            return False, str(exc)

    def _extract_code_from_email(self, msg) -> Optional[str]:
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                if content_type == "text/plain" or content_type == "text/html":
                    try:
                        body = part.get_payload(decode=True).decode()
                        code = self._parse_code_from_body(body)
                        if code:
                            return code
                    except:
                        continue
        else:
            try:
                body = msg.get_payload(decode=True).decode()
                return self._parse_code_from_body(body)
            except:
                return None

        return None

    def _parse_code_from_body(self, body: str) -> Optional[str]:
        patterns = [
            r'(?:code|Code|CODE)[\s:]*([A-Z0-9]{5})',
            r'([A-Z0-9]{5})',
        ]

        for pattern in patterns:
            match = re.search(pattern, body)
            if match:
                code = match.group(1) if '(' in pattern else match.group(0)
                if len(code) == 5 and code.isalnum():
                    return code

        return None

    def _fetch_message(self, mail: imaplib.IMAP4, email_id: bytes):
        status, msg_data = mail.fetch(email_id, '(RFC822)')
        if status != 'OK':
            return None

        for response_part in msg_data:
            if isinstance(response_part, tuple):
                return email.message_from_bytes(response_part[1])
        return None

    def _fetch_message_date(self, mail: imaplib.IMAP4, email_id: bytes) -> Optional[datetime]:
        status, msg_data = mail.fetch(email_id, '(BODY.PEEK[HEADER.FIELDS (DATE)])')
        if status != 'OK':
            return None

        for response_part in msg_data:
            if isinstance(response_part, tuple):
                header_bytes = response_part[1]
                header_text = header_bytes.decode(errors='ignore')
                for line in header_text.splitlines():
                    if line.lower().startswith('date:'):
                        date_value = line.split(':', 1)[1].strip()
                        parsed = parsedate_to_datetime(date_value)
                        return self._normalize_timestamp(parsed)
        return None

    def _normalize_timestamp(self, dt: Optional[datetime]) -> Optional[datetime]:
        if not dt:
            return None
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc).replace(tzinfo=None)
