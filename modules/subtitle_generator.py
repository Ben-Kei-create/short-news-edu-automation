# modules/subtitle_generator.py
import os
from pathlib import Path

def generate_subtitles(theme, script_text, audio_file):
    """
    台本から簡易的に字幕ファイル(SRT)を生成する。
    注意: 音声タイミングの完全な自動同期は高度な処理が必要なため、
          ここでは1文ごとに固定秒数で区切る簡易的なサンプルとなっている。
    
    Args:
        theme (str): 動画のテーマ。出力ファイル名に使用。
        script_text (str): 台本テキスト。
        audio_file (str): 音声ファイル（全体の秒数取得用）。

    Returns:
        str: 生成されたSRTファイルのパス。失敗した場合はNone。
    """
    try:
        # moviepyは比較的大きなライブラリなので、必要な時だけインポート
        from moviepy.audio.io.AudioFileClip import AudioFileClip
        audio_clip = AudioFileClip(audio_file)
        total_duration = audio_clip.duration

        # 台本を句点（。）で改行し、文ごとに分割
        sentences = [s.strip() for s in script_text.replace("。", "。\n").split("\n") if s.strip()]
        if not sentences:
            print("  - 字幕を生成する文がありません。")
            return None
        
        num_sentences = len(sentences)
        duration_per_sentence = total_duration / num_sentences

        # SRTフォーマットの文字列を作成
        lines = []
        for i, sentence in enumerate(sentences):
            start_time = i * duration_per_sentence
            end_time = start_time + duration_per_sentence
            start_hms = _seconds_to_hms(start_time)
            end_hms = _seconds_to_hms(end_time)
            lines.append(f"{i+1}\n{start_hms} --> {end_hms}\n{sentence}\n\n")

        # 出力パスを生成
        output_dir = "output/subtitles"
        os.makedirs(output_dir, exist_ok=True)
        safe_theme_name = "".join(c for c in theme if c.isalnum() or c in (' ', '-')).rstrip()
        output_path = os.path.join(output_dir, f"{safe_theme_name}.srt")

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