import configparser
import os

CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.ini')

def get_token():
    config = configparser.ConfigParser()
    config.read(CONFIG_PATH, encoding='utf-8')
    return config.get('auth', 'token', fallback=None)

def get_podcast_config():
    config = configparser.ConfigParser()
    config.read(CONFIG_PATH, encoding='utf-8')
    podcast_cfg = config['podcast']
    return {
        'llm_model_name': podcast_cfg.get('llm_model_name', 'gemini-2.5-pro-preview-06-05'),
        'upload_folder': podcast_cfg.get('upload_folder', './uploads'),
        'pdf_folder': podcast_cfg.get('pdf_folder', './uploads/pdf'),
        'mp3_folder': podcast_cfg.get('mp3_folder', './uploads/mp3')
    }

def get_gemini_api_key():
    config = configparser.ConfigParser()
    config.read(CONFIG_PATH, encoding='utf-8')
    return config.get('gemini', 'api_key', fallback=None)

def get_openai_api_key():
    config = configparser.ConfigParser()
    config.read(CONFIG_PATH, encoding='utf-8')
    return config.get('openai', 'api_key', fallback=None)

# 可扩展更多配置读取函数