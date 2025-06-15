import os
from werkzeug.utils import secure_filename
from loguru import logger
import hashlib
import datetime
import re
from flask import current_app
from pydub import AudioSegment
import math
import whisper

from server.repositories.file_repository import FileRepository
from podcastfy.client import generate_podcast
from server.config_util import get_podcast_config
from server.services.video_service import create_video

class PodcastService:
    @staticmethod
    def _process_subtitles(audio_path):
        """使用 openai-whisper base 模型对音频进行转写，生成精确对齐的SRT字幕，并将字幕文件保存到 uploads/subtitles 下，文件名与 mp3 一致"""
        try:
            # 加载 whisper base 模型
            model = whisper.load_model("base")
            # 识别音频，返回带时间轴的结果
            result = model.transcribe(audio_path, task="transcribe", language="en")
            # 生成 SRT 文件内容，保存到 uploads/subtitles
            base_name = os.path.splitext(os.path.basename(audio_path))[0]
            subtitles_dir = os.path.join("uploads", "subtitles")
            os.makedirs(subtitles_dir, exist_ok=True)
            srt_path = os.path.join(subtitles_dir, f"{base_name}.srt")
            with open(srt_path, 'w', encoding='utf-8') as f:
                for i, segment in enumerate(result["segments"]):
                    # 格式化时间
                    start = PodcastService._format_time(segment["start"])
                    end = PodcastService._format_time(segment["end"])
                    text = segment["text"].strip()
                    f.write(f"{i+1}\n{start} --> {end}\n{text}\n\n")
            return srt_path
        except Exception as e:
            logger.error(f"Whisper生成字幕时出错: {e}")
            raise

    @staticmethod
    def _format_time(seconds):
        """将秒数转换为SRT时间格式 (HH:MM:SS,mmm)"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        seconds = seconds % 60
        milliseconds = int((seconds - int(seconds)) * 1000)
        return f"{hours:02d}:{minutes:02d}:{int(seconds):02d},{milliseconds:03d}"

    @staticmethod
    def _notify_progress(stage, message=None):
        """发送进度通知"""
        if hasattr(current_app, 'broadcast_progress'):
            current_app.broadcast_progress(stage, message)

    @staticmethod
    def handle_pdf_upload(file, app_ctx, generate_video=True, paper_title=None, paper_publish=None):
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
                            # 检查是否存在对应的视频
                            video_path = mp3_path.replace('.mp3', '.mp4')
                            if os.path.exists(video_path):
                                return {
                                    "message": "File already exists, mp3 and video found.",
                                    "output_path": mp3_path,
                                    "video_path": video_path
                                }, 200
                            else:
                                # 生成视频，使用 paper_title 和 paper_publish
                                publish_info = paper_publish
                                title = paper_title if paper_title else os.path.splitext(fname)[0]
                                video_path = PodcastService._generate_video(mp3_path, title, app_ctx, publish_info=publish_info)
                                return {
                                    "message": "File already exists, mp3 found, video generated.",
                                    "output_path": mp3_path,
                                    "video_path": video_path
                                }, 201
                        else:
                            # 生成mp3
                            output_file_path = PodcastService._generate_mp3(existing_path, app_ctx)
                            # 生成视频
                            video_path = PodcastService._generate_video(output_file_path, title, app_ctx)
                            logger.success("重复PDF生成mp3和视频: {}, {}", output_file_path, video_path)
                            return {
                                "message": "File already exists, mp3 and video generated.",
                                "output_path": output_file_path,
                                "video_path": video_path
                            }, 201

        # 保存文件
        file.save(filepath)
        logger.info("文件已保存: {}", filepath)

        # 生成mp3和（可选）视频
        try:
            output_file_path = PodcastService._generate_mp3(filepath, app_ctx)
            video_path = None
            if generate_video:
                # 优先用 paper_title
                title = paper_title if paper_title else os.path.splitext(filename)[0]
                video_path = PodcastService._generate_video(output_file_path, title, app_ctx, publish_info=paper_publish)
                logger.success("播客和视频生成成功: {}, {}", output_file_path, video_path)
            else:
                logger.success("播客生成成功（未生成视频）: {}", output_file_path)
            result = {
                "message": "File uploaded and processed successfully",
                "output_path": output_file_path
            }
            if video_path:
                result["video_path"] = video_path
            return result, 201
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

    @staticmethod
    def _generate_video(mp3_path, title, app_ctx, publish_info=None):
        """生成视频"""
        try:
            cfg = get_podcast_config()
            video_folder = cfg.get('video_folder', os.path.join(os.path.dirname(cfg['mp3_folder']), 'videos'))
            os.makedirs(video_folder, exist_ok=True)

            # 生成字幕文件
            subtitle_path = PodcastService._process_subtitles(mp3_path)
            
            # 生成视频文件名
            video_filename = os.path.basename(mp3_path).replace('.mp3', '.mp4')
            output_path = os.path.join(video_folder, video_filename)

            # 通知开始生成视频
            PodcastService._notify_progress('video', '开始生成视频...')
            
            # 生成视频
            create_video(mp3_path, title, subtitle_path, output_path, publish_info=publish_info)
            
            # 通知视频生成完成
            PodcastService._notify_progress('video', '视频生成完成')
            logger.info("视频生成完成: {}", output_path)
            
            return output_path
        except Exception as e:
            logger.error(f"生成视频时出错: {e}")
            PodcastService._notify_progress('error', f"视频生成失败: {str(e)}")
            raise

    @staticmethod
    def handle_mp3_upload(file, app_ctx, paper_title=None, paper_publish=None):
        cfg = get_podcast_config()
        mp3_folder = cfg['mp3_folder']
        video_folder = cfg.get('video_folder', os.path.join(os.path.dirname(mp3_folder), 'videos'))
        os.makedirs(mp3_folder, exist_ok=True)
        os.makedirs(video_folder, exist_ok=True)

        filename = secure_filename(file.filename)
        mp3_path = os.path.join(mp3_folder, filename)
        file.save(mp3_path)
        logger.info("MP3文件已保存: {}", mp3_path)

        # 生成视频文件名
        video_filename = os.path.splitext(filename)[0] + '.mp4'
        output_path = os.path.join(video_folder, video_filename)

        # 标题优先用 paper_title
        title = paper_title if paper_title else os.path.splitext(filename)[0]

        # 生成字幕文件
        subtitle_path = PodcastService._process_subtitles(mp3_path)

        # 生成视频时拼接发表信息
        publish_info = paper_publish

        PodcastService._notify_progress('video', '开始生成视频...')
        try:
            create_video(mp3_path, title, subtitle_path, output_path, publish_info=publish_info)
            PodcastService._notify_progress('video', '视频生成完成')
            logger.info("视频生成完成: {}", output_path)
            return {
                "message": "MP3 uploaded and video generated successfully",
                "output_path": mp3_path,
                "video_path": output_path
            }, 201
        except Exception as e:
            logger.error("处理MP3生成视频出错: {}", e)
            PodcastService._notify_progress('error', f"视频生成失败: {str(e)}")
            return {"error": f"Error processing MP3: {e}"}, 500