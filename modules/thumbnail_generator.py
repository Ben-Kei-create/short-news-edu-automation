import os
import datetime
from PIL import Image, ImageDraw, ImageFont
import numpy as np
from moviepy.editor import ImageClip, VideoFileClip # VideoFileClip を追加
import traceback

# find_font 関数を settings からフォントパスを取得するように修正
def find_font(settings):
    """利用可能なフォントパスを検索する。settingsからフォントパスを取得する。"""
    font_path = settings.get('subtitles', {}).get('font_path')
    if font_path and os.path.exists(font_path):
        print(f"  - 設定されたフォントを使用します: {font_path}")
        return font_path
    else:
        print(f"  - 警告: 設定されたフォントファイルが見つからないか、パスが不正です: {font_path}")
        # デフォルトのシステムフォントを試す (macOSの場合)
        default_mac_font = '/System/Library/Fonts/ヒラギノ角ゴ ProN W3.otf'
        if os.path.exists(default_mac_font):
            print(f"  - デフォルトのシステムフォントを使用します: {default_mac_font}")
            return default_mac_font
        
        print("  - 警告: 利用可能な日本語フォントが見つかりませんでした。Arialで代用します。")
        return 'Arial' # Fallback to Arial

# generate_thumbnail 関数の引数に video_file を追加
def generate_thumbnail(theme, images, args, settings, video_file=None):
    """
    動画のテーマと画像リストからサムネイルを生成する。
    settings['youtube']['auto_generate_thumbnail'] が True の場合、動画からサムネイルを抽出する。
    """
    output_dir = "output/thumbnails"
    os.makedirs(output_dir, exist_ok=True)
    safe_theme_name = "".join(c for c in theme if c.isalnum() or c in (' ', '-')).rstrip()[:50]
    output_path = os.path.join(output_dir, f"{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}_{safe_theme_name}_thumbnail.jpg")

    auto_generate_thumbnail = settings.get('youtube', {}).get('auto_generate_thumbnail', False)
    thumbnail_frame_time = settings.get('youtube', {}).get('thumbnail_frame_time', 5)

    base_image_pil = None

    if auto_generate_thumbnail and video_file and os.path.exists(video_file):
        print(f"  - 動画 ({video_file}) からサムネイルを自動生成します ({thumbnail_frame_time}秒地点)。")
        try:
            clip = VideoFileClip(video_file)
            # 指定した時間からフレームを抽出
            frame = clip.get_frame(thumbnail_frame_time)
            base_image_pil = Image.fromarray(frame)
            clip.close()
        except Exception as e:
            print(f"  - エラー: 動画からのサムネイル抽出に失敗しました: {e}")
            traceback.print_exc()
            base_image_pil = None # 失敗したら通常の画像生成にフォールバック
    
    if base_image_pil is None: # 動画からの抽出に失敗したか、自動生成がFalseの場合
        if not images:
            print("  - サムネイル生成用の画像がありません。")
            return None
        base_image_path = images[0]
        try:
            base_image_pil = Image.open(base_image_path)
        except (IOError, OSError) as e:
            print(f"  - エラー: サムネイルのベース画像 ({base_image_path}) の読み込みエラー: {e}")
            return None

    try:
        # Resize image (assuming 1920x1080 for YouTube thumbnail)
        # YouTubeのサムネイルは1280x720が推奨だが、ここでは動画のアスペクト比に合わせる
        # 動画が縦長(1080x1920)なので、サムネイルも縦長にする
        target_width = 1080 # 動画の幅に合わせる
        target_height = 1920 # 動画の高さに合わせる
        
        # 画像を中央に配置し、余白を黒で埋める
        resized_image = Image.new("RGB", (target_width, target_height), (0, 0, 0))
        
        # 元画像の縦横比を維持してリサイズ
        img_width, img_height = base_image_pil.size
        scale = min(target_width / img_width, target_height / img_height)
        new_width = int(img_width * scale)
        new_height = int(img_height * scale)
        
        temp_image = base_image_pil.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # 中央にペースト
        paste_x = (target_width - new_width) // 2
        paste_y = (target_height - new_height) // 2
        resized_image.paste(temp_image, (paste_x, paste_y))
        
        draw = ImageDraw.Draw(resized_image)

        # Find and load font (settingsから取得するように変更)
        font_path = find_font(settings)
        try:
            # サムネイル用のフォントサイズは字幕とは別に設定するか、調整する
            # ここでは字幕のフォントサイズをベースに調整
            base_font_size = settings.get('subtitles', {}).get('font_size', 48)
            title_font = ImageFont.truetype(font_path, base_font_size + 20) if font_path else ImageFont.load_default(size=base_font_size + 20)
            series_font = ImageFont.truetype(font_path, base_font_size - 10) if font_path else ImageFont.load_default(size=base_font_size - 10)
        except (IOError, KeyError) as e:
            print(f"  - 警告: フォントの読み込みに失敗しました ({e})。デフォルトフォントで代替します。")
            base_font_size = 60 # Fallback size
            title_font = ImageFont.load_default(size=base_font_size + 20)
            series_font = ImageFont.load_default(size=base_font_size - 10)

        # Prepare text
        title_color = settings.get('subtitles', {}).get('font_color', 'white') # 字幕の色を流用
        series_color = (255, 255, 0)  # Yellow
        series_text = "しくじりニュース" # 固定値

        # Draw text with simple stroke
        def draw_text_with_stroke(img_draw, pos, text, font, fill_color):
            x, y = pos
            stroke_width = 2
            stroke_color = "black"
            # Draw stroke
            for i in range(-stroke_width, stroke_width + 1):
                for j in range(-stroke_width, stroke_width + 1):
                    if i != 0 or j != 0:
                        img_draw.text((x + i, y + j), text, font=font, fill=stroke_color)
            # Draw text
            img_draw.text(pos, text, font=font, fill=fill_color)

        # Calculate positions and draw
        # タイトルを画像の上部に配置
        title_bbox = draw.textbbox((0, 0), theme, font=title_font)
        title_x = (resized_image.width - (title_bbox[2] - title_bbox[0])) / 2
        title_y = 50 # 上からのマージン
        draw_text_with_stroke(draw, (title_x, title_y), theme, title_font, title_color)

        # シリーズ名を画像の下部に配置
        series_bbox = draw.textbbox((0, 0), series_text, font=series_font)
        series_x = (resized_image.width - (series_bbox[2] - series_bbox[0])) / 2
        series_y = resized_image.height - 150 # 下からのマージン
        draw_text_with_stroke(draw, (series_x, series_y), series_text, series_font, series_color)

        # Save image
        resized_image.convert("RGB").save(output_path, "JPEG", quality=95)

        print(f"  -> サムネイル生成完了: {output_path}")
        return output_path

    except Exception as e:
        print(f"  - サムネイル生成中に予期せぬエラーが発生しました: {e}")
        traceback.print_exc()
        return None