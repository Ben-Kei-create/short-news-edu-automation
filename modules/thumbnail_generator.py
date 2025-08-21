import os
from moviepy.video.VideoClip import ImageClip # Keep ImageClip for the final conversion
from moviepy.video.compositing.CompositeVideoClip import CompositeVideoClip
from pathlib import Path
import numpy as np # New import
from PIL import Image, ImageDraw, ImageFont # New imports

def generate_thumbnail(theme, images):
    """
    動画のテーマと画像リストからサムネイルを生成する。
    """
    if not images:
        print("  - サムネイル生成用の画像がありません。")
        return None

    base_image_path = images[0]
    
    output_dir = "output/thumbnails"
    os.makedirs(output_dir, exist_ok=True)
    import datetime
    current_date = datetime.datetime.now().strftime("%Y%m%d")
    safe_theme_name = "".join(c for c in theme if c.isalnum() or c in (' ', '-')).rstrip()
    output_path = os.path.join(output_dir, f"{current_date}_{safe_theme_name}_thumbnail.jpg")

    try:
        # Load image using Pillow
        pil_image = Image.open(base_image_path)
        # Resize the image to a standard thumbnail size, e.g., 1920x1080 or similar aspect ratio
        # For simplicity, let's assume a target width and calculate height to maintain aspect ratio
        target_width = 1920 # Assuming a common video width
        # Calculate height to maintain aspect ratio
        aspect_ratio = pil_image.width / pil_image.height
        target_height = int(target_width / aspect_ratio)
        pil_image = pil_image.resize((target_width, target_height), Image.Resampling.LANCZOS)

        draw = ImageDraw.Draw(pil_image)

        # Load a font (adjust path as necessary for your system)
        # Common font paths for macOS: /Library/Fonts/Arial.ttf or /System/Library/Fonts/Arial.ttf
        try:
            title_font = ImageFont.truetype("/Library/Fonts/Arial.ttf", 80)
            series_font = ImageFont.truetype("/Library/Fonts/Arial.ttf", 50)
        except IOError:
            print("  - フォントファイルが見つかりません。システムにArial.ttfがインストールされているか確認してください。")
            print("    代替フォントを使用するか、フォントパスを修正してください。")
            # Fallback to a default font if Arial.ttf is not found, or raise an error
            # For now, let's just use a generic font if truetype fails, or handle it more gracefully.
            # If this fails, the user will need to provide a valid font path.
            title_font = ImageFont.load_default()
            series_font = ImageFont.load_default()


        # Text colors
        title_color = (255, 255, 255) # White
        series_color = (255, 255, 0) # Yellow

        # Calculate text positions
        # For center alignment, need text size
        # Get text bounding box (left, top, right, bottom)
        # textbbox requires a position, but we only need the size for centering.
        # We can use (0,0) as a dummy position to get the size.
        title_bbox = draw.textbbox((0, 0), theme, font=title_font)
        title_text_width = title_bbox[2] - title_bbox[0]
        title_text_height = title_bbox[3] - title_bbox[1]

        series_bbox = draw.textbbox((0, 0), "しくじりニュース", font=series_font)
        series_text_width = series_bbox[2] - series_bbox[0]
        series_text_height = series_bbox[3] - series_bbox[1]

        title_x = (pil_image.width - title_text_width) / 2
        title_y = 50 # Top padding

        series_x = (pil_image.width - series_text_width) / 2
        series_y = pil_image.height - 150 # Bottom padding

        # Draw text
        draw.text((title_x, title_y), theme, font=title_font, fill=title_color)
        draw.text((series_x, series_y), "しくじりニュース", font=series_font, fill=series_color)

        # Convert Pillow image to MoviePy ImageClip
        pil_image = pil_image.convert("RGB") # Add this line to convert to RGB
        img_clip = ImageClip(np.array(pil_image))

        # Save the frame (MoviePy's save_frame handles the conversion to JPG)
        img_clip.save_frame(output_path)
        print(f"  -> サムネイル生成完了: {output_path}")
        return output_path

    except Exception as e:
        print(f"  - サムネイル生成エラー: {e}")
        return None