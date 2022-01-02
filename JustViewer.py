import os.path
import sys

from PyQt5.QtWidgets import QApplication

from package.main_window import MainWindow, QOpenBox
import package.app_base as ab

    
if __name__ == '__main__':
    if not QApplication.instance():
        app = QApplication(sys.argv)
    else:
        app = QApplication.instance() 

    if not os.path.exists(ab.LOG_DIR):
        os.makedirs(ab.LOG_DIR)

    LOG_FILE = os.path.join(ab.LOG_DIR, ab.LOG_FILE)

#    window = QOpenBox(log_file=LOG_FILE)
    window = MainWindow(log_file=LOG_FILE)
    window.show()

    app.exec_()