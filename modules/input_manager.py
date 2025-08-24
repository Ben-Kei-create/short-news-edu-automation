# modules/input_manager.py
import argparse
import feedparser
import random
import traceback
import requests
from .theme_selector import filter_duplicate_themes, select_themes_for_batch
from .utils import load_settings # settingsを読み込むために追加

def parse_args():
    parser = argparse.ArgumentParser(description="ショート動画自動生成パイプライン")
    # 全般設定
    parser.add_argument("--theme", type=str, nargs='+', help="動画テーマを1つ以上指定")
    parser.add_argument("--bgm_path", type=str, help="BGMファイルパス")
    parser.add_argument("--script_file", type=str, help="台本ファイルパス")
    parser.add_argument("--manual_images", type=str, help="手動画像フォルダパス")

    # 画像生成AI設定
    parser.add_argument("--use_sd_api", action='store_false', default=True, help="Stable Diffusion APIを使用して画像を生成する (デフォルト: True)")
    parser.add_argument("--use_google_search", action='store_false', default=True, help="Google Custom Searchを使用してWebから画像を検索・利用する (デフォルト: True)")
    parser.add_argument("--use_dalle", action='store_false', default=True, help="DALL-Eを使用して画像を生成する (デフォルト: True)")
    parser.add_argument("--style", type=str, default="cinematic, dramatic", help="画像の画風に関連するプロンプト")
    parser.add_argument("--sd_model", type=str, help="使用するStable Diffusionのベースモデル名")
    parser.add_argument("--lora_model", type=str, help="使用するLoRAモデル名 (拡張子なし)")
    parser.add_argument("--lora_weight", type=float, default=0.8, help="LoRAの適用強度 (デフォルト: 0.8)")

    # 字幕・フォント設定
    parser.add_argument("--font", type=str, help="字幕に使用するフォントファイル名 (input/fonts/ 内)")

    # 動画設定
    parser.add_argument("--image_duration", type=float, default=5.0, help="各画像の表示時間 (秒) (デフォルト: 5.0)")

    # SNS投稿設定
    parser.add_argument("--post-to-youtube", action='store_false', default=True, help="生成した動画をYouTubeにアップロードする (デフォルト: True)")

    return parser.parse_args()

def fetch_news_from_feed(rss_url, keywords=None, categories=None, max_articles=None):
    """
    単一のRSSフィードからニュースを取得し、キーワード/カテゴリでフィルタリングする。
    """
    news_items = []
    try:
        response = requests.get(rss_url, verify=False)
        response.raise_for_status()
        feed = feedparser.parse(response.content)

        if feed.bozo:
            print(f"警告: RSSフィード ({rss_url}) の解析中に問題が発生しました: {feed.bozo_exception}")
        
        for entry in feed.entries:
            title = entry.title
            content = entry.get('summary', '') or entry.get('description', '') # summary or description for content
            
            # キーワードフィルタリング
            if keywords:
                if not any(keyword.lower() in title.lower() or keyword.lower() in content.lower() for keyword in keywords):
                    continue
            
            # カテゴリフィルタリング (feedparserのcategoriesはタプルリスト)
            if categories:
                entry_categories = [tag['term'].lower() for tag in entry.get('tags', [])]
                if not any(cat.lower() in entry_categories for cat in categories):
                    continue
            
            news_items.append(title)
            if max_articles and len(news_items) >= max_articles:
                break

    except requests.exceptions.RequestException as e:
        print(f"エラー: RSSフィード ({rss_url}) の取得に失敗しました。詳細: {e}")
        traceback.print_exc()
    except Exception as e:
        print(f"エラー: RSSフィード ({rss_url}) の処理中に予期せぬエラーが発生しました。詳細: {e}")
        traceback.print_exc()
    return news_items

def get_themes(args, settings):
    if args.theme:
        print(f"{len(args.theme)}件のテーマが指定されました。")
        return args.theme
    
    print("テーマが指定されていないため、設定ファイルに基づいてニュースから自動取得します。")
    
    all_news_titles = []
    rss_settings = settings.get('rss', {})
    feeds = rss_settings.get('feeds', [])
    max_articles_per_feed = rss_settings.get('max_articles_per_feed', 5)

    if not feeds:
        print("エラー: settings.yamlにRSSフィードが設定されていません。")
        return []

    for feed_config in feeds:
        feed_name = feed_config.get('name', 'Unknown Feed')
        feed_url = feed_config.get('url')
        feed_keywords = feed_config.get('keywords')
        feed_categories = feed_config.get('categories')

        if not feed_url:
            print(f"警告: フィード '{feed_name}' のURLが設定されていません。スキップします。")
            continue
        
        print(f"  - フィード '{feed_name}' からニュースを取得中...")
        news_from_feed = fetch_news_from_feed(
            feed_url, 
            keywords=feed_keywords, 
            categories=feed_categories, 
            max_articles=max_articles_per_feed
        )
        all_news_titles.extend(news_from_feed)
    
    if not all_news_titles:
        print("ニュースが取得できませんでした。")
        return []

    unique_news = filter_duplicate_themes(all_news_titles)
    print(f"DEBUG: unique_news = {unique_news}") # デバッグ用
    
    selected_themes = []

    # 1本目: 最近のトップニュース (Recent Top News)
    if len(unique_news) > 0:
        selected_themes.append(unique_news[0])
        print(f"  - 1本目 (最近のトップニュース): {unique_news[0]}")
    
    # 2本目: トレンド (Trends) - 弱い代理
    if len(unique_news) > 1:
        selected_themes.append(unique_news[1])
        print(f"  - 2本目 (トレンド - 弱い代理): {unique_news[1]}")

    # 3本目: あまり知られていないが面白いニュース (Less-known but interesting news) - 弱い代理
    if len(unique_news) > 2:
        remaining_news = unique_news[2:]
        if remaining_news:
            random_interesting_news = random.choice(remaining_news)
            selected_themes.append(random_interesting_news)
            print(f"  - 3本目 (あまり知られていないが面白いニュース - 弱い代理): {random_interesting_news})")
        
    print(f"{len(selected_themes)}件のテーマを自動選定しました。")
    return selected_themes