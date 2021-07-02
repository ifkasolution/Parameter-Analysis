import sys
import time
import subprocess
from PyQt5.QtWidgets import (QHeaderView, QTableView, QVBoxLayout, QHBoxLayout, QFormLayout, QTreeView, QApplication,
                             QSplashScreen,
                             QLabel, QFileDialog, QPushButton, QLineEdit, QSplitter, QTabWidget, QFrame)
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QPixmap, QIcon
from PyQt5 import QtCore
import timeit
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
import matplotlib
import logging

from Read_romax_output_to_database import read_rmx_output
from Read_Database import readDb
from Draw_network import draw_network
from Read_romax_xml_to_database import read_romax_xml
from Compare_DB import compare_db
from Read_Mlab_output_to_database import mlab_fun  # must after adams modul or error occures
from Evaluate_db import evaluation_db
import os



class MplCanvas(FigureCanvasQTAgg):
    def __init__(self, parent=None, width=8, height=6, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        super(MplCanvas, self).__init__(fig)


def numberconverter(value):
    try:
        if value:
            float(value)
            a = float(value)
        else:
            a = 'NONE'
    except ValueError:
        a = value
    return a


def start_server(prefix):
    open(prefix.Batch_Log_Name, 'w').close()
    comm = subprocess.Popen([prefix.Software_Name, '-startAsServer',
                             '5555', prefix.Batch_Log_Name])

    result = 'Starting Listening server on port'
    timeout = time.time() + 30  # 30 s from now
    lines = [' ']
    while not result in lines[-1]:
        print(lines[-1])
        with open(prefix.Batch_Log_Name, 'r', encoding='utf-8') as fp:
            lines = fp.read().splitlines()
        fp.close()
        if len(lines) == 0:
            lines = ['waiting...']
        time.sleep(2)
        if time.time() > timeout:
            stop_server(prefix)
            print('Restarting')
            start_server(prefix)
            break
    print(lines[-1])


def stop_server(prefix):
    stop_xml = prefix.rmx_shutdown
    comm = subprocess.Popen([prefix.rmx_server, '-i', stop_xml], shell=True, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT)
    print('RMX Server end')


class dataBase(QFrame):
    def __init__(self, prefix, db):
        super().__init__()
        self.prefix = prefix
        self.db = db
        self.model = QStandardItemModel()
        self.tree = QTreeView(self)
        self.tree.header().setDefaultSectionSize(180)
        self.tree.setModel(self.model)
        self.tree.clicked.connect(self.getValue)
        # Table view
        self.table = QTableView()
        data_table_ini = [' ', ' ']
        self.Table_Model = TableModel(data_table_ini)
        self.table.setModel(self.Table_Model)
        self.table.hide()
        splitter_geometry = QSplitter(QtCore.Qt.Horizontal)
        splitter_geometry.addWidget(self.tree)
        splitter_geometry.addWidget(self.table)

        # Database tree view testplan
        self.model_testplan = QStandardItemModel()
        self.tree_testplan = QTreeView(self)
        self.tree_testplan.header().setDefaultSectionSize(180)
        self.tree_testplan.setModel(self.model_testplan)
        self.tree_testplan.clicked.connect(self.getValue_simout)

        # Table view
        # # simulation results table

        self.table_testplan = QTableView()
        self.table_eva = QTableView()

        # # Tab view
        self.tab_simout = QTabWidget()
        self.tab_simout.addTab(self.table_eva, 'Evaluation Results')
        self.tab_simout.addTab(self.table_testplan, 'Simulation Results')
        self.tab_simout.setObjectName('subTab')
        self.tab_simout.tabBar().setObjectName('subTabBar')
        self.tab_simout.hide()

        # combine in spliter
        splitter_testplan = QSplitter(QtCore.Qt.Horizontal)
        splitter_testplan.addWidget(self.tree_testplan)
        splitter_testplan.addWidget(self.tab_simout)

        tab_db = QTabWidget()
        tab_db.addTab(splitter_geometry, 'Geometry')
        tab_db.addTab(splitter_testplan, 'Test Plan')

        tab_db.setTabPosition(QTabWidget.South)

        # Database
        self.setObjectName('subFrame')
        Database_frame_label = QLabel()
        Database_frame_label.setObjectName('subFrameLabel')
        Database_frame_label.setText('Data Base')
        Database_widgets_vbox = QVBoxLayout()
        Database_widgets_vbox.addWidget(Database_frame_label)
        Database_widgets_vbox.addWidget(tab_db)
        Database_widgets_vbox.setSpacing(0)
        Database_widgets_vbox.setContentsMargins(0, 0, 0, 0)
        self.setLayout(Database_widgets_vbox)

    def update_tables(self):
        self.model.clear()
        self.model.setHorizontalHeaderLabels(['Name', 'dbID'])
        self.addTreeItems()
        self.addTreeItems_testplan()
        self.tree.collapseAll()
        self.tree.hideColumn(1)

    def getValue(self, val):
        row = self.model.itemFromIndex(val).row()
        if self.model.itemFromIndex(val).parent():
            Attri_table = self.model.itemFromIndex(val).parent().child(row, 1).text()
            ID = self.model.itemFromIndex(val).parent().child(row, 2).text()
            if Attri_table == self.prefix.Attribute_List:
                col_name = ['PartAttribName', 'AttribType', 'UpdateDate', 'AttribValue', 'AttribUnit', 'AttribIdx']
                where = " WHERE PartID =" + ID
                allattrib = self.db.query_in_db(col_name, Attri_table, where)
                if len(allattrib) > 0:
                    table_new = []
                    for each in allattrib:
                        table_new.append([each['PartAttribName'],
                                          numberconverter(each['AttribValue']),
                                          each['AttribUnit'],
                                          each['AttribIdx'],
                                          each['UpdateDate']])
                    self.Table_Model = TableModel(table_new)
                    self.Table_Model.setHeaderData(0, QtCore.Qt.Horizontal, 'Name')
                    self.Table_Model.setHeaderData(1, QtCore.Qt.Horizontal, 'Value')
                    self.table.setModel(self.Table_Model)
                    self.table.show()
                else:
                    self.table.hide()
            else:
                col_name2 = ['AssemAttribName', 'AttribType', 'UpdateDate', 'AttribValue', 'AttribUnit', 'AttribIdx']
                where2 = " WHERE AssemID =" + ID
                allattrib2 = self.db.query_in_db(col_name2, Attri_table, where2)
                if len(allattrib2) > 0:
                    table_new = []
                    for each in allattrib2:
                        table_new.append([each['AssemAttribName'],
                                          numberconverter(each['AttribValue']),
                                          each['AttribUnit'],
                                          each['AttribIdx'],
                                          each['UpdateDate']])
                    self.Table_Model = TableModel(table_new)
                    self.Table_Model.setHeaderData(0, QtCore.Qt.Horizontal, 'Name')
                    self.Table_Model.setHeaderData(1, QtCore.Qt.Horizontal, 'Value')
                    self.table.setModel(self.Table_Model)
                    self.table.show()
                else:
                    self.table.hide()

    def getValue_simout(self, val):
        row = self.model_testplan.itemFromIndex(val).row()
        if self.model_testplan.itemFromIndex(val).parent():
            state_vale = []
            parent = self.model_testplan.itemFromIndex(val).parent()
            for row_all in range(parent.rowCount()):
                state = parent.child(row_all, 0).checkState()
                if state == QtCore.Qt.Unchecked:
                    state_vale.append(0)
                else:
                    state_vale.append(1)
            if sum(state_vale) == 0:
                parent.setCheckState(QtCore.Qt.Unchecked)
            elif sum(state_vale) == parent.rowCount():
                parent.setCheckState(QtCore.Qt.Checked)
            else:
                parent.setCheckState(QtCore.Qt.PartiallyChecked)
            Attri_table = parent.child(row, 2).text()
        else:
            Attri_table = self.model_testplan.item(row, 2).text()
            parent = self.model_testplan.item(row, 0)
            for row_all in range(parent.rowCount()):
                if parent.checkState() == QtCore.Qt.Unchecked:
                    parent.child(row_all, 0).setCheckState(QtCore.Qt.Unchecked)
                elif parent.checkState() == QtCore.Qt.Checked:
                    parent.child(row_all, 0).setCheckState(QtCore.Qt.Checked)
        if Attri_table == self.prefix.output:
            ID = self.model_testplan.itemFromIndex(val).parent().child(row, 1).text()
            col_name = ['ResultID', 'PartID', 'PartName', 'ResultName', 'ResultValue',
                        'ResultUnit', 'ResultType', 'ResultIndex', 'UpdateDATE']
            where = " WHERE TestCaseID =" + ID
            allattrib = self.db.query_in_db(col_name, Attri_table, where)
            if len(allattrib) > 0:
                table_new = []
                for each in allattrib:
                    table_new.append([each['ResultID'],
                                      each['PartID'],
                                      each['PartName'],
                                      each['ResultName'],
                                      numberconverter(each['ResultValue']),
                                      each['ResultUnit'],
                                      each['ResultIndex'],
                                      each['ResultType'],
                                      each['UpdateDATE']])
                self.table_testplan_cont = TableModel(table_new)
                self.table_testplan_cont.headerDataTulip = (
                    'ID', 'PartID', 'PartName', 'Name', 'Value', 'Unit', 'Idx', 'Type', 'Update Date')
                self.table_testplan.setModel(self.table_testplan_cont)
                self.tab_simout.show()
            col_name = ['EvaID', 'PartID', 'PartName', 'EvaluationName', 'EvaluationValue', 'EvaluationUnit']
            where = " WHERE TestCaseID =" + ID
            alleva = self.db.query_in_db(col_name, self.prefix.ifka_eva, where)
            if len(alleva) > 0:
                table_eva = []
                for each_eva in alleva:
                    table_eva.append([each_eva['EvaID'],
                                      each_eva['PartID'],
                                      each_eva['PartName'],
                                      each_eva['EvaluationName'],
                                      numberconverter(each_eva['EvaluationValue']),
                                      each_eva['EvaluationUnit']])
                self.table_eva_cont = TableModel(table_eva)
                self.table_eva_cont.headerDataTulip = (
                    'ID', 'PartID', 'PartName', 'Name', 'Value', 'Unit', 'Idx', 'Type', 'Update Date')
                self.table_eva.setModel(self.table_eva_cont)
        else:
            self.tab_simout.hide()

    def addTreeItems_testplan(self):
        self.model_testplan.clear()
        self.model_testplan.setHorizontalHeaderLabels(['Test Plan', 'ID', 'Type'])
        self.tree_testplan.hideColumn(2)
        query_testplan = "SELECT DISTINCT TestPlan, TestPlanID FROM " + self.prefix.Test_Plan
        all_testplan = self.db.query_in_db_advanced(query_testplan)
        for each_testplan in all_testplan:
            root = QStandardItem(each_testplan[0])
            self.model_testplan.appendRow([root, QStandardItem(str(each_testplan[1])), QStandardItem('NONE')])
            root.setCheckable(True)
            root.setAutoTristate(True)
            root.setCheckState(QtCore.Qt.Checked)
            col = ['TestCase', 'TestCaseID']
            Where = " WHERE TestPlan='" + each_testplan[0] + "'"
            all_testcase = self.db.query_in_db(col, self.prefix.Test_Plan, Where)
            for each_testcase in all_testcase:
                node = QStandardItem(each_testcase['TestCase'])
                id = QStandardItem(str(each_testcase['TestCaseID']))
                node.setCheckable(True)
                node.setAutoTristate(True)
                node.setCheckState(QtCore.Qt.Checked)
                root.appendRow([node, id, QStandardItem(self.prefix.output)])

    def addTreeItems(self):
        self.model.clear()
        self.model.setHorizontalHeaderLabels(['Name', 'Part', 'ID', 'Type', 'Update Date'])
        allcata = self.db.query_in_db_advanced("SELECT DISTINCT AssemCatalog FROM " + self.prefix.assembly)
        for each_cata in allcata:
            root = QStandardItem(each_cata[0])
            self.model.appendRow([root, QStandardItem('None')])
            where_clause = " WHERE AssemCatalog = '" + each_cata[0] + "'"
            col_name = ['AssemName', 'AssemID', 'AssemType', 'UpdateDate']
            all_assem = self.db.query_in_db(col_name, self.prefix.assembly, where_clause)
            for each_assem in all_assem:
                Node = QStandardItem(each_assem['AssemName'])
                root.appendRow([Node, QStandardItem(QStandardItem(self.prefix.Assem_Attribute_List)),
                                QStandardItem(str(each_assem['AssemID'])),
                                QStandardItem(each_assem['AssemType']),
                                QStandardItem(str(each_assem['UpdateDate']))])
                if each_cata[0] == 'Assembly':
                    col_name_part = ['PartName', 'PartID', 'PartType', 'UpdateDate']
                    where_clause_part = " WHERE AssemID = " + str(each_assem['AssemID'])
                    all_part = self.db.query_in_db(col_name_part, self.prefix.part_list, where_clause_part)
                    for each_part in all_part:
                        Node2 = QStandardItem(each_part['PartName'])
                        Node.appendRow(
                            [Node2, QStandardItem(self.prefix.Attribute_List), QStandardItem(str(each_part['PartID'])),
                             QStandardItem(each_part['PartType']),
                             QStandardItem(str(each_part['UpdateDate']))])

    def selectedTestCase(self):
        TestCaseid_read = []
        for row in range(self.model_testplan.rowCount()):
            each_pa = self.model_testplan.item(row, 0)
            if each_pa.hasChildren():
                for row_c in range(each_pa.rowCount()):
                    if each_pa.child(row_c, 0).checkState() == QtCore.Qt.Checked:
                        TestCaseid_read.append(each_pa.child(row_c, 1).text())
        if len(TestCaseid_read) == 0:
            TestCaseid = '*'
        else:
            TestCaseid = TestCaseid_read
        return TestCaseid


class visualizeFrame(QFrame):
    def __init__(self):
        super().__init__()
        matplotlib.use('Qt5Agg')
        logging.getLogger('matplotlib.font_manager').disabled = True
        # Initilized from file
        self.network_layout = draw_network()
        self.sc = MplCanvas(self, width=5, height=4, dpi=100)
        GearboxLayout_frame_label = QLabel()
        GearboxLayout_frame_label.setObjectName('subFrameLabel')
        GearboxLayout_frame_label.setText('Layout')
        GearboxLayout_frame_vbox = QVBoxLayout()
        GearboxLayout_frame_vbox.addWidget(GearboxLayout_frame_label)
        GearboxLayout_frame_vbox.addWidget(self.sc)
        GearboxLayout_frame_vbox.setSpacing(0)
        GearboxLayout_frame_vbox.setContentsMargins(0, 0, 0, 0)
        self.setLayout(GearboxLayout_frame_vbox)
        self.setObjectName('subFrame')

    def drawing(self, data):
        self.sc.axes.clear()
        self.network_layout.add_edge(data)
        self.network_layout.show(self.sc.axes)


class changedIOSplitter(QSplitter):
    def __init__(self):
        super().__init__(QtCore.Qt.Horizontal)

        changedInputFrame = QFrame()
        self.change_table_input = QTableView()
        change_table_input_label = QLabel()
        change_table_input_label.setObjectName('subFrameLabel')
        change_table_input_label.setText('Changed Model Parameters')
        change_table_input_vbox = QVBoxLayout()
        change_table_input_vbox.addWidget(change_table_input_label)
        change_table_input_vbox.addWidget(self.change_table_input)
        change_table_input_vbox.setSpacing(0)
        change_table_input_vbox.setContentsMargins(0, 0, 0, 0)
        changedInputFrame.setLayout(change_table_input_vbox)
        changedInputFrame.setObjectName('subFrame')

        changedOutputFrame = QFrame()
        self.change_table_output = QTableView()
        self.change_table_evaluation = QTableView()
        tab_compare = QTabWidget()
        tab_compare.setTabPosition(QTabWidget.South)
        tab_compare.addTab(self.change_table_evaluation, 'Changed Evalution')
        tab_compare.addTab(self.change_table_output, 'Detail Changes')
        change_table_output_label = QLabel()
        change_table_output_label.setObjectName('subFrameLabel')
        change_table_output_label.setText('Changed Simulation Results')
        change_table_output_vbox = QVBoxLayout()
        change_table_output_vbox.addWidget(change_table_output_label)
        change_table_output_vbox.addWidget(tab_compare)
        change_table_output_vbox.setSpacing(0)
        change_table_output_vbox.setContentsMargins(0, 0, 0, 0)
        changedOutputFrame.setObjectName('subFrame')
        changedOutputFrame.setLayout(change_table_output_vbox)

        self.addWidget(changedInputFrame)  # left changed input data
        self.addWidget(changedOutputFrame)  # right changed output data

    def update_tables(self, input_compare, output_compare, compare_eva):
        if len(output_compare) == 0:
            output_compare = [['None', 'Change', 'Found']]
        if len(input_compare) == 0:
            input_compare = [['None', 'Change', 'Found']]
        self.Change_Table_Model_input = TableModel(input_compare)
        self.Change_Table_Model_input.headerDataTulip = (
            'ID', 'Name', 'Feature', 'Unit', 'Value', 'Change to', 'Change Rate', '+/-', 'Catalogue')
        self.change_table_input.setModel(self.Change_Table_Model_input)
        self.Change_Table_Model_output = TableModel(output_compare)
        self.Change_Table_Model_output.headerDataTulip = (
            'ID', 'Name', 'Feature', 'Unit', 'Value', 'Change to', 'Change Rate', '+/-', 'Catalogue')
        sortable_model = QtCore.QSortFilterProxyModel()
        sortable_model.setSourceModel(self.Change_Table_Model_output)
        sortable_model.setFilterKeyColumn(2)
        self.change_table_output.setModel(sortable_model)

        compare_eva = []
        if len(compare_eva) == 0:
            compare_eva = [['None', 'Change', 'Found']]
        self.Change_Table_Model_evaluation = TableModel(compare_eva)
        self.Change_Table_Model_evaluation.headerDataTulip = (
            'ID', 'Name', 'Feature', 'Unit', 'Value', 'Change to', 'Change Rate', '+/-', 'Catalogue')
        self.change_table_evaluation.setModel(self.Change_Table_Model_evaluation)


class commandFrame(QFrame):
    def __init__(self, prefix):
        super().__init__()
        self.prefix = prefix
        self.lkRmx_btn = QPushButton('      Link Romax', self)
        self.lkRmx_btn.setIcon(QIcon(self.prefix.dir + '\Design\Design_Button_Link.png'))
        self.lkRmx_btn.setIconSize(QtCore.QSize(40, 40))
        self.udt_btn = QPushButton('     Update Database', self)
        self.udt_btn.setIcon(QIcon(self.prefix.dir + '\Design\Design_Button_Update.png'))
        self.udt_btn.setIconSize(QtCore.QSize(40, 40))
        self.ldt_btn = QPushButton('      Load Data', self)
        self.ldt_btn.setIcon(QIcon(self.prefix.dir + '\Design\Design_Button_Load.png'))
        self.ldt_btn.setIconSize(QtCore.QSize(40, 40))
        self.eva_btn = QPushButton('         Evaluate', self)
        self.eva_btn.setIcon(QIcon(self.prefix.dir + '\Design\Design_Button_Evaluation.png'))
        self.eva_btn.setIconSize(QtCore.QSize(40, 40))

        self.path_field = QLineEdit()
        self.path_field.setText(self.prefix.rmx_file)
        self.path_field.setObjectName('inputEdit')
        self.name_field = QLineEdit()
        self.name_field.setText(self.prefix.Gearbox_name)
        self.name_field.setObjectName('inputEdit')
        self.label_name = QLabel()
        self.label_name.setText('Gearbox Name')
        self.label_name.setObjectName('inputLabel')
        self.label_path = QLabel()
        self.label_path.setText('RMX File Path')
        self.label_path.setObjectName('inputLabel')

        vbox = QVBoxLayout()
        hbox = QHBoxLayout()
        hbox1 = QHBoxLayout()

        Form_input = QFormLayout()
        Form_input.addRow(self.label_name, self.name_field)
        Form_input.addRow(self.label_path, self.path_field)
        Form_input.setHorizontalSpacing(0)
        hbox.addStretch(1)
        hbox.addLayout(Form_input, 50)
        hbox.addWidget(self.lkRmx_btn)

        hbox1.addStretch(3)
        hbox1.addWidget(self.udt_btn)
        hbox1.addWidget(self.ldt_btn)
        hbox1.addWidget(self.eva_btn)
        vbox.addLayout(hbox)
        vbox.addLayout(hbox1)
        self.setLayout(vbox)
        self.setObjectName('subFrame')


class mainFunction(QFrame):
    def __init__(self, pref, db):
        super().__init__()
        self.prefix = pref
        self.db = db
        # ---------------Initialize----------
        self.read_rmx_input = read_romax_xml(self.prefix, self.db)
        self.read_rmx_output = read_rmx_output(self.prefix, self.db)

        self.compare_db = compare_db(self.prefix, self.db)
        self.mlab_fun = mlab_fun(self.prefix, self.db)
        self.evaluation_db = evaluation_db(self.prefix, self.db)
        self.data = readDb(self.prefix, self.db)
        # ---Splash Window----------------------------------------------------------------------
        print("----------start server rmx----------------------------------------------------------")
        # ---Launch Rmx-------------------------------------------------------------------
        start_server(self.prefix)
        print("----------start server rmx-done-------------------------------------------------")
        # --TAB 1---------------------------------------------------------------------------------------
        self.dbFrame = dataBase(self.prefix, self.db)
        self.vFrame = visualizeFrame()
        self.cioFrame = changedIOSplitter()
        self.ctrFrame = commandFrame(self.prefix)

        self.ctrFrame.lkRmx_btn.clicked.connect(lambda: self.openFileNameDialog(self.ctrFrame.path_field))
        self.ctrFrame.udt_btn.clicked.connect(self.upload_data)
        self.ctrFrame.ldt_btn.clicked.connect(self.download_data)
        self.ctrFrame.eva_btn.clicked.connect(self.run_evaluation)

        # splitter row 1
        splitter1 = QSplitter(QtCore.Qt.Horizontal)
        splitter1.addWidget(self.dbFrame)  # left database
        splitter1.addWidget(self.vFrame)  # right visualization of system
        splitter1.setSizes((80, 20))

        # Layout row 2
        splitter_all = QSplitter(QtCore.Qt.Vertical)
        splitter_all.addWidget(splitter1)
        splitter_all.addWidget(self.cioFrame)

        # all layout
        vbox_all = QVBoxLayout()
        vbox_all.addWidget(self.ctrFrame)
        vbox_all.addWidget(splitter_all)
        self.setLayout(vbox_all)
        self.setObjectName('tabFrame')

    def save_setting(self):
        self.prefix.conf_data["rmx"].update({"modelPath": self.ctrFrame.path_field.text(),
                                             "modelName": self.ctrFrame.name_field.text()})
        self.prefix.Gearbox_name = self.ctrFrame.name_field.text()
        self.prefix.rmx_file = self.ctrFrame.path_field.text()

    def run_evaluation(self):
        self.save_setting()
        self.dbFrame.update_tables()
        timestr = time.strftime("%Y%m%d-%H%M%S")
        filepath = self.prefix.simulation_outputfile + timestr + '.xml'

        print("----------Reading data from rmx-------------------------------------------------")
        TestCaseid = self.dbFrame.selectedTestCase()
        print('Selected ID ', TestCaseid)
        # RMX
        # 生成一个xml命令让romax跑完所有的Loadcase，并且将生成的运行结果以xml储存到filepath里
        self.read_rmx_output.load_rmx_xml_with_sim(filepath, TestCaseid)
        # 将filepath里生成的xml运行结果读入database，
        # 其中包括assembly; part_list; assemb_attribute_list; attribute_lis以及test_plan.
        # 涉及到的Romax的内部区域分别是root; connection; database以及DutyCycles(并没有调取他的主要attribute，比如ShadowComponents)
        self.read_rmx_input.initialize_db_with_xml(filepath, self.prefix.db_tabels_temp())

        self.read_rmx_output.read_rmx_to_db(filepath, self.prefix.db_tabels_temp(), TestCaseid)
        # Matlab
        print("----------Reading data from MATLAB-------------------------------------------------")
        self.mlab_fun.pv_Sim(1, TestCaseid)
        # Drawing
        self.data.read_all(self.prefix.db_tabels_temp(), TestCaseid)
        print("----------Draw Network-------------------------------------------------------------")
        self.vFrame.drawing(self.data)
        # Evaluation
        start = timeit.default_timer()
        print("----------Comparing results-------------------------------------------------------------")
        self.evaluation_db.run(self.prefix.db_tabels_temp(), TestCaseid)
        # Comparison
        input_compare, output_compare, compare_eva = self.compare_db.compare_all(self.vFrame.network_layout)
        stop = timeit.default_timer()
        print('compare: ', stop - start)
        self.cioFrame.update_tables(input_compare, output_compare, compare_eva)
        self.show()

    def download_data(self):
        print("----------Loading results-------------------------------------------------------------")
        self.save_setting()
        self.dbFrame.update_tables()
        data = readDb(self.prefix, self.db)
        data.read_all(self.prefix.db_tabels(), '*')
        self.vFrame.drawing(data)

    def openFileNameDialog(self, lineEdit):
        line_content = lineEdit.text()
        if os.path.exists(line_content):
            subprocess.Popen([self.prefix.conf_data['rmx']["software"], line_content])
        else:
            options = QFileDialog.Options()
            # options |= QFileDialog.DontUseNativeDialog
            fileName, _ = QFileDialog.getOpenFileName(self, "QFileDialog.getOpenFileName()", "",
                                                      "All Files (*);;Python Files (*.py)", options=options)
            if fileName:
                fileName = fileName.replace('/', '\\')
                lineEdit.setText(fileName)

    def upload_data(self):
        if self.ctrFrame.path_field.text():
            start = timeit.default_timer()
            print("----------Uploading results-------------------------------------------------------------")
            self.save_setting()
            print("----------Reading data from rmx----------------------------------------------------------")
            # RMX
            self.read_rmx_input.load_rmx_xml()
            self.read_rmx_input.initialize_db_with_xml(self.prefix.Outputfile, self.prefix.db_tabels())
            self.read_rmx_output.load_rmx_xml_with_sim(self.prefix.Outputfile, '*')
            self.read_rmx_output.read_rmx_to_db(self.prefix.Outputfile, self.prefix.db_tabels(), '*')
            # Read RMX data out of DB
            self.data.read_all(self.prefix.db_tabels(), '*')
            self.vFrame.drawing(self.data)
            # Matlab
            print("----------Reading data from MATLAB----------------------------------------------------------")
            self.mlab_fun.pv_Sim(0, '*')
            # Evaluation
            self.evaluation_db.run(self.prefix.db_tabels(), '*')
            self.download_data()
            self.show()

    def closeEvent(self, event):
        print("closing window")
        self.save_setting()
        stop_server(self.prefix)


class TableModel(QtCore.QAbstractTableModel):
    def __init__(self, data):
        super(TableModel, self).__init__()
        self._data = data
        self.headerDataTulip = ('Name', 'Value', 'Unit', 'Idx', 'Update Date')

    def headerData(self, column: int, orientation, role: QtCore.Qt.ItemDataRole):
        return (self.headerDataTulip[column]
                if role == QtCore.Qt.DisplayRole and orientation == QtCore.Qt.Horizontal
                else None)

    def data(self, index, role):
        if role == QtCore.Qt.DisplayRole:
            # See below for the nested-list data structure.
            # .row() indexes into the outer list,
            # .column() indexes into the sub-list
            return self._data[index.row()][index.column()]

    def rowCount(self, index):
        # The length of the outer list.
        return len(self._data)

    def columnCount(self, index):
        # The following takes the first sub-list, and returns
        # the length (only works if all rows are an equal length)
        return len(self._data[0])


if __name__ == '__main__':
    matplotlib.use('Qt5Agg')
    logging.getLogger('matplotlib.font_manager').disabled = True
    from My_DB_Connector import db_connecotor
    from All_prefix import prefix_info
    from config import IfkaConfig

    pref = prefix_info()
    db = db_connecotor()
    db.build_connector()
    cf = IfkaConfig(pref, db)
    # cf.import_rmx_map()
    # cf.read()
    app = QApplication(sys.argv)
    win = mainFunction(pref, db)
    win.show()
    sys.exit(app.exec_())
