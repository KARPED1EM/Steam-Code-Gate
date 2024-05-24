import os
import sys

from typing import List

from alibabacloud_captcha20230305.client import Client as captcha20230305Client
from alibabacloud_tea_openapi import models as open_api_models
from alibabacloud_captcha20230305 import models as captcha_20230305_models
from alibabacloud_tea_util import models as util_models
from alibabacloud_tea_util.client import Client as UtilClient

class Captcha:
    def __init__(self):
        pass

    @staticmethod
    def create_client() -> captcha20230305Client:
        config = open_api_models.Config(
            access_key_id='', # 访问阿里云人机验证的RAM用户的ID
            access_key_secret='' # RAM用户的密钥
        )
        config.endpoint = f'captcha.cn-shanghai.aliyuncs.com'
        return captcha20230305Client(config)

    @staticmethod
    def verify(captcha_verify_param):
        client = Captcha.create_client()
        verify_captcha_request = captcha_20230305_models.VerifyCaptchaRequest(
            captcha_verify_param=captcha_verify_param
        )
        try:
            response = client.verify_captcha_with_options(verify_captcha_request, util_models.RuntimeOptions())
            return (response, None)
        except Exception as error:
            print(error.message)
            print(error.data.get("Recommend"))
            UtilClient.assert_as_string(error.message)
            return(None, error.message)