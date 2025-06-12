import os
from flask import Flask, request, jsonify
import sys

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = './uploads' # 设置上传文件保存目录
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True) # 创建上传目录
# 前端页面和静态资源已分离，无需再由 Flask 提供

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

from podcastfy.resource import PodcastResource

# 注册 RESTful 路由
from podcastfy.auth import jwt_required

app.add_url_rule(
    '/api/v1/podcasts',
    view_func=PodcastResource.as_view('podcast_resource', decorators=[jwt_required]),
    methods=['POST']
)

if __name__ == '__main__':
    # 为了方便开发，这里直接运行 Flask 应用
    # 在生产环境中，你可能需要使用 Gunicorn 或 uWSGI 等 WSGI 服务器
    app.run(debug=True, port=8088) # 在端口 5000 上运行