import os
import datetime
from moviepy.editor import *
from moviepy.video.tools.subtitles import SubtitlesClip
from moviepy.audio.fx import all as afx
import numpy as np
import traceback

def compose_video(theme, images, audio_segments_info, bgm_path, subtitle_file, font_filename=None, image_duration=5.0, settings=None):
    """
    複数の画像、ナレーション、BGM、字幕を結合して一つの動画を生成する。
    """
    if not images or not audio_segments_info:
        print("エラー: 動画の生成に必要な画像または音声セグメントが不足しています。")
        return None

    # リソース解放のために、クリップ変数をあらかじめ定義
    image_clips = []
    valid_audio_clips = []
    video_clip = narration_clip_raw = narration_clip = subtitles_clip = bgm_clip_full = bgm_clip = final_audio = final_clip = None
    output_path = None

    try:
        # --- 1. 画像クリップを作成 ---
        duration_per_image = settings['video_composer']['image_duration']
        print(f"  - 画像スライドショーを作成中 ({duration_per_image}秒/枚)... ")
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
            except (OSError, IOError, Exception) as e:
                print(f"  - 警告: 画像ファイル ({img_path}) の読み込みに失敗しました: {e}")
                print("      -> プレースホルダー画像で代替します。")
                try:
                    placeholder_path = settings['general']['placeholder_image_path']
                    if os.path.exists(placeholder_path):
                        clip = ImageClip(placeholder_path).set_duration(duration_per_image)
                        clip_resized = clip.resize(width=1080)
                        background = ColorClip(size=(1080, 1920), color=(0, 0, 0)).set_duration(duration_per_image)
                        centered_clip = CompositeVideoClip([background, clip_resized.set_position("center")])
                        image_clips.append(centered_clip)
                    else:
                        print(f"  - エラー: プレースホルダー画像が見つかりません: {placeholder_path}")
                        continue
                except Exception as placeholder_e:
                    print(f"  - エラー: プレースホルダー画像の読み込みにも失敗しました: {placeholder_e}")
                    continue
        
        if not image_clips:
            print("エラー: 有効な画像クリップがありません。")
            return None
        
        video_clip = concatenate_videoclips(image_clips, method="compose")
        video_duration = video_clip.duration

        # --- 2. 音声クリップを作成 ---
        print("  - 音声セグメントを結合し、長さを調整中...")
        for seg in audio_segments_info:
            if seg["path"] and os.path.exists(seg["path"]):
                try:
                    valid_audio_clips.append(AudioFileClip(seg["path"]))
                except Exception as e:
                    print(f"  - 警告: 音声ファイル ({seg['path']}) の読み込みエラー: {e}")
                    continue

        if not valid_audio_clips:
            print("エラー: 有効な音声クリップがありません。")
            return None
        
        narration_clip_raw = concatenate_audioclips(valid_audio_clips)
        narration_clip = narration_clip_raw.fx(vfx.speedx, factor=narration_clip_raw.duration / video_duration)

        # --- 3. 字幕クリップを作成 ---
        print("  - 字幕を準備中...")
        if subtitle_file and os.path.exists(subtitle_file):
            try:
                font_path = ''
                if font_filename and os.path.exists(os.path.join("input/fonts", font_filename)):
                    font_path = os.path.join("input/fonts", font_filename)
                elif os.path.exists('/System/Library/Fonts/ヒラギノ角ゴ ProN W3.otf'):
                    font_path = '/System/Library/Fonts/ヒラギノ角ゴ ProN W3.otf'
                else:
                    font_path = 'Arial'
                    print(f"  - 警告: 日本語フォントが見つかりません。'{font_path}' で代用します。")

                generator = lambda txt: TextClip(txt, font=font_path, fontsize=settings['video_composer']['font_size'], color=settings['video_composer']['font_color'], stroke_color=settings['video_composer']['font_stroke_color'], stroke_width=settings['video_composer']['font_stroke_width'], method='caption', size=(settings['video_composer']['subtitle_width'], None))
                subtitles = SubtitlesClip(subtitle_file, generator)
                subtitles_clip = subtitles.set_position(('center', settings['video_composer']['subtitle_position_y_ratio']))
            except Exception as e:
                print(f"  - 警告: 字幕クリップの作成中に予期せぬエラーが発生しました: {e}")

        # --- 4. BGMを準備 ---
        print("  - BGMを準備中...")
        if bgm_path and os.path.exists(bgm_path):
            try:
                bgm_clip_full = AudioFileClip(bgm_path).volumex(settings['video_composer']['bgm_volume'])
                bgm_clip = afx.audio_loop(bgm_clip_full, duration=video_duration)
            except Exception as e:
                print(f"  - 警告: BGMの読み込み/加工中に予期せぬエラーが発生しました: {e}")

        # --- 5. 音声と動画を合成 ---
        print("  - 音声と動画を合成中...")
        audio_clips_to_compose = [c for c in [narration_clip, bgm_clip] if c is not None]
        final_audio = CompositeAudioClip(audio_clips_to_compose)
        final_clip = video_clip.set_audio(final_audio)
        if subtitles_clip:
            final_clip = CompositeVideoClip([final_clip, subtitles_clip])
        final_clip.duration = video_duration
        final_clip.fps = settings['video_composer']['output_fps']

        # --- 6. 動画ファイルとして書き出し ---
        output_dir = "output/videos"
        os.makedirs(output_dir, exist_ok=True)
        current_date = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_theme_name = "".join(c for c in theme if c.isalnum() or c in (' ', '-')).rstrip()[:50]
        output_path = os.path.join(output_dir, f"{current_date}_{safe_theme_name}.mp4")

        print(f"  - 動画ファイルに書き出し中: {output_path}")
        final_clip.write_videofile(output_path, codec="libx264", audio_codec="aac", temp_audiofile='temp-audio.m4a', remove_temp=True, verbose=False, logger=None)
        
        print(f"動画生成完了: {output_path}")
        return output_path

    except Exception as e:
        print(f"動画生成中に致命的なエラーが発生しました: {e}")
        traceback.print_exc()
        return None

    finally:
        # --- 7. リソース解放 ---
        print("  - リソースを解放中...")
        clips_to_close = image_clips + valid_audio_clips + [video_clip, narration_clip_raw, narration_clip, subtitles_clip, bgm_clip_full, bgm_clip, final_audio, final_clip]
        for clip in clips_to_close:
            if clip:
                try:
                    clip.close()
                except Exception:
                    pass # 解放時のエラーは無視