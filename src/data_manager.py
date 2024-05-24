import json, os, shutil, time

from code_info import CodeInfo

file_name = 'codes_cache.json'

class DataManager:
    
    @staticmethod
    def read_from_file() -> list[type[CodeInfo]]:
        try:
            if not os.path.exists(file_name):
                return None
            with open(file_name, 'r') as f:
                data = json.load(f)
                code_list = [CodeInfo.from_json(code) for code in data]
                f.close()
                return code_list
        except Exception as e:
            shutil.copyfile(file_name, file_name + '.{}.bak'.format(int(time.time())))
            os.remove(file_name)
            print("===========================================")
            print("读取缓存邮件时解析失败，将备份并删除无效文件")

    @staticmethod
    def save_to_file(code_list):
        data = [code.to_json() for code in code_list]
        with open(file_name, 'w') as f:
            json.dump(data, f)
            f.close()