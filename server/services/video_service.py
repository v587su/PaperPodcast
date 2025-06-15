from server.utils.video_utils import create_subtitle_clips, create_waveform_animation_clip
from moviepy import AudioFileClip, TextClip, CompositeVideoClip
import os

DEFAULT_FONT_PATH = "data/font/SourceHanSansCN-Bold.otf"

def create_video(audio_path, title, subtitle_path, output_path, publish_info=None):
    """Create video with title, waveform animation and subtitles"""
    try:
        print(f"\n开始处理视频...")
        print(f"音频文件: {audio_path}")
        print(f"标题: {title}")
        print(f"字幕文件: {subtitle_path}")
        if publish_info:
            print(f"发表信息: {publish_info}")
        
        # Get audio duration
        audio = AudioFileClip(audio_path)
        duration = audio.duration
        print(f"音频时长: {duration:.2f}秒")
        
        # Create waveform animation
        print("\n生成波形动画...")
        waveform_clip = create_waveform_animation_clip(audio_path, duration, fps=12, size=(1920, 270))
        print("波形动画已生成")
        
        # Create title clip
        print("\n创建标题...")
        title_clip = TextClip(
            text=title,
            font_size=80,
            color='#00BFFF',  # 亮蓝色
            stroke_color='#222222',
            stroke_width=4,
            text_align='center',
            font=DEFAULT_FONT_PATH,
            method='caption',
            size=(1800, 300),
            bg_color=None,
        ).with_duration(duration).with_position(("center", 50))
        print("标题创建完成")
        
        # Create publish info clip
        if publish_info:
            publish_clip = TextClip(
                text=publish_info,
                font_size=48,
                color='#888888',
                stroke_color='#222222',
                stroke_width=2,
                text_align='center',
                font=DEFAULT_FONT_PATH,
                method='caption',
                size=(1800, 60),
                bg_color=None,
            ).with_duration(duration).with_position(("center", 350))
            print("发表信息创建完成")
        else:
            publish_clip = None
        
        # Create subtitle clips
        print("\n处理字幕...")
        subtitle_clips = create_subtitle_clips(subtitle_path, duration) if subtitle_path else []
        print(f"共处理 {len(subtitle_clips)} 条字幕")
        
        # Combine all clips
        print("\n组合视频片段...")
        waveform_clip = waveform_clip.with_position(("center", 510))
        video_layers = [title_clip]
        if publish_clip:
            video_layers.append(publish_clip)
        video_layers.append(waveform_clip)
        for text_clip, start_time in subtitle_clips:
            video_layers.append(text_clip.with_start(start_time))
        video = CompositeVideoClip(video_layers, size=(1920, 1080), bg_color=(0,0,0))
        print(f"共添加 {len(subtitle_clips)} 条字幕")
        
        # Add audio
        print("\n添加音频...")
        final_video = video.with_audio(audio)
        print("音频添加完成")
        
        # Write output file
        print(f"\n开始写入视频文件: {output_path}")
        final_video.write_videofile(output_path, fps=12)
        print("视频文件写入完成")
        
        # Clean up
        print("\n清理临时文件...")
        if hasattr(waveform_clip, '_cleanup'):
            waveform_clip._cleanup()
        print("清理完成")
        
    except Exception as e:
        print(f"\n错误: {str(e)}")
        print(f"错误类型: {type(e)}")
        import traceback
        print(f"错误堆栈:\n{traceback.format_exc()}")
        raise 