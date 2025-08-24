# modules/subtitle_generator.py
import os
from pathlib import Path

def generate_subtitles(theme, audio_segments_info): # Changed signature
    """
    音声セグメントの情報から字幕ファイル(SRT)を生成する。
    各セグメントの正確な再生時間を使用して、より正確な字幕を生成する。
    
    Args:
        theme (str): 動画のテーマ。出力ファイル名に使用。
        audio_segments_info (list): 音声セグメントの情報（パス、再生時間、テキスト）のリスト。

    Returns:
        str: 生成されたSRTファイルのパス。失敗した場合はNone。
    """
    try:
        if not audio_segments_info:
            print("  - 字幕を生成する音声セグメントがありません。")
            return None
        
        lines = []
        current_time = 0.0

        for i, segment in enumerate(audio_segments_info):
            if segment["path"] is None or segment["duration"] == 0:
                # エラーなどで音声が生成されなかったセグメントはスキップ
                continue

            start_time = current_time
            end_time = current_time + segment["duration"]
            
            start_hms = _seconds_to_hms(start_time)
            end_hms = _seconds_to_hms(end_time)
            
            lines.append(f"{i+1}\n{start_hms} --> {end_hms}\n{segment['text']}\n\n")
            
            current_time = end_time

        # 出力パスを生成
        output_dir = "output/subtitles"
        os.makedirs(output_dir, exist_ok=True)
        import datetime
        current_date = datetime.datetime.now().strftime("%Y%m%d")
        safe_theme_name = "".join(c for c in theme if c.isalnum() or c in (' ', '-')).rstrip()
        output_path = os.path.join(output_dir, f"{current_date}_{safe_theme_name}.srt")

        # ファイルに書き出し
        with open(output_path, "w", encoding="utf-8") as f:
            f.writelines(lines)

        print(f"  -> 字幕生成完了: {output_path}")
        return output_path

    except Exception as e:
        print(f"  - 字幕生成エラー: {e}")
        return None

def _seconds_to_hms(seconds):
    """秒をSRTのタイムスタンプ形式（HH:MM:SS,ms）に変換する"""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds - int(seconds)) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"