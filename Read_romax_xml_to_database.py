import os
import subprocess
import time
import timeit
from datetime import datetime

from lxml import etree
from lxml import objectify

from All_prefix import prefix_info
from My_DB_Connector import db_connecotor
from config import IfkaConfig


def make_xml_input(part_dict):
    _type_name = part_dict["type_name"]  # "part"
    _name = part_dict["attribute"]  # "getriebe"
    _sub_type = part_dict["part_attrib_type"]
    _sub_attrib = part_dict["part_attrib"]
    _output = part_dict["Output"]
    _part = etree.Element(_type_name, _name)
    for _sub_type_1, _sub_attrib_1 in zip(_sub_type, _sub_attrib):
        all = etree.Element(_sub_type_1, _sub_attrib_1)
        all.append(etree.Element('Argument', value=_output))
        _part.append(all)
    return _part


def number_or_string(value):
    try:
        float(value)
        return True
    except ValueError:
        return False


class read_romax_xml():
    def __init__(self, prefix, connector):
        self.prefix = prefix
        self.db = connector

    def load_rmx_xml(self):
        if os.path.exists(self.prefix.Outputfile):
            os.remove(self.prefix.Outputfile)
        batch_file = etree.Element("ParametricModification", file=self.prefix.rmx_file)
        part_1_attrib = []
        part_1_attrib_type = []
        part_1_name = self.prefix.Gearbox_name
        part_1_attrib.append({"name": "exportXMLTo:", "priority": "3"})
        part_1_attrib_type.append("Action")
        part = {"type_name": "Part",
                "attribute": {"name": part_1_name},
                "part_attrib_type": part_1_attrib_type,
                "part_attrib": part_1_attrib,
                "Output": self.prefix.Outputfile}
        part_1_all = make_xml_input(part)
        batch_file.append(part_1_all)
        with open(self.prefix.Batch_Input_Name, "wb") as f:
            f.write(etree.tostring(batch_file, pretty_print=True))
        comm = subprocess.Popen([self.prefix.rmx_server, '-i',
                                 self.prefix.Batch_Input_Name, '-o', self.prefix.Batch_Output_Name],
                                shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        data = comm.stdout.read()
        print(data)
        # return prefix.Outputfile

    def compare_db_with_xml(self, filepath):
        while not os.path.exists(filepath):
            time.sleep(1)
        with open(filepath, "r", encoding="utf-8") as fobj:
            xml = fobj.read()
        xml_decode = xml.encode('utf-8')
        root = objectify.fromstring(xml_decode)
        self.initialize_db_with_xml(filepath, self.prefix.db_tabels_temp())
        print("--Compare Input Parameter------------------------------")
        prix_type = {'prefix': 'http://www.w3.org/2001/XMLSchema-instance'}
        col = ['PartAttribName', 'AttribValue', 'RomaxPath', 'PartID', 'AttribUnit']
        all_result = self.db.query_in_db(col, self.prefix.Attribute_List, ' ')
        input_change = []
        for each in all_result:
            value = root.xpath(each['RomaxPath'], namespaces=prix_type)
            if '/@Ref' in each['RomaxPath']:
                db_value = str(value[0])
            else:
                db_value = value[0].text
            if db_value != each['AttribValue'] and each['PartAttribName'] != 'UserDefined':
                col_assem = ['PartName']
                where_assem = " WHERE PartID=" + str(each['PartID'])
                assem_name = self.db.query_in_db(col_assem, self.prefix.Part_List, where_assem)
                print('The Value ' + each['PartAttribName'] + assem_name[0]['PartName'] + ' CHANGED!')
                if number_or_string(db_value):
                    changed_value = float(db_value)
                else:
                    changed_value = db_value
                if number_or_string(each['AttribValue']):
                    unchanged_value = float(each['AttribValue'])
                else:
                    unchanged_value = each['AttribValue']
                input_change.append(
                    [each['PartID'], assem_name[0]['PartName'], each['PartAttribName'], each['AttribUnit'],
                     unchanged_value, changed_value])
            if each['PartAttribName'] == 'UserDefined':
                if 'state' in value[0].attrib:
                    UserDefined = 'False'
                else:
                    UserDefined = 'True'
                if UserDefined != each['AttribValue']:
                    print('The Value ' + each['PartAttribName'] + assem_name[0]['PartName'] + ' CHANGED!')

        col = ['AssemAttribName', 'AttribValue', 'RomaxPath', 'AssemID', 'AttribUnit']
        all_result = self.db.query_in_db(col, self.prefix.Assem_Attribute_List, ' ')
        for each in all_result:
            value = root.xpath(each['RomaxPath'], namespaces=prix_type)
            if '/@Ref' in each['RomaxPath']:
                if len(value) == 0 and each['AssemAttribName'] == 'Part2ID':
                    db_value = 'Ground'
                elif each['AssemAttribName'] == 'Part1ID' or each['AssemAttribName'] == 'Part2ID':
                    col_part = ['PartID', 'RomaxID']
                    where_romaxid = " WHERE RomaxID = '" + str(value[0]) + "'"
                    all_partID = self.db.query_in_db(col_part, self.prefix.Part_List, where_romaxid)
                    if len(all_partID) == 0:
                        db_value = str(value[0])
                    else:
                        db_value = str(all_partID[0]['PartID'])
                else:
                    db_value = str(value[0])
            else:
                if len(value) == 0:
                    db_value = 'NONE'
                else:
                    db_value = value[0].text
            flag = 0
            if db_value != each['AttribValue']:
                col_assem = ['AssemName']
                where_assem = " WHERE AssemID=" + str(each['AssemID'])
                assem_name = self.db.query_in_db(col_assem, self.prefix.Assembly, where_assem)
                print('The Value ' + each['AssemAttribName'] + ' of ' + assem_name[0]['AssemName'] + ' CHANGED! from ' +
                      each['AttribValue'] + ' to ' + db_value)
                if number_or_string(db_value):
                    changed_value = float(db_value)
                else:
                    changed_value = db_value
                if number_or_string(each['AttribValue']):
                    unchanged_value = float(each['AttribValue'])
                    if abs(float(each['AttribValue']) - float(db_value)) > 0.000000001:
                        flag = 1
                else:
                    unchanged_value = each['AttribValue']
                    flag = 1
                if flag == 1:
                    input_change.append(
                        [each['AssemID'], assem_name[0]['AssemName'], each['AssemAttribName'], each['AttribUnit'],
                         unchanged_value, changed_value])
        print("--done------------------------------")
        return input_change

    def initialize_db(self, db_table):
        self.db.db_cursor.execute("CREATE DATABASE IF NOT EXISTS getriebe")
        self.db.db_cursor.execute("CREATE DATABASE IF NOT EXISTS romax_mapping")
        self.db.db_cursor.execute(
            f"""CREATE TABLE IF NOT EXISTS  {self.prefix.database}.{db_table['AssemList']} (AssemID INT AUTO_INCREMENT PRIMARY KEY, AssemName VARCHAR(255), AssemType VARCHAR(255), AssemCatalog VARCHAR(255),UpdateDate DATE, RomaxID VARCHAR(255), RomaxPath VARCHAR(255))""")

        self.db.db_cursor.execute(
            f"""CREATE TABLE IF NOT EXISTS {self.prefix.database}.{db_table['PartList']} (PartID INT AUTO_INCREMENT PRIMARY KEY, AssemID INT, FOREIGN KEY(AssemID) REFERENCES {db_table['AssemList']} (AssemID), PartName VARCHAR(255), PartType VARCHAR(255),  UpdateDATE DATE, RomaxID VARCHAR(255), RomaxPath VARCHAR(255))""")
        self.db.db_cursor.execute(
            f"""CREATE TABLE IF NOT EXISTS  {self.prefix.database}.{db_table['PartAttrib']} (PartAttributeID INT AUTO_INCREMENT PRIMARY KEY, PartAttribName VARCHAR(255), AttribType VARCHAR(255), AttribValue VARCHAR(255), AttribUnit VARCHAR(255), PartID INT, RomaxPath VARCHAR(255), AttribIdx INT, FOREIGN KEY(PartID) REFERENCES {db_table['PartList']} (PartID), UpdateDate DATE)""")
        self.db.db_cursor.execute(
            f"""CREATE TABLE IF NOT EXISTS {self.prefix.database}.{db_table['AssemAttrib']} (AssemAttributeID INT AUTO_INCREMENT PRIMARY KEY, AssemAttribName VARCHAR(255), AttribType VARCHAR(255), AttribValue VARCHAR(255), AttribUnit VARCHAR(255), AssemID INT, RomaxPath VARCHAR(255), AttribIdx INT, FOREIGN KEY (AssemID) REFERENCES {db_table['AssemList']} (AssemID), UpdateDate DATE)""")
        self.db.db_cursor.execute(
            f"""CREATE TABLE IF NOT EXISTS {self.prefix.database}.{db_table['TestPlan']}  (TestPlan VARCHAR(255),TestCase VARCHAR(255), TestPlanID INT, TestCaseID INT AUTO_INCREMENT PRIMARY KEY,ClosedClutch VARCHAR(255), Temperature DOUBLE, InputLoad INT,OutputLoad INT,RomaxPath VARCHAR(255))""")
        # --Temperary----------------------------------------
        for each in db_table:
            print(db_table[each], self.db.table_exist(db_table[each]))
            if self.db.table_exist(db_table[each]):
                DELETE_rows = "Delete FROM " + db_table[each]
                self.db.db_cursor.execute(DELETE_rows)
        # --Temperary----------------------------------------

    def initialize_db_with_xml(self, filepath, db_table):
        self.initialize_db(db_table)  # 新建表头，删除原表内容
        while not os.path.exists(filepath):
            time.sleep(1)
        with open(filepath, "r", encoding="utf-8") as fobj:
            xml = fobj.read()
        xml_decode = xml.encode('utf-8')
        self.root = objectify.fromstring(xml_decode)
        print("--initialize input _with_xml------------------------------")
        start = timeit.default_timer()
        self.romax_mapping_read_xml = self.prefix.romax_mapping_read_xml_sql

        # --Predifinition Write Order------------------------------
        mySql_insert_Assembly = ['AssemID', 'AssemName', 'AssemType', 'AssemCatalog', 'UpdateDate', 'RomaxID',
                                 'RomaxPath']
        mySql_insert_Part = ['PartID', 'AssemID', 'PartName', 'PartType', 'UpdateDate', 'RomaxID', 'RomaxPath']
        mySql_insert_Assembly_Attrib = ['AssemAttributeID', 'AssemID', 'AssemAttribName', 'AttribType', 'UpdateDate',
                                        'AttribValue', 'AttribUnit', 'RomaxPath', 'AttribIdx']
        mySql_insert_Part_Attrib = ['PartAttributeID', 'PartID', 'PartAttribName', 'AttribType', 'UpdateDate',
                                    'AttribValue', 'AttribUnit', 'RomaxPath', 'AttribIdx']
        mySql_insert_Test_Plan = ['TestPlan', 'TestCase', 'TestPlanID', 'TestCaseID', 'ClosedClutch',
                                  'RomaxPath', 'Temperature', 'InputLoad', 'OutputLoad']
        # now = datetime.now()
        # formatted_date = now.strftime('%Y-%m-%d')

        # ----Assembly, Part and their attributes List-------
        self.assembly_to_insert = []
        self.part_to_insert = []
        self.assembly_attrib_to_insert = []
        self.part_attrib_to_insert = []
        self.pos_to_insert = []
        self.testplan_to_insert = []
        self.output_to_insert = []
        self.assembly_index = 1
        self.part_index = 1
        self.assembly_attrib_index = 1
        self.part_attrib_index = 1

        all_assem = self.prefix.Assembly_list()
        for eachone in all_assem:
            # 将所有root中的所有关于assembly(assembly_to_insert); component(part_to_insert);
            # assembly的attribute(assembly_attrib_to_insert);component的attribute(part_attrib_to_insert)分别打包成字典
            self.find_all_assemble(eachone, all_assem[eachone], 'Assembly')
        for eachone in self.prefix.Connection():
            # 将所有connection下得所有element(assembly_to_insert); element的attribute(assembly_attrib_to_insert)分别打包成字典 (connection没有component)
            self.find_all_assemble(eachone, [], 'Connection')
        for each in self.prefix.Databas:
            # 将所有database下得所有element(assembly_to_insert); element的attribute(assembly_attrib_to_insert)分别打包成字典 (database没有component)
            self.find_all_assemble(each, [], 'DataBase')
        # -------------tables: assembly------------------
        self.db.insertall_in_db(mySql_insert_Assembly, self.assembly_to_insert, db_table['AssemList'])
        # -------------tables: part_list--------------------
        self.db.insertall_in_db(mySql_insert_Part, self.part_to_insert, db_table['PartList'])
        # -------------tables: asssem_attribute_list-----------------
        self.db.insertall_in_db(mySql_insert_Assembly_Attrib, self.assembly_attrib_to_insert, db_table['AssemAttrib'])
        # -------------tables: attribute_list------------------
        self.db.insertall_in_db(mySql_insert_Part_Attrib, self.part_attrib_to_insert, db_table['PartAttrib'])

        Query_update_Part = "UPDATE " + db_table['AssemAttrib'] + ", " + db_table['PartList'] + " " + \
                            "SET " + db_table['AssemAttrib'] + ".AttribValue = " + db_table['PartList'] + ".PartID " \
                                                                                                          "WHERE " + \
                            db_table['AssemAttrib'] + ".AssemAttribName  Like  'Part%' " + \
                            "AND " + db_table['AssemAttrib'] + ".AttribValue = " + db_table['PartList'] + ".RomaxID;"
        self.db.db_cursor.execute(Query_update_Part)
        Query_update_Part = "UPDATE " + db_table['AssemAttrib'] + " " + \
                            "Set " + db_table['AssemAttrib'] + ".AttribValue = " + \
                            "if ( " + db_table['AssemAttrib'] + ".AttribValue" + \
                            "='NONE', 'Ground'," + db_table['AssemAttrib'] + ".AttribValue)" + \
                            "where " + db_table['AssemAttrib'] + ".AssemAttribName  Like  'Part%';"
        self.db.db_cursor.execute(Query_update_Part)
        # ---------------计算轴的位置-----------------------
        self.cal_part_coordinat(db_table)
        self.db.insertall_in_db(mySql_insert_Part_Attrib, self.pos_to_insert, db_table['PartAttrib'])
        # ---------------调取loadcase的信息-----------------
        self.find_all_testplan(db_table)
        self.db.insertall_in_db(mySql_insert_Test_Plan, self.testplan_to_insert, db_table['TestPlan'])

        # ----Done--------------------------------------
        self.db.mydb.commit()
        stop = timeit.default_timer()
        print('initialize_db_with_xml time: ', stop - start)

    def cal_part_coordinat(self, db_table):
        shaft_cor = self.db_query(self.prefix.ShaftCoordination)
        shaft_prefix = shaft_cor[0]['Use_Prefix']
        shaft_xpath = shaft_cor[0]['xPath']
        shaft_all = self.root.xpath(shaft_xpath.format(""), namespaces={'prefix': shaft_prefix, })
        shaft_cor_attr = self.db_query_attrib(self.prefix.ShaftCoordination)
        now = datetime.now()
        formatted_date = now.strftime('%Y-%m-%d')
        for each in shaft_all:
            pos = {}
            pos_to_insert = []
            if 'state' in each.Origin.attrib:
                UserDefined = 'False'
            else:
                UserDefined = 'True'
            pos_dict = {'PartAttributeID': self.part_attrib_index, 'PartID': 0, 'PartAttribName': 'UserDefined',
                        'AttribType': 'ShaftPosition',
                        'UpdateDate': formatted_date, 'AttribValue': UserDefined, 'AttribUnit': '',
                        'RomaxPath': shaft_xpath.format("and @PartName='" + each.attrib['PartName'] + "'") + "/Origin",
                        'AttribIdx': 0}
            pos_to_insert.append(pos_dict)
            self.part_attrib_index = self.part_attrib_index + 1
            for each_attrib in shaft_cor_attr:
                pos_name = each_attrib['Attribute_Name']
                pos_unit = each_attrib['Unit']
                pos_type = each_attrib['Attribute_Type']
                pos_val = each.xpath('./' + each_attrib['xPath'])
                pos[pos_name] = pos_val[0]
                if '@Ref' in each_attrib['xPath']:
                    value = str(pos_val[0])
                else:
                    value = pos_val[0].text
                pos_pat = shaft_xpath.format("and @PartName='" + each.attrib['PartName'] + "'") + each_attrib['xPath']
                if pos_name != "ShaftID":
                    pos_dict = {'PartAttributeID': self.part_attrib_index, 'PartID': 0, 'PartAttribName': pos_name,
                                'AttribType': pos_type,
                                'UpdateDate': formatted_date, 'AttribValue': value, 'AttribUnit': pos_unit,
                                'RomaxPath': pos_pat, 'AttribIdx': 0}
                    pos_to_insert.append(pos_dict.copy())
                    self.part_attrib_index = self.part_attrib_index + 1
            query = "SELECT PartID From " + db_table['PartList'] + " WHERE RomaxID = '" + pos['ShaftID'] + "'"
            self.db.db_cursor.execute(query)
            partID = self.db.db_cursor.fetchall()
            for each in pos_to_insert:
                each['PartID'] = partID[0][0]
            self.pos_to_insert = self.pos_to_insert + pos_to_insert

    def find_all_testplan(self, table):
        testplans = self.root.DutyCycles.getchildren()
        id_plan = 1
        id_case = 1
        for each in testplans:
            testplan_name = each.Name.text
            testcase = each.LoadCases.getchildren()
            for each_case in testcase:
                each_case_name = each_case.Name.text
                each_case_temp = each_case.Temperature.pyval
                each_case_input_rmx = each_case.InputPowerLoad.attrib['Ref']
                query_partid = self.db.query_in_db(['PartID'], table['PartList'],
                                                   " WHERE RomaxID ='{}'".format(each_case_input_rmx))
                each_case_input = query_partid[0]['PartID']
                each_case_Output_rmx = each_case.OutputPowerLoad.attrib['Ref']
                query_partid = self.db.query_in_db(['PartID'], table['PartList'],
                                                   " WHERE RomaxID ='{}'".format(each_case_Output_rmx))
                each_case_output = query_partid[0]['PartID']
                clutch_info = each_case.xpath("./ShadowConnections/Element[@prefix:type='SSDClutchedConnectionPF']",
                                              namespaces={'prefix': 'http://www.w3.org/2001/XMLSchema-instance', })
                closed_clutch = []
                for each_clutch in clutch_info:
                    if each_clutch.ClutchState.text == 'true':
                        clutch_rmx_id = each_clutch.Real.attrib['Ref']
                        clutch_id_query = self.db.query_in_db(['AssemID'], table['AssemList'],
                                                              " WHERE RomaxID ='{}'".format(clutch_rmx_id))
                        clutch_id = clutch_id_query[0]['AssemID']
                        closed_clutch.append(str(clutch_id))
                sep = ', '
                closed_clutch_str = sep.join(closed_clutch)
                xpath = ".//DutyCycles/Element[Name='{}']/LoadCases/Element[Name='{}']".format(testplan_name,
                                                                                               each_case_name)
                self.testplan_to_insert.append(
                    {'TestPlan': testplan_name, 'TestCase': each_case_name, 'TestPlanID': id_plan,
                     'TestCaseID': id_case, 'RomaxPath': xpath, 'Temperature': each_case_temp,
                     'InputLoad': each_case_input, 'OutputLoad': each_case_output, 'ClosedClutch': closed_clutch_str})
                id_case = id_case + 1
            id_plan = id_plan + 1

    def find_all_assemble(self, Assembly, Part, catalogue):
        assem_path = self.db_query(Assembly)
        assem_attrib_path = self.db_query_attrib(Assembly)
        # ['MapID', 'xPath', 'Attribute_Name', 'Romax_Name', 'Attribute_Type', 'Use_Prefix',
        #  'Romax_Version']
        assem_type = "'" + assem_path[0]['Romax_Name'] + "'"
        assem_prefix = assem_path[0]['Use_Prefix']
        assem_xpath = assem_path[0]['xPath']
        # 调取出所有绝对路径下Element标签属性等于e.g. SSDShaftAssembly的内容，即调取所有root下的e.g. SSDShaftAssembly
        # （除此之外还有e.g. SSDDetailedHelicalGearSet,SSDConceptClutch等等没有调取）
        assem = self.root.xpath(assem_xpath.format(assem_type), namespaces={'prefix': assem_prefix, })
        now = datetime.now()
        formatted_date = now.strftime('%Y-%m-%d')
        for each_assem in assem:
            if 'UniqueID' in each_assem.attrib:
                each_assem_id = each_assem.attrib['UniqueID']
                each_assem_name = each_assem.attrib['Name']
                assem_xpath_id = assem_type + " and @UniqueID='" + each_assem_id + "'"
            else:
                each_assem_id = "NONE"
                each_assem_name = each_assem.attrib['Name']
                assem_xpath_id = assem_type + " and @Name='" + each_assem_name + "'"
            assem_xpath_full = assem_xpath.format(assem_xpath_id)
            assem_dict = {'AssemID': self.assembly_index, 'AssemName': each_assem_name, 'AssemType': Assembly,
                          'AssemCatalog': catalogue,
                          'UpdateDate': formatted_date, 'RomaxID': each_assem_id, 'RomaxPath': assem_xpath_full}
            self.assembly_to_insert.append(assem_dict.copy())
            for each_assem_att in assem_attrib_path:
                assembly_attrib_to_insert = {}
                # ['MapID', 'xPath', 'Attribute_Name', 'Romax_Name', 'Unit', 'Attribute_Type', 'Use_Prefix', 'Romax_Version']
                assem_attrib_xpath = assem_xpath_full + each_assem_att['xPath']
                assem_attrib_Name = each_assem_att['Attribute_Name']
                assem_attrib_Type = each_assem_att['Attribute_Type']
                assem_attrib_unit = each_assem_att['Unit']
                assem_attrib_AssemID = self.assembly_index
                assem_attrib = each_assem.xpath(
                    './' + each_assem_att['xPath'])  # Instead of read the full path to speed up
                if len(assem_attrib) == 0:
                    assem_attrib_value = 'NONE'
                elif '@' in each_assem_att['xPath']:
                    assem_attrib_value = str(assem_attrib[0])
                else:
                    assem_attrib_value = assem_attrib[0].text
                assembly_attrib_to_insert = {'AssemAttributeID': self.assembly_attrib_index,
                                             'AssemID': assem_attrib_AssemID,
                                             'AssemAttribName': assem_attrib_Name, 'AttribType': assem_attrib_Type,
                                             'UpdateDate': formatted_date, 'AttribValue': assem_attrib_value,
                                             'AttribUnit': assem_attrib_unit,
                                             'RomaxPath': assem_attrib_xpath, 'AttribIdx': 0}
                self.assembly_attrib_to_insert.append(assembly_attrib_to_insert.copy())
                self.assembly_attrib_index = self.assembly_attrib_index + 1
            for each_part in Part:
                part_path = self.db_query(each_part)
                part_type = "'" + part_path[0]['Romax_Name'] + "'"
                part_prefix = part_path[0]['Use_Prefix']
                part_xpath = part_path[0]['xPath']
                part_path_attr = part_path[0]['Attribute_Name']
                part_xpath_format = part_type
                part_all = each_assem.xpath('./' + part_xpath.format(part_xpath_format),
                                            namespaces={'prefix': part_prefix, })
                part_attrib_path = self.db_query_attrib(each_part)
                for each_element in part_all:
                    element_id = each_element.attrib['UniqueID']
                    element_name = each_element.attrib['Name']
                    element_xpath_format = part_type + " and @UniqueID='" + element_id + "'"
                    element_xpath_full = '/' + part_xpath.format(element_xpath_format)
                    part_to_insert_dict = {'PartID': self.part_index, 'AssemID': self.assembly_index,
                                           'PartName': element_name,
                                           'PartType': each_part, 'UpdateDate': formatted_date, 'RomaxID': element_id,
                                           'RomaxPath': element_xpath_full}
                    self.part_to_insert.append(part_to_insert_dict.copy())
                    for each_part_attrib in part_attrib_path:
                        part_attrib_xpath = element_xpath_full + each_part_attrib['xPath']
                        part_attrib_Name = each_part_attrib['Attribute_Name']
                        part_attrib_Type = each_part_attrib['Attribute_Type']
                        part_attrib_unit = each_part_attrib['Unit']
                        part_attrib_PartID = self.part_index
                        part_attrib = each_element.xpath('.' + each_part_attrib['xPath'])
                        if len(part_attrib) > 1:
                            for i in range(len(part_attrib)):
                                part_attrib_value = part_attrib[i].text
                                part_attrib_dict = {'PartAttributeID': self.part_attrib_index,
                                                    'PartID': part_attrib_PartID,
                                                    'PartAttribName': part_attrib_Name, 'AttribType': part_attrib_Type,
                                                    'UpdateDate': formatted_date,
                                                    'AttribValue': part_attrib_value, 'AttribUnit': part_attrib_unit,
                                                    'RomaxPath': '(' + part_attrib_xpath + ')[' + str(i + 1) + ']',
                                                    'AttribIdx': i + 1}
                                self.part_attrib_to_insert.append(part_attrib_dict.copy())
                                self.part_attrib_index = self.part_attrib_index + 1
                        elif len(part_attrib) == 1:
                            if '@' in each_part_attrib['xPath']:
                                part_attrib_value = str(part_attrib[0])
                            else:
                                part_attrib_value = part_attrib[0].text
                            part_attrib_dict = {'PartAttributeID': self.part_attrib_index, 'PartID': part_attrib_PartID,
                                                'PartAttribName': part_attrib_Name, 'AttribType': part_attrib_Type,
                                                'UpdateDate': formatted_date,
                                                'AttribValue': part_attrib_value, 'AttribUnit': part_attrib_unit,
                                                'RomaxPath': part_attrib_xpath, 'AttribIdx': 1}
                            self.part_attrib_to_insert.append(part_attrib_dict.copy())
                            self.part_attrib_index = self.part_attrib_index + 1
                        else:
                            part_attrib_dict = {'PartAttributeID': self.part_attrib_index, 'PartID': part_attrib_PartID,
                                                'PartAttribName': part_attrib_Name, 'AttribType': part_attrib_Type,
                                                'UpdateDate': formatted_date,
                                                'AttribValue': 'NONE', 'AttribUnit': part_attrib_unit,
                                                'RomaxPath': part_attrib_xpath, 'AttribIdx': 0}
                            self.part_attrib_to_insert.append(part_attrib_dict.copy())
                            self.part_attrib_index = self.part_attrib_index + 1
                    self.part_index = self.part_index + 1
            self.assembly_index = self.assembly_index + 1
        return self.assembly_to_insert, self.part_to_insert

    def db_query(self, Attribute_Name):
        NameList = ['MapID', 'xPath', 'Attribute_Name', 'Romax_Name', 'Attribute_Type', 'Use_Prefix',
                    'Romax_Version']
        separator = ', '
        NameList_all = separator.join(NameList)
        Query = "SELECT " + NameList_all + " FROM " + self.romax_mapping_read_xml + " WHERE Attribute_Name = %s"
        self.db.db_cursor.execute(Query, (Attribute_Name,))
        result = self.db.db_cursor.fetchall()
        query_result = []
        for each in result:
            query_result.append(dict(zip(NameList, each)))
        return query_result

    # 从数据库romax_mapping.read_xml调取特定Attribute_Name的Element的所有read信息，其中最重要的是xpath

    def db_query_attrib(self, Attribute_Name):
        NameList = ['MapID', 'xPath', 'Attribute_Name', 'Romax_Name', 'Unit', 'Attribute_Type', 'Use_Prefix',
                    'Romax_Version']
        separator = ', '
        NameList_all = separator.join(NameList)
        Query = "SELECT " + NameList_all + " FROM " + self.romax_mapping_read_xml + \
                " where SubMapID = (Select MapID FROM romax_mapping.read_xml where Attribute_Name = %s)"
        self.db.db_cursor.execute(Query, (Attribute_Name,))
        result = self.db.db_cursor.fetchall()
        query_result = []
        for each in result:
            query_result.append(dict(zip(NameList, each)))
        return query_result

    # 从数据库romax_mapping.read_xml调取特定Attribute_Name的Element下面的所有Element(一般是他的attribute)信息

    def get_part_position(self, PartID_INT):
        pos = {}
        PartID = str(PartID_INT)
        self.db.db_cursor = self.mydb.cursor()
        querypos = "SELECT PartType FROM derex.part_list WHERE PartID =" + PartID
        self.db.db_cursor.execute(querypos)
        type = self.db.db_cursor.fetchone()
        if type[0] == 'Shaft':
            querypos = "SELECT * FROM attribute_list \
                        WHERE AttribType = 'ShaftPosition' AND PartID =" + PartID
            self.db.db_cursor.execute(querypos)
            result = self.db.db_cursor.fetchall()
        else:
            querypos = "SELECT * FROM attribute_list \
                        WHERE AttribType = 'ShaftPosition' AND PartID = \
                        (SELECT AttribValue FROM assem_attribute_list Where \
                        AssemAttribName = 'Part1ID' AND AssemID = \
                        (SELECT AssemID FROM assem_attribute_list \
                        Where AssemAttribName = 'Part2ID' AND AttribValue =" + PartID + "))"
            self.db.db_cursor.execute(querypos)
            result = self.db.db_cursor.fetchall()
            querypos = "SELECT AttribValue FROM assem_attribute_list Where \
                                    AssemAttribName = 'Offset' AND AssemID = \
                                    (SELECT AssemID FROM assem_attribute_list \
                                    Where AssemAttribName = 'Part2ID' AND AttribValue =" + PartID + ")"
            self.db.db_cursor.execute(querypos)
            result_offset = self.db.db_cursor.fetchone()
            if result_offset:
                pos['Offset'] = result_offset[0]
        for each in result:
            pos[each[1]] = each[3]

        return pos


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


if __name__ == '__main__':
    db = db_connecotor()
    db.build_connector()
    pref = prefix_info()
    cf = IfkaConfig(pref, db)
    start_server(pref)

    all_parameter = read_romax_xml(pref, db)
    all_parameter.load_rmx_xml()
    # all_parameter.initialize_db_with_xml()
    # file = r"C:\IFKA\IFKA\IFKA Prototype - Documents\Technical Review (Jira)\MA Meng\Program\RMX\simoutput20201005-104819.xml"
    # filepath = pref.simulation_outputfile_debug
    filepath = pref.Outputfile
    all_parameter.initialize_db_with_xml(filepath, pref.db_tabels())
    # for idx in range(10):
    #     print(idx)
    #     print (all_parameter.get_part_position(idx+1))
    print("-------------------Read completed----------------------------------------------")
