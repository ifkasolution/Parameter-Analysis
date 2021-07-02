import os
import subprocess
import time
from datetime import datetime

from lxml import etree, objectify

from SALib.sample import saltelli, fast_sampler
from SALib.analyze import sobol, fast

import numpy as np
import ctypes

import matplotlib.pyplot as plt
import matplotlib.colors as mat_colors
from matplotlib.ticker import MultipleLocator
import matplotlib.cm as cm
import matplotlib.colorbar as cbar
import matplotlib
from pandas import DataFrame

import json

import csv
from math import inf


# from multiprocessing.dummy import Pool as ThreadPool
# from SALib.test_functions import Ishigami
class Server:
    """
    Bearbeitung der Server von Romax

    Parameters
    ----------
    :param prefix_all : class vordefinierter Parameter z.B. Speicherort
    :param database : class von database inklusiv relevante operators z.B. build connector

    Supported operators:
    ---------
    start, start server
    stop_server, stop server
    """
    def __init__(self, prefix_all, database):
        # ---------------Initializing----------------------------------------------------
        self.prefix = prefix_all
        self.db = database

    def start(self):
        open(self.prefix.Batch_Log_Name, 'w').close()
        comm = subprocess.Popen([self.prefix.Software_Name, '-startAsServer',
                                 '5555', self.prefix.Batch_Log_Name])

        result = 'Starting Listening server on port'
        timeout = time.time() + 30  # 30 s from now
        lines = [' ']
        while result not in lines[-1]:
            print(lines[-1])
            with open(self.prefix.Batch_Log_Name, 'r', encoding='utf-8') as fp:
                lines = fp.read().splitlines()
            fp.close()
            if len(lines) == 0:
                lines = ['waiting...']
            time.sleep(2)
            if time.time() > timeout:
                print('Fail to open rmx')
                break

    def stop_server(self):
        stop_xml = self.prefix.rmx_shutdown
        comm = subprocess.Popen([self.prefix.rmx_server, '-i', stop_xml], shell=True, stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT)
        print('Server Stoped')


class InsertIntoDb:
    """
    Schnittstelle zwischen Mysql und Python zur Betätigung in Datenbank

    Parameters
    ----------
    :param pref : class vordefinierter Parameter z.B. Speicherort
    :param database : class von database inklusiv relevante operators z.B. build connector

    Supported operators:
    ---------
    create_table, aufbauen eine Tabelle
    delete_content, Löchen eine Tabelle
    get_result_to_insert, bekommen Inhalt/Daten irgendwo zum einfügen in die Tabelle
    insert, einfügen Daten in Datenbank
    """
    def __init__(self, pref, database):
        self.prefix = pref
        self.db = database
        self.col_list = None
        self.value_list_dict = None
        self.to_table = None

    def create_table(self):
        pass

    def delete_content(self):
        pass

    def get_result_to_insert(self, which_id):
        pass

    def insert(self):
        insert_value = []
        value_holder = []
        for idx in range(len(self.col_list)):
            value_holder.append('%s')

        for each in self.value_list_dict:
            insert_row = []
            for eachkey in self.col_list:
                insert_row.append(each[eachkey])
            insert_value.append(tuple(insert_row.copy()))
        separator = ', '
        query_insert = "INSERT INTO " + self.to_table + " (" + separator.join(self.col_list) + ") values (" \
                       + separator.join(value_holder) + ")"
        self.db.db_cursor.executemany(query_insert, insert_value)
        self.db.mydb.commit()


class RmxXml(InsertIntoDb):
    """
    ablegen die Simulationsergebnisse bezüglich Drivecycle aus XML-File in die Datenbank

    Parameters
    ----------
    :param pref : class vordefinierter Parameter z.B. Speicherort
    :param database : class von database inklusiv relevante operators z.B. build connector
    :param file_path: Pfad von ausgegebene XML-File nach Simulation
    :param which_id: idex von Testcase
    :param GetTestCase Funktion, die RomaxPath von Loadcase abrufen
    Supported operators:
    ---------
    create_table, aufbauen eine Tabelle über Simulationsoutput
    delete_content, Löschen dise Tabelle
    get_result_to_insert, abrufen Daten über Drivecycle aus XML-File
    """
    def __init__(self, pref, database, file_path, which_id, GetTestCase):
        self.root = read_xml_to_object(file_path)
        self.GetTestCase = GetTestCase
        InsertIntoDb.__init__(self, pref, database)
        self.Colm_to_insert = ["ResultID", "TestCaseID", "PartID", "PartName", "ResultName", "ResultRomaxName",
                               "ResultValue", "ResultUnit", "ResultType", "ResultIndex", "RomaxPath", "UpdateDATE"]
        self.result_to_insert = self.get_result_to_insert(which_id)
        self.to_table = self.prefix.db_tabels()['Output']

    def create_table(self):
        self.db.db_cursor.execute("CREATE TABLE IF NOT EXISTS " + self.to_table + " "
                                                                                  "(ResultID INT AUTO_INCREMENT PRIMARY KEY, "
                                                                                  "TestCaseID INT, "
                                                                                  "PartID INT, "
                                                                                  "PartName VARCHAR(255), "
                                                                                  "ResultName VARCHAR(255), "
                                                                                  "ResultRomaxName VARCHAR(255), "
                                                                                  "ResultValue VARCHAR(255), "
                                                                                  "ResultUnit VARCHAR(20), "
                                                                                  "ResultType VARCHAR(100), "
                                                                                  "ResultIndex INT, "
                                                                                  "RomaxPath VARCHAR(255),"
                                                                                  "UpdateDATE DATE)")

    def delete_content(self):
        self.db.db_cursor.execute("Delete FROM " + self.to_table)

    def get_result_to_insert(self, which_id):
        print('-------------writing into db --------')
        db_table = self.prefix.db_tabels()

        now = datetime.now()
        formatted_date = now.strftime('%Y-%m-%d')
        # ----to be read from excel------------
        self.create_table()
        self.delete_content()
        value_to_insert = {k: '' for k in self.Colm_to_insert}

        # # get names in simulation output list
        # NameList = ['ResultID', 'TestCaseID', 'AssemID', 'PartID', 'AssemName', 'PartName', 'PartType']
        table_test_plan = db_table['TestPlan']
        testcase = self.GetTestCase(self.db, which_id, table_test_plan).running()  # 获取用来读取dutycycles里内容的xpath
        partlist_name = ['PartID', 'PartName', 'PartType', 'RomaxID']
        Partlist = self.db.query_in_db(partlist_name, db_table['PartList'], '')
        self.result_id = 1
        result_to_insert = []
        for each_testcase in testcase:
            search_path = each_testcase['RomaxPath']
            testcase_node = self.root.xpath(search_path)[0]
            for each_part in Partlist:
                map_info = ['MapID', 'xPath', 'Attribute_Name', 'Romax_Name', 'Attribute_Type', 'Use_Prefix', 'Unit']
                map_filter = " WHERE Attribute_Type = '{}'".format(each_part['PartType'])
                map_result = self.db.query_in_db(map_info, self.prefix.romax_mapping_output_xml_sql, map_filter)
                if len(map_result) > 0:
                    submap_info = ['MapID', 'xPath', 'Attribute_Name', 'Romax_Name', 'Attribute_Type', 'Use_Prefix',
                                   'Unit']
                    map_filter = " WHERE subMapID = '{}'".format(map_result[0]['MapID'])
                    submap_result = self.db.query_in_db(submap_info, self.prefix.romax_mapping_output_xml_sql,
                                                        map_filter)
                    for each_attrib in submap_result:
                        xpath_attrib = map_result[0]['xPath'].format(each_part['RomaxID']) + each_attrib['xPath']
                        xpath_result_all = testcase_node.xpath('.' + xpath_attrib,
                                                               namespaces={'prefix': each_attrib['Use_Prefix'], })
                        idx_vector = 0
                        for xpath_result in xpath_result_all:
                            value_to_insert['ResultID'] = self.result_id
                            value_to_insert['TestCaseID'] = each_testcase['TestCaseID']
                            value_to_insert['PartID'] = each_part['PartID']
                            value_to_insert['PartName'] = each_part['PartName']
                            value_to_insert['ResultName'] = each_attrib['Attribute_Name']
                            value_to_insert['ResultRomaxName'] = each_attrib['Romax_Name']
                            value_to_insert['RomaxPath'] = ''
                            if '@' in xpath_attrib[-10:]:
                                db_value = str(xpath_result)
                            else:
                                db_value = xpath_result[0].text
                            value_to_insert['ResultValue'] = db_value
                            value_to_insert['ResultUnit'] = each_attrib['Unit']
                            value_to_insert['ResultType'] = each_attrib['Attribute_Type']
                            value_to_insert['ResultIndex'] = idx_vector
                            value_to_insert['UpdateDATE'] = formatted_date
                            result_to_insert.append(value_to_insert.copy())
                            idx_vector = idx_vector + 1
                            self.result_id = self.result_id + 1
        return result_to_insert


class ShaftSafty(RmxXml):
    def __init__(self, pref, database, file_path, which_id):
        RmxXml.__init__(self, pref, database, file_path, which_id, GetTestCase)

    def get_result_to_insert(self, which_id):
        db_table = self.prefix.db_tabels()
        self.create_table()
        table_test_plan = db_table['TestPlan']
        test_case = self.GetTestCase(self.db, which_id, table_test_plan).running()  # 获取用来读取dutycycles里内容的xpath
        test_cass_ids = [str(case['TestCaseID']) for case in test_case]
        result_to_insert = []
        col_name = ['PartID', 'PartName', 'PartType']
        where_type = " WHERE PartType = 'Shaft'"
        all_results = self.db.query_in_db(col_name, db_table['PartList'], where_type)
        now = datetime.now()
        formatted_date = now.strftime('%Y-%m-%d')
        print('Calculating the safety factor of shafts')
        for each in all_results:
            # query Material
            where_type = f" WHERE PartID = {str(each['PartID'])} AND PartAttribName= 'Material'"
            query_material_name = self.db.query_in_db(['PartAttribName', 'AttribValue'], db_table['PartAttrib'],
                                                      where_type)
            material_col = ['AssemAttribName', 'AttribValue']
            material_where = f" WHERE AssemAttribName in ('TorsionAllowableStressValue','BendingAllowableStressValue', 'AxialAllowableStressValue')" \
                             f" And AssemID = (SELECT AssemID From {db_table['AssemList']} " \
                             f" WHERE  AssemName = '{query_material_name[0]['AttribValue']}') "
            material = self.db.query_in_db(material_col, db_table['AssemAttrib'], material_where)
            material_info = {}
            for each_material in material:
                material_info[each_material['AssemAttribName']] = each_material['AttribValue']
            bend_allow = float(material_info['BendingAllowableStressValue'])
            tension_allowed = float(material_info['AxialAllowableStressValue'])
            torsion_allowed = float(material_info['TorsionAllowableStressValue'])
            # query Shaft Sim Result
            col = ['TestCaseID', 'ResultName', 'ResultIndex', 'ResultValue']
            where = f" WHERE PartID = {str(each['PartID'])} AND TestCaseID in ({','.join(test_cass_ids)}) AND ResultName " \
                    "in ('BendingLeft', 'BendingRight', 'TensionLeft','TensionRight', 'TorsionLeft','TorsionRight' )"
            result = self.db.query_in_db(col, db_table['Output'], where)
            for each_test in test_cass_ids:
                bend = []
                tension = []
                torsion = []
                for each_result in result:
                    if each_result['TestCaseID'] == int(each_test):
                        RN = each_result['ResultName']
                        if RN == 'BendingLeft' or RN == 'BendingRight':
                            bend.append(float(each_result['ResultValue']))
                        elif RN == 'TensionLeft' or RN == 'TensionRight':
                            tension.append(float(each_result['ResultValue']))
                        elif RN == 'TorsionLeft' or RN == 'TorsionRight':
                            torsion.append(float(each_result['ResultValue']))
                bend_max = abs(max(bend, key=abs))
                tension_max = abs(max(tension, key=abs))
                torsion_max = abs(max(torsion, key=abs))
                try:
                    s = ((bend_max / bend_allow + tension_max / tension_allowed) ** 2 + (
                            torsion_max / torsion_allowed) ** 2) ** -0.5
                except:
                    print('ok')
                    s = None
                # print('PartID', each['PartID'], 'S', S)
                value_to_insert = {}
                value_to_insert['ResultID'] = self.result_id
                value_to_insert['TestCaseID'] = each_test
                value_to_insert['PartID'] = each['PartID']
                value_to_insert['PartName'] = each['PartName']
                value_to_insert['ResultName'] = 'ShaftSafetyFactor'
                value_to_insert['ResultRomaxName'] = ''
                value_to_insert['RomaxPath'] = ''
                value_to_insert['ResultValue'] = s
                value_to_insert['ResultUnit'] = '-'
                value_to_insert['ResultType'] = 'ShaftLifeTime'
                value_to_insert['ResultIndex'] = 0
                value_to_insert['UpdateDATE'] = formatted_date
                result_to_insert.append(value_to_insert.copy())
                self.result_id += 1
        return result_to_insert


class GetOutputFromXml:
    """
    erwerben die bestimmte Daten über Output direkt aus XML-File

    Parameters
    ----------
    :param db : class von database inklusiv relevante operators z.B. build connector

    Supported operators:
    ---------
    get_field, allgemiene Funktion, die bestimmte Filed abrufen kann
    output_at_changing, return bestimmte Daten über Output nach Änderung der Parameter
    """
    def __init__(self, db):
        self.db = db
        self.col_list = ["xPath_attribute", "RomaxID", "xPath_shadowcomponent", "xPath_loadcase", "Use_Prefix"]

    def get_field(self, output_list):
        # raw_to_find = [str(tuple(output_list[i].values())) for i in range(len(output_list))]
        # col_list_sql = ",".join(col_list)
        # query_script = f"""select {col_list_sql} from getriebe.output_path_list where (TestCaseID,PartID,Name) in ({",".join(raw_to_find)});"""
        col_list_sql = ",".join(self.col_list)
        raw_to_find = [str(output_list[i]['AllID']) for i in range(len(output_list))]
        query_script = f"select {col_list_sql} from getriebe.output_path_list where AllID in ({','.join(raw_to_find)}) order by field(AllID,{','.join(raw_to_find)}) "
        return self.db.execute_script_in_db(query_script, self.col_list)

    def output_at_changing(self, output_list, filepath):
        root = read_xml_to_object(filepath)
        result_all = []
        for each in self.get_field(output_list):
            x = root.xpath(
                each['xPath_loadcase'] + each['xPath_shadowcomponent'].format(each['RomaxID']) + each[
                    'xPath_attribute'], namespaces={'prefix': each['Use_Prefix'], })
            result_all.append(x[0])
        return result_all


class OutputReporting:
    """
    generieren Bug-Report falls Fehler bei Batchrunning auftritt

    Parameters
    ----------
    :param Batch_Output_path : Pfad von Output XML-FIle
    """
    def __init__(self, Batch_Output_path):
        self.path = Batch_Output_path

    def get(self):
        with open(self.path, "r", encoding="utf-8") as report_xml:
            report_to_read = report_xml.read()
        report_str = str(report_to_read.encode('utf-8')).split('Exceptions>')
        message = []
        if len(report_str) != 1:
            root_report = objectify.fromstring(f"<Exceptions>{report_str[1]}Exceptions>")
            for each in root_report.iter('MessageText'):
                message.append(each)
        return message


class BatchRunning:
    """
    Durchführung Batchrunning

    Parameters
    ----------
    :param prefix : class vordefinierter Parameter z.B. Speicherort
    :param database : class der database inklusiv relevante operators z.B. build connector
    :param batch_input: batch-objekt z.B. Varibale, Action, Result und deren ID in Datenbank
    :param batch_input_path: Pfad von leere batchfile
    :param batch_output_path: Pfad von ausgegebene batchfile
    :param batch_file: hinzufügende batchfile

    Supported operators:
    ---------
    get_field, allgemiene Funktion, die bestimmte Filed aus Datenbank abrufen kann
    get_node_info, erwerben die Batchname aus Spaltwert in tabelle z.B. variablelist,actionlist oder resultlist
    appending, hinfügen die neue batchinhalt nach vorhandene batchfile (In diesem fall ist batch_file nicht None)
    running, lassen batchrunning laufen (einmal refresch, einmal formale Running)
    """
    def __init__(self, prefix, database, batch_input=None, batch_input_path=None,
                 batch_output_path=None, batch_file=None):
        self.prefix = prefix
        self.db = database
        if batch_file is None:
            self.batch_file = etree.Element("ParametricModification", file=self.prefix.rmx_file)
        else:
            self.batch_file = batch_file
        self.node_info = {"node_name": [],
                          "node_attrib": [],
                          "child_node_name": [],
                          "child_node_attrib": [],
                          "argument_of_child_node": []}
        self.col_list = []
        self.batch_table = []
        self.batch_input = batch_input
        self.batch_input_path = batch_input_path
        self.batch_output_path = batch_output_path

    def get_field(self):
        col_list_sql = ",".join(self.col_list)
        raw_to_find = [str(self.batch_input[i]['AllID']) for i in range(len(self.batch_input))]
        query_script = f"select {col_list_sql} from {self.batch_table} where AllID in ({','.join(raw_to_find)}) order by field(AllID,{','.join(raw_to_find)}) "
        return self.db.execute_script_in_db(query_script, self.col_list)

    def get_node_info(self):
        self.get_field()

    def appending(self):
        self.get_node_info()

        for idx in range(len(self.node_info["node_name"])):
            node = etree.Element(self.node_info["node_name"][idx], self.node_info["node_attrib"][idx])
            child_node = etree.Element(self.node_info["child_node_name"][idx], self.node_info["child_node_attrib"][idx])
            if self.node_info["argument_of_child_node"][idx]:
                for each_argument in self.node_info["argument_of_child_node"][idx]:
                    child_node.append(etree.Element('Argument', value=each_argument))
            node.append(child_node)
            self.batch_file.append(node)
        return self.batch_file

    def running(self):
        with open(self.batch_input_path,
                  "wb") as f:  # write batch file for variable changing and outputting into XML
            f.write(etree.tostring(self.batch_file, pretty_print=True))
        self.prefix.generating_refresh()
        refresh_xml = self.prefix.refresh_xml
        comm = subprocess.Popen([self.prefix.rmx_server, '-i',
                                 refresh_xml, '-o', self.prefix.refresh_output])
        while not os.path.exists(self.batch_input_path):
            time.sleep(1)
        comm = subprocess.run([self.prefix.rmx_server, '-i',
                               self.batch_input_path, '-o',
                               self.batch_output_path])


class ChangeVariable(BatchRunning):
    """
    Durchführung Batchrunning in Bereich von Änderung der Variable
    """
    def __init__(self, prefix, database, batch_input=None, batch_input_path=None,
                 batch_output_path=None, new_batch_file=None):
        BatchRunning.__init__(self, prefix, database, batch_input, batch_input_path,
                              batch_output_path, new_batch_file)
        self.col_list = ["AllID", "Name", "MapID", "VariableType", "NameInXml", "TypeInXml", "UnitInXml", "AssemName1",
                         "AssemName2", "PartName", "TestPlan", "TestCase", "AttribIdx"]
        self.batch_table = "getriebe.variable_list"

    def get_node_info(self):
        batch_type = "Variable"
        value_list = [str(self.batch_input[i]['Attribvalue']) for i in range(len(self.batch_input))]
        for each_info, each_value in zip(self.get_field(), value_list):
            name_in_xml = each_info['NameInXml'].format(GearboxName=self.prefix.Gearbox_name,
                                                        AssemName1=each_info['AssemName1'],
                                                        AssemName2=each_info['AssemName2'],
                                                        PartName=each_info['PartName'], TestPlan=each_info['TestPlan'],
                                                        TestCase=each_info['TestCase'],
                                                        AttribIdx=each_info['AttribIdx'])
            part_attrib = {"name": each_info['Name'],
                           "nameUser": str(int(each_info['AllID'])),
                           "type": each_info['TypeInXml'],
                           "unit": each_info['UnitInXml'],
                           "value": each_value}
            self.node_info["node_name"].append(each_info['VariableType'])
            self.node_info["node_attrib"].append({"name": name_in_xml})
            self.node_info["child_node_name"].append(batch_type)
            self.node_info["child_node_attrib"].append(part_attrib)
            self.node_info["argument_of_child_node"].append([])


class GetResult(BatchRunning):
    """
    Durchführung Batchrunning in Bereich von erwerben der Ergebnisse
    """
    def __init__(self, prefix, database, batch_input=None, batch_input_path=None,
                 batch_output_path=None, new_batch_file=None):
        BatchRunning.__init__(self, prefix, database, batch_input, batch_input_path,
                              batch_output_path, new_batch_file)
        self.col_list = ["AllID", "Name", "MapID", "ResultType", "NameInXml", "UnitInXml", "AssemName1", "AssemName2",
                         "PartName", "TestPlan", "TestCase"]
        self.batch_table = "getriebe.result_list"

    def get_node_info(self):
        batch_type = "Result"
        for each_info in self.get_field():
            name_in_xml = each_info['NameInXml'].format(GearboxName=self.prefix.Gearbox_name,
                                                        AssemName1=each_info['AssemName1'],
                                                        AssemName2=each_info['AssemName2'],
                                                        PartName=each_info['PartName'],
                                                        TestPlan=each_info['TestPlan'],
                                                        TestCase=each_info['TestCase'])
            part_attrib = {"name": each_info['Name'],
                           "nameUser": str(int(each_info['AllID'])),
                           "unit": each_info['UnitInXml'],
                           "value": ""}
            self.node_info["node_name"].append(each_info['ResultType'])
            self.node_info["node_attrib"].append({"name": name_in_xml})
            self.node_info["child_node_name"].append(batch_type)
            self.node_info["child_node_attrib"].append(part_attrib)
            self.node_info["argument_of_child_node"].append([])


class ExecuteAction(BatchRunning):
    """
    Durchführung Batchrunning in Bereich von durchführung der Action
    """
    def __init__(self, prefix, database, batch_input=None, batch_input_path=None,
                 batch_output_path=None, new_batch_file=None):
        BatchRunning.__init__(self, prefix, database, batch_input, batch_input_path,
                              batch_output_path, new_batch_file)
        self.col_list = ["Name", "ActionType", "NameInXml", "ArgumentValue1", "ArgumentValue2", "ArgumentValue3",
                         "ArgumentValue4", "AssemName1", "AssemName2",
                         "PartName", "TestPlan", "TestCase"]
        self.batch_table = "getriebe.action_list"

    def get_node_info(self):
        batch_type = "Action"
        for each_info, each_id in zip(self.get_field(), self.batch_input):
            name_in_xml = each_info['NameInXml'].format(GearboxName=self.prefix.Gearbox_name,
                                                        AssemName1=each_info['AssemName1'],
                                                        AssemName2=each_info['AssemName2'],
                                                        PartName=each_info['PartName'],
                                                        TestPlan=each_info['TestPlan'],
                                                        TestCase=each_info['TestCase'])
            part_attrib = {"name": each_info['Name'],
                           "priority": str(each_id['priority'])}
            self.node_info["node_name"].append(each_info['ActionType'])
            self.node_info["node_attrib"].append({"name": name_in_xml})
            self.node_info["child_node_name"].append(batch_type)
            self.node_info["child_node_attrib"].append(part_attrib)
            argument = []
            for idx in range(4):
                if each_info[f"ArgumentValue{idx + 1}"] is not '':
                    argument.append(each_info[f"ArgumentValue{idx + 1}"].format(path=each_id["path"]))
            self.node_info["argument_of_child_node"].append(argument)


class ExportRmxXml(ExecuteAction):
    """
    Durchführung Batchrunning für Initialisierung der Datenbank wenn keine Parameter geändert wird
    """
    # def __init__(self, prefix, database):
    #     ExecuteAction.__init__(self, prefix, database)

    def get_node_info(self):
        self.node_info["node_name"].append('Part')
        self.node_info["node_attrib"].append({"name": '.\\Getriebe'})
        self.node_info["child_node_name"].append('Action')
        self.node_info["child_node_attrib"].append({'name': 'exportXMLTo:', 'priority': '1'})
        self.node_info["argument_of_child_node"].append([self.batch_input])

    def appending_and_running(self):
        self.appending()
        self.running()


class ResultMapping(GetResult):
    """
    Bei Erstellung von Batchfile wurden die Parameter aller Node --NameUser eingetragen, die AllID in der datenbank entsprechen.
    Bei Ablesen die Ergebnisse in XML-Outputfile müssen die Info über aller Node (Assembly1, Assembly2...) durch NameUser nähmlich AllID
    aus Datenbank abrufen werden. (NameUser in Batchfile-->AllID in Datenbank-->Info in Datenbank)

    Parameters
    ----------
    :param prefix : class vordefinierter Parameter z.B. Speicherort
    :param database : class der database inklusiv relevante operators z.B. build connector
    :param batch_input: batch-objekt z.B. Varibale, Action, Result und deren ID in Datenbank
    :param batch_input_path: Pfad von leere batchfile
    :param batch_output_path: Pfad von ausgegebene batchfile
    :param batch_file: hinzufügende batchfile

    Supported operators:
    ---------

    get_node_info, erwerben die Info aus Spaltwert in tabelle z.B. variablelist,actionlist oder resultlist
    mapping, durchführung Abbildungsprozess
    """
    def __init__(self, prefix, database, batch_input=None, batch_input_path=None,
                 batch_output_path=None, new_batch_file=None):
        GetResult.__init__(self, prefix, database, batch_input, batch_input_path,
                           batch_output_path, new_batch_file)
        self.mapped_name = {"Name": [], "AssemName1": [], "AssemName2": [], "PartName": [], "TestCase": [],
                            "AttribIdx": []}

    def mapping(self):
        self.get_node_info()
        return self.mapped_name

    def get_node_info(self):
        for each_info in self.get_field():
            self.mapped_name["Name"].append(each_info['Name'])
            try:
                self.mapped_name["AssemName1"].append(each_info['AssemName1'])
                self.mapped_name["AssemName2"].append(each_info['AssemName2'])
            except KeyError:
                self.mapped_name["AssemName1"].append([])
                self.mapped_name["AssemName2"].append([])
            self.mapped_name["PartName"].append(each_info['PartName'])
            self.mapped_name["TestCase"].append(each_info['TestCase'])
            try:
                self.mapped_name["AttribIdx"].append(each_info['AttribIdx'])
            except KeyError:
                self.mapped_name["AttribIdx"].append([])


class OutputMapping(ResultMapping):
    """
    Bei Erstellung von Batchfile wurden die Parameter aller Node --NameUser eingetragen, die AllID in der datenbank entsprechen.
    Bei Ablesen die Ergebnisse in XML-Outputfile müssen die Info über aller Node hier Output (Assembly1, Assembly2...) durch NameUser nähmlich AllID
    aus Datenbank abrufen werden. (NameUser in Batchfile-->AllID in Datenbank-->Info in Datenbank)
    """
    def __init__(self, prefix, database, batch_input=None, batch_input_path=None,
                 batch_output_path=None, new_batch_file=None):
        ResultMapping.__init__(self, prefix, database, batch_input, batch_input_path,
                               batch_output_path, new_batch_file)
        self.col_list = ["TestCase", "PartName", "Name"]
        self.batch_table = "getriebe.output_path_list"


class VariableMapping(ResultMapping):
    """
    Bei Erstellung von Batchfile wurden die Parameter aller Node --NameUser eingetragen, die AllID in der datenbank entsprechen.
    Bei Ablesen die Ergebnisse in XML-Outputfile müssen die Info über aller Node hier Varibale (Assembly1, Assembly2...) durch NameUser nähmlich AllID
    aus Datenbank abrufen werden. (NameUser in Batchfile-->AllID in Datenbank-->Info in Datenbank)
    """
    def __init__(self, prefix, database, batch_input=None, batch_input_path=None,
                 batch_output_path=None, new_batch_file=None):
        ResultMapping.__init__(self, prefix, database, batch_input, batch_input_path,
                               batch_output_path, new_batch_file)
        self.col_list = ["Name", "MapID", "VariableType", "NameInXml", "TypeInXml", "UnitInXml", "AssemName1",
                         "AssemName2", "PartName", "TestPlan", "TestCase", "AttribIdx"]
        self.batch_table = "getriebe.variable_list"


class ActionMapping(ResultMapping):
    """
    Bei Erstellung von Batchfile wurden die Parameter aller Node --NameUser eingetragen, die AllID in der datenbank entsprechen.
    Bei Ablesen die Ergebnisse in XML-Outputfile müssen die Info über aller Node hier Action (Assembly1, Assembly2...) durch NameUser nähmlich AllID
    aus Datenbank abrufen werden. (NameUser in Batchfile-->AllID in Datenbank-->Info in Datenbank)
    """
    def __init__(self, prefix, database, batch_input=None, batch_input_path=None,
                 batch_output_path=None, new_batch_file=None):
        ResultMapping.__init__(self, prefix, database, batch_input, batch_input_path,
                               batch_output_path, new_batch_file)
        self.col_list = ["Name", "ActionType", "NameInXml", "ArgumentValue1", "ArgumentValue2", "ArgumentValue3",
                         "ArgumentValue4", "AssemName1", "AssemName2",
                         "PartName", "TestPlan", "TestCase"]
        self.batch_table = "getriebe.action_list"


class CreateTableThroughOthers:
    """
    manche Tabelle können aus weitere vorhandene Tabelle generieren, um an die vorhandene Getriebestruktur anzupassen.
    """
    def __init__(self, database, pref):
        self.db = database
        self.pref = pref
        self.query_script_drop = None
        self.query_script_creating = None

    def creating(self):
        self.db.db_cursor.execute(self.query_script_drop, multi=False)
        self.db.db_cursor.execute(self.query_script_creating, multi=False)


class VariableList(CreateTableThroughOthers):
    """
    manche Tabelle können aus weitere vorhandene Tabelle generieren, um an die vorhandene Getriebestruktur anzupassen.
    alle Daten für Erstellung der Batchfile über Variable werden in diese Tabelle abgelegt
    """
    def __init__(self, database, pref):
        CreateTableThroughOthers.__init__(self, database, pref)
        self.query_script_drop = f"drop table if exists {self.pref.database}.{self.pref.variable_listname}"
        self.query_script_creating = f"""create table if not exists {self.pref.database}.{self.pref.variable_listname} as
                        (with variable_list_dummy9 as
                        (with variable_list_dummy8 as
                        (with variable_list_dummy6 as
                        (with variable_list_dummy7 as
                        (with
                        mapping_assembly_connection as
                        (with variable_list_dummy3 as
                        (with variable_list_dummy4 as
                        (select AssemName,AssemType,AssemAttribName,AttribValue
                        from getriebe.assembly inner join getriebe.assem_attribute_list
                        using (AssemID) where AssemType='DetailedHelicalGearMesh' and AssemAttribName='Part1ID' )
                        select AssemName as AssemName2,AssemID
                        from variable_list_dummy4 inner join getriebe.part_list on variable_list_dummy4.AttribValue=getriebe.part_list.PartID)
                        select AssemName2,AssemName as AssemName1 from variable_list_dummy3 inner join getriebe.assembly using (AssemID)),
                        main_table as
                        (with variable_list_dummy2 as
                        (select Name,MapID,VariableType,PartType,NameInXml,TypeInXml,UnitInXml,AssemName,AssemID
                        from romax_mapping.batch_variable left join getriebe.assembly using (AssemType))
                        select Name,MapID,VariableType,NameInXml,TypeInXml,UnitInXml,AssemName as AssemName1,PartName,PartID
                        from variable_list_dummy2 left join getriebe.part_list
                        on variable_list_dummy2.PartType=getriebe.part_list.PartType and variable_list_dummy2.AssemID=getriebe.part_list.AssemID
                        where (variable_list_dummy2.PartType='' and PartName is null) or (PartName is not null))
                        select Name,MapID,VariableType,NameInXml,TypeInXml,UnitInXml,main_table.AssemName1,AssemName2,PartName,PartID
                        from main_table left join mapping_assembly_connection
                        on main_table.AssemName1=mapping_assembly_connection.AssemName1 and main_table.NameInXml like '%AssemName2%')
                        select Name,MapID,VariableType,NameInXml,TypeInXml,UnitInXml,AssemName1,AssemName2,PartName,PartID,TestPlan,TestCase
                        from variable_list_dummy7 left join getriebe.test_plan on variable_list_dummy7.NameInXml like '%TestCase%')
                        select distinct Name,MapID,VariableType,NameInXml,TypeInXml,UnitInXml,AssemName1,AssemName2,PartName,TestPlan,TestCase,AttribIdx
                        from variable_list_dummy6 left join getriebe.attribute_list
                        on variable_list_dummy6.PartID=getriebe.attribute_list.PartID and variable_list_dummy6.NameInXml like '%AttribIdx%')
                        select @s:=@s+1 as AllID, dummy8.* from variable_list_dummy8 as dummy8,(SELECT @s:= 0) AS s)
                        select * from variable_list_dummy9 where (AttribIdx is null) or (AttribIdx!=0))"""


class OutputPathList(CreateTableThroughOthers):
    """
    manche Tabelle können aus weitere vorhandene Tabelle generieren, um an die vorhandene Getriebestruktur anzupassen.
    alle Daten für Erstellung der Batchfile über Outputpath werden in diese Tabelle abgelegt
    """
    def __init__(self, database, pref):
        CreateTableThroughOthers.__init__(self, database, pref)
        self.query_script_drop = f"drop table if exists {self.pref.database}.{self.pref.output_path_listname}"
        self.query_script_creating = f"""create table if not exists {self.pref.database}.{self.pref.output_path_listname} as
                        (with tab_dummy3 as
                        (with tab_dummy1 as
                        (with tab_dummy2 as
                        (select MapID,PartID,PartName,xPath as xPath_shadowcomponent,RomaxID 
                        from romax_mapping.output_xml inner join getriebe.part_list on romax_mapping.output_xml.Attribute_Type=getriebe.part_list.PartType)
                        select PartID,PartName,Attribute_Name,Romax_Name,Attribute_Type,Unit,RomaxID,xPath as xPath_attribute,xPath_shadowcomponent,Use_Prefix 
                        from romax_mapping.output_xml inner join tab_dummy2 as t on t.MapID=romax_mapping.output_xml.SubMapID)
                        select TestCase,TestCaseID,PartID,PartName,Attribute_Name,Romax_Name,Attribute_Type,Unit,xPath_attribute,RomaxID,xPath_shadowcomponent,RomaxPath as xPath_loadcase,Use_Prefix 
                        from getriebe.test_plan cross join tab_dummy1)
                        select @s:=@s+1 as AllID,TestCase,TestCaseID,PartID,PartName,Attribute_Name as Name,Romax_Name,Attribute_Type,Unit,xPath_attribute,RomaxID,xPath_shadowcomponent,xPath_loadcase,Use_Prefix 
                        from tab_dummy3,(SELECT @s:= 0) AS s)"""


class ResultList(CreateTableThroughOthers):
    """
    manche Tabelle können aus weitere vorhandene Tabelle generieren, um an die vorhandene Getriebestruktur anzupassen.
    alle Daten für Erstellung der Batchfile über Result werden in diese Tabelle abgelegt
    """
    def __init__(self, database, pref):
        CreateTableThroughOthers.__init__(self, database, pref)
        self.query_script_drop = f"drop table if exists {self.pref.database}.{self.pref.result_listname}"
        self.query_script_creating = f"""create table if not exists {self.pref.database}.{self.pref.result_listname} as
                            (with
                            result_list_dummy8 as
                            (with result_list_dummy7 as
                            (with
                            mapping_assembly_connection as
                            (with result_list_dummy3 as
                            (with result_list_dummy4 as
                            (select AssemName,AssemType,AssemAttribName,AttribValue
                            from getriebe.assembly inner join getriebe.assem_attribute_list
                            using (AssemID) where AssemType='DetailedHelicalGearMesh' and AssemAttribName='Part1ID' )
                            select AssemName as AssemName2,AssemID
                            from result_list_dummy4 inner join getriebe.part_list on result_list_dummy4.AttribValue=getriebe.part_list.PartID)
                            select AssemName2,AssemName as AssemName1 from result_list_dummy3 inner join getriebe.assembly using (AssemID)),
                            main_table as
                            (with result_list_dummy2 as
                            (select Name,MapID,ResultType,PartType,NameInXml,UnitInXml,AssemName,AssemID
                            from romax_mapping.batch_result left join getriebe.assembly using (AssemType))
                            select Name,MapID,ResultType,NameInXml,UnitInXml,AssemName as AssemName1,PartName,PartID
                            from result_list_dummy2 left join getriebe.part_list
                            on result_list_dummy2.PartType=getriebe.part_list.PartType and result_list_dummy2.AssemID=getriebe.part_list.AssemID
                            where (result_list_dummy2.PartType='' and PartName is null) or (PartName is not null))
                            select Name,MapID,ResultType,NameInXml,UnitInXml,main_table.AssemName1,AssemName2,PartName,PartID
                            from main_table left join mapping_assembly_connection
                            on main_table.AssemName1=mapping_assembly_connection.AssemName1 and main_table.NameInXml like '%AssemName2%')
                            select Name,MapID,ResultType,NameInXml,UnitInXml,AssemName1,AssemName2,PartName,PartID,TestCase
                            from result_list_dummy7 left join getriebe.test_plan on result_list_dummy7.NameInXml like '%TestCase%'),
                            testplan_distinct as
                            (select distinct TestPlan from getriebe.test_plan)
                            select @s:=@s+1 as AllID,Name,MapID,ResultType,NameInXml,UnitInXml,AssemName1,AssemName2,PartName,PartID,TestPlan,TestCase
                            from result_list_dummy8 left join testplan_distinct on result_list_dummy8.NameInXml like '%TestPlan%',(SELECT @s:= 0) AS s)
                            """


class ActionList(CreateTableThroughOthers):
    """
    manche Tabelle können aus weitere vorhandene Tabelle generieren, um an die vorhandene Getriebestruktur anzupassen.
    alle Daten für Erstellung der Batchfile über Action werden in diese Tabelle abgelegt
    """
    def __init__(self, database, pref):
        CreateTableThroughOthers.__init__(self, database, pref)
        self.query_script_drop = f"drop table if exists {self.pref.database}.{self.pref.action_listname}"
        self.query_script_creating = f"""create table if not exists {self.pref.database}.{self.pref.action_listname} as
                            (with
                            Action_list_dummy8 as
                            (with Action_list_dummy7 as
                            (with
                            mapping_assembly_connection as
                            (with Action_list_dummy3 as
                            (with Action_list_dummy4 as
                            (select AssemName,AssemType,AssemAttribName,AttribValue
                            from getriebe.assembly inner join getriebe.assem_attribute_list
                            using (AssemID) where AssemType='DetailedHelicalGearMesh' and AssemAttribName='Part1ID' )
                            select AssemName as AssemName2,AssemID
                            from Action_list_dummy4 inner join getriebe.part_list on Action_list_dummy4.AttribValue=getriebe.part_list.PartID)
                            select AssemName2,AssemName as AssemName1 from Action_list_dummy3 inner join getriebe.assembly using (AssemID)),
                            main_table as
                            (with Action_list_dummy2 as
                            (select Name,ActionType,PartType,NameInXml,ArgumentValue1,ArgumentValue2,ArgumentValue3,ArgumentValue4,AssemName,AssemID
                            from romax_mapping.batch_action left join getriebe.assembly using (AssemType))
                            select Name,ActionType,NameInXml,ArgumentValue1,ArgumentValue2,ArgumentValue3,ArgumentValue4,AssemName as AssemName1,PartName
                            from Action_list_dummy2 left join getriebe.part_list
                            on Action_list_dummy2.PartType=getriebe.part_list.PartType and Action_list_dummy2.AssemID=getriebe.part_list.AssemID
                            where (Action_list_dummy2.PartType='' and PartName is null) or (PartName is not null))
                            select Name,ActionType,NameInXml,ArgumentValue1,ArgumentValue2,ArgumentValue3,ArgumentValue4,main_table.AssemName1,AssemName2,PartName
                            from main_table left join mapping_assembly_connection
                            on main_table.AssemName1=mapping_assembly_connection.AssemName1 and main_table.NameInXml like '%AssemName2%')
                            select Name,ActionType,NameInXml,ArgumentValue1,ArgumentValue2,ArgumentValue3,ArgumentValue4,AssemName1,AssemName2,PartName,TestCase
                            from Action_list_dummy7 left join getriebe.test_plan on Action_list_dummy7.NameInXml like '%TestCase%'),
                            testplan_distinct as
                            (select distinct TestPlan from getriebe.test_plan)
                            select @s:=@s+1 as AllID,Name,ActionType,NameInXml,ArgumentValue1,ArgumentValue2,ArgumentValue3,ArgumentValue4,AssemName1,AssemName2,PartName,TestPlan,TestCase
                            from Action_list_dummy8 left join testplan_distinct on Action_list_dummy8.NameInXml like '%TestPlan%',(SELECT @s:= 0) AS s)
                            """


class Plotting:
    """
    Plottingmodul

    Parameters
    ----------
    :param colors : Intensitätsmatrix
    :param label_list_x : list vob label in x-Achse
    :param label_list_y: list vob label in y-Achse
    :param new_order_result: Pfad von Speicherort des Plots
    :param label_colorbar: label von Colorbar

    Supported operators:
    ---------

    sa_block, zeichnen die Blockdiagramm von SA
    """
    def __init__(self, colors, label_list_x, label_list_y, new_order_result, label_colorbar="Sensitivität"):
        self.colors = colors
        self.label_list_x = label_list_x
        self.label_list_y = label_list_y
        self.label_colorbar = label_colorbar
        self.new_order_result = new_order_result

        # self.lc = lc

    def sa_block(self):
        matplotlib.use('Agg')
        user32 = ctypes.windll.user32
        width = user32.GetSystemMetrics(0)
        height = user32.GetSystemMetrics(1)
        num_x = len(self.label_list_x)
        num_y = len(self.label_list_y)
        interval_x = 10
        interval_y = 10
        plt.figure(figsize=(width / 100., height / 100.), dpi=100)
        ax = plt.axes()
        norm = mat_colors.Normalize(vmin=np.min(self.colors), vmax=np.max(self.colors))
        cmap = cm.rainbow
        for i in range(num_x):
            plt.plot([interval_x * i, interval_x * i], [0, num_y * interval_y], color='black', linestyle="--")
            for j in range(num_y):
                plt.plot([0, num_x * interval_x], [interval_y * j, interval_y * j], color='black', linestyle="--")
                x1 = np.linspace(interval_x * i, interval_x * (i + 1), 10)
                y1 = interval_y * j
                y2 = interval_y * (j + 1)
                ax.fill_between(x1, y1, y2, facecolor=cmap(norm(self.colors[j][i])))
                plt.text((interval_x * (i + 0.5)), (y1 + y2) / 2, '%.2f' % self.colors[j][i], ha='center',
                         va='bottom', fontsize=9)

        plt.xlim(0, num_x * interval_x)
        plt.ylim(0, num_y * interval_y)
        ax.xaxis.set_major_locator(MultipleLocator(interval_x))  # 设置y主坐标间隔 1
        ax.yaxis.set_major_locator(MultipleLocator(interval_y))  # 设置y主坐标间隔 1
        ax.xaxis.grid(True, which='major')  # major,color='black'
        ax.yaxis.grid(True, which='major')  # major,color='black'

        plt.xticks([(index + 0.5) * interval_x for index in range(num_x)], self.label_list_x, fontweight='bold',
                   rotation=60)
        plt.yticks([(index + 0.5) * interval_y for index in range(num_y)], self.label_list_y, fontweight='bold')
        # plt.axis('equal')
        ax.grid(False)
        cax, _ = cbar.make_axes(ax, shrink=0.9, pad=0.05)
        cb = cbar.ColorbarBase(cax, cmap=plt.cm.rainbow, norm=norm)

        cb.set_label(self.label_colorbar, rotation=270, labelpad=15, fontsize=16, fontweight='bold')
        # plt.title(f'SA under {self.lc}')
        # plt.tight_layout()
        # plt.subplots_adjust(left=0.05)
        plt.savefig(f"{self.new_order_result}\\{'_'.join(self.label_colorbar.split())}.png")


class Getfield:
    """
    abrufen Fieldinhalt (query_col_list) aus Datenbank bezüglich Where-Info

    Parameters
    ----------
    :param db : database
    :param query_col_list : List der Spaltname zum Ablesen
    :param db_table: Tabelle zum Ablesen
    :param where_info_dict: Bedingungen für Abrufen mit Format Dict {Columenname: ColumnWertlist}

    """
    def __init__(self, db, query_col_list, db_table, where_info_dict=None):
        self.db = db
        self.query_col_list = query_col_list
        self.where_info_dict = where_info_dict
        self.db_table = db_table

    def running(self):
        where_col = []
        for each_key in [*self.where_info_dict]:
            where_col.append([f"\'{x}\'" for x in self.where_info_dict[each_key]])

        where_col_transfer = [f"({','.join(x)})" for x in list(map(list, zip(*where_col)))]
        if self.where_info_dict is None:
            where_claus = ""
        else:
            where_claus = f"where ({','.join([*self.where_info_dict])}) in ({','.join(where_col_transfer)})"
        col_list = ",".join(self.query_col_list)
        query_script = f"select {col_list} from {self.db_table} {where_claus}"
        return self.db.execute_script_in_db(query_script, self.query_col_list)


class GetID(Getfield):
    """
    abrufen AllID aus Datenbank bezüglich Attributname und Testcase

    Parameters
    ----------
    :param db : database
    :param test_case : Loadcase als Bedingungen zur Ablsen
    :param execute_list: Attributname z.B. componentPowerLoss
    :param db_table: Tabelle zum Ablesen
    """
    def __init__(self, db, test_case, execute_list, db_table):
        query_col_list = ["AllID"]
        where_info_dict = {"Name": sum([[x] * len(test_case) for x in execute_list], []),
                           "TestCase": test_case * len(execute_list)}
        Getfield.__init__(self, db, query_col_list, db_table, where_info_dict)


class GetTestCase(Getfield):
    """
    abrufen Name der TestCase aus Datenbank bezüglich ID der Testcase

    Parameters
    ----------
    :param db : database
    :param which_id : ID der Testcase
    :param db_table: Tabelle zum Ablesen
    """
    def __init__(self, db, which_id, db_table):
        if which_id == '*':
            where_info_dict = None
        else:
            where_info_dict = {"TestCaseID": list(map(str, which_id))}
        query_col_list = ['TestPlan', 'TestCase', 'TestCaseID', 'RomaxPath']
        Getfield.__init__(self, db, query_col_list, db_table, where_info_dict)


# def test_case_path(db, table_test_plan, which_id):
#     if which_id == '*':
#         where_clause = " "
#     else:
#         where_clause = f" WHERE TestCaseID in ({','.join(list(map(str, which_id)))})"
#     test_case_name = ['TestPlan', 'TestCase', 'TestCaseID', 'RomaxPath']
#
#     return db.query_in_db(test_case_name, table_test_plan, where_clause)


def read_xml_to_object(file_path):
    while not os.path.exists(file_path):
        time.sleep(1)
    with open(file_path, "r", encoding="utf-8") as fobj:
        xml = fobj.read()
    xml_decode = xml.encode('utf-8')
    return objectify.fromstring(xml_decode)


def batch_appending(batch_typ):
    batch_file_to_append = batch_typ[0].appending()
    for each_batch_typ in batch_typ[1:]:
        each_batch_typ.batch_file = batch_file_to_append
        batch_file_to_append = each_batch_typ.appending()
    return batch_typ[-1]


def get_file_path(time_file, sampling, v_number):
    if time_file != "":
        new_order = f"{pref.SA}\\{time_file}"
        new_order_batch_output = f"{new_order}\\batch output"
        new_order_result = f"{new_order}\\result"

    else:
        new_order = f"{pref.SA}\\{datetime.now().strftime('%m-%d-%Y_%Hh%Mm%Ss')} with {str(sampling)} sample and {v_number} variable SOBOL"
        new_order_batch_output = f"{new_order}\\batch output"
        new_order_result = f"{new_order}\\result"
        os.mkdir(new_order)
        os.mkdir(new_order_batch_output)
        os.mkdir(new_order_result)
    return new_order, new_order_batch_output, new_order_result


def get_info(allid, class_name):
    # ----------------------info of result----------------------------
    get_all_id_list = [{"AllID": int(each_id)} for each_id in allid]
    mapping_list = class_name(pref, db, get_all_id_list).mapping()
    lc_list = mapping_list.get('TestCase', None)
    name_list = mapping_list.get('Name', None)
    part_list = []
    for x, y, z in zip(mapping_list.get('PartName', None), mapping_list.get('AssemName2', None),
                       mapping_list.get('AssemName1', None)):
        if x is None and y is None:
            part_list.append(z)
        elif x is not None:
            part_list.append(x)
        else:
            part_list.append(y)
    return lc_list, part_list, name_list


def get_idx(lc_list, name_list, all_result, decimal):
    # ----------------------get result on gearbox level-----------------
    all_result = np.array(all_result)
    lc_distinct = list(set(lc_list))
    sum_pl = []
    min_lt = []
    allidx_pl = []
    allidx_lt = []
    allidx_load_axial = []
    allidx_load_radial = []
    for each_lc in lc_distinct:
        idx_pl = [idx for idx, (x, y) in enumerate(zip(lc_list, name_list)) if
                  x == each_lc and y in ['componentPowerLoss', 'powerLoss']]
        allidx_pl.append(idx_pl)
        idx_lt = [idx for idx, (x, y) in enumerate(zip(lc_list, name_list)) if
                  x == each_lc and y in ['isoLifeSec', 'bendingDamage']]
        allidx_lt.append(idx_lt)

        idx_load_axial = [idx for idx, (x, y) in enumerate(zip(lc_list, name_list)) if
                          x == each_lc and y == 'shaftLoadAxial']
        allidx_load_axial.append(idx_load_axial)
        idx_load_radial = [idx for idx, (x, y) in enumerate(zip(lc_list, name_list)) if
                           x == each_lc and y == 'shaftLoadRadial']
        allidx_load_radial.append(idx_load_radial)

        bd_idx = [idx for idx, (m, n) in enumerate(zip(lc_list, name_list)) if
                  m == each_lc and n == 'bendingDamage']
        cd_idx = [idx for idx, (m, n) in enumerate(zip(lc_list, name_list)) if
                  m == each_lc and n == 'contactDamage']
        sum_pl_1 = []
        min_lt_1 = []
        for idx_result in range(all_result.shape[0]):
            pl = all_result[idx_result, idx_pl]
            sum_pl_1.append(pl.sum())
            max_bd_cd = np.array(
                [max(x, y) if max(x, y) != 0 else 1e-20 for x, y in
                 zip(all_result[idx_result, bd_idx], all_result[idx_result, cd_idx])])

            all_result[idx_result, bd_idx] = 60000000 * 60 * 60 / max_bd_cd
            lt = all_result[idx_result, idx_lt]
            min_lt_1.append(min(lt))
        min_lt.append(min_lt_1)
        sum_pl.append(sum_pl_1)
    lt_pl_gearbox = np.array(min_lt + sum_pl)
    name_list_changed = ["Powerloss" if idx in sum(allidx_pl, []) else x for idx, x in enumerate(name_list)]
    name_list_changed = ["Lifetime" if idx in sum(allidx_lt, []) else x for idx, x in enumerate(name_list_changed)]
    return allidx_pl, allidx_lt, allidx_load_radial, allidx_load_axial, \
           np.around(all_result.T, decimal), name_list_changed, lt_pl_gearbox, lc_distinct


def get_s(all_idx, variable_list, si_all):
    s1 = np.zeros(shape=(len(all_idx), len(variable_list)))
    st = np.zeros_like(s1)
    for idx, each_idx in enumerate(all_idx):
        s1[idx] = si_all[each_idx]['S1']
        st[idx] = si_all[each_idx]['ST']
    s1[np.isnan(s1)] = 0
    st[np.isnan(st)] = 0
    return s1, st


if __name__ == '__main__':
    """
    zu v11: Durch Username werden Ergebnisse mit Reihefolge abgerufen. 
    """
    start = time.time()
    print("-------------------Read completed----------------------------------------------")
    from All_prefix import prefix_info
    from My_DB_Connector import db_connecotor
    from config import IfkaConfig
    from Read_romax_xml_to_database import read_romax_xml

    pref = prefix_info()
    db = db_connecotor()
    db.build_connector()

    # --------------Reading of Romax-Mapping------------------------
    set_config = IfkaConfig(pref, db)

    # ----------------start server------------------------
    s = Server(pref, db)
    s.stop_server()
    s.start()
    # --------------initialising of datanbank----------------------------
    file_path = pref.dir + r'\RMX\sa_original_data.xml'
    ExportRmxXml(pref, db, file_path, pref.Batch_Input_Name, pref.Batch_Output_Name).appending_and_running()
    all_parameter = read_romax_xml(pref, db)
    all_parameter.initialize_db_with_xml(file_path, pref.db_tabels())

    # --------------creating tool-list----------------------------
    for each_class in [ActionList, ResultList, OutputPathList, VariableList]:
        each_class(db, pref).creating()
    # -------------------get variable and dataset-------------------
    var_list = [{'AllID': 16, "ExpectedValue": 2.1e-2}, {'AllID': 17, "ExpectedValue": 1.8e-2}]  # Facewidth
                # {'AllID': 18, "ExpectedValue": 1.884e-2}, {'AllID': 19, "ExpectedValue": 1.5e-2},
                # {'AllID': 20, "ExpectedValue": 2.35e-2}, {'AllID': 21, "ExpectedValue": 2.3e-2},
                #
                # {'AllID': 397, "ExpectedValue": 1.5e-002}, {'AllID': 398, "ExpectedValue": 8.6e-002},  # offset
                # {'AllID': 399, "ExpectedValue": 9.42e-003}, {'AllID': 400, "ExpectedValue": 3.16e-002},
                # {'AllID': 401, "ExpectedValue": 2.465e-002}, {'AllID': 402, "ExpectedValue": 2.51e-002},
                # # {'AllID': 712, "ExpectedValue": 0.12927}, {'AllID': 713, "ExpectedValue": 0.12927},
                # # {'AllID': 714, "ExpectedValue": 0.12927}, {'AllID': 715, "ExpectedValue": 0.12927},
                # # {'AllID': 716, "ExpectedValue": 0.12927}, {'AllID': 717, "ExpectedValue": 0.12927},
                # # {'AllID': 718, "ExpectedValue": 0.12927}, {'AllID': 719, "ExpectedValue": 0.12927},
                #
                # # {'AllID': 722, "ExpectedValue": 6.0e-003},
                # # {'AllID': 723, "ExpectedValue": 4.45e-002} B2
                # # {'AllID': 726, "ExpectedValue": 9.9e-002}, {'AllID': 727, "ExpectedValue": 5.2949e-002},
                #
                # {'AllID': 22, "ExpectedValue": 6.667e-07}, {'AllID': 23, "ExpectedValue": 6.667e-07},  # roughness
                # {'AllID': 24, "ExpectedValue": 4.16666e-007}, {'AllID': 25, "ExpectedValue": 4.16666e-007},
                # {'AllID': 26, "ExpectedValue": 3.0e-007}, {'AllID': 27, "ExpectedValue": 3.0e-007},
                #
                # {'AllID': 1766, "ExpectedValue": 0.039},  # lubrikant
                #
                # {'AllID': 720, "ExpectedValue": 0.12917}, {'AllID': 721, "ExpectedValue": 1.51e-002},  # offset
                # {'AllID': 724, "ExpectedValue": 7.5e-003},
                # {'AllID': 725, "ExpectedValue": 0.128}]  # lubricantLevel of gearbox

    # {'AllID': 4, "ExpectedValue": 0.305}, {'AllID': 5, "ExpectedValue": 0.305},
    # {'AllID': 6, "ExpectedValue": 0.349}]

    # {'AllID': 349, 'ExpectedValue': 0.5499},  # profileShiftCoefficient of 1. Gang Pinion
    # {'AllID': 4, "ExpectedValue": 0.305},  # PressureAngle of 1. Gang

    # bound = [[0.02, 0.025], [0.015, 0.025], [0.1, 0.132], [6e-07, 8e-07], [0.02, 0.044], [6.5e-003, 8.5e-003],
    #          [0.076, 0.096], [0.002, 0.005], [0.2, 0.3]]
    # bound = [[each_var['ExpectedValue'] * 0.9, each_var['ExpectedValue'] * 1.1] for idx, each_var in enumerate(var_list)
    #          if idx in range(19)] + [[0.11, 0.13], [7.5e-3, 1.51e-002], [6.5e-003, 8.5e-003],
    #                                  [0.1242, 0.1252]]
    bound = [[each_var['ExpectedValue'] * 0.9, each_var['ExpectedValue'] * 1.1] for idx, each_var in enumerate(var_list)]
    problem = {'num_vars': len(var_list),
               'names': [f"variable_{str(each_variable['AllID'])}" for each_variable in var_list],
               'bounds': bound}
    calc_second = False

    sampling = 65

    # filename = "04-01-2021_00h29m43s with 800 sample and 7 variable SOBOL"
    # filename = "04-09-2021_18h42m00s with 100 sample and 23 variable SOBOL"
    filename = r"05-29-2021_13h01m10s with 65 sample and 2 variable SOBOL"
    new_order, new_order_batch_output, new_order_result = get_file_path(filename, sampling, len(var_list))

    if filename == "":
        # ---------------------batch running of all variable group-------------
        # param_val = saltelli.sample(problem, sampling, calc_second_order=calc_second)
        param_val = fast_sampler.sample(problem, sampling)

        case_id_list = [1]
        case_info = GetTestCase(db, case_id_list, f"{pref.database}.{pref.Test_Plan}").running()
        test_case = [each_case_info["TestCase"] for each_case_info in case_info]

        query_col_list = ['AllID']

        act = ['runStaticAnalysisNotify']
        id_act = GetID(db, test_case, act, f"{pref.database}.{pref.action_listname}").running()

        # apply_design = [{"AllID": 17, "path": "", "priority": 1}]
        # act_list = apply_design + [{"AllID": each_aly['AllID'], "path": "", "priority": idx + 2} for idx, each_aly in
        #                            enumerate(id_act)]

        act_list = [{"AllID": each_aly['AllID'], "path": "", "priority": idx + 1} for idx, each_aly in
                    enumerate(id_act)]

        each_result = ['componentPowerLoss', 'powerLoss', 'isoLifeSec', 'bendingDamage', 'contactDamage',
                       'shaftLoadRadial', 'shaftLoadAxial']
        result_list = GetID(db, test_case, each_result, f"{pref.database}.{pref.result_listname}").running()

        info_id = {"id_var": [x['AllID'] for x in var_list], "id_res": [int(x['AllID']) for x in result_list]}
        with open(f"{new_order}\\info_id.json", 'w') as fp:
            json.dump(info_id, fp)
        # 'totalPowerflowLoss'

        error_report = []
        for idx, each_param_val in enumerate(param_val):
            if idx % 100 == 0 and idx != 0:
                s.stop_server()
                s.start()
            print(f"\nvariable group {idx + 1} for all case... running")
            for idx_var in range(len(var_list)):
                var_list[idx_var]["Attribvalue"] = each_param_val[idx_var]

            batch_func = [ChangeVariable(pref, db, var_list), ExecuteAction(pref, db, act_list),
                          GetResult(pref, db, result_list)]
            obj_to_run = batch_appending(batch_func)
            obj_to_run.batch_input_path = pref.Batch_Input_Name
            obj_to_run.batch_output_path = f"{new_order_batch_output}\\{idx + 1}.xml"
            obj_to_run.running()

            error_report.append(OutputReporting(obj_to_run.batch_output_path).get())
        print(f"\nrunning of all variable group for all Case... done")

    '''---------------------reading---------------------------------'''
    print("batch output file ... reading")
    res_comp = []
    root = None
    filenames_list = [int(x.split('.')[0]) for x in os.listdir(new_order_batch_output)]
    filenames_list.sort()
    filenames_batch_output = [f"{str(x)}.xml" for x in filenames_list]

    with open(f"{new_order}\\info_id.json", 'r') as fp:
        info_id = json.load(fp)
    id_res = info_id['id_res']
    id_var = info_id['id_var']
    for idx, each_filename_batch_output in enumerate(filenames_batch_output):
        batch_output_file = f"{new_order_batch_output}\\{each_filename_batch_output}"
        root = read_xml_to_object(batch_output_file)
        res_val_list = []
        for each_id_res in id_res:
            res_val = root.xpath(f"Case/Result[@nameUser='{str(each_id_res)}']/@value")[0]
            res_val_list.append(float(res_val))
        res_comp.append(res_val_list)

    print(f"\nreading of all batch output file... done")
    """-------------------------get info--------------------------------------"""
    decimal = 2
    lc_res_list, part_res_list, name_res_list = get_info(id_res, ResultMapping)
    idx_pl, idx_lt, idx_load_radial, idx_load_axial, res_comp, name_res_list_modi, res_gearbox, lc_uniq_list = get_idx(
        lc_res_list, name_res_list, res_comp, decimal)
    # res_comp;res_gearbox(lf_pl):  [component, sample]
    lc_var_list, part_var_list, name_var_list = get_info(id_var, VariableMapping)
    """----------------------------SA-----------------------------------------"""
    res = np.vstack((res_comp, res_gearbox))
    si_all = []
    for each_res in res:
        # si_all.append(sobol.analyze(problem, each_res, calc_second_order=calc_second))
        si_all.append(fast.analyze(problem, each_res))

    """----------------------getting ST-----------------------------------------"""
    s1, st = get_s(range(len(si_all)), var_list, si_all)
    """-----------------------plotting------------------------------------------"""
    lc_to_show = 0
    size_s_comp = res_comp.shape[0]
    idx_lt_to_show = idx_lt[lc_to_show] + [size_s_comp + lc_to_show]
    idx_pl_to_show = idx_pl[lc_to_show] + [size_s_comp + lc_to_show + len(lc_uniq_list)]
    idx_load_axi_to_show = idx_load_axial[lc_to_show]
    idx_load_rad_to_show = idx_load_radial[lc_to_show]

    separator = '\n'
    label_x = [f"{x}{separator}{y}" if x is not None else y for x, y in
               zip(part_var_list, name_var_list)]

    for s, idx_slice, label_gearbox, title_s in zip([s1, st, s1, st, s1, st, s1, st],
                                                    [idx_lt_to_show, idx_lt_to_show,
                                                     idx_pl_to_show, idx_pl_to_show,
                                                     idx_load_axi_to_show, idx_load_axi_to_show,
                                                     idx_load_rad_to_show, idx_load_rad_to_show],
                                                    ["minimal Lifetime", "minimal Lifetime", "Sum of Powerloss",
                                                     "Sum of Powerloss", "axial_load", "axial_load", "radial_load",
                                                     "radial_load"],
                                                    ["S1", "ST", "S1", "ST", "S1", "ST", "S1", "ST"]):
        label_gearbox1 = [] if label_gearbox == "axial_load" or label_gearbox == "radial_load" else [label_gearbox]
        label_y = [f"{x}{separator}{separator.join(y.split('->'))}" for idx, (x, y) in
                   enumerate(zip(part_res_list, name_res_list_modi)) if
                   idx in idx_slice] + label_gearbox1
        label_colorbar = f"Sensitivity Index {title_s} for {label_gearbox.split()[-1]} under {lc_uniq_list[lc_to_show]}"
        s_selected = np.around(s[idx_slice], 2)
        # s_selected_sort = []
        # for each_s_selected in s_selected:
        #     s_selected_sort.append(np.argsort(each_s_selected).astype(int))
        # s_selected_sort = np.array(s_selected_sort)
        Plotting(s_selected, label_x, label_y, new_order_result, label_colorbar).sa_block()
        data = {}
        for idx_x, each_label_x in enumerate(label_x):
            data[each_label_x] = {}
            for idx_y, each_label_y in enumerate(label_y):
                data[each_label_x][each_label_y] = s_selected[idx_y, idx_x]
        df = DataFrame(data)
        df.to_csv(f"{new_order_result}\\{'_'.join(label_colorbar.split())}.csv", ';')

    data = {}
    for idx, key in enumerate([f"{x}\\{y}" for idx, (x, y) in enumerate(zip(part_res_list, name_res_list_modi))]):
        data[key] = res_comp[idx]
    df = DataFrame(data)
    df.to_csv(f"{new_order_result}\\output.csv", ';')

    end = time.time()
    print(f"{end - start} Sec.")
