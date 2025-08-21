# modules/audio_manager.py
import os
import uuid
import requests
from dotenv import load_dotenv

def generate_voice(script_text, voice_id="21m00Tcm4TlvDq8ikWAM"):
    """
    ElevenLabs TTSで台本を音声化し、tempフォルダにユニークなファイル名で保存する。
    """
    load_dotenv()
    api_key = os.getenv("ELEVENLABS_API_KEY")
    if not api_key:
        raise ValueError("環境変数 'ELEVENLABS_API_KEY' が設定されていません。")

    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": api_key
    }
    data = {
        "text": script_text,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {
            "stability": 0.7,
            "similarity_boost": 0.75
        }
    }

    temp_dir = "temp"
    os.makedirs(temp_dir, exist_ok=True)
    output_path = os.path.join(temp_dir, f"voice_{uuid.uuid4()}.mp3")

    try:
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()

        with open(output_path, 'wb') as f:
            f.write(response.content)
        
        print(f"  -> 音声生成完了: {output_path}")
        return output_path

    except requests.exceptions.RequestException as e:
        print(f"  - 音声生成エラー: {e}")
        return None
