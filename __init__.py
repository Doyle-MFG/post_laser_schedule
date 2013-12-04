import sys
import os
import time
from PyQt4 import QtGui, QtCore

sys.path.insert(0, os.path.split(__file__)[0])

import dbConnection
from main import Main

from reportlab.pdfbase import _fontdata_widths_courier #@UnresolvedImport @UnusedImport
from reportlab.pdfbase import _fontdata_widths_courierbold #@UnresolvedImport @UnusedImport
from reportlab.pdfbase import _fontdata_widths_courieroblique #@UnresolvedImport @UnusedImport
from reportlab.pdfbase import _fontdata_widths_courierboldoblique #@UnresolvedImport @UnusedImport
from reportlab.pdfbase import _fontdata_widths_helvetica #@UnresolvedImport @UnusedImport
from reportlab.pdfbase import _fontdata_widths_helveticabold #@UnresolvedImport @UnusedImport
from reportlab.pdfbase import _fontdata_widths_helveticaoblique #@UnresolvedImport @UnusedImport
from reportlab.pdfbase import _fontdata_widths_helveticaboldoblique #@UnresolvedImport @UnusedImport
from reportlab.pdfbase import _fontdata_widths_timesroman #@UnresolvedImport @UnusedImport
from reportlab.pdfbase import _fontdata_widths_timesbold #@UnresolvedImport @UnusedImport
from reportlab.pdfbase import _fontdata_widths_timesitalic #@UnresolvedImport @UnusedImport
from reportlab.pdfbase import _fontdata_widths_timesbolditalic #@UnresolvedImport @UnusedImport
from reportlab.pdfbase import _fontdata_widths_symbol #@UnresolvedImport @UnusedImport
from reportlab.pdfbase import _fontdata_widths_zapfdingbats #@UnresolvedImport @UnusedImport
from reportlab.pdfbase import _fontdata_enc_winansi #@UnresolvedImport @UnusedImport
from reportlab.pdfbase import _fontdata_enc_macroman #@UnresolvedImport @UnusedImport
from reportlab.pdfbase import _fontdata_enc_standard #@UnresolvedImport @UnusedImport
from reportlab.pdfbase import _fontdata_enc_symbol #@UnresolvedImport @UnusedImport
from reportlab.pdfbase import _fontdata_enc_zapfdingbats #@UnresolvedImport @UnusedImport
from reportlab.pdfbase import _fontdata_enc_pdfdoc #@UnresolvedImport @UnusedImport
from reportlab.pdfbase import _fontdata_enc_macexpert #@UnresolvedImport @UnusedImport


def main():

    def update_splash(text):
        splash.showMessage(text)
        app.processEvents()

    app = QtGui.QApplication(sys.argv)
    splash_img = QtGui.QPixmap("splash.png")
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
    myapp.show()
    update_splash("GUI Loaded...")
    myapp.load_tabs()
    update_splash("Loading Actions...")
    myapp.load_actions()
    splash.finish(myapp)
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()