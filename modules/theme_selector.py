# modules/theme_selector.py
def filter_duplicate_themes(theme_list):
    return list(set(theme_list))

def select_themes_for_batch(theme_list, batch_size=5):
    return theme_list[:batch_size]