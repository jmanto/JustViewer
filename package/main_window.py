import os.path
import glob
import subprocess

from time import sleep

from functools import partial

from PyQt5 import QtWidgets, QtCore, QtGui

import package.app_base as ab

FILEBROWSER_PATH = os.path.join(os.getenv('WINDIR'), 'explorer.exe')


class QOpenBox(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        x, y = ab.window_corner(ab.width, ab.height)
        self.setGeometry(x, y, ab.width, ab.height)

        self.lbl_picture = QtWidgets.QLabel()
        self.lbl_picture.setPixmap(QtGui.QPixmap("assets/OpenPicture.png"))

        style = ab.apply_style()
        self.setStyleSheet(style)

        layout = QtWidgets.QGridLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.lbl_picture, 0, 0, 1, 1)

        self.setLayout(layout)

        self.setWindowFlags(QtCore.Qt.FramelessWindowHint)

        self.show()
        sleep(2)
        self.close()


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, log_file="log_file.txt"):
        super().__init__()

        self.window_maximized = False
        self.viewer_width = 1635
        self.viewer_height = 945

        self.LOG_FILE = log_file

        self.all_image = list()
        self.to_delete = list()
        self.id = 0
        self.nb_images = 0

        self.rootDir = ""

        self.setWindowTitle("JustViewer")
        self.setWindowIcon(QtGui.QIcon('assets/JustViewer.png'))

        self.open_icon = self.style().standardIcon(QtWidgets.QStyle.SP_FileIcon)
        self.openDir_icon = self.style().standardIcon(QtWidgets.QStyle.SP_DirIcon)
        self.clip_icon = self.style().standardIcon(QtWidgets.QStyle.SP_FileLinkIcon)
        self.showclip_icon = self.style().standardIcon(QtWidgets.QStyle.SP_DirLinkIcon)

        self.setup_ui()

        wb = QOpenBox()
        wb.show()

        self.showMaximized()

    def setup_ui(self):
        self.create_widgets()
        self.modify_widgets()
        self.create_layouts()
        self.add_widgets_to_layouts()
        self.setup_connections()

    def create_widgets(self):
        self.graphicsView = QtWidgets.QGraphicsView()
        self.infoLabel = QtWidgets.QLineEdit()
        self.treeWidget = QtWidgets.QTreeWidget()

        self.toolbar = QtWidgets.QToolBar()

        # ACTIONS
        self.act_open = self.toolbar.addAction(self.open_icon, "Open File")
        self.act_openDir = self.toolbar.addAction(self.openDir_icon, "Open Directory")
        self.act_clip = self.toolbar.addAction(self.clip_icon, "To Clipboard")
        self.act_showclip = self.toolbar.addAction(self.showclip_icon, "Show Clipboard Folder")

    def modify_widgets(self):
        style = ab.apply_style()
        self.setStyleSheet(style)
        self.act_clip.setDisabled(True)

        self.graphicsView.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContentsOnFirstShow)
        self.graphicsView.setAlignment(QtCore.Qt.AlignJustify|QtCore.Qt.AlignVCenter)

        self.treeWidget.headerItem().setText(0, "Folders and Files")
        self.treeWidget.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Ignored)

    def create_layouts(self):
        self.layout_v = QtWidgets.QVBoxLayout()
        self.layout_all = QtWidgets.QGridLayout()

    def add_widgets_to_layouts(self):
        self.addToolBar(self.toolbar)

        self.layout_v.addWidget(self.infoLabel)
        self.layout_v.addWidget(self.graphicsView)

        self.layout_all.addWidget(self.treeWidget, 0, 0, 1, 1)
        self.layout_all.addLayout(self.layout_v, 0, 1, 1, 1)

        self.layout_all.setColumnStretch(0, 1)
        self.layout_all.setColumnStretch(1, 12)

        wid = QtWidgets.QWidget(self)
        self.setCentralWidget(wid)

        wid.setLayout(self.layout_all)

    def setup_connections(self):
        QtWidgets.QShortcut(QtGui.QKeySequence("F"), self, self.change_window_state)
        QtWidgets.QShortcut(QtGui.QKeySequence("A"), self, self.fast_backward)
        QtWidgets.QShortcut(QtGui.QKeySequence("S"), self, self.fast_forward)

        self.graphicsView.viewport().installEventFilter(self)

        self.treeWidget.itemDoubleClicked.connect(self.onItemClicked)

        self.act_open.triggered.connect(self.open)
        self.act_openDir.triggered.connect(self.openDir)
        self.act_clip.triggered.connect(self.clip)
        self.act_showclip.triggered.connect(partial(self.explore, self.LOG_FILE))

    def eventFilter(self, source, event):
        if source == self.graphicsView.viewport() and event.type() == QtCore.QEvent.Wheel:
            if event.angleDelta().y() < 0:
                self.nextImage()
            else:
                self.previousImage()

        return False  # A garder pour éviter une erreur

    def change_window_state(self):
        self.window_maximized = not self.window_maximized

        if self.window_maximized:
            self.showFullScreen()
            self.treeWidget.hide()
            self.infoLabel.hide()
            self.layout_all.setColumnStretch(0, 0)
            self.layout_all.setColumnStretch(1, 1)
        else:
            self.showMaximized()
            self.treeWidget.show()
            self.infoLabel.show()

    def clip(self):
        if self.all_image:
            with open(self.LOG_FILE, "a") as f:
                f.write(self.all_image[self.id] + "\n")

    def explore(self, path):
        path = os.path.normpath(path)

        if os.path.isdir(path):
            subprocess.run([FILEBROWSER_PATH, path])
        elif os.path.isfile(path):
            subprocess.run([FILEBROWSER_PATH, '/select,', os.path.normpath(path)])

    def load_project_structure(self, startpath, tree, first_call=True):
        if first_call:
            tree.clear()

        for element in os.listdir(startpath):
            path_info = os.path.join(startpath, element)
            parent_itm = QtWidgets.QTreeWidgetItem(tree, [os.path.basename(element)])

            if os.path.isdir(path_info):
                self.load_project_structure(path_info, parent_itm, first_call=False)
                parent_itm.setIcon(0, QtGui.QIcon('assets/dossier.png'))
            else:
                parent_itm.setIcon(0, QtGui.QIcon('assets/fichier.png'))

    def getItemFullPath(self, item):
        out = item.text(0)

        if item.parent():
            out = self.getItemFullPath(item.parent()) + "/" + out # TODO: os

        return out

    def onItemClicked(self, it, col):
        fullfilename = os.path.join(self.rootDir, self.getItemFullPath(it))

        if os.path.isdir(fullfilename):
            gen = glob.iglob(fullfilename + r"/**/*.*", recursive=True)
            res = [f for f in gen if
                   ".png" in f or ".jpeg" in f or ".jpg" in f or ".JPG" in f or ".bmp" in f or ".gif" in f]
            self.all_image = list()
            self.to_delete = list()

            for file in res:
                self.all_image.append(os.path.normpath(file))
                self.to_delete.append(False)

            self.id = 0
            self.nb_images = len(self.all_image)

            fileName = self.all_image[self.id]
            self.update_buttons()
            self.showImageInView(fileName)

    def open(self):
        options = QtWidgets.QFileDialog.Options()

        fileName, _ = QtWidgets.QFileDialog.getOpenFileName(self, 'Select an image file', '',
                                                  'Images (*.png *.jpeg *.jpg *.bmp *.gif)', options=options)

        if fileName:
            gen = glob.iglob(os.path.dirname(fileName) + r"/**/*.*", recursive=True)
            res = [f for f in gen if ".png" in f or ".jpeg" in f or ".jpg" in f or ".bmp" in f or ".gif" in f]

            self.all_image = list()

            for file in res:
                self.all_image.append(os.path.normpath(file))
                self.to_delete.append(False)

            self.id = 0
            self.nb_images = len(self.all_image)

            fileName = self.all_image[self.id]
            print(fileName)
            self.update_buttons()
            self.showImageInView(fileName)

    def openDir(self):
        file_dialog = QtWidgets.QFileDialog(self)
        file_dialog.setFileMode(QtWidgets.QFileDialog.Directory)

        directory = QtWidgets.QFileDialog.getExistingDirectory(self, "Select a directory", "", QtWidgets.QFileDialog.ShowDirsOnly)

        if directory:
            self.load_project_structure(directory, self.treeWidget)
            self.rootDir = directory

    def showImageInView(self, fileName):
        v_width = self.graphicsView.size()

        scene = QtWidgets.QGraphicsScene(self)
        pixmap = QtGui.QPixmap(fileName).scaled(v_width - QtCore.QSize(2, 2), QtCore.Qt.KeepAspectRatio)
        item = QtWidgets.QGraphicsPixmapItem(pixmap)
        scene.addItem(item)

        self.graphicsView.setScene(scene)
        self.infoLabel.setText(f"[{self.id + 1}/{self.nb_images}]: {fileName}")

    def previousImage(self):
        self.id = (self.id - 1) % self.nb_images

        fileName = self.all_image[self.id]
        self.showImageInView(fileName)

    def nextImage(self):
        self.id = (self.id + 1) % self.nb_images

        fileName = self.all_image[self.id]
        self.showImageInView(fileName)

    def fast_backward(self):
        self.id = (self.id - round(self.nb_images / 20)) % self.nb_images

        fileName = self.all_image[self.id]
        self.showImageInView(fileName)

    def fast_forward(self):
        self.id = (self.id + round(self.nb_images / 20)) % self.nb_images

        fileName = self.all_image[self.id]
        self.showImageInView(fileName)

    def update_buttons(self):
        self.act_clip.setDisabled(False)

