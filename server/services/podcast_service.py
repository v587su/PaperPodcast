import os
from werkzeug.utils import secure_filename
from loguru import logger
import hashlib
import datetime
import re
from flask import current_app

from server.repositories.file_repository import FileRepository
from podcastfy.client import generate_podcast
from server.config_util import get_podcast_config

class PodcastService:
    @staticmethod
    def _notify_progress(stage, message=None):
        """发送进度通知"""
        if hasattr(current_app, 'broadcast_progress'):
            current_app.broadcast_progress(stage, message)

    @staticmethod
    def handle_pdf_upload(file, app_ctx):
        cfg = get_podcast_config()
        pdf_folder = cfg['pdf_folder']
        os.makedirs(pdf_folder, exist_ok=True)
        # 文件类型和MIME校验
        if not file.filename.lower().endswith('.pdf'):
            logger.warning("文件类型校验失败: {}", file.filename)
            return {"error": "Invalid file type. Only PDF files are allowed."}, 400
        if file.mimetype != 'application/pdf':
            logger.warning("MIME类型校验失败: {}", file.mimetype)
            return {"error": "Invalid MIME type. Only PDF files are allowed."}, 400

        # 文件大小限制
        file.seek(0, os.SEEK_END)
        file_length = file.tell()
        file.seek(0)
        if file_length > 50 * 1024 * 1024:
            logger.warning("文件过大: {} bytes", file_length)
            return {"error": "File too large. Max size is 50MB."}, 400

        # PDF头校验
        file_head = file.read(5)
        file.seek(0)
        if file_head != b'%PDF-':
            logger.warning("文件头校验失败: {}", file_head)
            return {"error": "File content is not a valid PDF."}, 400

        filename = secure_filename(file.filename)
        filepath = os.path.join(pdf_folder, filename)

        # 检查重复文件
        upload_hash = FileRepository.file_hash(file)
        for fname in os.listdir(pdf_folder):
            existing_path = os.path.join(pdf_folder, fname)
            if os.path.isfile(existing_path):
                with open(existing_path, 'rb') as ef:
                    if FileRepository.file_hash(ef) == upload_hash:
                        logger.warning("检测到重复文件: {}", fname)
                        mp3_path = FileRepository.find_mp3_for_pdf(fname, app_ctx)
                        if mp3_path:
                            logger.info("已存在对应mp3: {}", mp3_path)
                            return {
                                "message": "File already exists, mp3 found.",
                                "output_path": mp3_path
                            }, 200
                        else:
                            # 生成mp3
                            output_file_path = PodcastService._generate_mp3(existing_path, app_ctx)
                            logger.success("重复PDF生成mp3: {}", output_file_path)
                            return {
                                "message": "File already exists, mp3 generated.",
                                "output_path": output_file_path
                            }, 201

        # 保存文件
        file.save(filepath)
        logger.info("文件已保存: {}", filepath)

        # 生成mp3
        try:
            output_file_path = PodcastService._generate_mp3(filepath, app_ctx)
            logger.success("播客生成成功: {}", output_file_path)
            return {
                "message": "File uploaded and processed successfully",
                "output_path": output_file_path
            }, 201
        except Exception as e:
            logger.error("处理PDF出错: {}", e)
            return {"error": f"Error processing PDF: {e}"}, 500

    @staticmethod
    def _get_next_mp3_number(audio_dir):
        """获取下一个可用的MP3文件编号"""
        max_num = 0
        for filename in os.listdir(audio_dir):
            if filename.endswith('.mp3'):
                # 使用正则表达式匹配文件名中的数字
                match = re.match(r'vol(\d+)\.mp3', filename)
                if match:
                    num = int(match.group(1))
                    max_num = max(max_num, num)
        return max_num + 1

    @staticmethod
    def _generate_mp3(pdf_path, app_ctx):
        cfg = get_podcast_config()
        custom_config = {
            "podcast_name": "Third Audience",
            "podcast_tagline": "Where human, machine and AI meet in code",
            "word_count": 4500,
            "conversation_style": ["humorous", "casual", "critical", "expository"],
            "roles": {
                "person1": "Paper Analyst",
                "person2": "Devil's Advocate"
            },
            "dialogue_structure": [
                "Cold Open (Hook)",
                "Paper Overview",
                "Methodology Deep Dive",
                "Findings Breakdown",
                "Limitations Debate",
                "Real-world Implications",
            ],
            "engagement_techniques": [
                "socratic questioning",
                "data visualization metaphors",
                "academic gossip",
                "cross-disciplinary parallels"
            ],
            "segment_rules": {
                "max_duration": 10,
                "mandatory_elements": [
                    "citation timestamps",
                    "jargon_alerts"
                ]
            },
            "creativity": 0.3
        }
        llm_model_name = cfg['llm_model_name']
        
        # 获取音频目录
        audio_dir = cfg['mp3_folder']
        os.makedirs(audio_dir, exist_ok=True)
        
        # 生成新的MP3文件名
        next_num = PodcastService._get_next_mp3_number(audio_dir)
        output_filename = f"vol{next_num:03d}.mp3"
        output_file_path = os.path.join(audio_dir, output_filename)
        
        try:
            # 通知开始生成脚本
            PodcastService._notify_progress('script_start')
            logger.info("开始生成播客脚本...")
            
            # 生成播客
            generated_path = generate_podcast(
                urls=[pdf_path],
                llm_model_name=llm_model_name,
                conversation_config=custom_config
            )
            
            transcript_path = generated_path.replace('.mp3', '.txt').replace('audio', 'transcripts')
    
            
            # 移动生成的文件到目标位置
            if os.path.exists(generated_path):
                os.rename(generated_path, output_file_path)
                logger.info(f"Renamed {generated_path} to {output_file_path}")
                
                # 重命名对应的transcript文件
                if os.path.exists(transcript_path):
                    new_transcript_path = output_file_path.replace('.mp3', '.txt')
                    os.rename(transcript_path, new_transcript_path)
                    logger.info(f"Renamed transcript {transcript_path} to {new_transcript_path}")
            else:
                raise Exception(f"Generated file not found at {generated_path}")
            
            # 通知完成
            PodcastService._notify_progress('complete', "播客生成完成")
            logger.info("播客生成完成")
                
            return output_file_path
        except Exception as e:
            logger.error(f"生成播客时出错: {e}")
            PodcastService._notify_progress('error', str(e))
            raise