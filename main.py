__title__ = "Post Laser Schedule"
import sys
import os
from PyQt4 import QtGui, QtCore

from query import query
from dbConnection import new_connection, start_transaction, commit_transaction, rollback_transaction
from functions import create_tab, create_missing_tab, get_selected_rows, StatusDialog, reset_cursor, \
    write_settings, read_settings, resize_table, set_statusbar
import report


class Main(QtGui.QMainWindow):
    tab_loaded = QtCore.pyqtSignal([str])

    def __init__(self, parent=None):
        QtGui.QMainWindow.__init__(self, parent)
        self.setWindowTitle(__title__)
        try:
            self.resize(read_settings("size").toSize())
            self.move(read_settings("pos").toPoint())
            self.setWindowState(QtCore.Qt.WindowStates(read_settings("state").toInt()[0]))
        except Exception as e:
            print e.message
            self.resize(1024, 768)
        self.statusBar().setVisible(True)
        self.tabs = QtGui.QTabWidget(self)
        self.title = QtGui.QLabel(__title__)
        self.title.setFont(QtGui.QFont("sans", 32, 63, True))
        self.scan = QtGui.QLineEdit()
        self.scan.setPlaceholderText("Tracking Number")
        self.scan.setMaximumWidth(250)
        self.central_layout = QtGui.QGridLayout()
        self.central_layout.addWidget(self.title, 0, 0)
        self.central_layout.addWidget(self.scan, 1, 0)
        self.central_layout.addWidget(self.tabs, 2, 0)
        self.central_widget = QtGui.QFrame()
        self.central_widget.setLayout(self.central_layout)
        self.setCentralWidget(self.central_widget)
        self.tabs.setFocus()
        self.move_action = QtGui.QAction("Move", self)
        self.update_action = QtGui.QAction("Update", self)
        self.hide_action = QtGui.QAction("Hide", self)
        self.priority_action = QtGui.QAction("Priority", self)
        self.refresh_action = QtGui.QAction("Refresh", self)
        self.print_action = QtGui.QAction("Print", self)
        self.missing_action = QtGui.QAction("Missing", self)
        self.add_action = QtGui.QAction("Add", self)

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
                widget.table.entered.connect(self.print_thumbnail)

    def load_actions(self):
        actions = [self.move_action, self.update_action, self.hide_action, self.priority_action,
                   self.refresh_action, self.print_action, self.missing_action, self.add_action]
        i = 1
        for action in actions:
            self.menuBar().addAction(action)
            action.setShortcut("F%d" % i)
            action.setToolTip("F%d" % i)
            action.triggered.connect(getattr(self, "%s_triggered" % action.text().toLower()))
            i += 1

    def resort_table(self, col, order):
        set_statusbar(self, "Sorting Table...")
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
        self.statusBar().clearMessage()

    def print_thumbnail(self, index):
        model = index.model()
        col = index.column()
        if col == 1:
            part = model.data(index).toString()
            self.sender().setToolTip('<img src="P:/%s.jpg" width="480" height="320"/>' % part)
        else:
            if self.sender().toolTip() != '':
                self.sender().setToolTip('')

    def update_data(self):
        set_statusbar(self, "Refreshing Data...")
        QtGui.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        self.tabs.clear()
        self.load_tabs()
        reset_cursor()
        self.statusBar().clearMessage()
        self.tabs.setFocus()

    def move_triggered(self, checked):
        model, rows = get_selected_rows(self)
        dbw, ok = new_connection("write")
        if not ok:
            return
        tracking_numbers = []
        if self.scan.text().length() == 10:
            tracking_numbers.append(self.scan.text())
            self.scan.setText("")
        elif rows.__len__() > 0:
            for row in rows:
                tracking_numbers.append(model.data(model.index(row, model.columnCount()-1)).toString())
        if tracking_numbers.__len__() > 0:
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
                set_statusbar(self, "Moving Selected Rows...")
                QtGui.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
                start_transaction("write")
                for tracking_number in tracking_numbers:
                    qry = query("move", [machine, tracking_number], dbw)
                    if not qry:
                        rollback_transaction("write")
                        text = "There was an error updating %s. Transaction cannot continue." % tracking_number
                        QtGui.QMessageBox.critical(None, "Update Error", text)
                        reset_cursor()
                        self.statusBar().clearMessage()
                        return
                commit_transaction("write")
                self.update_data()
            reset_cursor()
            set_statusbar(self, "Move Successful!", 2)

    def update_triggered(self, checked):
        model, rows = get_selected_rows(self)
        dbw, ok = new_connection("write")
        if not ok:
            return
        tracking_numbers = []
        qty = False
        if self.scan.text().length() == 10:
            tracking = self.scan.text()
            qry = query("get_qty", [tracking])
            if qry:
                qry.first()
                quantity = qry.value(0).toInt()[0]
            else:
                quantity = 0
            tracking_numbers.append([tracking, quantity])
            self.scan.setText("")
        elif rows.__len__() > 0:
            for row in rows:
                tracking = model.data(model.index(row, model.columnCount()-1)).toString()
                quantity = model.data(model.index(row, 2)).toInt()[0]
                tracking_numbers.append([tracking, quantity])
        if tracking_numbers.__len__() > 0:
            status_dialog = StatusDialog(self)
            new_status, finished = status_dialog.get_data()
            if finished:
                set_statusbar(self, "Updating Selected Rows")
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
                        self.statusBar().clearMessage()
                        return
                    if qty:
                        qry = query("update_qty", [qty, tracking_number[0]], dbw)
                        if not qry:
                            rollback_transaction("write")
                            reset_cursor()
                            self.statusBar().clearMessage()
                            return
                    else:
                        qty = tracking_number[1]
                    qry = query("status", [new_status, user_id, tracking_number[0], finished, qty], dbw)
                    if not qry:
                        rollback_transaction("write")
                        text = "There was an error updating %s. Transaction cannot continue." % tracking_number
                        QtGui.QMessageBox.critical(None, "Update Error", text)
                        reset_cursor()
                        self.statusBar().clearMessage()
                        return
                commit_transaction("write")
                self.update_data()
            reset_cursor()
            set_statusbar(self, "Update Successful!", 3)

    def hide_triggered(self, checked):
        model, rows = get_selected_rows(self)
        dbw, ok = new_connection("write")
        if not ok:
            return
        tracking_numbers = []
        if self.scan.text().length() == 10:
            tracking_numbers.append(self.scan.text())
            self.scan.setText("")
        elif rows.__len__() > 0:
            for row in rows:
                tracking_numbers.append(model.data(model.index(row, model.columnCount()-1)).toString())
        if tracking_numbers.__len__() > 0:
            set_statusbar(self, "Hiding Selected Rows")
            QtGui.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
            start_transaction("write")
            for tracking_number in tracking_numbers:
                qry = query("hide", [tracking_number], dbw)
                if not qry:
                    rollback_transaction("write")
                    text = "There was an error updating %s. Transaction cannot continue." % tracking_number
                    QtGui.QMessageBox.critical(None, "Update Error", text)
                    reset_cursor()
                    self.statusBar().clearMessage()
                    return
            text = "Are you sure you want to hide %d items?" % tracking_numbers.__len__()
            ok = QtGui.QMessageBox.question(None, "Are you sure?", text, 1, 2)
            if ok == 1:
                commit_transaction("write")
                self.update_data()
            else:
                rollback_transaction("write")
            reset_cursor()
            set_statusbar(self, "Hide Successful!", 3)

    def missing_triggered(self, checked):
        model, rows = get_selected_rows(self)
        dbw, ok = new_connection("write")
        if not ok:
            return
        tracking_numbers = []
        if self.scan.text().length() == 10:
            tracking_numbers.append(self.scan.text())
            self.scan.setText("")
        elif rows.__len__() > 0:
            for row in rows:
                tracking_numbers.append(model.data(model.index(row, model.columnCount()-1)).toString())
        if tracking_numbers.__len__() > 0:
            set_statusbar(self, "Marking Selected Rows as Missing")
            QtGui.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
            start_transaction("write")
            for tracking_number in tracking_numbers:
                qry = query("missing", [tracking_number], dbw)
                if not qry:
                    rollback_transaction("write")
                    text = "There was an error updating %s. Transaction cannot continue." % tracking_number
                    QtGui.QMessageBox.critical(None, "Update Error", text)
                    reset_cursor()
                    self.statusBar().clearMessage()
                    return
            text = "Are you sure you want to toggle missing on %d items?" % tracking_numbers.__len__()
            ok = QtGui.QMessageBox.question(None, "Are you sure?", text, 1, 2)
            if ok == 1:
                commit_transaction("write")
                self.update_data()
            else:
                rollback_transaction("write")
            reset_cursor()
            set_statusbar(self, "Successfully Marked!", 3)

    def priority_triggered(self, checked):
        model, rows = get_selected_rows(self)
        dbw, ok = new_connection("write")
        if not ok:
            return
        tracking_numbers = []
        if self.scan.text().length() == 10:
            tracking_numbers.append(self.scan.text())
            self.scan.setText("")
        elif rows.__len__() > 0:
            for row in rows:
                tracking_numbers.append(model.data(model.index(row, model.columnCount()-1)).toString())
        if tracking_numbers.__len__() > 0:
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
                set_statusbar(self, "Changing Priority on Selected Rows")
                start_transaction("write")
                for tracking_number in tracking_numbers:
                    qry = query("priority", [new, tracking_number], dbw)
                    if not qry:
                        rollback_transaction("write")
                        text = "There was an error updating %s. Transaction cannot continue." % tracking_number
                        QtGui.QMessageBox.critical(None, "Update Error", text)
                        reset_cursor()
                        self.statusBar().clearMessage()
                        return
                commit_transaction("write")
                self.update_data()
            reset_cursor()
            set_statusbar(self, "Priority Changed Successfully!", 3)

    def print_triggered(self, checked):
        model, rows = get_selected_rows(self)
        tracking_numbers = []
        if self.scan.text().length() == 10:
            tracking_numbers.append(self.scan.text())
            self.scan.setText("")
        elif rows.__len__() > 0:
            for row in rows:
                tracking_numbers.append(model.data(model.index(row, model.columnCount()-1)).toString())
        if tracking_numbers.__len__() > 0:
            QtGui.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
            set_statusbar(self, "Printing Report")
            part_report = report.WorkOrder()
            for tracking_number in tracking_numbers:
                qry = query("report_header_data", [tracking_number])
                if qry:
                    qry.first()
                    h_data = [qry.value(0).toString(), qry.value(1).toString(), qry.value(2).toString(), ]
                else:
                    reset_cursor()
                    self.statusBar().clearMessage()
                    return False
                qry = query("report_data", [tracking_number])
                if qry:
                    rows = qry.size()
                    row_data = []
                    while qry.next():
                        row_data.append(qry.record())
                else:
                    reset_cursor()
                    self.statusBar().clearMessage()
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
            self.statusBar().clearMessage()

    def add_triggered(self, checked):
        dbw, ok = new_connection("write")
        if not ok:
            return
        if self.scan.text().length() == 10:
            tracking_number = self.scan.text()
            self.scan.setText("")
            QtGui.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
            set_statusbar(self, "Added Part...")
            start_transaction("write")
            qry = query("show", [tracking_number], dbw)
            if qry:
                qry = query("get_finished", [tracking_number])
                if qry:
                    qry.first()
                    if qry.value(0).toString() != '0':
                        text = ("The part you are adding is marked as finished and won't be displayed on the list.\n"
                                "Do you want to add a new status?")
                        ok = QtGui.QMessageBox.question(None, "Status Shows Finished", text, 1, 2)
                        if ok == 1:
                            if commit_transaction("write"):
                                set_statusbar(self, "Part Added Successfully!", 3)
                                self.scan.setText(tracking_number)
                                self.update_action.trigger()
                            else:
                                rollback_transaction("write")
                                self.statusBar().clearMessage()
                                reset_cursor()
                                return
                        else:
                            rollback_transaction("write")
                            self.statusBar().clearMessage()
                            reset_cursor()
                            return
                    else:
                        if commit_transaction("write"):
                            self.update_data()
                            set_statusbar(self, "Part Added Successfully!", 3)
                            reset_cursor()
                        else:
                            rollback_transaction("write")
                            self.statusBar().clearMessage()
                            reset_cursor()
                            return
                else:
                    rollback_transaction("write")
                    self.statusBar().clearMessage()
                    reset_cursor()
                    return
            else:
                rollback_transaction("write")
                self.statusBar().clearMessage()
                reset_cursor()
                return

    def refresh_triggered(self, checked):
        self.update_data()

    def closeEvent(self, event):
        set_statusbar(self, "Saving State...")
        write_settings("size", self.size())
        write_settings("pos", self.pos())
        write_settings("state", self.windowState())
        set_statusbar(self, "Goodbye...")