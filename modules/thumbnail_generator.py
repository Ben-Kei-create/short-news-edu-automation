import os
import datetime
from PIL import Image, ImageDraw, ImageFont
import numpy as np
from moviepy.editor import ImageClip

def find_font(args):
    """利用可能なフォントパスを検索する。カスタムフォント、システムフォントの順で探す。"""
    # 1. Check for custom font specified via args
    if args and args.font:
        custom_font_path = os.path.join("input/fonts", args.font)
        if os.path.exists(custom_font_path):
            print(f"  - カスタムフォントを使用します: {custom_font_path}")
            return custom_font_path
        else:
            print(f"  - 警告: 指定されたフォントファイルが見つかりません: {custom_font_path}")

    # 2. If no custom font, check for default macOS font
    default_mac_font = '/System/Library/Fonts/ヒラギノ角ゴ ProN W3.otf'
    if os.path.exists(default_mac_font):
        print(f"  - デフォルトのシステムフォントを使用します: {default_mac_font}")
        return default_mac_font

    # 3. If no suitable font is found
    print("  - 警告: 利用可能な日本語フォントが見つかりませんでした。")
    return None

def generate_thumbnail(theme, images, args, settings):
    """
    動画のテーマと画像リストからサムネイルを生成する。
    """
    if not images:
        print("  - サムネイル生成用の画像がありません。")
        return None

    base_image_path = images[0]
    output_dir = "output/thumbnails"
    os.makedirs(output_dir, exist_ok=True)
    safe_theme_name = "".join(c for c in theme if c.isalnum() or c in (' ', '-')).rstrip()[:50]
    output_path = os.path.join(output_dir, f"{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}_{safe_theme_name}_thumbnail.jpg")

    try:
        pil_image = Image.open(base_image_path)
    except (IOError, OSError) as e:
        print(f"  - エラー: サムネイルのベース画像 ({base_image_path}) の読み込みエラー: {e}")
        return None

    try:
        # Resize image
        target_width = 1920
        aspect_ratio = pil_image.width / pil_image.height
        target_height = int(target_width / aspect_ratio)
        pil_image = pil_image.resize((target_width, target_height), Image.Resampling.LANCZOS)

        draw = ImageDraw.Draw(pil_image)

        # Find and load font
        font_path = find_font(args)
        try:
            font_size = settings['video_composer']['font_size']
            title_font = ImageFont.truetype(font_path, font_size + 20) if font_path else ImageFont.load_default(size=font_size + 20)
            series_font = ImageFont.truetype(font_path, font_size - 10) if font_path else ImageFont.load_default(size=font_size - 10)
        except (IOError, KeyError) as e:
            print(f"  - 警告: フォントの読み込みに失敗しました ({e})。デフォルトフォントで代替します。")
            font_size = 60 # Fallback size
            title_font = ImageFont.load_default(size=font_size + 20)
            series_font = ImageFont.load_default(size=font_size - 10)

        # Prepare text
        title_color = settings.get('video_composer', {}).get('font_color', 'white')
        series_color = (255, 255, 0)  # Yellow
        series_text = "しくじりニュース"

        # Draw text with simple stroke
        def draw_text_with_stroke(pos, text, font, fill_color):
            x, y = pos
            stroke_width = 2
            stroke_color = "black"
            # Draw stroke
            for i in range(-stroke_width, stroke_width + 1):
                for j in range(-stroke_width, stroke_width + 1):
                    if i != 0 or j != 0:
                        draw.text((x + i, y + j), text, font=font, fill=stroke_color)
            # Draw text
            draw.text(pos, text, font=font, fill=fill_color)

        # Calculate positions and draw
        title_bbox = draw.textbbox((0, 0), theme, font=title_font)
        title_x = (pil_image.width - (title_bbox[2] - title_bbox[0])) / 2
        title_y = 50
        draw_text_with_stroke((title_x, title_y), theme, title_font, title_color)

        series_bbox = draw.textbbox((0, 0), series_text, font=series_font)
        series_x = (pil_image.width - (series_bbox[2] - series_bbox[0])) / 2
        series_y = pil_image.height - 150
        draw_text_with_stroke((series_x, series_y), series_text, series_font, series_color)

        # Save image
        pil_image.convert("RGB").save(output_path, "JPEG", quality=95)

        print(f"  -> サムネイル生成完了: {output_path}")
        return output_path

    except Exception as e:
        print(f"  - サムネイル生成中に予期せぬエラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        return None
