import os
from pathlib import Path

LOG_DIR = os.path.join(Path.home(), ".JustViewer")
LOG_FILE = "log_file.txt"
CSS_FILE = "assets/style.css"

SCREEN_WIDTH = 1920
SCREEN_HEIGHT = 1080

width = 480
height = 300


def window_corner(width, height):
    x = round((SCREEN_WIDTH - width) / 2)
    y = round((SCREEN_HEIGHT - height) / 2)
    return x, y

def apply_style():
    with open(CSS_FILE, "r") as f:
        style = f.read()

    return style