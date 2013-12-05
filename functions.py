from PyQt4 import QtSql, QtGui, QtCore
from query import query

colors = (QtGui.QColor(215, 40, 40), QtGui.QColor(215, 130, 25), QtGui.QColor(205, 195, 25),
          QtGui.QColor(40, 190, 40), QtGui.QColor(60, 60, 255))


class colorized_QSqlQueryModel(QtSql.QSqlQueryModel):
    def __init__(self, parent=None, *args):
        QtSql.QSqlQueryModel.__init__(self, parent, *args)

    def data(self, index, role=QtCore.Qt.DisplayRole):
        data = QtSql.QSqlQueryModel.data(self, index, role)
        if index.column() == 0:
            if not index.isValid():
                return data
            elif role == QtCore.Qt.DisplayRole:
                global color
                color = colors[int(data.toString().rightJustified(3, QtCore.QChar('0'))[0])]
            elif role == QtCore.Qt.BackgroundRole:
                return QtGui.QBrush(color)
            elif role == QtCore.Qt.ForegroundRole:
                return QtGui.QBrush(QtCore.Qt.black)
        return data


def resize_table(table):
    table.resizeColumnsToContents()
    for i in range(table.max_widths.__len__()):
        if table.columnWidth(i) > table.max_widths[i]:
            table.setColumnWidth(i, table.max_widths[i])


def create_tab(machine, name):
        tab = QtGui.QFrame()
        tab.setWindowTitle(name)
        tab.setLayout(QtGui.QGridLayout())
        tab.table = QtGui.QTableView()
        tab.table.machine = machine
        qry = query("parts", [machine, "`Part #` Asc"])
        if qry:
            mod = colorized_QSqlQueryModel()
            mod.setQuery(qry)
            tab.table.setModel(mod)
            tab.table.max_widths = [50, 150, 50, 300, 125, 100, 100]
            resize_table(tab.table)
            tab.layout().addWidget(tab.table)
            tab.table.setSortingEnabled(True)
            header = tab.table.horizontalHeader()
            header.setSortIndicatorShown(True)
            header.setStretchLastSection(True)
            header.setSortIndicator(1, 0)
            tab.table.verticalHeader().setVisible(False)
        return tab


def create_missing_tab(name):
        tab = QtGui.QFrame()
        tab.setWindowTitle(name)
        tab.setLayout(QtGui.QGridLayout())
        tab.table = QtGui.QTableView()
        qry = query("missing_parts")
        if qry:
            mod = colorized_QSqlQueryModel()
            mod.setQuery(qry)
            tab.table.setModel(mod)
            tab.table.max_widths = [50, 150, 50, 300, 125, 100, 100]
            resize_table(tab.table)
            tab.layout().addWidget(tab.table)
        return tab


def get_selected_rows(self):
    index_list = self.tabs.currentWidget().table.selectedIndexes()
    rows = []
    if index_list.__len__() < 1:
        return False, rows
    else:
        for index in index_list:
            if index.row() not in rows:
                rows.append(index.row())
        return index_list[0].model(), rows


def get_users():
    qry = query("get_users")
    if qry:
        users = [""]
        while qry.next():
            users.append(qry.value(0).toString())
        if not users:
            QtGui.QMessageBox.critical(None, "Users Error", "User list could not be loaded...")
            return False
    else:
        return False
    return users


def reset_cursor():
    while QtGui.QApplication.overrideCursor():
        QtGui.QApplication.restoreOverrideCursor()


def write_settings(name, value):
    settings = QtCore.QSettings("Doyle Mfg", "Post_Laser_Schedule")
    settings.setDefaultFormat(1)
    settings.beginGroup('main')
    settings.setValue(name, value)
    settings.endGroup()


def read_settings(name):
    settings = QtCore.QSettings("Doyle Mfg", "Post_Laser_Schedule")
    settings.setDefaultFormat(1)
    settings.beginGroup('main')
    value = settings.value(name, None)
    return value


class StatusDialog(QtGui.QDialog):
    state = []

    def __init__(self, parent=None):
        QtGui.QDialog.__init__(self, parent)
        status = self.get_status()
        self.status_combo = QtGui.QComboBox()
        self.status_combo.setEditable(True)
        self.status_combo.addItems(status)
        self.finished_check = QtGui.QCheckBox()
        self.finished_check.setChecked(False)
        self.finished_check.setText("Finished")
        self.status_combo.currentIndexChanged.connect(self.get_state)
        accept_button = QtGui.QPushButton()
        accept_button.setText("Accept")
        accept_button.clicked.connect(self.accept)
        cancel_button = QtGui.QPushButton()
        cancel_button.setText("Cancel")
        cancel_button.clicked.connect(self.reject)

        layout = QtGui.QGridLayout()
        layout.addWidget(self.status_combo, 0, 0, 0, 1)
        layout.addWidget(self.finished_check, 0, 2)
        layout.addItem(QtGui.QSpacerItem(1, 0), 1, 0)
        layout.addWidget(accept_button, 1, 1)
        layout.addWidget(cancel_button, 1, 2)
        self.setLayout(layout)
    
    def get_data(self):
        ok = self.exec_()
        if ok:
            status = self.status_combo.currentText()
            finished = self.finished_check.isChecked()
            if finished:
                finished = "-1"
            else:
                finished = "0"
            return status, finished
        else:
            return False, False

    def get_status(self):
        qry = query("get_status")
        status = []
        if qry:
            while qry.next():
                status.append(qry.value(0).toString())
                self.state.append(qry.value(1).toString())
        return status

    def get_state(self, index):
        state = self.state[index]
        if state == "-1":
            self.finished_check.setChecked(True)
        else:
            self.finished_check.setChecked(False)