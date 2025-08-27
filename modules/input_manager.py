# modules/input_manager.py
import argparse
import feedparser
import random
import traceback
import requests
from .theme_selector import filter_duplicate_themes, select_themes_for_batch
from .utils import load_settings # settingsを読み込むために追加

def parse_args():
    parser = argparse.ArgumentParser(
        description="設定ファイルに基づきショート動画を自動生成します。引数で一部の動作を上書きできます。"
    )
    
    # --- 動作を上書きするオプション引数 ---
    parser.add_argument(
        "--theme", 
        type=str, 
        nargs='+', 
        help="RSS取得をスキップし、指定したテーマで動画を生成します。"
    )
    parser.add_argument(
        "--script-path", 
        type=str, 
        help="台本生成をスキップし、指定したテキストファイルを使用します。"
    )
    parser.add_argument(
        "--bgm-path", 
        type=str, 
        help="settings.yamlのBGM設定を上書きし、指定したBGMファイルを使用します。"
    )
    
    # YouTube投稿設定の上書き
    post_group = parser.add_mutually_exclusive_group()
    post_group.add_argument(
        "--post", 
        action="store_true", 
        help="settings.yamlの設定を無視して、強制的にYouTubeに投稿します。"
    )
    post_group.add_argument(
        "--no-post", 
        action="store_true", 
        help="settings.yamlの設定を無視して、YouTubeへの投稿を強制的にスキップします。"
    )

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

def get_themes(settings):
    if 'runtime_themes' in settings:
        print(f"{len(settings['runtime_themes'])}件のテーマが指定されました。")
        return settings['runtime_themes']
    
    print("テーマが指定されていないため、設定ファイルに基づいてニュースから自動取得します。")
    
    all_news_titles = []
    rss_settings = settings.get('rss', {})
    feeds = rss_settings.get('feeds', [])
    max_articles_per_feed = rss_settings.get('max_articles_per_feed', 5)

    if not feeds:
        print("エラー: settings.yamlにRSSフィードが設定されていません。")
        return []

    for feed_url in feeds:
        feed_name = feed_url # URLをそのまま名前として使用

        if not feed_url:
            print(f"警告: フィード '{feed_name}' のURLが設定されていません。スキップします。")
            continue
        
        print(f"  - フィード '{feed_name}' からニュースを取得中...")
        # 現在のsettings.yamlのRSSフィードはURL文字列のみなので、keywords/categoriesは渡さない
        news_from_feed = fetch_news_from_feed(
            feed_url, 
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