# modules/input_manager.py
import argparse
import feedparser
import random
from .theme_selector import filter_duplicate_themes, select_themes_for_batch

def parse_args():
    parser = argparse.ArgumentParser(description="ショート動画自動生成パイプライン")
    parser.add_argument("--theme", type=str, nargs='+', help="動画テーマを1つ以上指定")
    parser.add_argument("--bgm_path", type=str, help="BGMファイルパス")
    parser.add_argument("--style", type=str, help="画像の画風")
    parser.add_argument("--script_file", type=str, help="台本ファイルパス")
    parser.add_argument("--manual_images", type=str, help="手動画像フォルダパス")
    return parser.parse_args()

import requests # Added import

def fetch_news_rss(rss_url="https://news.google.com/rss?hl=ja&gl=JP&ceid=JP:ja"):
    try:
        response = requests.get(rss_url, verify=False) # Use requests to fetch, disable SSL verify
        response.raise_for_status() # Raise an exception for HTTP errors
        feed = feedparser.parse(response.content) # Pass content to feedparser
    except requests.exceptions.RequestException as e:
        print(f"RSSフィードの取得に失敗しました: {e}")
        return []
    
    if feed.bozo:
        print(f"RSSフィードの解析に失敗しました: {feed.bozo_exception}")
        return []
    news_items = [entry.title for entry in feed.entries]
    return news_items

def get_themes(args, batch_size=3):
    if args.theme:
        print(f"{len(args.theme)}件のテーマが指定されました。")
        return args.theme
    
    print("テーマが指定されていないため、Google Newsから自動取得します。")
    news = fetch_news_rss()
    if not news:
        print("ニュースが取得できませんでした。")
        return []

    unique_news = filter_duplicate_themes(news)
    random.shuffle(unique_news) # ランダムに並び替え
    
    selected_themes = select_themes_for_batch(unique_news, batch_size=batch_size)
    print(f"{len(selected_themes)}件のテーマを自動選定しました。")
    return selected_themes
