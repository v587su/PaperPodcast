import os
from flask import Flask, request, jsonify
import sys
from flask_sock import Sock
import json
from threading import Lock

from server.config_util import get_podcast_config, get_gemini_api_key, get_openai_api_key
from server.services.video_service import create_video

# 设置 GEMINI_API_KEY 环境变量
os.environ["GEMINI_API_KEY"] = get_gemini_api_key() or ""

# 设置 OPENAI_API_KEY 环境变量
os.environ["OPENAI_API_KEY"] = get_openai_api_key() or ""

app = Flask(__name__)
sock = Sock(app)
podcast_cfg = get_podcast_config()
app.config['UPLOAD_FOLDER'] = podcast_cfg['upload_folder']  # 统一用配置文件
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True) # 创建上传目录

# WebSocket连接管理
ws_clients = set()
ws_lock = Lock()

def broadcast_progress(stage, message=None):
    """向所有WebSocket客户端广播进度信息"""
    with ws_lock:
        for client in ws_clients:
            try:
                client.send(json.dumps({
                    'type': 'progress',
                    'stage': stage,
                    'message': message
                }))
            except Exception as e:
                print(f"Error broadcasting to client: {e}")

# 将broadcast_progress函数注册到app
app.broadcast_progress = broadcast_progress

@sock.route('/ws/progress')
def progress_ws(ws):
    """WebSocket连接处理"""
    with ws_lock:
        ws_clients.add(ws)
    try:
        while True:
            # 保持连接活跃
            ws.receive()
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        with ws_lock:
            ws_clients.remove(ws)

from flask import send_from_directory

@app.route("/", methods=["GET"])
def root_redirect():
    # 自动跳转到前端页面
    return (
        '<meta http-equiv="refresh" content="0;url=/frontend/index.html">'
        '<p>正在跳转到前端页面...<br>'
        'If not redirected, please open <a href="/frontend/index.html">frontend/index.html</a> manually.</p>'
    )

@app.route('/frontend/<path:filename>')
def frontend_static(filename):
    # 允许通过 /frontend/ 访问前端静态文件
    return send_from_directory('frontend', filename)

@app.route('/api/v1/podcasts/download/<path:filename>')
def download_podcast(filename):
    # 从配置中获取MP3文件夹路径
    cfg = get_podcast_config()
    mp3_folder = cfg['mp3_folder']
    return send_from_directory(mp3_folder, filename, as_attachment=True)

@app.route('/api/v1/videos/download/<path:filename>')
def download_video(filename):
    # 从配置中获取视频文件夹路径
    cfg = get_podcast_config()
    video_folder = cfg.get('video_folder', os.path.join(os.path.dirname(cfg['mp3_folder']), 'videos'))
    return send_from_directory(video_folder, filename, as_attachment=True)

from server.controllers.podcast_controller import PodcastController
from server.controllers.video_controller import VideoController
from server.auth import jwt_required

app.add_url_rule(
    '/api/v1/podcasts',
    view_func=PodcastController.as_view('podcast_resource'),
    methods=['POST']
)

app.add_url_rule(
    '/api/v1/videos',
    view_func=VideoController.as_view('video_resource'),
    methods=['POST']
)

if __name__ == '__main__':
    # 为了方便开发，这里直接运行 Flask 应用
    # 在生产环境中，你可能需要使用 Gunicorn 或 uWSGI 等 WSGI 服务器
    app.run(debug=True, port=8088) # 在端口 8088 上运行