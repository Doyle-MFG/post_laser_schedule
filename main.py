__title__ = "Post Laser Schedule"
import sys
import os
from PyQt4 import QtGui, QtCore

from query import query
from dbConnection import new_connection, start_transaction, commit_transaction, rollback_transaction
from functions import create_tab, create_missing_tab, get_selected_rows, StatusDialog, reset_cursor, \
    write_settings, read_settings, resize_table
import report


class Main(QtGui.QMainWindow):
    tab_loaded = QtCore.pyqtSignal([str])

    def __init__(self, parent=None):
        QtGui.QMainWindow.__init__(self, parent)
        self.setWindowTitle(__title__)
        try:
            self.resize(read_settings("size").toSize())
            self.move(read_settings("pos").toPoint())
            self.setWindowState(read_settings("state"))
        except Exception as e:
            print e.message
            self.resize(1024, 768)
        self.tabs = QtGui.QTabWidget(self)
        self.title = QtGui.QLabel(__title__)
        self.title.setFont(QtGui.QFont("sans", 32, 63, True))
        self.central_layout = QtGui.QGridLayout()
        self.central_layout.addWidget(self.title, 0, 0)
        self.central_layout.addWidget(self.tabs, 1, 0)
        self.central_widget = QtGui.QFrame()
        self.central_widget.setLayout(self.central_layout)
        self.setCentralWidget(self.central_widget)
        self.move_action = QtGui.QAction("Move", self)
        self.update_action = QtGui.QAction("Update", self)
        self.hide_action = QtGui.QAction("Hide", self)
        self.priority_action = QtGui.QAction("Priority", self)
        self.refresh_action = QtGui.QAction("Refresh", self)
        self.print_action = QtGui.QAction("Print", self)
        self.missing_action = QtGui.QAction("Missing", self)
        self.show()

    def load_tabs(self):
        qry = query("schedules")
        if qry:
            tabs = []
            while qry.next():
                tabs.append([qry.value(0).toString(), qry.value(1).toString()])
            tab_widgets = []
            for tab in tabs:
                self.tab_loaded.emit("Loading %s..." % str(tab[1]))
                tab_widgets.append(create_tab(*tab))
            self.tab_loaded.emit("Loading Missing...")
            tab_widgets.append(create_missing_tab("Missing"))
            for widget in tab_widgets:
                self.tabs.addTab(widget, widget.windowTitle())
                widget.table.horizontalHeader().sortIndicatorChanged.connect(self.resort_table)

    def load_actions(self):
        actions = [self.move_action, self.update_action, self.hide_action, self.priority_action,
                   self.refresh_action, self.print_action, self.missing_action]
        i = 1
        for action in actions:
            self.menuBar().addAction(action)
            action.setShortcut("F%d" % i)
            action.setToolTip("F%d" % i)
            action.triggered.connect(getattr(self, "%s_triggered" % action.text().toLower()))
            i += 1

    def resort_table(self, col, order):
        QtGui.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        header = self.sender()
        table = header.parent()
        table_model = table.model()
        sort_by = table_model.headerData(col, QtCore.Qt.Horizontal).toString()
        if order:
            sort_by = "`%s` Desc" % sort_by
        else:
            sort_by = "`%s` Asc" % sort_by
        qry = query("parts", [table.machine, sort_by])
        if qry:
            table_model.setQuery(qry)
            resize_table(table)
        reset_cursor()

    def update_data(self):
        QtGui.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        self.tabs.clear()
        self.load_tabs()
        reset_cursor()

    def move_triggered(self, checked):
        model, rows = get_selected_rows(self)
        dbw, ok = new_connection("write")
        if not ok:
            return
        if rows.__len__() > 0:
            qry = query("machines")
            if qry:
                machines = []
                while qry.next():
                    machines.append(qry.value(0).toString())
            else:
                return
            new, ok = QtGui.QInputDialog.getItem(None, "Pick a New Schedule", "Pick a New Schedule", machines, 0, 0)
            if ok:
                qry = query("get_machine", [new])
                if qry:
                    qry.first()
                    machine = qry.value(0).toString()
                else:
                    QtGui.QMessageBox.critical(None, "Machine Error", "Could not find '%s'" % new)
                    return
                QtGui.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
                tracking_numbers = []
                for row in rows:
                    tracking_numbers.append(model.data(model.index(row, 6)).toString())
                QtGui.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
                start_transaction("write")
                for tracking_number in tracking_numbers:
                    qry = query("move", [machine, tracking_number], dbw)
                    if not qry:
                        rollback_transaction("write")
                        text = "There was an error updating %s. Transaction cannot continue." % tracking_number
                        QtGui.QMessageBox.critical(None, "Update Error", text)
                        reset_cursor()
                        return
                commit_transaction("write")
                self.update_data()
            QtGui.QApplication.restoreOverrideCursor()

    def update_triggered(self, checked):
        model, rows = get_selected_rows(self)
        dbw, ok = new_connection("write")
        if not ok:
            return
        if rows.__len__() > 0:
            status_dialog = StatusDialog(self)
            new_status, finished = status_dialog.get_data()
            if new_status:
                tracking_numbers = []
                qty = False
                for row in rows:
                    tracking = model.data(model.index(row, 6)).toString()
                    quantity = int(model.data(model.index(row, 2)).toString())
                    tracking_numbers.append([tracking, quantity])
                if rows.__len__() == 1:
                    newqty, ok = QtGui.QInputDialog.getInt(None, "New Quantity", "New Quantity", tracking_numbers[0][1])
                    if ok:
                        qty = newqty
                QtGui.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
                start_transaction("write")
                for tracking_number in tracking_numbers:
                    qry = query("get_user_id", [dbw.login])
                    if qry:
                        qry.first()
                        user_id = qry.value(0).toString()
                    else:
                        QtGui.QMessageBox.critical(None, "User Not Found", "Could not find user %s" % dbw.login)
                        rollback_transaction("write")
                        reset_cursor()
                        return
                    if qty:
                        qry = query("update_qty", [qty, tracking_number[0]], dbw)
                        if not qry:
                            rollback_transaction("write")
                            reset_cursor()
                            return
                    else:
                        qty = tracking_number[1]
                    qry = query("status", [new_status, user_id, tracking_number[0], finished, qty], dbw)
                    if not qry:
                        rollback_transaction("write")
                        text = "There was an error updating %s. Transaction cannot continue." % tracking_number
                        QtGui.QMessageBox.critical(None, "Update Error", text)
                        reset_cursor()
                        return
                commit_transaction("write")
                self.update_data()
            QtGui.QApplication.restoreOverrideCursor()

    def hide_triggered(self, checked):
        model, rows = get_selected_rows(self)
        dbw, ok = new_connection("write")
        if not ok:
            return
        if rows.__len__() > 0:
            tracking_numbers = []
            for row in rows:
                tracking_numbers.append(model.data(model.index(row, 6)).toString())
            QtGui.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
            start_transaction("write")
            for tracking_number in tracking_numbers:
                qry = query("hide", [tracking_number], dbw)
                if not qry:
                    rollback_transaction("write")
                    text = "There was an error updating %s. Transaction cannot continue." % tracking_number
                    QtGui.QMessageBox.critical(None, "Update Error", text)
                    reset_cursor()
                    return
            text = "Are you sure you want to hide %d items?" % tracking_numbers.__len__()
            ok = QtGui.QMessageBox.question(None, "Are you sure?", text, 1, 2)
            if ok == 1:
                commit_transaction("write")
                self.update_data()
            else:
                rollback_transaction("write")
            QtGui.QApplication.restoreOverrideCursor()

    def missing_triggered(self, checked):
        model, rows = get_selected_rows(self)
        dbw, ok = new_connection("write")
        if not ok:
            return
        if rows.__len__() > 0:
            tracking_numbers = []
            for row in rows:
                tracking_numbers.append(model.data(model.index(row, 6)).toString())
            QtGui.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
            start_transaction("write")
            for tracking_number in tracking_numbers:
                qry = query("missing", [tracking_number], dbw)
                if not qry:
                    rollback_transaction("write")
                    text = "There was an error updating %s. Transaction cannot continue." % tracking_number
                    QtGui.QMessageBox.critical(None, "Update Error", text)
                    reset_cursor()
                    return
            text = "Are you sure you want to toggle missing on %d items?" % tracking_numbers.__len__()
            ok = QtGui.QMessageBox.question(None, "Are you sure?", text, 1, 2)
            if ok == 1:
                commit_transaction("write")
                self.update_data()
            else:
                rollback_transaction("write")
            reset_cursor()

    def priority_triggered(self, checked):
        model, rows = get_selected_rows(self)
        dbw, ok = new_connection("write")
        if not ok:
            return
        if rows.__len__() > 0:
            qry = query("machines")
            if qry:
                machines = []
                while qry.next():
                    machines.append(qry.value(0).toString())
            else:
                return
            new, ok = QtGui.QInputDialog.getInt(None, "Set New Priority", "Set New Priority", 350, 000, 499, 0)
            QtGui.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
            if ok:
                tracking_numbers = []
                for row in rows:
                    tracking_numbers.append(model.data(model.index(row, 6)).toString())
                start_transaction("write")
                for tracking_number in tracking_numbers:
                    qry = query("priority", [new, tracking_number], dbw)
                    if not qry:
                        rollback_transaction("write")
                        text = "There was an error updating %s. Transaction cannot continue." % tracking_number
                        QtGui.QMessageBox.critical(None, "Update Error", text)
                        reset_cursor()
                        return
                commit_transaction("write")
                self.update_data()
            QtGui.QApplication.restoreOverrideCursor()

    def print_triggered(self, checked):
        model, rows = get_selected_rows(self)
        if rows.__len__() > 0:
            QtGui.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
            tracking_numbers = []
            for row in rows:
                tracking_numbers.append(model.data(model.index(row, 6)).toString())

            part_report = report.WorkOrder()
            for tracking_number in tracking_numbers:
                qry = query("report_header_data", [tracking_number])
                if qry:
                    qry.first()
                    h_data = [qry.value(0).toString(), qry.value(1).toString(), qry.value(2).toString(), ]
                else:
                    reset_cursor()
                    return False
                qry = query("report_data", [tracking_number])
                if qry:
                    rows = qry.size()
                    row_data = []
                    while qry.next():
                        row_data.append(qry.record())
                else:
                    reset_cursor()
                    return False
                prints = 'P:/'
                part_report.add_page(h_data, rows, row_data, prints)

            part_report.build()
            pdf_file = "indWo.pdf"
            if sys.platform.startswith('linux'):
                os.system('xdg-open %s' % pdf_file)
            elif sys.platform.startswith('win32'):
                os.startfile('%s' % pdf_file)
            reset_cursor()

    def refresh_triggered(self, checked):
        self.update_data()

    def closeEvent(self, event):
        write_settings("size", self.size())
        write_settings("pos", self.pos())
        write_settings("state", self.windowState())