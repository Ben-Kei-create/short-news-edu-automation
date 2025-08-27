# modules/subtitle_generator.py
import os
import datetime
import logging

logger = logging.getLogger(__name__)

def _seconds_to_srt_timestamp(seconds):
    """秒をSRTのタイムスタンプ形式（HH:MM:SS,ms）に変換する"""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds - int(seconds)) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

def generate_subtitles(theme, audio_segments_info, settings):
    """
    音声セグメントの情報から字幕ファイル(SRT)を生成する。
    
    Args:
        theme (str): 動画のテーマ。出力ファイル名に使用。
        audio_segments_info (list): 音声セグメントの情報（パス、再生時間、テキスト）のリスト。
        settings (dict): 設定情報。

    Returns:
        str: 生成されたSRTファイルのパス。失敗した場合はNone。
    """
    if not audio_segments_info:
        logger.warning("字幕を生成するための音声セグメント情報がありません。")
        return None

    try:
        srt_lines = []
        current_time = 0.0

        for i, segment in enumerate(audio_segments_info):
            duration = segment.get('duration')
            text = segment.get('text')

            if not duration or not text:
                logger.warning(f"セグメント {i+1} に再生時間またはテキストがありません。スキップします。")
                continue

            start_time = current_time
            end_time = current_time + duration
            
            start_hms = _seconds_to_srt_timestamp(start_time)
            end_hms = _seconds_to_srt_timestamp(end_time)
            
            srt_lines.append(f"{i+1}\n{start_hms} --> {end_hms}\n{text}\n\n")
            
            current_time = end_time

        if not srt_lines:
            logger.warning("有効な字幕行を1つも生成できませんでした。")
            return None

        # 出力パスを生成
        output_dir = "output/subtitles"
        os.makedirs(output_dir, exist_ok=True)
        safe_theme = "".join(c for c in theme if c.isalnum())[:50]
        output_path = os.path.join(output_dir, f"{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}_{safe_theme}.srt")

        with open(output_path, "w", encoding="utf-8") as f:
            f.writelines(srt_lines)

        logger.info(f"字幕ファイルを生成しました: {output_path}")
        return output_path

    except Exception as e:
        logger.error(f"字幕生成中に予期せぬエラーが発生しました: {e}", exc_info=True)
        return None
