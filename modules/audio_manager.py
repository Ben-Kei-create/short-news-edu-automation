# modules/audio_manager.py
import os
from pathlib import Path
import requests

# APIキーは環境変数 ELEVENLABS_API_KEY に保存
API_KEY = os.getenv("ELEVENLABS_API_KEY")
BASE_URL = "https://api.elevenlabs.io/v1/text-to-speech"

def generate_voice(script_text, voice_id="21m00Tcm4TlvDq8ikWAM", output_file="voice.mp3"):
    """
    ElevenLabs TTSで台本を音声化
    Args:
        script_text (str): 音声化したいテキスト
        voice_id (str): 音声ID（ElevenLabsの声）
        output_file (str): 出力音声ファイル名
    Returns:
        str: 生成音声ファイルパス
    """
    if not API_KEY:
        raise ValueError("ELEVENLABS_API_KEY が設定されていません。")

    url = f"{BASE_URL}/{voice_id}"
    headers = {
        "xi-api-key": API_KEY,
        "Content-Type": "application/json"
    }
    data = {
        "text": script_text,
        "voice_settings": {
            "stability": 0.7,
            "similarity_boost": 0.7
        }
    }

    try:
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()

        # 音声データを保存
        Path(output_file).write_bytes(response.content)
        print(f"音声生成完了: {output_file}")
        return output_file

    except Exception as e:
        print(f"音声生成エラー: {e}")
        return None