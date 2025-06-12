import configparser
import os

CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.ini')

def get_token():
    config = configparser.ConfigParser()
    config.read(CONFIG_PATH, encoding='utf-8')
    return config.get('auth', 'token', fallback=None)

# 可扩展更多配置读取函数