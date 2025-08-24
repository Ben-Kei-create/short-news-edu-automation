import pytest
from unittest.mock import patch, MagicMock
import argparse
import requests

# 変更: fetch_news_rss を fetch_news_from_feed に変更
from modules.input_manager import parse_args, fetch_news_from_feed, get_themes
from modules.theme_selector import filter_duplicate_themes

# parse_argsのテスト
def test_parse_args_default_values():
    """引数なしの場合のデフォルト値をテスト"""
    with patch('sys.argv', ['make_short.py']):
        args = parse_args()
        assert args.theme is None
        assert args.bgm_path is None
        assert args.script_file is None
        assert args.manual_images is None
        assert args.use_sd_api is True # 変更後のデフォルト値
        assert args.use_google_search is True # 変更後のデフォルト値
        assert args.use_dalle is True # 変更後のデフォルト値
        assert args.post_to_youtube is True # 変更後のデフォルト値
        assert args.style == "cinematic, dramatic"
        assert args.sd_model is None
        assert args.lora_model is None
        assert args.lora_weight == 0.8
        assert args.font is None
        assert args.image_duration == 5.0

def test_parse_args_custom_values():
    """カスタム引数を渡した場合の値をテスト"""
    test_args = [
        "--theme", "歴史", "科学",
        "--bgm_path", "./bgm.mp3",
        "--script_file", "./script.txt",
        "--manual_images", "./images",
        "--use_sd_api", "False", # Falseを指定してデフォルトを上書き
        "--use_google_search", "False",
        "--use_dalle", "False",
        "--post-to-youtube", "False",
        "--style", "anime",
        "--sd_model", "model_v1",
        "--lora_model", "lora_v1",
        "--lora_weight", "0.5",
        "--font", "NotoSansJP",
        "--image_duration", "3.0"
    ]
    with patch('sys.argv', ['make_short.py'] + test_args):
        args = parse_args()
        assert args.theme == ["歴史", "科学"]
        assert args.bgm_path == "./bgm.mp3"
        assert args.script_file == "./script.txt"
        assert args.manual_images == "./images"
        assert args.use_sd_api is False # 変更後のデフォルト値
        assert args.use_google_search is False # 変更後のデフォルト値
        assert args.use_dalle is False # 変更後のデフォルト値
        assert args.post_to_youtube is False # 変更後のデフォルト値
        assert args.style == "anime"
        assert args.sd_model == "model_v1"
        assert args.lora_model == "lora_v1"
        assert args.lora_weight == 0.5
        assert args.font == "NotoSansJP"
        assert args.image_duration == 3.0

# fetch_news_from_feedのテスト (旧 fetch_news_rss)
@patch('requests.get')
def test_fetch_news_from_feed_success(mock_requests_get):
    """RSSフィードの取得が成功した場合をテスト"""
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.content = b'<rss><channel><item><title>News 1</title></item><item><title>News 2</title></item></channel></rss>'
    mock_requests_get.return_value = mock_response

    # 変更: fetch_news_from_feed を呼び出す
    news = fetch_news_from_feed("http://example.com/rss") # URLを渡す
    assert news == ["News 1", "News 2"]
    mock_requests_get.assert_called_once_with("http://example.com/rss", verify=False)

@patch('requests.get')
def test_fetch_news_from_feed_request_exception(mock_requests_get):
    """requests.exceptions.RequestExceptionが発生した場合をテスト"""
    mock_requests_get.side_effect = requests.exceptions.RequestException("Network error")
    # 変更: fetch_news_from_feed を呼び出す
    news = fetch_news_from_feed("http://example.com/rss")
    assert news == []

@patch('requests.get')
def test_fetch_news_from_feed_bozo_exception(mock_requests_get):
    """feedparser.FeedParserDict.bozoがTrueの場合をテスト"""
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.content = b'<rss><channel><item><title>News 1</title></item></channel>'
    mock_requests_get.return_value = mock_response

    with patch('feedparser.parse') as mock_feedparser_parse:
        mock_feed = MagicMock()
        mock_feed.bozo = True
        mock_feed.bozo_exception = "XML parsing error"
        mock_feed.entries = [MagicMock(title="News 1")] # bozoでもentriesは返る可能性がある
        mock_feedparser_parse.return_value = mock_feed

        # 変更: fetch_news_from_feed を呼び出す
        news = fetch_news_from_feed("http://example.com/rss")
        assert news == ["News 1"]

# get_themesのテスト
# settings 引数を追加し、モックする
@patch('modules.input_manager.fetch_news_from_feed') # 変更
@patch('modules.input_manager.filter_duplicate_themes')
def test_get_themes_from_args(mock_filter_duplicate_themes, mock_fetch_news_from_feed):
    """--theme引数が指定された場合をテスト"""
    mock_args = argparse.Namespace(theme=["テーマA", "テーマB"])
    mock_settings = MagicMock() # settings をモック
    themes = get_themes(mock_args, mock_settings) # settings を渡す
    assert themes == ["テーマA", "テーマB"]
    mock_fetch_news_from_feed.assert_not_called()
    mock_filter_duplicate_themes.assert_not_called()

@patch('modules.input_manager.fetch_news_from_feed') # 変更
@patch('modules.input_manager.filter_duplicate_themes')
def test_get_themes_auto_selection_success(mock_filter_duplicate_themes, mock_fetch_news_from_feed):
    """--theme引数なしで自動選定が成功した場合をテスト"""
    mock_args = argparse.Namespace(theme=None)
    mock_settings = { # settings をモック
        'rss': {
            'feeds': [
                {'name': 'Feed1', 'url': 'http://feed1.com/rss', 'keywords': [], 'categories': []},
                {'name': 'Feed2', 'url': 'http://feed2.com/rss', 'keywords': [], 'categories': []}
            ],
            'max_articles_per_feed': 5
        }
    }
    # get_themesのロジックに合わせて、十分なニュースを返すようにモック
    mock_fetch_news_from_feed.side_effect = [
        [f"News {i}" for i in range(5)], # Feed1から5件
        [f"More News {i}" for i in range(5)] # Feed2から5件
    ]
    mock_filter_duplicate_themes.return_value = [f"Unique News {i}" for i in range(10)] # 10個のユニークニュースを返す

    themes = get_themes(mock_args, mock_settings) # settings を渡す
    assert len(themes) == 3 # 厳密に3件選定されることを確認
    assert themes[0] == "Unique News 0" # 1本目
    assert themes[1] == "Unique News 1" # 2本目
    assert themes[2] in [f"Unique News {i}" for i in range(2, 10)] # 3本目はランダムなので範囲で確認
    assert mock_fetch_news_from_feed.call_count == 2 # 2つのフィードが呼び出されたことを確認
    mock_filter_duplicate_themes.assert_called_once()

@patch('modules.input_manager.fetch_news_from_feed') # 変更
@patch('modules.input_manager.filter_duplicate_themes')
def test_get_themes_auto_selection_no_news(mock_filter_duplicate_themes, mock_fetch_news_from_feed):
    """--theme引数なしでニュースが取得できなかった場合をテスト"""
    mock_args = argparse.Namespace(theme=None)
    mock_settings = { # settings をモック
        'rss': {
            'feeds': [
                {'name': 'Feed1', 'url': 'http://feed1.com/rss', 'keywords': [], 'categories': []}
            ],
            'max_articles_per_feed': 5
        }
    }
    mock_fetch_news_from_feed.return_value = []

    themes = get_themes(mock_args, mock_settings) # settings を渡す
    assert themes == []
    mock_fetch_news_from_feed.assert_called_once()
    mock_filter_duplicate_themes.assert_not_called()
