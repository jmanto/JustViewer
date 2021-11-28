import os.path
import glob
import sys

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QSizePolicy, QMessageBox, QMainWindow, QMenu, QAction, QGraphicsScene, QGraphicsPixmapItem, \
    qApp, QFileDialog, QDialog, QVBoxLayout, QLineEdit, QWidget, QTreeWidget, QGridLayout, QGraphicsView, QAbstractScrollArea

import qtmodern.styles
import qtmodern.windows


class Dialog(QDialog):

    def __init__(self, parent=None):
        super(Dialog, self).__init__(parent)
        self.questionMessage()

    def questionMessage(self):
        reply = QMessageBox.question(self, "QMessageBox.question()",
                "Les images marquées vont être effacées.",
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)
        if reply == QMessageBox.Yes:
            print("Yes")
        elif reply == QMessageBox.No:
            print("No")
        else:
            print("Cancel")


class QImageViewer(QMainWindow):
    def __init__(self):
        super().__init__()

        self.all_image = list()
        self.to_delete = list()
        self.id = 0
        self.nb_images = 0

        self.rootDir = ""

        layout = QVBoxLayout()

        self.graphicsView = QGraphicsView()
        self.graphicsView.setSizeAdjustPolicy(QAbstractScrollArea.AdjustToContentsOnFirstShow)
        self.graphicsView.setAlignment(Qt.AlignJustify|Qt.AlignVCenter)
        self.graphicsView.setObjectName("graphicsView")

        self.infoLabel = QLineEdit()

        layout.addWidget(self.infoLabel)
        layout.addWidget(self.graphicsView)

        layout_all = QGridLayout()

        self.treeWidget = QTreeWidget()
        self.treeWidget.setObjectName("treeWidget")
        self.treeWidget.headerItem().setText(0, "Structure")
        self.treeWidget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Ignored)

        self.treeWidget.itemDoubleClicked.connect(self.onItemClicked)

        layout_all.addWidget(self.treeWidget, 1, 1)
        layout_all.addLayout(layout, 1, 2)

        layout_all.setColumnStretch(2, 1)

        widget = QWidget()
        widget.setLayout(layout_all)

        self.setCentralWidget(widget)

        self.createActions()
        self.createMenus()

        self.setWindowTitle("Image Viewer")
        self.showMaximized()

    def load_project_structure(self, startpath, tree):
        from PyQt5.QtWidgets import QTreeWidgetItem
        from PyQt5.QtGui import QIcon

        for element in os.listdir(startpath):
            path_info = startpath + "/" + element
            parent_itm = QTreeWidgetItem(tree, [os.path.basename(element)])

            if os.path.isdir(path_info):
                self.load_project_structure(path_info, parent_itm)
                parent_itm.setIcon(0, QIcon('assets/dossier.png'))
            else:
                parent_itm.setIcon(0, QIcon('assets/fichier.png'))

    def getItemFullPath(self, item):
        out = item.text(0)
    
        if item.parent():
            out = self.getItemFullPath(item.parent()) + "/" + out
    
        return out;
    
    def onItemClicked(self, it, col):
        fullfilename = self.rootDir + self.getItemFullPath(it) + "/"

        if os.path.isdir(fullfilename):
            gen = glob.iglob(os.path.dirname(fullfilename) + r"/**/*.*", recursive=True)
            res = [f for f in gen if ".png" in f or ".jpeg" in f or ".jpg" in f or ".bmp" in f or ".gif" in f]
            
            self.all_image = list()
            self.to_delete = list()

            for file in res:
                self.all_image.append(file)
                self.to_delete.append(False)

            self.id = 0
            self.nb_images = len(self.all_image)

            fileName = self.all_image[self.id]
            self.showImageInView(fileName)

    def open(self):
        options = QFileDialog.Options()

        fileName, _ = QFileDialog.getOpenFileName(self, 'Sélectionner un fichier image', '',
                                                  'Images (*.png *.jpeg *.jpg *.bmp *.gif)', options=options)
        
      
        if fileName:
            gen = glob.iglob(os.path.dirname(fileName) + r"/**/*.*", recursive=True)
            res = [f for f in gen if ".png" in f or ".jpeg" in f or ".jpg" in f or ".bmp" in f or ".gif" in f]

            self.all_image = list()

            for file in res:
                self.all_image.append(file)
                self.to_delete.append(False)

            self.id = 0
            self.nb_images = len(self.all_image)
            fileName = self.all_image[self.id]
    
            self.showImageInView(fileName)

    def openDir(self):
        file_dialog = QFileDialog(self)
        file_dialog.setFileMode(QFileDialog.Directory)

        directory = QFileDialog.getExistingDirectory(self, "Sélectionner un répertoire", "", QFileDialog.ShowDirsOnly)

        if directory:
            self.load_project_structure(directory, self.treeWidget)
            self.rootDir = directory + "/"

    def showImageInView(self, fileName):
        scene = QGraphicsScene(self)
        image_path = fileName
        pixmap = QPixmap(image_path).scaled(viewer_width, viewer_height, Qt.KeepAspectRatio)
        item = QGraphicsPixmapItem(pixmap)
        scene.addItem(item)
        self.graphicsView.setScene(scene)

        self.infoLabel.setText(f"[{self.id + 1}/{self.nb_images}]: {fileName}")

        if self.to_delete[self.id]:
            self.infoLabel.setStyleSheet("color: red;")
        else:
            self.infoLabel.setStyleSheet("color: black;")

        # TODO: first time only (enabled)
        self.deleteAct.setEnabled(True)
        self.previousImageAct.setEnabled(True)
        self.nextImageAct.setEnabled(True)
        self.markDeleteAct.setEnabled(True)
        self.markDeleteDirAct.setEnabled(True)

    def previousImage(self):
        self.id = (self.id - 1) % self.nb_images

        fileName = self.all_image[self.id]
        self.showImageInView(fileName)

    def nextImage(self):
        self.id = (self.id + 1) % self.nb_images

        fileName = self.all_image[self.id]
        self.showImageInView(fileName)

    def make_for_delete(self):
        self.to_delete[self.id] = True

    def make_for_delete_dir(self):
        current_dir = os.path.dirname(self.all_image[self.id])

        for i, file in enumerate(self.all_image):
            if os.path.dirname(file) == current_dir:
                self.to_delete[i] = True

    def deleteImage(self):
        Dialog.show(self)
        for status, file in zip(self.to_delete, self.all_image):
            if status:
                os.remove(file)

    def about(self):
        QMessageBox.about(self, "About Image Viewer",
                          "<p>Ce programme basique, inspiré d'exemples, permet d'afficher des images \
                           en les mettant à l'échelle de la fenêtre.</p> \
                            <p>Deux modes de navigations existent: soit une première image est choisie, \
                            et toutes les images dans le mêem dossier et dans les sous-dossiers sont sélectionnées. Soit \
                            un répertoire est choisi, et la navigation peut se faire dans les sous-dossiers.</p> \
                            <p>Améliorations à prévoir: remise à zéro de l'arborescence lorsqu'on choisi un nouveau dossier racine.</p> \
                            <p>Icônes conçues par <b>Vignesh Oviyan</b>, flaticon</p>"
                        )

    def createActions(self):
        self.openAct = QAction("&Open...", self, shortcut="Ctrl+O", triggered=self.open)
        self.openDirAct = QAction("&Open Folder...", self, triggered=self.openDir)
        self.deleteAct = QAction("&Delete...", self, enabled=False, triggered=self.deleteImage)
        self.exitAct = QAction("E&xit", self, shortcut="Ctrl+Q", triggered=self.close)

        self.previousImageAct = QAction("Previous Image", self, shortcut="Ctrl+S", enabled=False, triggered=self.previousImage)
        self.nextImageAct = QAction("Next Image", self, shortcut="Ctrl+D", enabled=False, triggered=self.nextImage)
        self.markDeleteAct = QAction("Mark Image", self, shortcut="Ctrl+E", enabled=False, triggered=self.make_for_delete)
        self.markDeleteDirAct = QAction("Mark Directory", self, shortcut="Ctrl+R", enabled=False, triggered=self.make_for_delete_dir)

        self.aboutAct = QAction("&About", self, triggered=self.about)
        self.aboutQtAct = QAction("About &Qt", self, triggered=qApp.aboutQt)

    def createMenus(self):
        self.fileMenu = QMenu("&File", self)
        self.fileMenu.addAction(self.openAct)
        self.fileMenu.addAction(self.openDirAct)
        self.fileMenu.addSeparator()
        self.fileMenu.addAction(self.deleteAct)
        self.fileMenu.addSeparator()
        self.fileMenu.addAction(self.exitAct)

        self.changeMenu = QMenu("&Change", self)
        self.changeMenu.addAction(self.previousImageAct)
        self.changeMenu.addAction(self.nextImageAct)
        self.changeMenu.addAction(self.markDeleteAct)
        self.changeMenu.addAction(self.markDeleteDirAct)

        self.helpMenu = QMenu("&Help", self)
        self.helpMenu.addAction(self.aboutAct)
        self.helpMenu.addAction(self.aboutQtAct)

        self.menuBar().addMenu(self.fileMenu)
        self.menuBar().addMenu(self.changeMenu)
        self.menuBar().addMenu(self.helpMenu)

    
if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication
    
    windowStyle = "fusion"

    viewer_width = 1635
    viewer_height = 945

    if not QApplication.instance():
        app = QApplication(sys.argv)
    else:
        app = QApplication.instance() 

    if windowStyle == "light":
        qtmodern.styles.light(app)

    elif windowStyle == "dark":
        qtmodern.styles.dark(app)
    else:
        app.setStyle("Fusion")

    window = QImageViewer()

    if windowStyle == "light" or windowStyle == "dark":
        mw = qtmodern.windows.ModernWindow(window)
        mw.show()
    else:
        window.show()

    app.exec_()