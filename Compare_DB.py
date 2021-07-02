import json
from datetime import datetime


def number_or_string(value):
    try:
        float(value)
        return True
    except:
        return False


class compare_db():
    def __init__(self, prefix, db):
        self.db = db
        self.prefix = prefix
        self.db_tables = self.prefix.db_tabels()
        self.db_tables_temp = self.prefix.db_tabels_temp()

    def compare_output(self):
        col_name = [self.db_tables['Output'] + '.TestCaseID',
                    self.db_tables['Output'] + '.PartName',
                    self.db_tables['Output'] + '.ResultName',
                    self.db_tables['Output'] + '.ResultUnit',
                    self.db_tables['Output'] + '.ResultValue',
                    self.db_tables_temp['Output'] + '.ResultValue']
        from_table = self.db_tables['Output'] + ',' + self.db_tables_temp['Output']
        where_clause = " WHERE (" + \
                       "{}.PartID={}.PartID AND ".format(self.db_tables['Output'], self.db_tables_temp['Output']) + \
                       "{}.TestCaseID={}.TestCaseID AND ".format(self.db_tables['Output'],
                                                                 self.db_tables_temp['Output']) + \
                       "{}.ResultName={}.ResultName AND ".format(self.db_tables['Output'],
                                                                 self.db_tables_temp['Output']) + \
                       "{}.ResultIndex={}.ResultIndex AND ".format(self.db_tables['Output'],
                                                                   self.db_tables_temp['Output']) + \
                       "CAST({}.ResultValue AS DECIMAL(30, 6))<>CAST({}.ResultValue AS DECIMAL(30, 6)) )".format(
                           self.db_tables['Output'], self.db_tables_temp['Output'])
        all_diff = self.db.query_in_db(col_name, from_table, where_clause)
        output_change = []
        for each in all_diff:
            sign1 = ''
            if number_or_string(each[self.db_tables['Output'] + '.ResultValue']):
                unchanged_value = float(each[self.db_tables['Output'] + '.ResultValue'])
                changed_value = float(each[self.db_tables_temp['Output'] + '.ResultValue'])
                changerat = (changed_value - unchanged_value) / (unchanged_value + 0.000000001) * 100
                if abs(changerat) > 0.1:
                    sign1 = ('+' if changerat > 0 else '-')
            else:
                unchanged_value = (each[self.db_tables['Output'] + '.ResultValue'])
                changed_value = (each[self.db_tables_temp['Output'] + '.ResultValue'])
                changerat = '-'
                sign1 = ''
            output_change.append([each[self.db_tables['Output'] + '.TestCaseID'],
                                  each[self.db_tables['Output'] + '.PartName'],
                                  each[self.db_tables['Output'] + '.ResultName'],
                                  each[self.db_tables['Output'] + '.ResultUnit'],
                                  unchanged_value,
                                  changed_value,
                                  changerat,
                                  sign1])
        print('----compare_db_with_xml------done --------')
        return output_change

    def compare_input(self):
        table_refer = self.db_tables
        table_temp = self.db_tables_temp
        col_name = [table_refer['PartAttrib'] + '.PartID',
                    table_refer['PartAttrib'] + '.PartAttribName',
                    table_refer['PartAttrib'] + '.AttribUnit',
                    table_refer['PartAttrib'] + '.AttribValue',
                    table_temp['PartAttrib'] + '.AttribValue']
        from_table = table_refer['PartAttrib'] + ', ' + table_temp['PartAttrib']
        where_clause = " WHERE (" + \
                       "{}.RomaxPath={}.RomaxPath AND ".format(table_refer['PartAttrib'], table_temp['PartAttrib']) + \
                       "{}.AttribValue<>{}.AttribValue  )".format(table_refer['PartAttrib'], table_temp['PartAttrib'])
        all_diff = self.db.query_in_db(col_name, from_table, where_clause)
        input_change_part = []
        input_change_assem = []
        for each in all_diff:
            col_assem = ['PartName', 'PartType']
            where_assem = " WHERE PartID=" + str(each[table_refer['PartAttrib'] + '.PartID'])
            assem_name = self.db.query_in_db(col_assem, table_refer['PartList'], where_assem)

            sign1 = ''
            if number_or_string(each[table_refer['PartAttrib'] + '.AttribValue']):
                unchanged_value1 = float(each[table_refer['PartAttrib'] + '.AttribValue'])
                changed_value1 = float(each[table_temp['PartAttrib'] + '.AttribValue'])
                changerat = (changed_value1 - unchanged_value1) / (unchanged_value1 + 0.000000001) * 100
                if abs(changerat) > 0.1:
                    sign1 = ('+' if changerat > 0 else '-')
                    unchanged_value = float(each[table_refer['PartAttrib'] + '.AttribValue'])
                    changed_value = float(each[table_temp['PartAttrib'] + '.AttribValue'])
                else:
                    continue
            else:
                unchanged_value = each[table_refer['PartAttrib'] + '.AttribValue']
                changed_value = each[table_temp['PartAttrib'] + '.AttribValue']
                changerat = '-'
                sign1 = ''
            input_change_part.append([each[table_refer['PartAttrib'] + '.PartID'],
                                      assem_name[0]['PartName'],
                                      each[table_refer['PartAttrib'] + '.PartAttribName'],
                                      each[table_refer['PartAttrib'] + '.AttribUnit'],
                                      unchanged_value,
                                      changed_value,
                                      changerat,
                                      assem_name[0]['PartType']])

        col_name = [table_refer['AssemAttrib'] + '.AssemID',
                    table_refer['AssemAttrib'] + '.AssemAttribName',
                    table_refer['AssemAttrib'] + '.AttribUnit',
                    table_refer['AssemAttrib'] + '.AttribValue',
                    table_temp['AssemAttrib'] + '.AttribValue']
        from_table = table_refer['AssemAttrib'] + ', ' + table_temp['AssemAttrib']
        where_clause = " WHERE (" + \
                       "{}.RomaxPath={}.RomaxPath AND ".format(table_refer['AssemAttrib'], table_temp['AssemAttrib']) + \
                       "{}.AttribValue<>{}.AttribValue  )".format(table_refer['AssemAttrib'], table_temp['AssemAttrib'])
        all_diff = self.db.query_in_db(col_name, from_table, where_clause)

        for each in all_diff:
            assemID = str(each[table_refer['AssemAttrib'] + '.AssemID'])
            col_assem = ['AssemName', 'AssemType']
            where_assem = " WHERE AssemID=" + assemID
            assem_name = self.db.query_in_db(col_assem, table_refer['AssemList'], where_assem)
            info_dic = {}
            col = ['AssemAttribName', 'AttribValue']
            where = f" WHERE AssemID = {assemID} AND AssemAttribName in ('Part1ID', 'Part2ID')"
            mount_info = self.db.query_in_db(col, table_refer['AssemAttrib'], where)
            for each_info in mount_info:
                info_dic[each_info['AssemAttribName']] = each_info['AttribValue']
            sign1 = ''
            if number_or_string(each[table_refer['AssemAttrib'] + '.AttribValue']):
                unchanged_value1 = float(each[table_refer['AssemAttrib'] + '.AttribValue'])
                changed_value1 = float(each[table_temp['AssemAttrib'] + '.AttribValue'])
                changerat = (changed_value1 - unchanged_value1) / (unchanged_value1 + 0.000000001) * 100
                if abs(changerat) > 0.1:
                    sign1 = ('+' if changerat > 0 else '-')
                    unchanged_value = float(each[table_refer['AssemAttrib'] + '.AttribValue'])
                    changed_value = float(each[table_temp['AssemAttrib'] + '.AttribValue'])
                else:
                    continue
            else:
                unchanged_value = each[table_refer['AssemAttrib'] + '.AttribValue']
                changed_value = each[table_temp['AssemAttrib'] + '.AttribValue']
                changerat = '-'
                sign1 = ''
            input_change_assem.append([each[table_refer['AssemAttrib'] + '.AssemID'],
                                       assem_name[0]['AssemName'],
                                       each[table_refer['AssemAttrib'] + '.AssemAttribName'],
                                       each[table_refer['AssemAttrib'] + '.AttribUnit'],
                                       unchanged_value,
                                       changed_value,
                                       changerat,
                                       assem_name[0]['AssemType'], info_dic['Part1ID'], info_dic['Part2ID']])
        print('----compare input------done --------')
        return input_change_part, input_change_assem

    def compare_evalutaion(self):
        eva_tabl = self.db_tables['Eva']
        part_tab = self.db_tables['PartList']
        eva_tabl_temp = self.db_tables_temp['Eva']
        diff = []
        col_name = [eva_tabl + '.TestCaseID',
                    eva_tabl + '.PartID',
                    eva_tabl + '.PartName',
                    eva_tabl + '.EvaluationName',
                    eva_tabl + '.EvaluationUnit',
                    eva_tabl + '.EvaluationValue',
                    eva_tabl + '.EvaluationInfo',
                    eva_tabl_temp + '.EvaluationValue']
        from_table = eva_tabl + ',' + eva_tabl_temp
        where_clause = " WHERE (" + \
                       "{}.PartID={}.PartID AND ".format(eva_tabl, eva_tabl_temp) + \
                       "{}.TestCaseID={}.TestCaseID AND ".format(eva_tabl, eva_tabl_temp) + \
                       "{}.EvaluationName={}.EvaluationName AND ".format(eva_tabl, eva_tabl_temp) + \
                       "CAST({}.EvaluationValue AS DECIMAL(30, 6))<>CAST({}.EvaluationValue AS DECIMAL(30, 6)) )" \
                       "ORDER BY TestCaseID,PartID;".format(eva_tabl, eva_tabl_temp)
        all_eva = self.db.query_in_db(col_name, from_table, where_clause)
        for each in all_eva:
            eva_1 = float(each[eva_tabl + '.EvaluationValue'])
            eva_2 = float(each[eva_tabl_temp + '.EvaluationValue'])
            changerat = (eva_2 - eva_1) / (eva_1 + 0.000000001) * 100
            if abs(changerat) > 0.1:
                part_type = self.db.query_in_db(['PartType'], part_tab, f" WHERE PartID = {each[eva_tabl + '.PartID']}")
                sign = ('+' if changerat > 0 else '-')
                diff.append([each[eva_tabl + '.TestCaseID'], each[eva_tabl + '.PartID'],
                             each[eva_tabl + '.PartName'], each[eva_tabl + '.EvaluationName'],
                             each[eva_tabl + '.EvaluationUnit'], eva_1, eva_2,
                             "{:.2f}".format(changerat), sign, each[eva_tabl + '.EvaluationInfo'],
                             part_type[0]['PartType']])
        return diff

    def compare_evacase(self):
        eva_tabl = self.db_tables['EvaCase']
        part_tab = self.db_tables['PartList']
        eva_tabl_temp = self.db_tables_temp['EvaCase']
        sim = self.db_tables['Output']
        sim_t = self.db_tables_temp['Output']
        col_name = [f'{eva_tabl}.EvaCaseID',
                    f' EvaName',
                    f'{eva_tabl}.Pass',
                    f'{eva_tabl}.EvaResult',
                    f'{sim}.PartName',
                    f'{eva_tabl_temp}.Pass',
                    f'{eva_tabl_temp}.EvaResult',
                    f'{sim_t}.PartName',
                    f'strcmp({eva_tabl}.pass, {eva_tabl_temp}.pass)']
        where_claus = f" inner join {eva_tabl_temp} USING (EvaCaseID) " \
                      f" inner join {self.prefix.ifka_testcase} USING (EvaCaseID) " \
                      f" inner join {sim} on ({sim}.ResultID = {eva_tabl}.ResultID)" \
                      f" inner join {sim_t} on ({sim_t}.ResultID ={eva_tabl_temp}.ResultID) "
        diff_result = self.db.query_in_db(col_name, eva_tabl, where_claus)
        diff = []
        for each in diff_result:
            diff_row = []
            for eachkey in col_name:
                if eachkey == f'strcmp({eva_tabl}.pass, {eva_tabl_temp}.pass)':
                    val = each[eachkey]
                    if 0 == float(val):
                        re_val = 'No change'
                    else:
                        re_val = 'Changed'
                    diff_row.append(re_val)
                else:
                    diff_row.append(each[eachkey])
            diff.append(diff_row.copy())

        return diff

    def compare_all(self, network):
        now = datetime.now()
        formatted_date = now.strftime('%Y-%m-%d')
        ID = self.initialize_db(self.prefix.Eva_Log) + 1
        _inputPart, _inputAssem = self.compare_input()
        _output = self.compare_output()
        _eva_all = self.compare_evalutaion()
        # _evacase = self.compare_evacase()
        _inputAll = []
        eva_to_insert = {}
        eva_db_part = []
        eva_db_assem = []
        for each_one in _inputPart:
            eva_to_insert = {}
            _inputAll.append(each_one[0:6])
            eva_to_insert['ID'] = ID
            ID += 1
            eva_to_insert['AssemID'] = 0
            eva_to_insert['PartID'] = each_one[0]
            eva_to_insert['TestCaseID'] = 0
            eva_to_insert['ParameterName'] = each_one[2]
            eva_to_insert['Value_Before'] = each_one[4]
            eva_to_insert['Value_After'] = each_one[5]
            eva_to_insert['Input_Output'] = 'Input'
            eva_to_insert['Relation_Path'] = ''
            eva_to_insert['UpdateDATE'] = formatted_date
            eva_to_insert['ParameterType'] = each_one[-1]
            eva_db_part.append(eva_to_insert.copy())

        for each_one in _inputAssem:
            eva_to_insert = {}
            _inputAll.append(each_one[0:6])
            eva_to_insert['ID'] = ID
            ID += 1
            eva_to_insert['AssemID'] = each_one[0]
            eva_to_insert['PartID'] = 0
            eva_to_insert['TestCaseID'] = 0
            eva_to_insert['ParameterName'] = each_one[2]
            eva_to_insert['Value_Before'] = each_one[4]
            eva_to_insert['Value_After'] = each_one[5]
            eva_to_insert['Input_Output'] = 'Input'
            eva_to_insert['Relation_Path'] = ''
            eva_to_insert['UpdateDATE'] = formatted_date
            eva_to_insert['part1ID'] = each_one[-2]
            eva_to_insert['part2ID'] = each_one[-1]
            eva_to_insert['ParameterType'] = each_one[-3]
            eva_db_assem.append(eva_to_insert.copy())

        eva_db = eva_db_part + eva_db_assem

        _eva = []
        for each_eva in _eva_all:
            eva_to_insert = {}
            eva_PartID = each_eva[1]
            eva_relation = []

            for each_input1 in eva_db_assem:
                input_ID = each_input1['ID']
                part1ID = each_input1['part1ID']
                part2ID = each_input1['part2ID']
                input_name = each_input1['ParameterName']
                input_type = each_input1['ParameterType']

                relationLen_temp = []
                partID_temp = []
                try:
                    relationLen1 = network.cal_path(part1ID, eva_PartID)
                    relationLen_temp.append(relationLen1)
                    partID_temp.append(part1ID)
                except:
                    continue
                try:
                    relationLen2 = network.cal_path(part2ID, eva_PartID)
                    relationLen_temp.append(relationLen2)
                    partID_temp.append(part2ID)
                except:
                    continue
                relationLen = min(relationLen_temp)
                # [input_AssemID,input_type, input_name,relationLen, each_eva[2], each_eva[3],  each_eva[-2]])
                # [input_AssemID, input_type, input_name,relationLen]
                eva_relation.append([input_ID, relationLen])

            for each_input2 in eva_db_part:
                input_ID = each_input2['ID']
                input_PartID = each_input2['PartID']
                input_name = each_input2['ParameterName']
                input_type = each_input2['ParameterType']
                relationLen = network.cal_path(input_PartID, eva_PartID)
                # [input_AssemID,input_type, input_name,relationLen, each_eva[2], each_eva[3],  each_eva[-2]])
                # [input_PartID, input_type, input_name,relationLen]
                eva_relation.append([input_ID, relationLen])
            realtion_path = json.dumps(eva_relation)
            print(realtion_path)
            eva_to_insert['ID'] = ID
            ID += 1
            eva_to_insert['AssemID'] = 0
            eva_to_insert['PartID'] = eva_PartID
            eva_to_insert['TestCaseID'] = each_eva[0]
            eva_to_insert['ParameterName'] = each_eva[3]
            eva_to_insert['Value_Before'] = each_eva[6]
            eva_to_insert['Value_After'] = each_eva[7]
            eva_to_insert['Input_Output'] = 'Output'
            eva_to_insert['Relation_Path'] = realtion_path
            eva_to_insert['UpdateDATE'] = formatted_date
            eva_to_insert['ParameterType'] = each_eva[-1] + '-' + each_eva[-2]
            eva_db.append(eva_to_insert.copy())
            each_eva.pop(1)
            each_eva.pop(-1)
            _eva.append(each_eva)
        col = list(eva_to_insert.keys())
        self.db.insertall_in_db(col, eva_db, self.prefix.Eva_Log)
        self.db.mydb.commit()
        return _inputAll, _output, _eva

    def initialize_db(self, table):
        # table = self.prefix.Adams_Result_Table
        col_name = ['ID INT AUTO_INCREMENT PRIMARY KEY',
                    'PartID INT ',
                    'AssemID INT',
                    'TestCaseID INT',
                    'ParameterName VARCHAR(50)',
                    'ParameterType  VARCHAR(50)',
                    'Value_Before VARCHAR(30)',
                    'Value_After VARCHAR(30)',
                    'Input_Output VARCHAR(10)',
                    'Relation_Path TEXT',
                    'UpdateDATE DATE']
        self.db.create_table(table, col_name)
        col = ['COUNT(*)']
        where = ''
        _result = self.db.query_in_db(col, table, where)
        return _result[0]['COUNT(*)']


if __name__ == '__main__':
    from All_prefix import prefix_info
    from My_DB_Connector import db_connecotor
    from Read_Database import readDb
    from Draw_network import draw_network

    prfix = prefix_info()
    db = db_connecotor()
    db.build_connector()
    input_table = prfix.db_tabels()

    data = readDb(prfix, db)
    data.read_all(input_table, ['1'])
    test = draw_network()
    test.add_edge(data)
    compare_test = compare_db(prfix, db)
    inputAll, _output, _eva, _evacase = compare_test.compare_all(test)
    print(_evacase)
    # compare_test.compare_all(test)
    # db.commit_it()
    # print(compare_test.compare_all())
    # print('1')
