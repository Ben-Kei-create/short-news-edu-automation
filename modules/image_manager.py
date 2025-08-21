# modules/image_manager.py
import os

def load_manual_images(folder_path):
    if not folder_path or not os.path.exists(folder_path):
        return []
    return [os.path.join(folder_path, f) for f in os.listdir(folder_path) if f.endswith(('.png','.jpg'))]

def generate_images(theme, style, num=5):
    # 仮: AI画像生成
    return [f"{theme}_{i}.png" for i in range(num)]