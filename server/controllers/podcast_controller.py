from flask import request, jsonify, current_app
from flask.views import MethodView
from server.services.podcast_service import PodcastService
from server.auth import jwt_required
from loguru import logger

class PodcastController(MethodView):
    @jwt_required
    def post(self):
        logger.info("收到上传请求，headers: {}", dict(request.headers))
        # 批量上传支持
        pdf_files = request.files.getlist('pdfFile')
        mp3_files = request.files.getlist('mp3File')
        files = pdf_files + mp3_files
        if not files:
            logger.warning("请求中缺少 pdfFile 或 mp3File 字段")
            return jsonify({"error": "No file part in the request"}), 400
        results = []
        paper_title = request.form.get('paper_title')
        paper_publish = request.form.get('paper_publish')
        generate_video = request.form.get('generate_video', '1') == '1'
        # 支持批量标题和发表
        paper_title_list = [s.strip() for s in paper_title.split(',')] if paper_title else []
        paper_publish_list = [s.strip() for s in paper_publish.split(',')] if paper_publish else []
        for idx, file in enumerate(files):
            if file.filename == '':
                logger.warning("未选择文件")
                results.append({"error": "No selected file"})
                continue
            filename = file.filename.lower()
            # 取对应的标题和发表
            cur_title = paper_title_list[idx] if idx < len(paper_title_list) else paper_title
            cur_publish = paper_publish_list[idx] if idx < len(paper_publish_list) else paper_publish
            if filename.endswith('.mp3'):
                result, status = PodcastService.handle_mp3_upload(file, current_app, paper_title=cur_title, paper_publish=cur_publish)
            else:
                result, status = PodcastService.handle_pdf_upload(file, current_app, generate_video=generate_video, paper_title=cur_title, paper_publish=cur_publish)
            results.append(result)
        return jsonify(results), 201