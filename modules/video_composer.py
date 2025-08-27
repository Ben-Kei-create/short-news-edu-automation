import os
import datetime
from moviepy.editor import *
from moviepy.video.tools.subtitles import SubtitlesClip
from moviepy.audio.fx import all as afx
import traceback
import logging

logger = logging.getLogger(__name__)

def compose_video(theme, images, audio_segments_info, bgm_path, subtitle_file, settings):
    """
    画像、ナレーション、BGM、字幕を結合して動画を生成する。
    """
    if not images or not audio_segments_info:
        logging.error("動画生成に必要な画像または音声セグメントが不足しています。")
        return None

    video_settings = settings.get('video', {})
    subtitle_settings = settings.get('subtitle', {})
    bgm_settings = settings.get('bgm', {})
    img_settings = settings.get('image', {})

    resolution = video_settings.get('resolution', [1080, 1920])
    image_duration = video_settings.get('image_duration', 5.0)
    output_fps = video_settings.get('fps', 30)
    bgm_volume = bgm_settings.get('volume', 0.2)

    # リソース解放のためのリスト
    clips_to_close = []

    try:
        # --- 1. 画像クリップを作成 ---
        logging.info(f"画像スライドショーを作成中 ({image_duration}秒/枚)... ")
        for img_path in images:
            if not os.path.exists(img_path):
                logging.warning(f"画像ファイルが見つかりません: {img_path}")
                placeholder_path = img_settings.get('placeholder_path')
                if placeholder_path and os.path.exists(placeholder_path):
                    logging.info(f"プレースホルダー画像で代替します: {placeholder_path}")
                    img_path = placeholder_path
                else:
                    continue # プレースホルダーもなければスキップ
            try:
                clip = ImageClip(img_path).set_duration(image_duration)
                # アスペクト比を保ったままリサイズし、黒背景の中央に配置
                clip_resized = clip.resize(width=resolution[0])
                background = ColorClip(size=resolution, color=(0, 0, 0)).set_duration(image_duration)
                centered_clip = CompositeVideoClip([background, clip_resized.set_position("center")])
                clips_to_close.append(clip)
                clips_to_close.append(background)
                clips_to_close.append(centered_clip)
                image_clips.append(centered_clip)
            except Exception as e:
                logging.error(f"画像ファイル ({img_path}) の読み込みに失敗しました: {e}", exc_info=True)
                continue
        
        if not image_clips:
            logging.error("有効な画像クリップが1枚も作成できませんでした。")
            return None
        
        video_clip = concatenate_videoclips(image_clips, method="compose")
        video_duration = video_clip.duration
        clips_to_close.append(video_clip)

        # --- 2. 音声クリップを作成 ---
        logging.info("音声セグメントを結合し、長さを調整中...")
        valid_audio_clips = []
        for seg in audio_segments_info:
            if seg.get("path") and os.path.exists(seg["path"]):
                try:
                    audio_clip = AudioFileClip(seg["path"])
                    valid_audio_clips.append(audio_clip)
                    clips_to_close.append(audio_clip)
                except Exception as e:
                    logging.warning(f"音声ファイル ({seg['path']}) の読み込みエラー: {e}")

        if not valid_audio_clips:
            logging.error("有効な音声クリップがありません。")
            return None
        
        narration_clip_raw = concatenate_audioclips(valid_audio_clips)
        # 動画の長さにナレーションを合わせる
        narration_clip = narration_clip_raw.fx(vfx.speedx, factor=narration_clip_raw.duration / video_duration)
        clips_to_close.extend([narration_clip_raw, narration_clip])

        # --- 3. 字幕クリップを作成 ---
        subtitles_clip = None
        if subtitle_file and os.path.exists(subtitle_file):
            logging.info("字幕を準備中...")
            try:
                font = subtitle_settings.get('font', 'Arial')
                if not os.path.exists(font):
                    logging.warning(f"指定されたフォントが見つかりません: {font}。Arialで代用します。")
                    font = 'Arial'
                
                generator = lambda txt: TextClip(txt, font=font, fontsize=subtitle_settings.get('fontsize', 48),
                                                color=subtitle_settings.get('color', 'white'),
                                                stroke_color=subtitle_settings.get('stroke_color', 'black'),
                                                stroke_width=subtitle_settings.get('stroke_width', 2),
                                                method='caption', size=(resolution[0] * 0.9, None))
                
                subtitles = SubtitlesClip(subtitle_file, generator)
                pos = subtitle_settings.get('position', 'bottom')
                margin = subtitle_settings.get('margin', 50)
                if pos == 'bottom':
                    subtitles_clip = subtitles.set_position(('center', resolution[1] - subtitles.h - margin))
                elif pos == 'center':
                    subtitles_clip = subtitles.set_position('center')
                else: # top
                    subtitles_clip = subtitles.set_position(('center', margin))
                clips_to_close.extend([subtitles, subtitles_clip])
            except Exception as e:
                logging.error(f"字幕クリップの作成中にエラーが発生しました: {e}", exc_info=True)

        # --- 4. BGMを準備 ---
        bgm_clip = None
        if bgm_path and os.path.exists(bgm_path):
            logging.info("BGMを準備中...")
            try:
                bgm_clip_full = AudioFileClip(bgm_path).volumex(bgm_volume)
                bgm_clip = afx.audio_loop(bgm_clip_full, duration=video_duration)
                clips_to_close.extend([bgm_clip_full, bgm_clip])
            except Exception as e:
                logging.warning(f"BGMの読み込み/加工中にエラーが発生しました: {e}")

        # --- 5. 音声と動画を合成 ---
        logging.info("最終的な音声と動画を合成中...")
        audio_to_compose = [narration_clip, bgm_clip] if bgm_clip else [narration_clip]
        final_audio = CompositeAudioClip(audio_to_compose)
        final_clip = video_clip.set_audio(final_audio)
        clips_to_close.extend([final_audio, final_clip])

        if subtitles_clip:
            final_clip = CompositeVideoClip([final_clip, subtitles_clip])
            clips_to_close.append(final_clip)

        final_clip.duration = video_duration
        final_clip.fps = output_fps

        # --- 6. 動画ファイルとして書き出し ---
        output_dir = "output/videos"
        safe_theme = "".join(c for c in theme if c.isalnum())[:50]
        output_path = os.path.join(output_dir, f"{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}_{safe_theme}.mp4")

        logging.info(f"動画ファイルに書き出し中: {output_path}")
        final_clip.write_videofile(output_path, codec="libx264", audio_codec="aac", temp_audiofile='temp-audio.m4a', remove_temp=True, verbose=False, logger=None)
        
        logging.info(f"動画生成完了: {output_path}")
        return output_path

    except Exception as e:
        logging.critical(f"動画生成中に致命的なエラーが発生しました: {e}", exc_info=True)
        return None

    finally:
        # --- 7. リソース解放 ---
        logging.info("moviepyリソースを解放します。")
        for clip in clips_to_close:
            if clip:
                try:
                    clip.close()
                except Exception:
                    pass
