# modules/input_manager.py
import argparse
import feedparser
import random
import traceback # 追加
from .theme_selector import filter_duplicate_themes, select_themes_for_batch

def parse_args():
    parser = argparse.ArgumentParser(description="ショート動画自動生成パイプライン")
    # 全般設定
    parser.add_argument("--theme", type=str, nargs='+', help="動画テーマを1つ以上指定")
    parser.add_argument("--bgm_path", type=str, help="BGMファイルパス")
    parser.add_argument("--script_file", type=str, help="台本ファイルパス")
    parser.add_argument("--manual_images", type=str, help="手動画像フォルダパス")

    # Stable Diffusion設定
    parser.add_argument("--use_sd_api", action='store_true', help="Stable Diffusion APIを使用して画像を生成する")
    parser.add_argument("--style", type=str, default="cinematic, dramatic", help="画像の画風に関連するプロンプト")
    parser.add_argument("--sd_model", type=str, help="使用するStable Diffusionのベースモデル名")
    parser.add_argument("--lora_model", type=str, help="使用するLoRAモデル名 (拡張子なし)")
    parser.add_argument("--lora_weight", type=float, default=0.8, help="LoRAの適用強度 (デフォルト: 0.8)")

    # 字幕・フォント設定
    parser.add_argument("--font", type=str, help="字幕に使用するフォントファイル名 (input/fonts/ 内)")

    # 動画設定
    parser.add_argument("--image_duration", type=float, default=5.0, help="各画像の表示時間 (秒) (デフォルト: 5.0)")

    return parser.parse_args()

import requests # Added import

def fetch_news_rss(rss_url="https://news.google.com/rss?hl=ja&gl=JP&ceid=JP:ja"):
    try:
        response = requests.get(rss_url, verify=False) # Use requests to fetch, disable SSL verify
        response.raise_for_status() # Raise an exception for HTTP errors
        feed = feedparser.parse(response.content) # Pass content to feedparser
    except requests.exceptions.RequestException as e:
        print(f"エラー: RSSフィードの取得に失敗しました。ネットワーク接続またはURLを確認してください: {e}")
        traceback.print_exc() # 詳細なスタックトレースを出力
        return []
    except Exception as e: # その他の予期せぬエラーを捕捉
        print(f"エラー: RSSフィードの取得中に予期せぬエラーが発生しました: {e}")
        traceback.print_exc()
        return []
    
    if feed.bozo:
        print(f"警告: RSSフィードの解析中に問題が発生しました: {feed.bozo_exception}")
        # 解析エラーがあっても、可能な限りニュースアイテムを返す
        news_items = [entry.title for entry in feed.entries]
        return news_items
    news_items = [entry.title for entry in feed.entries]
    return news_items

def get_themes(args, batch_size=3):
    if args.theme:
        print(f"{len(args.theme)}件のテーマが指定されました。")
        return args.theme
    
    print("テーマが指定されていないため、Google Newsから自動取得します。")
    news = fetch_news_rss()
    print(f"DEBUG: news = {news}") # デバッグ用
    if not news:
        print("ニュースが取得できませんでした。")
        return []

    unique_news = filter_duplicate_themes(news)
    print(f"DEBUG: unique_news = {unique_news}") # デバッグ用
    
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
