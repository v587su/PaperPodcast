import os
import datetime
from loguru import logger

def generate_podcast(urls, llm_model_name='gemini-2.5-pro-preview-06-05', conversation_config=None, mp3_output_dir=None):
    """
    实际实现：根据传入的PDF文件路径列表，生成播客音频文件
    """
    if not urls or not isinstance(urls, list):
        logger.error("urls 参数无效: {}", urls)
        raise ValueError("urls must be a list of file paths")
    pdf_path = urls[0]
    logger.info("开始生成播客，PDF路径: {}", pdf_path)

    # 默认对话配置
    if conversation_config is None:
        conversation_config = {
            "podcast_name": "Third Audience Podcast",
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

    # 这里应调用实际的播客生成逻辑
    # TODO: 替换为真实的 LLM+TTS 处理
    # 目前仅模拟生成 mp3 文件
    mp3_path = pdf_path.replace('.pdf', '.mp3')
    with open(mp3_path, 'wb') as f:
        f.write(b'FAKE MP3 CONTENT')

    # 按日期重命名
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    base_name = os.path.splitext(os.path.basename(pdf_path))[0]
    new_mp3_name = f"{today}-{base_name}.mp3"
    new_mp3_path = os.path.join(os.path.dirname(mp3_path), new_mp3_name)
    os.rename(mp3_path, new_mp3_path)
    logger.success("播客生成完成，输出文件: {}", new_mp3_path)

    return new_mp3_path