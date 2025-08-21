# modules/post_log_manager.py
import csv
from datetime import datetime

def log_video(video_file, theme, images, style, bgm_file, log_file="output/logs/log.csv"):
    with open(log_file, mode='a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([video_file, theme, ";".join(images), style, bgm_file, datetime.now()])
    print(f"ログを記録: {log_file}")

def post_to_sns(video_file, title="", description="", hashtags=None):
    print(f"SNSに投稿: {video_file}")