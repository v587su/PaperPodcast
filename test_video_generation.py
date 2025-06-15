import os
from server.services.video_service import create_video
from server.services.podcast_service import PodcastService
from server.config_util import get_podcast_config
from moviepy import AudioFileClip
import tempfile

def test_video_generation():
    # 获取配置
    cfg = get_podcast_config()
    mp3_folder = cfg['mp3_folder']
    video_folder = cfg.get('video_folder', os.path.join(os.path.dirname(mp3_folder), 'videos'))
    os.makedirs(video_folder, exist_ok=True)

    # 测试文件路径
    mp3_filename = "vol008.mp3"
    transcript_filename = "transcript_1e60b62e7fb64d6b9afb0924a6f7e4d1.txt"
    
    # 构建完整路径
    mp3_path = os.path.join(mp3_folder, mp3_filename)
    transcript_path = os.path.join('data', 'transcripts', transcript_filename)
    
    # 检查文件是否存在
    if not os.path.exists(mp3_path):
        print(f"错误: MP3文件不存在: {mp3_path}")
        return
    if not os.path.exists(transcript_path):
        print(f"错误: 字幕文件不存在: {transcript_path}")
        return

    try:
        print("开始处理字幕...")
        # 处理字幕
        subtitle_path = PodcastService._process_subtitles(transcript_path, mp3_path)
        print(f"字幕处理完成: {subtitle_path}")

        # 设置输出路径
        output_filename = os.path.splitext(mp3_filename)[0] + '_test.mp4'
        output_path = os.path.join(video_folder, output_filename)

        # 只截取前n秒音频
        n = 3
        print(f"截取前{n}秒音频...")
        temp_audio = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
        temp_audio_path = temp_audio.name
        temp_audio.close()
        audio_clip = AudioFileClip(mp3_path).with_start(0).with_end(n)
        audio_clip.write_audiofile(temp_audio_path)
        audio_clip.close()

        # 只保留前5秒字幕（直接用原字幕文件，create_video会自动同步）
        print("开始生成5秒视频...")
        create_video(
            audio_path=temp_audio_path,
            title="Highly Compressed Tokenizer Can Generate Without Training",  # 这里可以根据需要修改标题
            subtitle_path=subtitle_path,
            output_path=output_path,
            publish_info="arXiv:2506.08007v1"
        )
        print(f"5秒视频生成完成: {output_path}")

        # 清理临时音频
        os.remove(temp_audio_path)

    except Exception as e:
        print(f"生成视频时出错: {str(e)}")

if __name__ == "__main__":
    test_video_generation() 