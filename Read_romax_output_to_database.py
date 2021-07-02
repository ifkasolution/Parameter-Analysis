from lxml import etree, objectify
import subprocess
from All_prefix import prefix_info
from datetime import datetime
from My_DB_Connector import db_connecotor
import time, os


def number_or_string(value):
    try:
        float(value)
        return True
    except ValueError:
        return False


def make_xml_input(part_dict):
    _type_name = part_dict["type_name"]
    _name = part_dict["attribute"]
    _sub_type = part_dict["part_attrib_type"]
    _sub_attrib = part_dict["part_attrib"]
    _part = etree.Element(_type_name, _name)
    if 'Output' in part_dict.keys():
        _output = part_dict["Output"]
        for _sub_type_1, _sub_attrib_1 in zip(_sub_type, _sub_attrib):
            all = etree.Element(_sub_type_1, _sub_attrib_1)
            all.append(etree.Element('Argument', value=_output))
            _part.append(all)
    else:
        for _sub_type_1, _sub_attrib_1 in zip(_sub_type, _sub_attrib):
            _part.append(etree.Element(_sub_type_1, _sub_attrib_1))
    return _part


class read_rmx_output():
    def __init__(self, pref, db):
        # ---------------Initializing----------------------------------------------------
        self.prefix = pref
        self.db = db

    def start_server(self):
        open(self.prefix.Batch_Log_Name, 'w').close()
        comm = subprocess.Popen([self.prefix.Software_Name, '-startAsServer',
                                 '5555', self.prefix.Batch_Log_Name])

        result = 'Starting Listening server on port'
        timeout = time.time() + 30  # 30 s from now
        lines = [' ']
        while not result in lines[-1]:
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
        print(' Server Stoped')

    def read_rmx_to_db(self, filepath, db_table, WhichID):
        print('-------------writing into db --------')

        if WhichID == '*':
            where_clause = " "
        else:
            seperator = ','
            where_clause = ' WHERE TestCaseID in (' + seperator.join(WhichID) + ')'
        while not os.path.exists(filepath):
            time.sleep(1)
        # --------------读取Romax的xml运行结果-----------
        with open(filepath, "r", encoding="utf-8") as fobj:
            xml = fobj.read()
        xml_decode = xml.encode('utf-8')
        root = objectify.fromstring(xml_decode)

        now = datetime.now()
        formatted_date = now.strftime('%Y-%m-%d')

        # ----tobereadfrom excel------------创建表头，删除已存在表的内容
        self.db.db_cursor.execute("CREATE TABLE IF NOT EXISTS " + db_table['Output'] + " "
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
        DELETE_rows = "Delete FROM " + db_table['Output']
        self.db.db_cursor.execute(DELETE_rows)

        Colm_to_insert = ["ResultID", "TestCaseID", "PartID", "PartName", "ResultName", "ResultRomaxName",
                          "ResultValue", "ResultUnit", "ResultType", "ResultIndex", "RomaxPath", "UpdateDATE"]
        value_to_insert = {k: '' for k in Colm_to_insert}

        # get names in simulation output list
        NameList = ['ResultID', 'TestCaseID', 'AssemID', 'PartID', 'AssemName', 'PartName', 'PartType']
        Testcase_name = ['TestCaseID', 'RomaxPath']
        Testcase = self.db.query_in_db(Testcase_name, db_table['TestPlan'], where_clause)
        partlist_name = ['PartID', 'PartName', 'PartType', 'RomaxID']
        Partlist = self.db.query_in_db(partlist_name, db_table['PartList'], '')
        self.result_id = 1
        self.result_to_insert = []
        testCaseID = []
        for each_testcase in Testcase:
            testCaseID.append(str(each_testcase['TestCaseID']))
            search_path = each_testcase['RomaxPath']
            testcase_node = root.xpath(search_path)[0]
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
                        idx_vector = 1
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
                            self.result_to_insert.append(value_to_insert.copy())
                            idx_vector = idx_vector + 1
                            self.result_id = self.result_id + 1
                        # self.db_cursor.executemany(mySql_insert_Output, self.output_to_insert)
        self.db.insertall_in_db(Colm_to_insert, self.result_to_insert, db_table['Output'])
        saftyShaft_to_insert = self.cal_shaft(db_table, testCaseID)
        self.db.insertall_in_db(Colm_to_insert, saftyShaft_to_insert, db_table['Output'])
        self.db.mydb.commit()

        print("--done------------------------------")

    def cal_shaft(self, db_table, TestCassIDs):
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
            Bend_allow = float(material_info['BendingAllowableStressValue'])
            Tension_allowed = float(material_info['AxialAllowableStressValue'])
            Torsion_allowed = float(material_info['TorsionAllowableStressValue'])
            # query Shaft Sim Result
            col = ['TestCaseID', 'ResultName', 'ResultIndex', 'ResultValue']
            where = f" WHERE PartID = {str(each['PartID'])} AND TestCaseID in ({','.join(TestCassIDs)}) AND ResultName " \
                    "in ('BendingLeft', 'BendingRight', 'TensionLeft','TensionRight', 'TorsionLeft','TorsionRight' )"
            result = self.db.query_in_db(col, db_table['Output'], where)
            for each_test in TestCassIDs:
                Bend = []
                Tension = []
                Torsion = []
                for each_result in result:
                    if each_result['TestCaseID'] == int(each_test):
                        RN = each_result['ResultName']
                        if RN == 'BendingLeft' or RN == 'BendingRight':
                            Bend.append(float(each_result['ResultValue']))
                        elif RN == 'TensionLeft' or RN == 'TensionRight':
                            Tension.append(float(each_result['ResultValue']))
                        elif RN == 'TorsionLeft' or RN == 'TorsionRight':
                            Torsion.append(float(each_result['ResultValue']))
                Bend_max = abs(max(Bend, key=abs))
                Tension_max = abs(max(Tension, key=abs))
                Torsion_max = abs(max(Torsion, key=abs))
                S = ((Bend_max / Bend_allow + Tension_max / Tension_allowed) ** 2 + (
                        Torsion_max / Torsion_allowed) ** 2) ** -0.5

                # print('PartID', each['PartID'], 'S', S)
                value_to_insert = {}
                value_to_insert['ResultID'] = self.result_id
                value_to_insert['TestCaseID'] = each_test
                value_to_insert['PartID'] = each['PartID']
                value_to_insert['PartName'] = each['PartName']
                value_to_insert['ResultName'] = 'ShaftSafetyFactor'
                value_to_insert['ResultRomaxName'] = ''
                value_to_insert['RomaxPath'] = ''
                value_to_insert['ResultValue'] = S
                value_to_insert['ResultUnit'] = '-'
                value_to_insert['ResultType'] = 'ShaftLifeTime'
                value_to_insert['ResultIndex'] = 0
                value_to_insert['UpdateDATE'] = formatted_date
                result_to_insert.append(value_to_insert.copy())
                self.result_id += 1
        return result_to_insert

    def rmx_output_evalutaion(self, db_table, eva_tabl):
        all_eva = []
        to_evaluate1 = {}
        to_evaluate2 = {}
        all_testcase = self.db.query_in_db(['TestCaseID'], self.prefix.Test_Plan, '')
        #     Shaft Max Bend tension shear
        to_evaluate1.update({"MaxBend": " in ('BendingLeft','BendingRight')",
                             "MaxTension": " in ('TensionLeft','TensionRight')",
                             "MaxTorsion": " in ('TorsionLeft','TorsionRight')"})

        to_evaluate2.update({"BendingDamage": " ='BendingDamage'",
                             "BendingStress": "='BendingStress'",
                             "ContactDamage": "='ContactDamage'",
                             "ContactStress": "='ContactStress'",
                             "SafetyFactorInBending": "='SafetyFactorInBending'",
                             "SafetyFactorInContact": "='SafetyFactorInContact'"})

        to_evaluate2.update({"IsoLifeSec": " ='IsoLifeSec'",
                             "IsoDamage": "='IsoDamage'"})

        self.db.db_cursor.execute("CREATE TABLE IF NOT EXISTS " + eva_tabl + " "
                                                                             "(EvaID INT AUTO_INCREMENT PRIMARY KEY, "
                                                                             "TestCaseID INT, "
                                                                             "PartID INT, "
                                                                             "PartName VARCHAR(255), "
                                                                             "EvaluationName VARCHAR(255), "
                                                                             "EvaluationValue VARCHAR(255), "
                                                                             "EvaluationUnit VARCHAR(20), "
                                                                             "EvaluationInfo VARCHAR(255), "
                                                                             "RomaxID VARCHAR(100))")

        DELETE_rows = "Delete FROM " + eva_tabl
        self.db.db_cursor.execute(DELETE_rows)
        for key in to_evaluate1:
            insert_eva = "INSERT INTO {}(EvaID,TestCaseID, PartID, PartName,EvaluationUnit,EvaluationName,EvaluationValue)".format(
                eva_tabl) + \
                         " SELECT ResultID,TestCaseID,PartID,PartName, ResultUnit,'{}' ,max(abs(CAST(ResultValue AS DECIMAL(40, 6))))".format(
                             key) + \
                         " FROM " + db_table + \
                         " WHERE ResultName " + to_evaluate1[key] + \
                         " group by TestCaseID,PartID;"
            self.db.db_cursor.execute(insert_eva)
        for key in to_evaluate2:
            insert_eva = "INSERT INTO {}(EvaID,TestCaseID, PartID, PartName,EvaluationUnit,EvaluationName,EvaluationValue)".format(
                eva_tabl) + \
                         " SELECT ResultID,TestCaseID,PartID,PartName, ResultUnit,'{}' , ResultValue ".format(key) + \
                         " FROM " + db_table + \
                         " WHERE ResultName " + to_evaluate2[key] + \
                         " group by TestCaseID,PartID;"
            self.db.db_cursor.execute(insert_eva)
        self.db.mydb.commit()

    def find_testcase(self, where):
        if where == '*':
            where_clause = " "
        else:
            seperator = ','
            where_clause = ' WHERE TestCaseID in (' + seperator.join(where) + ')'
        query_alltests = "Select TestPlan, TestCase FROM " + self.prefix.Test_Plan + where_clause
        self.db.db_cursor.execute(query_alltests)
        row = self.db.db_cursor.fetchall()
        return row

    def load_rmx_xml_with_sim(self, filepath, whichID='*'):
        if os.path.exists(filepath):
            os.remove(filepath)
        print('-------------let rmx run --------')
        Gearbox_name = ".\\" + self.prefix.Gearbox_name
        File_Name = self.prefix.rmx_file
        self.Batch_file = etree.Element("ParametricModification", file=File_Name)
        testcase = self.find_testcase(whichID)
        for eachone in testcase:
            self.generate_torun_dutycycle(eachone[0], eachone[1])
        part_1_attrib = []
        part_1_attrib_type = []
        part_1_name = Gearbox_name
        part_1_attrib.append({"name": "exportXMLTo:", "priority": "3"})
        part_1_attrib_type.append("Action")
        part = {"type_name": "Part",
                "attribute": {"name": part_1_name},
                "part_attrib_type": part_1_attrib_type,
                "part_attrib": part_1_attrib,
                "Output": filepath}  # 这里命令Romax将生成的运行结果以xml储存到filepath里，命名格式为simoutput + timestr + '.xml'
        part_1_all = make_xml_input(part)
        self.Batch_file.append(part_1_all)
        with open(self.prefix.Batch_Input_Name, "wb") as f:
            f.write(etree.tostring(self.Batch_file, pretty_print=True))
        self.prefix.generating_refresh()
        refresh_xml = self.prefix.refresh_xml
        comm = subprocess.Popen([self.prefix.rmx_server, '-i',
                                 refresh_xml, '-o', self.prefix.Batch_Output_Name])
        # Romax每执行一次batch需要一个输入的xml文件作为命令，然后生成一个xml作为完成文件以及一个text文件作为进程描述
        comm = subprocess.run([self.prefix.rmx_server, '-i',
                               self.prefix.Batch_Input_Name, '-o', self.prefix.Batch_Output_Name])
        print('-------------done --------')

    def generate_torun_dutycycle(self, DutyCycle, Loadcase):
        part_1_attrib = []
        part_1_attrib_type = []
        part_1_name = self.prefix.Gearbox_name \
                      + ">>" + DutyCycle + "\\" + Loadcase
        part_1_attrib.append({"name": "runStaticAnalysisNotify", "priority": "1"})
        part_1_attrib_type.append("Action")
        part_1_attrib.append({"name": "runDynamicAnalysisFromOptimizer", "priority": "2"})
        part_1_attrib_type.append("Action")
        part = {"type_name": "Case",
                "attribute": {"name": part_1_name},
                "part_attrib_type": part_1_attrib_type,
                "part_attrib": part_1_attrib}
        part_1_all = make_xml_input(part)
        self.Batch_file.append(part_1_all)


if __name__ == '__main__':
    import timeit

    print("-------------------Read completed----------------------------------------------")
    pref = prefix_info()
    db = db_connecotor()
    db.build_connector()
    batch_file = read_rmx_output(pref, db)
    # start = timeit.default_timer()
    file_path = pref.simulation_outputfile_debug
    # batch_file.start_server()
    # batch_file.load_rmx_xml_with_sim(filepath, ['1'])
    batch_file.read_rmx_to_db(file_path, pref.db_tabels_temp(), '*')
    # batch_file.compare_db_with_xml("E:\OneDrive\IFKA\IFKA_software\simple_gearbox\simoutputtest2.xml")
    # print(batch_file.compare_output_evalutaion(batch_file.prefix.ifka_eva, batch_file.prefix.ifka_eva_temp))
    # stop = timeit.default_timer()
    # print('Compare', stop - start)
    # batch_file.read_rmx_to_db("E:\OneDrive\IFKA\IFKA_software\simple_gearbox\simoutput20200612-163054.xml",batch_file.prefix.output_temp)
    # batch_file.stop_server()
    #
    # batch_file.compare_output_evalutaion(batch_file.prefix.ifka_eva, batch_file.prefix.ifka_eva_temp)
##### import test finished #################################################
