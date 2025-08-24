# modules/audio_manager.py
import os
import uuid
from dotenv import load_dotenv
from google.cloud import texttospeech # New import
from moviepy.audio.io.AudioFileClip import AudioFileClip # New import

# generate_voice 関数の引数に settings を追加
def generate_voice(script_text, settings):
    """
    Google Cloud TTSで台本を音声化し、tempフォルダにユニークなファイル名で保存する。
    テキストを文やフレーズに分割し、それぞれの音声ファイルパスと再生時間を返す。
    """
    load_dotenv()
    # Google Cloud TTSクライアントはGOOGLE_APPLICATION_CREDENTIALS環境変数を使用します
    # そのため、APIキーを直接コード内で設定する必要はありません。
    # 環境変数が設定されていない場合は、認証エラーが発生します。
    try:
        client = texttospeech.TextToSpeechClient()
    except google.api_core.exceptions.GoogleAuthError as e:
        print(f"  - エラー: Google Cloud TTSクライアントの認証に失敗しました。google_credentials.json または GOOGLE_APPLICATION_CREDENTIALS 環境変数を確認してください: {e}")
        return []
    except Exception as e:
        print(f"  - エラー: Google Cloud TTSクライアントの初期化中に予期せぬエラーが発生しました: {e}")
        return []

    # 音声の設定 (日本語、女性の声、標準)
    voice = texttospeech.VoiceSelectionParams(
        language_code="ja-JP",
        name=settings['google_tts']['voice_name'], # settings から取得
        ssml_gender=getattr(texttospeech.SsmlVoiceGender, settings['google_tts']['ssml_gender']), # settings から取得
    )

    # 音声フォーマットの設定 (MP3)
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3,
        speaking_rate=settings['google_tts']['speaking_rate'] # settings から取得
    )

    temp_dir = "temp"
    os.makedirs(temp_dir, exist_ok=True)

    # テキストを文やフレーズに分割
    # 日本語の句読点に基づいて分割します。より高度な分割が必要な場合は、別途ライブラリを検討してください。
    # 句読点の後にスペースがない場合も考慮
    segments = []
    current_segment = ""
    for char in script_text:
        current_segment += char
        if char in ["。", "！", "？", ".", "!", "?"]:
            segments.append(current_segment.strip())
            current_segment = ""
    if current_segment.strip(): # 最後のセグメントが句読点で終わらない場合
        segments.append(current_segment.strip())

    audio_segments_info = []

    print(f"  - テキストを{len(segments)}個のセグメントに分割しました。")

    for i, segment_text in enumerate(segments):
        if not segment_text:
            continue

        synthesis_input = texttospeech.SynthesisInput(text=segment_text)
        output_path = os.path.join(temp_dir, f"voice_{uuid.uuid4()}.mp3")

        try:
            response = client.synthesize_speech(
                input=synthesis_input, voice=voice, audio_config=audio_config
            )

            with open(output_path, "wb") as out:
                out.write(response.audio_content)
            
            # 音声ファイルの再生時間を取得
            audio_clip = AudioFileClip(output_path)
            duration = audio_clip.duration
            audio_clip.close() # リソースを解放

            audio_segments_info.append({"path": output_path, "duration": duration, "text": segment_text})
            print(f"    - セグメント {i+1}: {output_path} ({duration:.2f}秒)")

        except google.api_core.exceptions.InvalidArgument as e:
            print(f"  - 音声生成エラー (セグメント '{segment_text[:30]}...'): 無効な引数です。テキストの内容を確認してください: {e}")
            audio_segments_info.append({"path": None, "duration": 0, "text": segment_text})
        except google.api_core.exceptions.ResourceExhausted as e:
            print(f"  - 音声生成エラー (セグメント '{segment_text[:30]}...'): リソースが枯渇しました。APIクォータを確認してください: {e}")
            audio_segments_info.append({"path": None, "duration": 0, "text": segment_text})
        except google.api_core.exceptions.GoogleAPIError as e:
            print(f"  - 音声生成エラー (セグメント '{segment_text[:30]}...'): Google APIエラーが発生しました: {e}")
            audio_segments_info.append({"path": None, "duration": 0, "text": segment_text})
        except Exception as e:
            print(f"  - 音声生成エラー (セグメント '{segment_text[:30]}...'): 予期せぬエラーが発生しました: {e}")
            audio_segments_info.append({"path": None, "duration": 0, "text": segment_text})

    return audio_segments_info
