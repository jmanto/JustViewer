import os.path
import glob
import subprocess

from functools import partial

from PyQt5 import QtWidgets, QtCore, QtGui

from PIL import Image, ImageOps, ExifTags
import exifread

import package.app_base as ab

FILEBROWSER_PATH = os.path.join(os.getenv('WINDIR'), 'explorer.exe')


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()

        self.help_window = ab.InfoWindow(title=ab.APP_NAME + " - Help", text=ab.help_str)

        self.window_maximized = False
        self.show_exif_info = True
        self.info_str = "No EXIF info"

        if not os.path.exists(ab.LOG_DIR):
            os.makedirs(ab.LOG_DIR)

        self.LOG_FILE = os.path.join(ab.LOG_DIR, ab.LOG_FILE)

        self.all_image = list()
        self.id = 0
        self.nb_images = 0

        self.rootDir = ""

        wb = ab.OpeningWindow(width=ab.width, height=ab.height)
        wb.show()

        self.open_icon = self.style().standardIcon(QtWidgets.QStyle.SP_FileIcon)
        self.openDir_icon = self.style().standardIcon(QtWidgets.QStyle.SP_DirIcon)
        self.clip_icon = self.style().standardIcon(QtWidgets.QStyle.SP_FileLinkIcon)
        self.showclip_icon = self.style().standardIcon(QtWidgets.QStyle.SP_DirLinkIcon)

        self.setup_ui()
        self.setWindowTitle(ab.APP_NAME)
        self.setWindowIcon(QtGui.QIcon(ab.APP_ICON))

        self.showMaximized()

    def setup_ui(self):
        self.create_widgets()
        self.modify_widgets()
        self.create_layouts()
        self.add_widgets_to_layouts()
        self.setup_connections()

    def create_widgets(self):
        self.graphicsView = QtWidgets.QGraphicsView()
        self.nbImage = QtWidgets.QLineEdit()
        self.treeWidget = QtWidgets.QTreeWidget()
        self.exifInfo = QtWidgets.QPlainTextEdit()
        self.toolbar = QtWidgets.QToolBar()

        self.picture_name = ab.OnTopInfo(self.graphicsView, "No image")

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

        self.nbImage.setAlignment(QtCore.Qt.AlignHCenter)

    def create_layouts(self):
        self.splitter_v = QtWidgets.QSplitter(QtCore.Qt.Vertical)
        self.splitter_h = QtWidgets.QSplitter(QtCore.Qt.Horizontal)

        self.layout_v = QtWidgets.QVBoxLayout()
        self.layout_all = QtWidgets.QGridLayout()

    def add_widgets_to_layouts(self):
        self.addToolBar(self.toolbar)

        self.splitter_v.addWidget(self.treeWidget)
        self.splitter_v.addWidget(self.nbImage)

        self.splitter_v.setStretchFactor(0, 10)
        self.splitter_v.setStretchFactor(1, 1)

        self.splitter_h.addWidget(self.splitter_v)
        self.splitter_h.addWidget(self.graphicsView)
        self.splitter_h.addWidget(self.exifInfo)

        self.splitter_h.setStretchFactor(0, 1)
        self.splitter_h.setStretchFactor(1, 12)
        self.splitter_h.setStretchFactor(2, 1)

        self.layout_all.addWidget(self.splitter_h)

        wid = QtWidgets.QWidget(self)
        self.setCentralWidget(wid)

        wid.setLayout(self.layout_all)

    def setup_connections(self):
        QtWidgets.QShortcut(QtGui.QKeySequence("F"), self, self.change_window_state)
        QtWidgets.QShortcut(QtGui.QKeySequence("A"), self, self.fast_backward)
        QtWidgets.QShortcut(QtGui.QKeySequence("S"), self, self.fast_forward)
        QtWidgets.QShortcut(QtGui.QKeySequence("E"), self, self.switch_info)
        QtWidgets.QShortcut(QtGui.QKeySequence("H"), self, self.show_help)
        QtWidgets.QShortcut(QtGui.QKeySequence("I"), self, self.show_picture_name)

        self.graphicsView.viewport().installEventFilter(self)

        self.treeWidget.itemDoubleClicked.connect(self.onItemClicked)

        self.act_open.triggered.connect(self.open)
        self.act_openDir.triggered.connect(self.openDir)
        self.act_clip.triggered.connect(self.clip)
        self.act_showclip.triggered.connect(partial(self.explore, self.LOG_FILE))

    def eventFilter(self, source, event):
        if source == self.graphicsView.viewport() and event.type() == QtCore.QEvent.Wheel and self.nb_images != 0:
            if event.angleDelta().y() < 0:
                self.nextImage()
            else:
                self.previousImage()

        if source == self.graphicsView.viewport() and event.type() == QtCore.QEvent.MouseButtonDblClick:
            self.show_exif_info = False
            self.exifInfo.hide()

            self.picture_name.hide()

            self.window_maximized = True
            self.showFullScreen()
            self.splitter_v.hide()

        return False  # A garder pour éviter une erreur

    def change_window_state(self):
        self.window_maximized = not self.window_maximized

        if self.window_maximized:
            self.showFullScreen()
            self.splitter_v.hide()
        else:
            self.showMaximized()
            self.splitter_v.show()

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

            for file in res:
                self.all_image.append(os.path.normpath(file))

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
            gen = glob.glob(os.path.dirname(fileName) + r"/**/*.*", recursive=True)
            res = [f for f in gen if ".png" in f or ".jpeg" in f or ".jpg" in f or ".bmp" in f or ".gif" in f]

            self.all_image = list()

            for file in res:
                self.all_image.append(os.path.normpath(file))

            self.id = 0
            self.nb_images = len(self.all_image)

            fileName = self.all_image[self.id]

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
        # Default values if EXIF datas are not available
        fileNametoUse = fileName
        self.info_str = "No EXIF info"
        exif_data = "Horizontal (normal)"

        # EXIF infos
        with open(fileName, "rb") as f:
            tags = exifread.process_file(f, details=False) # stop_tag='Image GPSInfo'

            if tags:
                self.info_str = "\n".join(key + ": " + str(value) for key, value in tags.items())

                exif_data = str(tags.get("Image Orientation"))
                if exif_data != "Horizontal (normal)":
                    img = Image.open(fileName)
                    img_tmp = ImageOps.exif_transpose(img)
                    img_tmp.save("temp.jpg")
                    fileNametoUse = "temp.jpg"

        v_width = self.graphicsView.size()
        scene = QtWidgets.QGraphicsScene(self)
        pixmap = QtGui.QPixmap(fileNametoUse).scaled(v_width - QtCore.QSize(2, 2), QtCore.Qt.KeepAspectRatio)
        item = QtWidgets.QGraphicsPixmapItem(pixmap)
        scene.addItem(item)

        self.graphicsView.setScene(scene)
        self.nbImage.setText(f"{self.id + 1} on {self.nb_images}")
        self.picture_name.label.setText(fileName)

        if self.exifInfo.isVisible():
            self.exifInfo.setPlainText(self.info_str)

        if exif_data != "Horizontal (normal)":
            os.remove("temp.jpg")

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

    def switch_info(self):
        self.show_exif_info = not self.show_exif_info

        if self.show_exif_info:
            self.exifInfo.setPlainText(self.info_str)
            self.exifInfo.show()
        else:
            self.exifInfo.hide()

    def show_help(self):
        if self.help_window.isVisible():
            self.help_window.hide()
        else:
            self.help_window.show()

    def show_picture_name(self):
        if self.picture_name.isVisible():
            self.picture_name.hide()
        else:
            self.picture_name.show()

    def resizeEvent(self, event):
        # Resize picture_name
        imageInfoWidth = int(max(self.picture_name.sizeHint().width(), self.graphicsView.width() * .6))
        imageInfoRect = QtCore.QRect(int((self.graphicsView.width() - imageInfoWidth) * .5), 20, imageInfoWidth, self.picture_name.sizeHint().height())
        self.picture_name.setGeometry(imageInfoRect)


