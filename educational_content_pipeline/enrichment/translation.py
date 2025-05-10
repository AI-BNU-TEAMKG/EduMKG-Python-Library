import requests
import random
import hashlib
import time
from typing import Optional
from .. import config # Relative import

def baidu_translate_text(text: str, from_lang: str = 'zh', to_lang: str = 'en') -> Optional[str]:
    """Translates text using Baidu Translate API."""
    appid = config.BAIDU_TRANSLATE_APPID
    appkey = config.BAIDU_TRANSLATE_APPKEY

    if not appid or not appkey:
        print("Baidu Translate API AppID or AppKey not configured.")
        return None

    url = 'https://fanyi-api.baidu.com/api/trans/vip/translate'
    salt = str(random.randint(32768, 65536))
    sign_str = appid + text + salt + appkey
    sign = hashlib.md5(sign_str.encode('utf-8')).hexdigest()

    params = {
        'q': text,
        'from': from_lang,
        'to': to_lang,
        'appid': appid,
        'salt': salt,
        'sign': sign
    }

    try:
        # Adding a small delay to avoid hitting rate limits too quickly if called in a loop
        time.sleep(0.5) # Adjust as needed
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        result = response.json()
        
        if 'trans_result' in result and result['trans_result']:
            return result['trans_result'][0]['dst']
        elif 'error_code' in result:
            print(f"Baidu Translate API error: {result['error_code']} - {result.get('error_msg', 'Unknown error')}")
            return None
        else:
            print(f"Baidu Translate failed with unexpected result: {result}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Baidu Translate request error: {e}")
        return None