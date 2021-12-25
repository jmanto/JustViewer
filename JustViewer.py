import os.path
import sys

from PyQt5.QtWidgets import QApplication

from package.main_window import MainWindow
import package.constants as pc

    
if __name__ == '__main__':
    if not QApplication.instance():
        app = QApplication(sys.argv)
    else:
        app = QApplication.instance() 

    if not os.path.exists(pc.APP_DIR):
        os.makedirs(pc.APP_DIR)

    LOG_FILE = os.path.join(pc.APP_DIR, pc.APP_LOG)

    window = MainWindow(log_file=LOG_FILE)
    window.show()

    app.exec_()