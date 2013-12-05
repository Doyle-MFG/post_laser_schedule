__author__ = 'rhanson'
import sys
from PyQt4 import QtSql, QtGui
import dbConnection

schedules = ('SELECT Machine_tbl.Machine_ID, Machine_tbl.Machine_Desc FROM `post_laser_schedule` '
             'join Machine_tbl on post_laser_schedule.machine = Machine_tbl.Machine_ID where missing=0 '
             'group by machine order by Machine_tbl.Machine_Desc')

parts = ('Select Priority, `Part #`, Qty, Description, Destination, Material, Tracking_num '
         'from post_laser_schedule where machine={0} and missing=0 Order by `Priority`, {1}')

missing_parts = ('Select Priority, `Part #`, Qty, Description, Destination, Material, Tracking_num '
                 'from post_laser_schedule where missing!=0')

machines = "Select Machine_Desc from Machine_tbl"

get_machine = "Select Machine_ID from Machine_tbl where Machine_Desc='{0}'"

move = "Update Work_Details_tbl set machine={0} where Tracking_num={1}"

get_status = "Select text, finished from status_values"

status = ("Insert into Status_tbl (Status_Description, User_ID, Tracking_num, Finished, StatQty) "
          "VALUES('{0}', {1}, {2}, '{3}', {4})")

update_qty = "Update Work_Details_tbl set Qty={0} where Tracking_num={1}"

hide = "Update Work_Details_tbl set `show`=0 where Tracking_num={0}"

missing = "Update Work_Details_tbl set missing=if(missing=0, -1, 0) where Tracking_num={0}"

priority = "Update Work_Details_tbl set priority={0} where Tracking_num={1}"

get_users = "Select Name from Users_tbl where active=1"

check_password = "Select if(password='{1}', True, False) from Users_tbl where Name='{0}'"

get_user_id = "Select User_Id from Users_tbl where Name='{0}'"

report_header_data = ("Select Job_num, date_Format(JDate, '%Y-%m-%d'), Machine_Desc from Work_Orders_tbl join "
                      "Machine_tbl on Work_Orders_tbl.Machine_ID = Machine_tbl.Machine_ID Where Job_ID = "
                      "(select Job_ID from Work_Details_tbl where Tracking_num = {0} limit 1)")

report_data = ("Select `Part Num`, `Qty`, `Desc`, `Mat`, `Process`, `Dest`, `Notes`, `Print`, "
               "`Hot`, `Order`, `Tracking` from workOrderData_qry Where `Tracking` = {0}")


def query(data, args=None, db='qt_sql_default_connection'):
    qry = QtSql.QSqlQuery(db)
    try:
        data = getattr(sys.modules[__name__], data)
    except AttributeError:
        QtGui.QMessageBox.critical(None, "Query Not Found", "A query matching %s was not found. Typo?" % data)
        return False
    if args:
        data = data.format(*args)
    if qry.exec_(data):
        return qry
    else:
        dbConnection.db_err(qry)
        return False