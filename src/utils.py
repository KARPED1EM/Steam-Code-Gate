import re, datetime

decode_types = ['utf-8', 'gb2312', 'gb18030', 'gbk', 'ascii', 'raw']

class Utils:

    @staticmethod
    def auto_decode(content):
        for decode_type in decode_types:
            if decode_type == 'raw':
                content = content.get_payload(decode=False)
                break
            else:
                try:
                    content = content.get_payload(decode=True).decode(decode_type)
                    break
                except:
                    continue
        return content
    
    @staticmethod
    def remove_brackets(text):
        text = re.sub(r'\(.*?\)', '', text)
        text = re.sub(r'\[.*?\]', '', text)
        text = re.sub(r'\{.*?\}', '', text)
        return text
    
    @staticmethod
    def convert_time_delta_to_relative_time(time_delta):
        if time_delta < datetime.timedelta(days=0, hours=0, minutes=1):
            latest_code_time = '%s秒前' %int(time_delta.seconds)
        elif time_delta < datetime.timedelta(days=0,hours=1):
            latest_code_time = '%s分钟前' %int(time_delta.seconds / 60)
        elif time_delta < datetime.timedelta(days=0, hours=24):
            latest_code_time = '%s小时前' %int(time_delta.seconds / 3600)
        else:
            latest_code_time = '%s天前' %(time_delta.days)
        return latest_code_time