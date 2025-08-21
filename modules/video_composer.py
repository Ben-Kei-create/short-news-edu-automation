# modules/video_composer.py
import os
from moviepy.video.VideoClip import ImageClip, ColorClip
from moviepy.video.compositing.CompositeVideoClip import CompositeVideoClip
from moviepy.video.compositing.CompositeVideoClip import concatenate_videoclips
from moviepy.audio.io.AudioFileClip import AudioFileClip
from moviepy.audio.AudioClip import CompositeAudioClip
from moviepy.audio.fx.MultiplyVolume import MultiplyVolume
from moviepy.audio.fx.AudioLoop import AudioLoop

def compose_video(theme, images, audio_path, bgm_path):
    """
    複数の画像、ナレーション音声、BGMを結合して一つの動画を生成する。

    Args:
        theme (str): 動画のテーマ. 出力ファイル名に使用.
        images (list): 画像ファイルのパスのリスト。
        audio_path (str): ナレーション音声ファイルのパス。
        bgm_path (str): BGMファイルのパス。

    Returns:
        str: 生成された動画ファイルのパス。失敗した場合はNone。
    """
    if not images:
        print("エラー: 動画に使用する画像がありません。")
        return None

    try:
        # 1. ナレーション音声を読み込み、動画全体の長さを決定
        print("  - 音声ファイルを読み込み中...")
        narration_clip = AudioFileClip(audio_path)
        video_duration = narration_clip.duration

        # 2. 画像クリップを作成し、動画の長さに合わせてスライドショーを作成
        print("  - 画像スライドショーを作成中...")
        duration_per_image = video_duration / len(images)
        image_clips = []
        for img_path in images:
            clip = (
                ImageClip(img_path)
                .with_duration(duration_per_image)
                .resized(height=1920) # 縦動画サイズに
            )
            # 中央に配置するための黒背景を作成
            background = ColorClip(size=(1080, 1920), color=(0, 0, 0)).with_duration(duration_per_image)
            centered_clip = CompositeVideoClip([background, clip.with_position("center")])
            image_clips.append(centered_clip)
        
        video_clip = concatenate_videoclips(image_clips, method="compose")

        # 3. BGMを準備（音量調整とループ）
        print("  - BGMを準備中...")
        bgm_clip = (
            AudioFileClip(bgm_path)
            .with_effects([MultiplyVolume(0.2)])  # BGMの音量を20%に
            .with_effects([AudioLoop(duration=video_duration)]) # 動画の長さに合わせてループ
        )

        # 4. ナレーションとBGMを合成
        print("  - 音声を合成中...")
        final_audio = CompositeAudioClip([narration_clip, bgm_clip])

        # 5. 映像と音声を結合
        final_clip = video_clip.with_audio(final_audio)

        # 6. 動画ファイルとして書き出し
        output_dir = "output/videos"
        os.makedirs(output_dir, exist_ok=True)
        # テーマ名から安全なファイル名を生成
        import datetime
        current_date = datetime.datetime.now().strftime("%Y%m%d")
        safe_theme_name = "".join(c for c in theme if c.isalnum() or c in (' ', '-')).rstrip()
        output_path = os.path.join(output_dir, f"{current_date}_{safe_theme_name}.mp4")

        print(f"  - 動画ファイルに書き出し中: {output_path}")
        final_clip.write_videofile(
            output_path,
            fps=24,
            codec="libx264",
            audio_codec="aac",
            ffmpeg_params=["-pix_fmt", "yuv420p"]
        )

        print(f"動画生成完了: {output_path}")
        return output_path

    except Exception as e:
        print(f"動画生成中にエラーが発生しました: {e}")
        return None
