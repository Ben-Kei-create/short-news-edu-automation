import pytest
from unittest.mock import patch, MagicMock
import argparse
import requests # 追加

from modules.input_manager import parse_args, fetch_news_rss, get_themes
from modules.theme_selector import filter_duplicate_themes # get_themesで利用

# parse_argsのテスト
def test_parse_args_default_values():
    """引数なしの場合のデフォルト値をテスト"""
    with patch('sys.argv', ['make_short.py']):
        args = parse_args()
        assert args.theme is None
        assert args.bgm_path is None
        assert args.script_file is None
        assert args.manual_images is None
        assert args.use_sd_api is False
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
        "--use_sd_api",
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
        assert args.use_sd_api is True
        assert args.style == "anime"
        assert args.sd_model == "model_v1"
        assert args.lora_model == "lora_v1"
        assert args.lora_weight == 0.5
        assert args.font == "NotoSansJP"
        assert args.image_duration == 3.0

# fetch_news_rssのテスト
@patch('requests.get')
def test_fetch_news_rss_success(mock_requests_get):
    """RSSフィードの取得が成功した場合をテスト"""
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.content = b'<rss><channel><item><title>News 1</title></item><item><title>News 2</title></item></channel></rss>'
    mock_requests_get.return_value = mock_response

    news = fetch_news_rss()
    assert news == ["News 1", "News 2"]
    mock_requests_get.assert_called_once_with("https://news.google.com/rss?hl=ja&gl=JP&ceid=JP:ja", verify=False)

@patch('requests.get')
def test_fetch_news_rss_request_exception(mock_requests_get):
    """requests.exceptions.RequestExceptionが発生した場合をテスト"""
    mock_requests_get.side_effect = requests.exceptions.RequestException("Network error")
    news = fetch_news_rss()
    assert news == []

@patch('requests.get')
def test_fetch_news_rss_bozo_exception(mock_requests_get):
    """feedparser.FeedParserDict.bozoがTrueの場合をテスト"""
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.content = b'<rss><channel><item><title>News 1</title></item></channel>'
    mock_requests_get.return_value = mock_response

    # feedparserのbozo属性をモック
    with patch('feedparser.parse') as mock_feedparser_parse:
        mock_feed = MagicMock()
        mock_feed.bozo = True
        mock_feed.bozo_exception = "XML parsing error"
        mock_feed.entries = [MagicMock(title="News 1")] # bozoでもentriesは返る可能性がある
        mock_feedparser_parse.return_value = mock_feed

        news = fetch_news_rss()
        assert news == ["News 1"]

# get_themesのテスト
@patch('modules.input_manager.fetch_news_rss')
@patch('modules.input_manager.filter_duplicate_themes')
def test_get_themes_from_args(mock_filter_duplicate_themes, mock_fetch_news_rss):
    """--theme引数が指定された場合をテスト"""
    mock_args = argparse.Namespace(theme=["テーマA", "テーマB"])
    themes = get_themes(mock_args)
    assert themes == ["テーマA", "テーマB"]
    mock_fetch_news_rss.assert_not_called()
    mock_filter_duplicate_themes.assert_not_called()

@patch('modules.input_manager.fetch_news_rss')
@patch('modules.input_manager.filter_duplicate_themes')
def test_get_themes_auto_selection_success(mock_filter_duplicate_themes, mock_fetch_news_rss):
    """--theme引数なしで自動選定が成功した場合をテスト"""
    mock_args = argparse.Namespace(theme=None)
    # get_themesのロジックに合わせて、3つ以上のユニークなニュースを返すようにモック
    mock_fetch_news_rss.return_value = [f"News {i}" for i in range(5)] # 5つのニュースを返す
    mock_filter_duplicate_themes.return_value = [f"Unique News {i}" for i in range(5)] # 5つのユニークニュースを返す

    themes = get_themes(mock_args)
    assert len(themes) == 3 # 厳密に3件選定されることを確認
    assert themes[0] == "Unique News 0" # 1本目
    assert themes[1] == "Unique News 1" # 2本目
    assert themes[2] in [f"Unique News {i}" for i in range(2, 5)] # 3本目はランダムなので範囲で確認
    mock_fetch_news_rss.assert_called_once()
    mock_filter_duplicate_themes.assert_called_once()

@patch('modules.input_manager.fetch_news_rss')
@patch('modules.input_manager.filter_duplicate_themes')
def test_get_themes_auto_selection_no_news(mock_filter_duplicate_themes, mock_fetch_news_rss):
    """--theme引数なしでニュースが取得できなかった場合をテスト"""
    mock_args = argparse.Namespace(theme=None)
    mock_fetch_news_rss.return_value = []

    themes = get_themes(mock_args)
    assert themes == []
    mock_fetch_news_rss.assert_called_once()
    mock_filter_duplicate_themes.assert_not_called()