from flask.views import MethodView
from flask import request, jsonify, current_app
import os
from server.auth import jwt_required
from server.services.video_service import create_video
from server.config_util import get_podcast_config

class VideoController(MethodView):
    @jwt_required
    def post(self):
        try:
            # 获取配置
            cfg = get_podcast_config()
            mp3_folder = cfg['mp3_folder']
            video_folder = cfg.get('video_folder', os.path.join(os.path.dirname(mp3_folder), 'videos'))
            os.makedirs(video_folder, exist_ok=True)

            # 获取请求参数
            data = request.get_json()
            mp3_filename = data.get('mp3_filename')
            title = data.get('title')
            subtitle_path = data.get('subtitle_path')

            if not all([mp3_filename, title, subtitle_path]):
                return jsonify({
                    'error': 'Missing required parameters: mp3_filename, title, and subtitle_path are required'
                }), 400

            # 构建文件路径
            mp3_path = os.path.join(mp3_folder, mp3_filename)
            video_filename = os.path.splitext(mp3_filename)[0] + '.mp4'
            output_path = os.path.join(video_folder, video_filename)

            # 生成视频
            current_app.broadcast_progress('video', '开始生成视频...')
            create_video(mp3_path, title, subtitle_path, output_path)
            current_app.broadcast_progress('video', '视频生成完成')

            return jsonify({
                'message': 'Video generated successfully',
                'video_filename': video_filename
            })

        except Exception as e:
            current_app.broadcast_progress('error', f'视频生成失败: {str(e)}')
            return jsonify({
                'error': f'Failed to generate video: {str(e)}'
            }), 500 