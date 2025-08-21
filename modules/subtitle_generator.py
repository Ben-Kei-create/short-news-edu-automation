# modules/subtitle_generator.py
from pathlib import Path

def generate_subtitles(script_text, audio_file, output_file="output/subtitles/subtitles.srt"):
    """
    台本から簡易的に字幕ファイル(SRT)を生成
    注意: 音声タイミングを完全自動同期は高度な処理が必要。
          ここでは簡易的に1文ごとに固定秒数で区切るサンプル。
    
    Args:
        script_text (str): 台本テキスト
        audio_file (str): 音声ファイル（秒数取得用）
        output_file (str): 出力SRTファイル
    Returns:
        str: 出力ファイルパス
    """
    try:
        # 音声秒数取得
        from moviepy.editor import AudioFileClip
        audio_clip = AudioFileClip(audio_file)
        total_duration = audio_clip.duration

        # 台本を文ごとに分割
        sentences = [s.strip() for s in script_text.replace("\u3002", "\u3002\n").split("\n") if s.strip()]
        num_sentences = len(sentences)
        duration_per_sentence = total_duration / max(1, num_sentences)

        # SRT作成
        lines = []
        for i, sentence in enumerate(sentences):
            start_time = i * duration_per_sentence
            end_time = start_time + duration_per_sentence
            start_hms = seconds_to_hms(start_time)
            end_hms = seconds_to_hms(end_time)
            lines.append(f"{i+1}\n{start_hms} --> {end_hms}\n{sentence}\n")

        Path(output_file).parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, "w", encoding="utf-8") as f:
            f.writelines(lines)

        print(f"字幕生成完了: {output_file}")
        return output_file

    except Exception as e:
        print(f"字幕生成エラー: {e}")
        return None

def seconds_to_hms(seconds):
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds - int(seconds)) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"
