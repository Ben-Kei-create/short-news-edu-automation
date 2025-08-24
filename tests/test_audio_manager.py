import pytest
from unittest.mock import patch, MagicMock, mock_open
import os

from modules.audio_manager import generate_voice

# settingsのモック
@pytest.fixture
def mock_settings():
    return {
        "google_tts": {
            "voice_name": "ja-JP-Wavenet-A",
            "ssml_gender": "FEMALE",
            "speaking_rate": 1.25,
            "min_duration_seconds": 58
        }
    }

# generate_voiceのテスト
@patch('modules.audio_manager.AudioFileClip')
@patch('google.cloud.texttospeech.TextToSpeechClient')
@patch('os.makedirs')
@patch('builtins.open', new_callable=mock_open)
@patch('os.path.exists', return_value=True)
@patch('os.path.isfile', return_value=True)
def test_generate_voice_success(mock_isfile, mock_exists, mock_file_open, mock_makedirs, mock_TextToSpeechClient, mock_AudioFileClip, mock_settings):
    """音声生成が成功した場合をテスト"""
    # Google Cloud TTSクライアントのモック
    mock_client_instance = MagicMock()
    mock_TextToSpeechClient.return_value = mock_client_instance
    mock_client_instance.synthesize_speech.return_value.audio_content = b"mock_audio_content"

    # AudioFileClipのモック
    mock_audio_clip_instance = MagicMock()
    mock_audio_clip_instance.duration = 5.0
    mock_audio_clip_instance.close.return_value = None
    
    # AudioFileClipコンストラクタのモック - ファイルパスに関係なく常にモックインスタンスを返す
    mock_AudioFileClip.return_value = mock_audio_clip_instance

    script_text = "これはテストです。二つ目の文です。"
    audio_segments_info = generate_voice(script_text, mock_settings)

    # アサーション
    assert len(audio_segments_info) == 2
    assert audio_segments_info[0]['duration'] == 5.0
    assert audio_segments_info[1]['duration'] == 5.0
    assert "これはテストです。" in audio_segments_info[0]['text']
    assert "二つ目の文です。" in audio_segments_info[1]['text']
    
    # モック呼び出しの検証
    mock_TextToSpeechClient.assert_called_once()
    assert mock_client_instance.synthesize_speech.call_count == 2
    assert mock_AudioFileClip.call_count == 2
    assert mock_audio_clip_instance.close.call_count == 2

@patch('google.cloud.texttospeech.TextToSpeechClient')
def test_generate_voice_client_init_error(mock_TextToSpeechClient, mock_settings):
    """Google Cloud TTSクライアント初期化エラーが発生した場合をテスト"""
    mock_TextToSpeechClient.side_effect = Exception("Init Error")

    script_text = "テスト"
    audio_segments_info = generate_voice(script_text, mock_settings)

    assert audio_segments_info == []

@patch('modules.audio_manager.AudioFileClip')
@patch('google.cloud.texttospeech.TextToSpeechClient')
@patch('os.makedirs')
@patch('builtins.open', new_callable=mock_open)
@patch('os.path.exists', return_value=True)
@patch('os.path.isfile', return_value=True)
def test_generate_voice_synthesis_error(mock_isfile, mock_exists, mock_file_open, mock_makedirs, mock_TextToSpeechClient, mock_AudioFileClip, mock_settings):
    """音声合成エラーが発生した場合をテスト"""
    mock_client_instance = MagicMock()
    mock_TextToSpeechClient.return_value = mock_client_instance
    mock_client_instance.synthesize_speech.side_effect = Exception("Synthesis Error")

    script_text = "テスト"
    audio_segments_info = generate_voice(script_text, mock_settings)

    assert len(audio_segments_info) == 1
    assert audio_segments_info[0]['path'] is None
    assert audio_segments_info[0]['duration'] == 0
    assert "テスト" in audio_segments_info[0]['text']
