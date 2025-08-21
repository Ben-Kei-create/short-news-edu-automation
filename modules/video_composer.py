# modules/video_composer.py
from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips, CompositeAudioClip
from pathlib import Path

def compose_video(images, audio_file, bgm_file=None, output_file="output/videos/output.mp4", fps=30, duration_per_image=12):
    """
    画像＋音声＋BGMを縦動画に合成
    Args:
        images (list): 画像ファイルパスリスト
        audio_file (str): セリフ音声ファイル
        bgm_file (str): BGM音声ファイル
        output_file (str): 出力動画パス
        fps (int): フレームレート
        duration_per_image (int): 1枚画像の表示秒数
    Returns:
        str: 出力動画パス
    """
    try:
        clips = []
        for img_path in images:
            clip = ImageClip(img_path).set_duration(duration_per_image).resize(height=1920)  # 縦動画にリサイズ
            clip = clip.resize(width=1080) if clip.w != 1080 else clip  # 幅1080px調整
            clips.append(clip)

        video = concatenate_videoclips(clips, method="compose")

        # セリフ音声
        if audio_file and Path(audio_file).exists():
            voice_clip = AudioFileClip(audio_file)
            video = video.set_audio(voice_clip)

        # BGMがある場合、音量調整して合成
        if bgm_file and Path(bgm_file).exists():
            bgm_clip = AudioFileClip(bgm_file).volumex(0.3)  # BGM小さめ
            if video.audio:
                composite_audio = CompositeAudioClip([video.audio, bgm_clip])
                video = video.set_audio(composite_audio)
            else:
                video = video.set_audio(bgm_clip)

        # 動画書き出し
        Path(output_file).parent.mkdir(parents=True, exist_ok=True)
        video.write_videofile(output_file, fps=fps)
        print(f"動画生成完了: {output_file}")
        return output_file

    except Exception as e:
        print(f"動画生成エラー: {e}")
        return None