# modules/utils.py
import os

def ensure_folder(folder_path):
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)