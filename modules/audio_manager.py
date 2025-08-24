import os
import uuid
import re
from google.cloud import texttospeech
from moviepy.audio.io.AudioFileClip import AudioFileClip
import google.api_core.exceptions
import traceback

def generate_voice(script_text, settings):
    """
    Google Cloud TTSで台本を音声化し、tempフォルダに保存する。
    成功した場合は音声セグメント情報のリストを、失敗した場合はNoneを返す。
    """
    # 最初に認証情報の存在をチェック
    credentials_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
    if not credentials_path or not os.path.exists(credentials_path):
        print("エラー: Google Cloudの認証情報が見つかりません。")
        print("環境変数 GOOGLE_APPLICATION_CREDENTIALS が正しく設定されているか確認してください。")
        return None

    try:
        client = texttospeech.TextToSpeechClient()
    except Exception as e:
        print(f"エラー: Google Cloud TTSクライアントの初期化に失敗しました: {e}")
        return None

    voice = texttospeech.VoiceSelectionParams(
        language_code="ja-JP",
        name=settings['google_tts']['voice_name'],
        ssml_gender=getattr(texttospeech.SsmlVoiceGender, settings['google_tts']['ssml_gender'])
    )
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3,
        speaking_rate=settings['google_tts']['speaking_rate']
    )

    os.makedirs("temp", exist_ok=True)

    # テキストを句読点で分割
    segments = [s.strip() for s in re.split('(。[。！？.!?])', script_text) if s.strip()]
    audio_segments_info = []
    print(f"  - テキストを{len(segments)}個のセグメントに分割しました。")

    for i, segment_text in enumerate(segments):
        if not segment_text:
            continue

        synthesis_input = texttospeech.SynthesisInput(text=segment_text)
        output_path = os.path.join("temp", f"voice_{uuid.uuid4()}.mp3")

        try:
            response = client.synthesize_speech(
                input=synthesis_input, voice=voice, audio_config=audio_config
            )
            with open(output_path, "wb") as out:
                out.write(response.audio_content)
            
            audio_clip = AudioFileClip(output_path)
            duration = audio_clip.duration
            audio_clip.close()

            audio_segments_info.append({"path": output_path, "duration": duration, "text": segment_text})
            print(f"    - セグメント {i+1}を生成: {output_path} ({duration:.2f}秒)")

        except (google.api_core.exceptions.GoogleAPIError, Exception) as e:
            print(f"  - エラー: 音声生成に失敗しました (セグメント: '{segment_text[:30]}...')。")
            print(f"    詳細: {e}")
            # 失敗した一時ファイルが残っていれば削除
            if os.path.exists(output_path):
                os.remove(output_path)
            # 一つでも失敗したら、全体の処理を中断してNoneを返す
            return None

    return audio_segments_info