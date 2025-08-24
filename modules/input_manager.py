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
    
    selected_themes = []

    # 1本目: 最近のトップニュース (Recent Top News)
    if len(unique_news) > 0:
        selected_themes.append(unique_news[0])
        print(f"  - 1本目 (最近のトップニュース): {unique_news[0]}")
    
    # 2本目: トレンド (Trends) - 弱い代理
    # Google News RSSから直接「トレンド」を特定するのは困難です。
    # ここでは、2番目に新しいニュースを「トレンド」の代理とします。
    # より正確なトレンドニュースのためには、専用のAPI（例: Google Trends API）が必要です。
    if len(unique_news) > 1:
        selected_themes.append(unique_news[1])
        print(f"  - 2本目 (トレンド - 弱い代理): {unique_news[1]}")

    # 3本目: あまり知られていないが面白いニュース (Less-known but interesting news) - 弱い代理
    # 「面白い」の定義は主観的であり、RSSフィードから自動で選定するのは非常に困難です。
    # ここでは、上位2つ以外のニュースからランダムに1つを選びます。
    # より適切なニュースのためには、手動でのキュレーションや、より高度なニュース分析が必要です。
    if len(unique_news) > 2:
        remaining_news = unique_news[2:]
        if remaining_news:
            random_interesting_news = random.choice(remaining_news)
            selected_themes.append(random_interesting_news)
            print(f"  - 3本目 (あまり知られていないが面白いニュース - 弱い代理): {random_interesting_news})")
        
    print(f"{len(selected_themes)}件のテーマを自動選定しました。")
    return selected_themes
