from flask import request, jsonify, current_app
from flask.views import MethodView
from server.services.podcast_service import PodcastService
from server.auth import jwt_required
from loguru import logger

class PodcastController(MethodView):
    @jwt_required
    def post(self):
        logger.info("收到上传请求，headers: {}", dict(request.headers))
        if 'pdfFile' not in request.files:
            logger.warning("请求中缺少 pdfFile 字段")
            return jsonify({"error": "No file part in the request"}), 400

        file = request.files['pdfFile']
        if file.filename == '':
            logger.warning("未选择文件")
            return jsonify({"error": "No selected file"}), 400

        # 只做参数校验，业务逻辑交给service
        result, status = PodcastService.handle_pdf_upload(file, current_app)
        return jsonify(result), status