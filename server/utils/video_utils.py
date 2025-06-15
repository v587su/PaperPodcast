import os
import tempfile
import pysrt
from moviepy import VideoFileClip, TextClip

DEFAULT_FONT_PATH = "data/font/SourceHanSansCN-Bold.otf"

def create_subtitle_clips(subtitle_path, duration):
    """Create subtitle clips from SRT file, only keep subtitles within duration"""
    subs = pysrt.open(subtitle_path)
    subtitle_clips = []
    for sub in subs:
        start_time = sub.start.ordinal / 1000.0
        end_time = sub.end.ordinal / 1000.0
        clip_duration = end_time - start_time
        if start_time >= duration:
            continue
        if end_time > duration:
            end_time = duration
            clip_duration = end_time - start_time
        if clip_duration <= 0:
            continue
        try:
            text_clip = TextClip(
                text=sub.text,
                font_size=44,
                color='white',
                stroke_color='#222222',
                stroke_width=2,
                text_align='center',
                font=DEFAULT_FONT_PATH,
                method='caption',
                size=(1800, 100),
                bg_color=None,
            ).with_duration(clip_duration).with_position(("center", 900))
            subtitle_clips.append((text_clip, start_time))
        except Exception as e:
            print(f"Error creating subtitle clip: {e}")
            continue
    return subtitle_clips

def create_waveform_animation_clip(audio_path, duration, fps=12, size=(1920, 320)):
    """用 seewav 命令行生成音频波形动画视频，并返回 VideoFileClip。高度压低，背景为黑色。"""
    import subprocess
    temp_video = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
    temp_video_path = temp_video.name
    temp_video.close()
    cmd = [
        "python", "-m", "seewav",
        "-r", str(fps),
        "-W", str(size[0]),
        "-H", str(size[1]),
        "-d", str(duration),
        audio_path,
        temp_video_path
    ]
    subprocess.run(cmd, check=True)
    waveform_clip = VideoFileClip(temp_video_path).with_duration(duration)
    def cleanup():
        if os.path.exists(temp_video_path):
            os.remove(temp_video_path)
    waveform_clip._cleanup = cleanup
    return waveform_clip 