import sys
import os
import time
from PyQt4 import QtGui, QtCore

sys.path.insert(0, os.path.split(__file__)[0])

import dbConnection
from main import Main
import images

from reportlab.pdfbase import _fontdata_widths_courier
from reportlab.pdfbase import _fontdata_widths_courierbold
from reportlab.pdfbase import _fontdata_widths_courieroblique
from reportlab.pdfbase import _fontdata_widths_courierboldoblique
from reportlab.pdfbase import _fontdata_widths_helvetica
from reportlab.pdfbase import _fontdata_widths_helveticabold
from reportlab.pdfbase import _fontdata_widths_helveticaoblique
from reportlab.pdfbase import _fontdata_widths_helveticaboldoblique
from reportlab.pdfbase import _fontdata_widths_timesroman
from reportlab.pdfbase import _fontdata_widths_timesbold
from reportlab.pdfbase import _fontdata_widths_timesitalic
from reportlab.pdfbase import _fontdata_widths_timesbolditalic
from reportlab.pdfbase import _fontdata_widths_symbol
from reportlab.pdfbase import _fontdata_widths_zapfdingbats
from reportlab.pdfbase import _fontdata_enc_winansi
from reportlab.pdfbase import _fontdata_enc_macroman
from reportlab.pdfbase import _fontdata_enc_standard
from reportlab.pdfbase import _fontdata_enc_symbol
from reportlab.pdfbase import _fontdata_enc_zapfdingbats
from reportlab.pdfbase import _fontdata_enc_pdfdoc
from reportlab.pdfbase import _fontdata_enc_macexpert


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