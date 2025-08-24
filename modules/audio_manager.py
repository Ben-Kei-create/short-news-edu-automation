import os
import uuid
import re
from google.cloud import texttospeech
from moviepy.audio.io.AudioFileClip import AudioFileClip
import google.api_core.exceptions
import requests
import logging # 追加

# ロガーを取得
logger = logging.getLogger(__name__)

def generate_voice(script_text, settings, use_voicevox_cli_arg=None):
    """
    Google Cloud TTSまたはVOICEVOXで台本を音声化し、tempフォルダに保存する。
    成功した場合は音声セグメント情報のリストを、失敗した場合はNoneを返す。
    """
    # CLI引数が指定された場合は、settings.yamlの設定を上書きする
    if use_voicevox_cli_arg is not None:
        use_voicevox = use_voicevox_cli_arg
    else:
        use_voicevox = settings.get('voicevox', {}).get('enabled', False)

    if use_voicevox:
        return _generate_voice_voicevox(script_text, settings)
    else:
        return _generate_voice_google_tts(script_text, settings)

def _generate_voice_google_tts(script_text, settings):
    # 既存のGoogle Cloud TTSのロジック
    # 最初に認証情報の存在をチェック
    credentials_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
    if not credentials_path or not os.path.exists(credentials_path):
        logger.error("Google Cloudの認証情報が見つかりません。")
        logger.error("環境変数 GOOGLE_APPLICATION_CREDENTIALS が正しく設定されているか確認してください。")
        return None

    try:
        client = texttospeech.TextToSpeechClient()
    except Exception as e:
        logger.error(f"Google Cloud TTSクライアントの初期化に失敗しました: {e}", exc_info=True)
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
    logger.info(f"テキストを{len(segments)}個のセグメントに分割しました (Google Cloud TTS)。")

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
            logger.info(f"セグメント {i+1}を生成: {output_path} ({duration:.2f}秒)")

        except (google.api_core.exceptions.GoogleAPIError, Exception) as e:
            logger.error(f"音声生成に失敗しました (セグメント: '{segment_text[:30]}...'): {e}", exc_info=True)
            # 失敗した一時ファイルが残っていれば削除
            if os.path.exists(output_path):
                os.remove(output_path)
            # 一つでも失敗したら、全体の処理を中断してNoneを返す
            return None

    return audio_segments_info

def _generate_voice_voicevox(script_text, settings):
    voicevox_settings = settings.get('voicevox', {})
    api_url = voicevox_settings.get('api_url')
    speaker_id = voicevox_settings.get('speaker_id')
    speed_scale = voicevox_settings.get('speed_scale', 1.0)
    intonation_scale = voicevox_settings.get('intonation_scale', 1.0)
    volume_scale = voicevox_settings.get('volume_scale', 1.0)
    pre_phrasing_rate = voicevox_settings.get('pre_phrasing_rate', 0.0)
    post_phrasing_rate = voicevox_settings.get('post_phrasing_rate', 0.0)
    output_sampling_rate = voicevox_settings.get('output_sampling_rate', 24000)

    if not api_url or speaker_id is None:
        logger.error("VOICEVOX APIのURLまたは話者IDが設定されていません。")
        return None

    os.makedirs("temp", exist_ok=True)

    segments = [s.strip() for s in re.split('(。[。！？.!?])', script_text) if s.strip()]
    audio_segments_info = []
    logger.info(f"テキストを{len(segments)}個のセグメントに分割しました (VOICEVOX)。")

    for i, segment_text in enumerate(segments):
        if not segment_text:
            continue

        try:
            # audio_query
            audio_query_params = {
                "text": segment_text,
                "speaker": speaker_id
            }
            audio_query_response = requests.post(f"{api_url}/audio_query", params=audio_query_params)
            audio_query_response.raise_for_status()
            query_data = audio_query_response.json()

            # synthesis
            synthesis_params = {
                "speaker": speaker_id,
                "speedScale": speed_scale,
                "intonationScale": intonation_scale,
                "volumeScale": volume_scale,
                "prePhonemeLength": pre_phrasing_rate,
                "postPhonemeLength": post_phrasing_rate,
                "outputSamplingRate": output_sampling_rate
            }
            synthesis_response = requests.post(f"{api_url}/synthesis", params=synthesis_params, json=query_data)
            synthesis_response.raise_for_status()

            output_path = os.path.join("temp", f"voice_{uuid.uuid4()}.wav") # VOICEVOXはWAV出力
            with open(output_path, "wb") as out:
                out.write(synthesis_response.content)

            audio_clip = AudioFileClip(output_path)
            duration = audio_clip.duration
            audio_clip.close()

            audio_segments_info.append({"path": output_path, "duration": duration, "text": segment_text})
            logger.info(f"セグメント {i+1}を生成: {output_path} ({duration:.2f}秒)")

        except requests.exceptions.RequestException as e:
            logger.error(f"VOICEVOX API呼び出しに失敗しました (セグメント: '{segment_text[:30]}...'): {e}", exc_info=True)
            if os.path.exists(output_path):
                os.remove(output_path)
            return None
        except Exception as e:
            logger.error(f"VOICEVOX音声生成中に予期せぬエラーが発生しました (セグメント: '{segment_text[:30]}...'): {e}", exc_info=True)
            if os.path.exists(output_path):
                os.remove(output_path)
            return None

    return audio_segments_info