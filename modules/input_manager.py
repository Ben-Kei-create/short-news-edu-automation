# modules/input_manager.py
import argparse
import feedparser

def parse_args():
    parser = argparse.ArgumentParser(description="ショート動画自動生成パイプライン")
    parser.add_argument("--theme", type=str, help="動画テーマを指定")
    parser.add_argument("--bgm_path", type=str, help="BGMファイルパス")
    parser.add_argument("--style", type=str, help="画像の画風")
    parser.add_argument("--script_file", type=str, help="台本ファイルパス")
    parser.add_argument("--manual_images", type=str, help="手動画像フォルダパス")
    return parser.parse_args()

def fetch_news_rss(rss_url="https://news.google.com/rss"):
    feed = feedparser.parse(rss_url)
    news_items = [entry.title for entry in feed.entries]
    return news_items

def get_theme(args):
    if args.theme:
        return args.theme
    news = fetch_news_rss()
    # ニュースからランダムで1件選ぶ
    import random
    return random.choice(news)