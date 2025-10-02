import datetime, re

decode_types = ["utf-8", "gb2312", "gb18030", "gbk", "ascii", "raw"]

class Utils:
    @staticmethod
    def auto_decode(part):
        for decode_type in decode_types:
            if decode_type == "raw":
                try:
                    return part.get_payload(decode=False)
                except Exception:
                    continue
            else:
                try:
                    return part.get_payload(decode=True).decode(decode_type)
                except Exception:
                    continue
        return ""

    @staticmethod
    def remove_brackets(text):
        text = re.sub(r"\(.*?\)", "", text)
        text = re.sub(r"\[.*?]", "", text)
        text = re.sub(r"\{.*?}", "", text)
        return text

    @staticmethod
    def convert_time_delta_to_relative_time(time_delta: datetime.timedelta):
        if time_delta < datetime.timedelta(minutes=1):
            return f"{int(time_delta.total_seconds())}秒前"
        elif time_delta < datetime.timedelta(hours=1):
            return f"{int(time_delta.total_seconds() // 60)}分钟前"
        elif time_delta < datetime.timedelta(hours=24):
            return f"{int(time_delta.total_seconds() // 3600)}小时前"
        else:
            return f"{time_delta.days}天前"