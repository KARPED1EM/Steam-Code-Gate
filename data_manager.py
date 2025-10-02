import json, logging, os, re, shutil, time
from typing import Any

from code_info import CodeInfo, CodeType

log = logging.getLogger("data_manager")

file_name = "codes_cache.json"

CODE_RE = re.compile(r"^[A-Z0-9]{5}$")

def normalize_region(region: str) -> str:
    if not region:
        return ""

    r = re.sub(r"(?is)<[^>]*>", "", region)
    r = re.sub(r"\s+", " ", r).strip()
    css_words = [
        "letter-spacing", "text-align", "font-size", "font-family", "color:",
        "padding", "margin", "style=", "class=", "width:", "height:"
    ]

    for w in css_words:
        if w in r.lower():
            r = ""
            break

    if len(r) > 40:
        r = r[:40].strip()

    r = "".join(ch for ch in r if ch.isprintable())
    return r

class DataManager:
    @staticmethod
    def read_from_file() -> list[Any] | None:
        try:
            if not os.path.exists(file_name):
                return None
            with open(file_name, "r", encoding="utf-8") as f:
                data = json.load(f)
                code_list = [CodeInfo.from_json(code) for code in data]
                return code_list
        except Exception:
            try:
                shutil.copyfile(file_name, file_name + f".{int(time.time())}.bak")
                os.remove(file_name)
                log.error("读取缓存邮件时解析失败，将备份并删除无效文件")
            except Exception:
                log.exception("备份/删除无效缓存文件失败")
            return None

    @staticmethod
    def save_to_file(code_list):
        try:
            data = [code.to_json() for code in code_list]
            with open(file_name, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False)
        except Exception:
            log.exception("保存缓存文件失败")

    @staticmethod
    def clean_cache_on_start(code_list: list[CodeInfo]) -> list[CodeInfo]:
        if not code_list:
            return []
        cleaned: list[CodeInfo] = []
        removed_login_bad_code = 0
        fixed_region = 0
        for c in code_list:
            # 清理/正则化 region
            old_region = c.region or ""
            nr = normalize_region(old_region)
            if not nr:
                nr = "未知"
            if nr != old_region:
                fixed_region += 1
            c.region = nr

            if c.type == CodeType.LOGIN:
                if not c.code or not CODE_RE.match(c.code):
                    removed_login_bad_code += 1
                    continue
            else:
                c.code = ""

            cleaned.append(c)

        if removed_login_bad_code or fixed_region:
            log.info("缓存清理：移除无效LOGIN记录=%s，修正region=%s", removed_login_bad_code, fixed_region)

        seen = set()
        unique: list[CodeInfo] = []
        for c in cleaned:
            if c.time in seen:
                continue
            seen.add(c.time)
            unique.append(c)
        return unique