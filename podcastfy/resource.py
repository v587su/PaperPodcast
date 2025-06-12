import os
from flask import request, jsonify
from werkzeug.utils import secure_filename
from flask.views import MethodView
from podcastfy.client import generate_podcast
from flask import current_app
from loguru import logger

from podcastfy.auth import jwt_required

class PodcastResource(MethodView):
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

        if file and file.filename.lower().endswith('.pdf'):
            # 文件MIME类型校验
            if file.mimetype != 'application/pdf':
                logger.warning("MIME类型校验失败: {}", file.mimetype)
                return jsonify({"error": "Invalid MIME type. Only PDF files are allowed."}), 400
            # 文件大小限制（最大10MB）
            file.seek(0, os.SEEK_END)
            file_length = file.tell()
            file.seek(0)
            if file_length > 10 * 1024 * 1024:
                logger.warning("文件过大: {} bytes", file_length)
                return jsonify({"error": "File too large. Max size is 10MB."}), 400
            # 简单PDF头校验
            file_head = file.read(5)
            file.seek(0)
            if file_head != b'%PDF-':
                logger.warning("文件头校验失败: {}", file_head)
                return jsonify({"error": "File content is not a valid PDF."}), 400

            filename = secure_filename(file.filename)
            pdf_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], 'pdf')
            os.makedirs(pdf_folder, exist_ok=True)
            filepath = os.path.join(pdf_folder, filename)

            # 检查 uploads 目录下是否已存在相同内容的文件（基于hash）
            import hashlib
            def file_hash(fobj):
                hash_obj = hashlib.sha256()
                fobj.seek(0)
                while True:
                    chunk = fobj.read(8192)
                    if not chunk:
                        break
                    hash_obj.update(chunk)
                fobj.seek(0)
                return hash_obj.hexdigest()

            upload_hash = file_hash(file)

            uploads_dir = pdf_folder
            for fname in os.listdir(uploads_dir):
                existing_path = os.path.join(uploads_dir, fname)
                if os.path.isfile(existing_path):
                    with open(existing_path, 'rb') as ef:
                        hash_obj = hashlib.sha256()
                        while True:
                            chunk = ef.read(8192)
                            if not chunk:
                                break
                            hash_obj.update(chunk)
                        if hash_obj.hexdigest() == upload_hash:
                            logger.warning("检测到重复文件: {}", fname)
                            return jsonify({"error": "File with same content already exists in uploads directory."}), 400

            file.save(filepath)
            logger.info("文件已保存: {}", filepath)

            if generate_podcast:
                try:
                    # 传递 mp3 输出目录参数
                    mp3_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], 'mp3')
                    os.makedirs(mp3_folder, exist_ok=True)
                    output_file_path = generate_podcast(urls=[filepath], mp3_output_dir=mp3_folder)
                    logger.success("播客生成成功: {}", output_file_path)
                    return jsonify({
                        "message": "File uploaded and processed successfully",
                        "output_path": output_file_path
                    }), 201
                except Exception as e:
                    logger.error("处理PDF出错: {}", e)
                    return jsonify({"error": f"Error processing PDF: {e}"}), 500
            else:
                logger.error("后端处理函数不可用")
                return jsonify({"error": "Backend processing function not available"}), 500
        else:
            logger.warning("文件类型校验失败: {}", file.filename)
            return jsonify({"error": "Invalid file type. Only PDF files are allowed."}), 400