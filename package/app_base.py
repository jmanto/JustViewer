import os
from pathlib import Path

from PyQt5 import QtWidgets, QtCore, QtGui
from time import sleep


# Apps specific
APP_NAME = "JustViewer"
APP_ICON = "assets/JustViewer.png"

LOG_DIR = os.path.join(Path.home(), ".JustViewer")
LOG_FILE = "log_file.txt"
CSS_FILE = "assets/style.css"

help_str = """
A: speed backward (approximately 5% of the whole number of pictures)

S: speed forward (approximately 5% of the whole number of pictures)

F: switch between full screen and normal mode

E: show/hide EXIF infos (if available)

I: show/hide the complete path to the image

H: show help

Version 1.2, June 2022
"""

# Generic
SCREEN_WIDTH = 1920
SCREEN_HEIGHT = 1080

width = 640
height = 360

width_info_box = 600
height_info_box = 400


class OpeningWindow(QtWidgets.QWidget):
    def __init__(self, width=600, height=400):
        super().__init__()

        x, y = window_corner(width, height)
        self.setGeometry(x, y, width, height)

        self.lbl_picture = QtWidgets.QLabel()
        self.lbl_picture.setPixmap(QtGui.QPixmap("assets/bg_black_white.png"))

        style = apply_style()
        self.setStyleSheet(style)

        layout = QtWidgets.QGridLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.lbl_picture, 0, 0, 1, 1)

        self.setLayout(layout)

        self.setWindowFlags(QtCore.Qt.FramelessWindowHint)

        self.show()
        sleep(2)
        self.close()


class InfoWindow(QtWidgets.QWidget):
    def __init__(self, type="Label", title="Window Title", text=""):
        super().__init__()
        if type == "Label":
            x, y = window_corner(width_info_box, height_info_box)
            self.setGeometry(x, y, width_info_box, height_info_box)

            self.lb_info = QtWidgets.QLabel()
            self.lb_info.setText(text)

            style = apply_style()
            self.setStyleSheet(style)

            layout = QtWidgets.QGridLayout()
            layout.setContentsMargins(0, 0, 0, 0)
            layout.addWidget(self.lb_info, 0, 0, 1, 1)
            self.setLayout(layout)

            self.setWindowTitle(title)
            self.setWindowIcon(QtGui.QIcon(APP_ICON))
        else:
            self.lb_info = QtWidgets.QTextEdit()
            self.lb_info.setText(text)

            style = apply_style()
            self.setStyleSheet(style)

            layout = QtWidgets.QGridLayout()
            layout.setContentsMargins(0, 0, 0, 0)
            layout.addWidget(self.lb_info, 0, 0, 1, 1)
            self.setLayout(layout)

            self.setWindowTitle(title)
            self.setWindowIcon(QtGui.QIcon(APP_ICON))


class OnTopInfo(QtWidgets.QFrame):
    def __init__(self, parent, text):
        super().__init__(parent)
        layout = QtWidgets.QHBoxLayout(self)
        self.label = QtWidgets.QLabel(text, alignment=QtCore.Qt.AlignCenter)
        layout.addWidget(self.label)


def window_corner(width, height):
    x = round((SCREEN_WIDTH - width) / 2)
    y = round((SCREEN_HEIGHT - height) / 2)
    return x, y


def apply_style():
    with open(CSS_FILE, "r") as f:
        style = f.read()

    return style