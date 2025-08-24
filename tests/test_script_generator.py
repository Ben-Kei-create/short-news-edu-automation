# tests/test_script_generator.py
from unittest.mock import patch, MagicMock
import pytest
from modules.script_generator import generate_script
# google.generativeai.types を正しくインポート
from google.generativeai import types

@pytest.fixture
def mock_settings():
    return {
        'api_keys': {
            'gemini': 'mock_gemini_api_key'
        }
    }

@patch('google.generativeai.GenerativeModel')
@patch('google.generativeai.configure')
def test_generate_script_success(mock_configure, mock_GenerativeModel, mock_settings):
    """正常なケースをテスト"""
    # モックの設定
    mock_model_instance = MagicMock()
    mock_GenerativeModel.return_value = mock_model_instance
    mock_response = MagicMock()
    mock_response.text = "【台本】\nテストの台本内容\n\n【文字数】320文字"
    mock_model_instance.generate_content.return_value = mock_response

    # テスト実行
    theme = "テストテーマ"
    result = generate_script(theme, mock_settings)

    # 検証
    assert result == "【台本】\nテストの台本内容\n\n【文字数】320文字"
    mock_configure.assert_called_once_with(api_key='mock_gemini_api_key')
    mock_GenerativeModel.assert_called_once_with('models/gemini-2.5-flash')
    mock_model_instance.generate_content.assert_called_once()

@patch('google.generativeai.GenerativeModel')
@patch('google.generativeai.configure')
def test_generate_script_no_api_key(mock_configure, mock_GenerativeModel, mock_settings):
    """APIキーが設定されていない場合をテスト"""
    mock_settings['api_keys']['gemini'] = None
    
    with pytest.raises(ValueError, match="設定ファイルに 'api_keys.gemini' が設定されていません。"):
        generate_script("テストテーマ", mock_settings)

@patch('google.generativeai.GenerativeModel')
@patch('google.generativeai.configure')
def test_generate_script_blocked_prompt_exception(mock_configure, mock_GenerativeModel, mock_settings):
    """BlockedPromptExceptionが発生した場合をテスト"""
    mock_model_instance = MagicMock()
    mock_GenerativeModel.return_value = mock_model_instance
    mock_model_instance.generate_content.side_effect = types.BlockedPromptException("Blocked")

    theme = "テストテーマ"
    result = generate_script(theme, mock_settings)

    assert result == f"エラーにより台本を生成できませんでした。テーマ: {theme}"

@patch('google.generativeai.GenerativeModel')
@patch('google.generativeai.configure')
def test_generate_script_other_exception(mock_configure, mock_GenerativeModel, mock_settings):
    """その他のExceptionが発生した場合をテスト"""
    mock_model_instance = MagicMock()
    mock_GenerativeModel.return_value = mock_model_instance
    mock_model_instance.generate_content.side_effect = Exception("Other error")

    theme = "テストテーマ"
    result = generate_script(theme, mock_settings)

    assert result == f"エラーにより台本を生成できませんでした。テーマ: {theme}"
