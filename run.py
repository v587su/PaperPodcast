import argparse
import os
from podcastfy.client import generate_podcast

parser = argparse.ArgumentParser()
parser.add_argument("--url", type=str, required=True)
args = parser.parse_args()

custom_config = {
    "podcast_name": "Third Audience Podcast",
    "word_count": 4500,  # 增加字数容纳论文拆解细节
    "conversation_style": ["humorous", "casual", "critical", "expository"], 
    "roles": {
        "person1": "Paper Analyst",  
        "person2": "Devil's Advocate"  
    },
    "dialogue_structure": [
        "Cold Open (Hook)",  # 新增悬念开场
        "Paper Overview", 
        "Methodology Deep Dive",
        "Findings Breakdown",
        "Limitations Debate",  # 强化批判性讨论
        "Real-world Implications",
    ],
    "engagement_techniques": [
        "socratic questioning",
        "data visualization metaphors",  # 新增数据比喻
        "academic gossip",  # 提及作者/评审趣闻
        "cross-disciplinary parallels"
    ],
    "segment_rules": {
        "max_duration": 10,  # 单环节最长分钟数
        "mandatory_elements": [
            "citation timestamps",  # 要求标注论文页码
            "jargon_alerts"  # 标记专业术语解释点
        ]
    },
    "creativity": 0.3  # 小幅提升用于生动比喻
}

file_path = generate_podcast(
    urls=[args.url],
    llm_model_name='gemini-2.5-pro-preview-06-05',
    conversation_config=custom_config
)

#rename the mp3 file name to todays' date
import datetime
today = datetime.datetime.now().strftime("%Y-%m-%d")
os.rename(file_path, f"{today}-{args.url.split('/')[-1].split('.')[0]}.mp3")
