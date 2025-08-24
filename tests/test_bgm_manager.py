import pytest
from unittest.mock import patch, MagicMock
import os

from modules.bgm_manager import select_bgm

# settingsのモック
@pytest.fixture
def mock_settings():
    return {
        "general": {
            "default_bgm_candidates": [
                "input/bgm/default_bgm.mp3",
                "sample.mp4"
            ]
        }
    }

# select_bgmのテスト
@patch('os.path.exists')
def test_select_bgm_user_path_exists(mock_exists, mock_settings):
    """ユーザー指定パスが存在する場合をテスト"""
    mock_exists.return_value = True
    bgm_path = "/path/to/user_bgm.mp3"
    result = select_bgm(bgm_path, mock_settings)
    assert result == bgm_path
    mock_exists.assert_called_once_with(bgm_path)

@patch('os.path.exists')
def test_select_bgm_user_path_not_exists_fallback_default(mock_exists, mock_settings, capsys):
    """ユーザー指定パスが存在せず、デフォルトBGMが見つかる場合をテスト"""
    mock_exists.side_effect = [False, True, False] # user_path, default_bgm.mp3, sample.mp4
    bgm_path = "/path/to/non_existent_bgm.mp3"
    result = select_bgm(bgm_path, mock_settings)
    assert result == "input/bgm/default_bgm.mp3"
    captured = capsys.readouterr()
    assert "警告: 指定されたBGMファイル '/path/to/non_existent_bgm.mp3' が見つかりません。デフォルトBGMを探します。" in captured.out
    assert "-> デフォルトBGMとして 'input/bgm/default_bgm.mp3' を使用します。" in captured.out

@patch('os.path.exists')
def test_select_bgm_no_path_fallback_sample(mock_exists, mock_settings, capsys):
    """ユーザー指定パスなしで、デフォルトBGMが見つからず、sample.mp4が見つかる場合をテスト"""
    mock_exists.side_effect = [False, True] # default_bgm.mp3, sample.mp4
    result = select_bgm(None, mock_settings)
    assert result == "sample.mp4"
    captured = capsys.readouterr()
    assert "-> デフォルトBGMとして 'sample.mp4' を使用します。" in captured.out

@patch('os.path.exists')
def test_select_bgm_no_bgm_found(mock_exists, mock_settings, capsys):
    """どのBGMも見つからない場合をテスト"""
    mock_exists.return_value = False
    with pytest.raises(FileNotFoundError, match="BGMファイルが見つかりません。"):
        select_bgm(None, mock_settings)
    captured = capsys.readouterr()
    assert "エラー: BGMファイルが見つかりません。" in captured.out
