import sys
import os
import time
from PyQt4 import QtGui, QtCore

sys.path.insert(0, os.path.split(__file__)[0])

import dbConnection
from main import Main
import images

from reportlab.pdfbase import *

#TODO: Scan to Add


def main():

    def update_splash(text):
        splash.showMessage(text)
        app.processEvents()

    app = QtGui.QApplication(sys.argv)
    splash_img = QtGui.QPixmap(':images/splash.png')
    splash = QtGui.QSplashScreen(splash_img, QtCore.Qt.WindowStaysOnTopHint)
    splash.show()
    time.sleep(.001)
    update_splash("Establishing Connection...")
    if not dbConnection.default_connection():
        QtGui.QMessageBox.critical(None, "No Connection!", "The database connection could not be established.")
        sys.exit(1)
    update_splash("Loading GUI...")
    myapp = Main()
    myapp.tab_loaded.connect(update_splash)
    myapp.setWindowIcon(QtGui.QIcon(':images/post_laser_schedule.ico'))
    myapp.show()
    update_splash("GUI Loaded...")
    myapp.load_tabs()
    update_splash("Loading Actions...")
    myapp.load_actions()
    splash.finish(myapp)
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()