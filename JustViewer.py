import os.path
import sys

from PyQt5.QtWidgets import QApplication

from package.main_window import MainWindow
import package.app_base as ab

    
if __name__ == '__main__':
    if not QApplication.instance():
        app = QApplication(sys.argv)
    else:
        app = QApplication.instance() 

    window = MainWindow()
    window.show()

    app.exec_()