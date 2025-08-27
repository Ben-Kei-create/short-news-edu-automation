# tests/test_script_generator.py
from unittest.mock import patch, MagicMock, call
import pytest
from modules.script_generator import generate_script
from google.generativeai import types

@pytest.fixture
def mock_settings():
    """テスト用の基本的なsettingsオブジェクトを返すフィクスチャ"""
    return {
        'api_keys': {
            'gemini': 'mock_gemini_api_key'
        },
        'script_generation': {
            'length': 'short',
            'tone': 'educational_humorous',
            'target_audience': 'general_public',
            'max_script_length_chars': 1000
        }
    }

@patch('google.generativeai.GenerativeModel')
@patch('google.generativeai.configure')
def test_generate_script_success(mock_configure, mock_GenerativeModel, mock_settings):
    """正常系: 台本の生成と抽出が成功するケース"""
    mock_model_instance = MagicMock()
    mock_GenerativeModel.return_value = mock_model_instance
    mock_response = MagicMock()
    mock_response.text = "【台本】\nテストの台本内容\n\n【文字数】320文字"
    mock_model_instance.generate_content.return_value = mock_response

    result = generate_script("テストテーマ", mock_settings)

    assert result == "テストの台本内容"
    mock_configure.assert_called_once_with(api_key='mock_gemini_api_key')
    mock_GenerativeModel.assert_called_once_with('models/gemini-1.5-flash')
    mock_model_instance.generate_content.assert_called_once()

@patch('google.generativeai.GenerativeModel')
@patch('google.generativeai.configure')
def test_generate_script_regex_mismatch(mock_configure, mock_GenerativeModel, mock_settings):
    """異常系: APIレスポンスの形式が不正で、正規表現がマッチしないケース"""
    mock_model_instance = MagicMock()
    mock_GenerativeModel.return_value = mock_model_instance
    mock_response = MagicMock()
    mock_response.text = "予期しない形式のレスポンスです。"
    mock_model_instance.generate_content.return_value = mock_response

    result = generate_script("テストテーマ", mock_settings)

    assert result is None

@patch('google.generativeai.GenerativeModel')
@patch('google.generativeai.configure')
def test_generate_script_truncation(mock_configure, mock_GenerativeModel, mock_settings):
    """正常系: 生成された台本が最大文字数を超えて、正しく切り詰められるケース"""
    mock_settings['script_generation']['max_script_length_chars'] = 10
    long_script = "これは非常に長い台本です。10文字を超えています。"
    
    mock_model_instance = MagicMock()
    mock_GenerativeModel.return_value = mock_model_instance
    mock_response = MagicMock()
    mock_response.text = f"【台本】{long_script}【文字数】100文字"
    mock_model_instance.generate_content.return_value = mock_response

    result = generate_script("テストテーマ", mock_settings)

    assert result == long_script[:10] + "..."
    assert len(result) == 13

@patch('google.generativeai.GenerativeModel')
@patch('google.generativeai.configure')
def test_generate_script_prompt_parameters(mock_configure, mock_GenerativeModel, mock_settings):
    """正常系: settingsのパラメータがプロンプトに正しく反映されるケース"""
    mock_settings['script_generation']['length'] = 'medium'
    mock_settings['script_generation']['tone'] = '専門的'
    mock_settings['script_generation']['target_audience'] = '研究者'

    mock_model_instance = MagicMock()
    mock_GenerativeModel.return_value = mock_model_instance
    mock_response = MagicMock()
    mock_response.text = "【台本】テスト【文字数】10文字"
    mock_model_instance.generate_content.return_value = mock_response

    generate_script("テストテーマ", mock_settings)

    # generate_contentに渡されたプロンプトを取得
    actual_prompt = mock_model_instance.generate_content.call_args[0][0]
    
    assert "厳密に90秒になるように" in actual_prompt
    assert "トーンは「専門的」" in actual_prompt
    assert "ターゲット視聴者は「研究者」" in actual_prompt

@patch('google.generativeai.configure')
def test_generate_script_no_api_key(mock_configure, mock_settings):
    """異常系: APIキーが設定されていないケース"""
    mock_settings['api_keys']['gemini'] = ""
    
    with pytest.raises(ValueError, match="設定ファイルに 'api_keys.gemini' が設定されていません。"):
        generate_script("テストテーマ", mock_settings)

@patch('google.generativeai.GenerativeModel')
@patch('google.generativeai.configure')
def test_generate_script_blocked_prompt(mock_configure, mock_GenerativeModel, mock_settings):
    """異常系: APIからBlockedPromptExceptionが返されるケース"""
    mock_model_instance = MagicMock()
    mock_GenerativeModel.return_value = mock_model_instance
    mock_model_instance.generate_content.side_effect = types.BlockedPromptException("Blocked")

    result = generate_script("不適切なテーマ", mock_settings)

    assert result == "エラーにより台本を生成できませんでした。テーマ: 不適切なテーマ"

@patch('google.generativeai.GenerativeModel')
@patch('google.generativeai.configure')
def test_generate_script_generic_exception(mock_configure, mock_GenerativeModel, mock_settings):
    """異常系: その他の一般的な例外が発生するケース"""
    mock_model_instance = MagicMock()
    mock_GenerativeModel.return_value = mock_model_instance
    mock_model_instance.generate_content.side_effect = Exception("Network error")

    result = generate_script("テストテーマ", mock_settings)

    assert result == "エラーにより台本を生成できませんでした。テーマ: テストテーマ"