import os
from moviepy.editor import *
from moviepy.video.tools.subtitles import SubtitlesClip
from moviepy.audio.fx import all as afx
import numpy as np

def compose_video(theme, images, audio_segments_info, bgm_path, subtitle_file, font_filename=None):
    """
    複数の画像、ナレーション、BGM、字幕を結合して一つの動画を生成する。
    画像の表示時間は5秒に固定し、音声の長さをそれに合わせる。
    """
    if not images:
        print("エラー: 動画に使用する画像がありません。")
        return None

    if not audio_segments_info:
        print("エラー: 動画に使用する音声セグメントがありません。")
        return None

    try:
        # --- 1. 画像クリップを作成 (5秒/枚に固定) ---
        print("  - 画像スライドショーを作成中 (5秒/枚)... ")
        duration_per_image = 5
        image_clips = []
        for img_path in images:
            if not os.path.exists(img_path):
                print(f"  - 警告: 画像ファイルが見つかりません: {img_path}")
                continue
            try:
                clip = ImageClip(img_path).set_duration(duration_per_image)
                clip_resized = clip.resize(width=1080)
                background = ColorClip(size=(1080, 1920), color=(0, 0, 0)).set_duration(duration_per_image)
                centered_clip = CompositeVideoClip([background, clip_resized.set_position("center")])
                image_clips.append(centered_clip)
            except Exception as e:
                print(f"  - 警告: 画像クリップ作成エラー ({img_path}): {e}")
                continue
        
        if not image_clips:
            print("エラー: 有効な画像クリップがありません。")
            return None
        
        video_clip = concatenate_videoclips(image_clips, method="compose")
        video_duration = video_clip.duration # 映像の合計時間を確定

        # --- 2. 音声クリップを作成し、長さを映像に合わせる ---
        print("  - 音声セグメントを結合し、長さを調整中...")
        valid_audio_clips = [AudioFileClip(seg["path"]) for seg in audio_segments_info if seg["path"] and os.path.exists(seg["path"])]
        if not valid_audio_clips:
            print("エラー: 有効な音声クリップがありません。")
            return None
        
        narration_clip_raw = concatenate_audioclips(valid_audio_clips)
        
        # 音声の再生速度を変更して、映像の長さに合わせる
        narration_clip = narration_clip_raw.fx(afx.speedx, factor=narration_clip_raw.duration / video_duration)

        # --- 3. 字幕クリップを作成 ---
        print("  - 字幕を準備中...")
        if subtitle_file and os.path.exists(subtitle_file):
            try:
                # フォントパスを決定
                font_path = ''
                if font_filename:
                    custom_font_path = os.path.join("input/fonts", font_filename)
                    if os.path.exists(custom_font_path):
                        font_path = custom_font_path
                        print(f"  - カスタムフォントを使用します: {font_path}")
                    else:
                        print(f"  - 警告: 指定されたフォントファイルが見つかりません: {custom_font_path}")
                
                if not font_path:
                    # デフォルトのシステムフォント（macOS用）
                    default_mac_font = '/System/Library/Fonts/ヒラギノ角ゴ ProN W3.otf'
                    if os.path.exists(default_mac_font):
                        font_path = default_mac_font
                        print(f"  - デフォルトのシステムフォントを使用します: {font_path}")
                    else:
                        # 最終フォールバック
                        font_path = 'Arial'
                        print(f"  - 警告: 日本語フォントが見つかりません。英語フォント '{font_path}' で代用します。")

                generator = lambda txt: TextClip(
                    txt, font=font_path, fontsize=60, color='white',
                    stroke_color='black', stroke_width=2, method='caption', size=(800, None)
                )
                subtitles = SubtitlesClip(subtitle_file, generator)
                subtitles_clip = subtitles.set_position(('center', 0.8))
            except Exception as e:
                print(f"  - 警告: 字幕クリップの作成に失敗しました: {e}")
                subtitles_clip = None
        else:
            subtitles_clip = None

        # --- 4. BGMを準備 ---
        print("  - BGMを準備中...")
        bgm_clip = None
        if bgm_path and os.path.exists(bgm_path):
            try:
                bgm_clip_full = AudioFileClip(bgm_path).volumex(0.08)
                bgm_clip = afx.audio_loop(bgm_clip_full, duration=video_duration)
            except Exception as e:
                print(f"  - 警告: BGM読み込み/加工エラー: {e}")

        # --- 5. 音声を合成 ---
        print("  - 音声を合成中...")
        audio_clips = [narration_clip]
        if bgm_clip:
            audio_clips.append(bgm_clip)
        final_audio = CompositeAudioClip(audio_clips)

        # --- 6. 最終的な動画を組み立て ---
        final_clip = video_clip.set_audio(final_audio)
        if subtitles_clip:
            final_clip = CompositeVideoClip([final_clip, subtitles_clip])
        final_clip.duration = video_duration
        final_clip.fps = 24

        # --- 7. 動画ファイルとして書き出し ---
        output_dir = "output/videos"
        os.makedirs(output_dir, exist_ok=True)
        import datetime
        current_date = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_theme_name = "".join(c for c in theme if c.isalnum() or c in (' ', '-')).rstrip()[:50]
        output_path = os.path.join(output_dir, f"{current_date}_{safe_theme_name}.mp4")

        print(f"  - 動画ファイルに書き出し中: {output_path}")
        final_clip.write_videofile(
            output_path, codec="libx264", audio_codec="aac",
            temp_audiofile='temp-audio.m4a', remove_temp=True,
            verbose=False, logger=None
        )

        # --- リソース解放 ---
        for clip in [narration_clip_raw, narration_clip, bgm_clip, video_clip, subtitles_clip, final_audio, final_clip] + valid_audio_clips + image_clips:
            if clip:
                try:
                    clip.close()
                except Exception as e:
                    pass # Ignore errors on closing clips

        print(f"動画生成完了: {output_path}")
        return output_path

    except Exception as e:
        print(f"動画生成中にエラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        return None
