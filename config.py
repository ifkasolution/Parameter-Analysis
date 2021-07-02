import csv
import configparser
import os
import types


class IfkaConfig:
    def __init__(self, prefix_class, db_class):
        self.db = db_class
        self.prefix = prefix_class
        self.conf = configparser.ConfigParser()
        self.conf_file = self.prefix.conf_file
        self.initialisation()

    def initialisation(self):
        self.import_rmx_map()
        self.read()

    def write_confi(self):
        conf_new = configparser.ConfigParser()
        for each in self.prefix.conf_data:
            conf_new.add_section(each)
            for each_item in self.prefix.conf_data[each]:
                conf_new.set(each, each_item, self.prefix.conf_data[each][each_item])
        conf_new.write(open(self.conf_file, "w"))

    def read(self):
        self.conf.read(self.conf_file, encoding="utf-8")
        sections = self.conf.sections()
        if len(sections) == 0:
            print('Create ini-file')
            self.write_confi()
            self.conf.read(self.conf_file, encoding="utf-8")

        for each in self.prefix.conf_data:
            for each_item in self.prefix.conf_data[each]:
                try:
                    self.prefix.conf_data[each][each_item] = self.conf[each][each_item]
                except:
                    self.prefix.conf_data[each][each_item] = ""
        rmx_software_exist = os.path.exists(self.prefix.conf_data['rmx']['software'])
        rmx_server_exist = os.path.exists(self.prefix.conf_data['rmx']['server'])
        self.prefix.Software_Name = self.prefix.conf_data['rmx']["software"]
        self.prefix.rmx_server = self.prefix.conf_data['rmx']["server"]
        self.prefix.Gearbox_name = self.prefix.conf_data['rmx']["modelName"]
        self.prefix.rmx_file = self.prefix.conf_data['rmx']["modelPath"]
        if rmx_software_exist and rmx_server_exist:
            check_pass_file = True
            print('All file path OK')
        else:
            check_pass_file = False
            print('Check file path!')
        return check_pass_file

    def import_rmx_map(self):
        self.db.db_cursor.execute("CREATE DATABASE IF NOT EXISTS " + self.prefix.database)
        self.db.db_cursor.execute("CREATE DATABASE IF NOT EXISTS " + self.prefix.rmx_map)
        self.db.db_cursor.execute(f"CREATE TABLE IF NOT EXISTS {self.prefix.romax_mapping_read_xml_sql} "
                                  "(MapID INT AUTO_INCREMENT PRIMARY KEY, "
                                  "xPath TEXT,"
                                  "Attribute_Name TEXT,"
                                  "Romax_Name TEXT,"
                                  "Attribute_Type TEXT,"
                                  "Use_Prefix TEXT,"
                                  "Romax_Version TEXT,"
                                  "Find_Parent_By TEXT,"
                                  "Unit TEXT,"
                                  "SubMapID INT)")
        self.db.db_cursor.execute(f"CREATE TABLE IF NOT EXISTS {self.prefix.romax_mapping_output_xml_sql} "
                                  "(MapID INT AUTO_INCREMENT PRIMARY KEY, "
                                  "xPath TEXT,"
                                  "Attribute_Name TEXT,"
                                  "Romax_Name TEXT,"
                                  "Attribute_Type TEXT,"
                                  "Use_Prefix TEXT,"
                                  "Romax_Version TEXT,"
                                  "Find_Parent_By TEXT,"
                                  "Unit TEXT,"
                                  "SubMapID INT)")
        # self.db.db_cursor.execute(f"CREATE TABLE IF NOT EXISTS {self.prefix.romax_mapping_attribute_name_sql} "
        #                           "(AttributeNameID INT AUTO_INCREMENT PRIMARY KEY, "
        #                           "PartAttribName VARCHAR(255), "
        #                           "PartAttribName_rmx_input VARCHAR(255))")
        # self.db.db_cursor.execute(f"CREATE TABLE IF NOT EXISTS {self.prefix.romax_mapping_unit_sql} "
        #                           "(UnitID INT AUTO_INCREMENT PRIMARY KEY, "
        #                           "AttribUnit VARCHAR(255), "
        #                           "AttribUnit_rmx_input VARCHAR(255), "
        #                           "multiplier VARCHAR(255), "
        #                           "type VARCHAR(255))")
        self.db.db_cursor.execute(f"CREATE TABLE IF NOT EXISTS {self.prefix.romax_mapping_variable_sql} "
                                  "(BatchID INT AUTO_INCREMENT PRIMARY KEY, "
                                  "Name VARCHAR(255), "
                                  "MapID INT, "
                                  "VariableType VARCHAR(255), "
                                  "AssemType VARCHAR(255), "
                                  "PartType VARCHAR(255), "
                                  "NameInXml VARCHAR(255), "
                                  "TypeInXml VARCHAR(255), "
                                  "UnitInXml VARCHAR(255))")
        self.db.db_cursor.execute(f"CREATE TABLE IF NOT EXISTS {self.prefix.romax_mapping_result_sql} "
                                  "(BatchID INT AUTO_INCREMENT PRIMARY KEY, "
                                  "Name VARCHAR(255), "
                                  "MapID INT, "
                                  "ResultType VARCHAR(255), "
                                  "AssemType VARCHAR(255), "
                                  "PartType VARCHAR(255), "
                                  "NameInXml VARCHAR(255), "
                                  "UnitInXml VARCHAR(255))")
        self.db.db_cursor.execute(f"CREATE TABLE IF NOT EXISTS {self.prefix.romax_mapping_action_sql} "
                                  "(BatchID INT AUTO_INCREMENT PRIMARY KEY, "
                                  "Name VARCHAR(255), "
                                  "ActionType VARCHAR(255), "
                                  "AssemType VARCHAR(255), "
                                  "PartType VARCHAR(255), "
                                  "NameInXml VARCHAR(255), "
                                  "ArgumentValue1 VARCHAR(255), "
                                  "ArgumentValue2 VARCHAR(255) ,"
                                  "ArgumentValue3 VARCHAR(255) ,"
                                  "ArgumentValue4 VARCHAR(255))")

        csv_path_list = [self.prefix.romax_mapping_read_xml_csv, self.prefix.romax_mapping_output_xml_csv,
                         # self.prefix.romax_mapping_attribute_name_csv, self.prefix.romax_mapping_unit_csv,
                         self.prefix.romax_mapping_variable_csv, self.prefix.romax_mapping_result_csv,
                         self.prefix.romax_mapping_action_csv]
        sql_path_list = [self.prefix.romax_mapping_read_xml_sql, self.prefix.romax_mapping_output_xml_sql,
                         # self.prefix.romax_mapping_attribute_name_sql, self.prefix.romax_mapping_unit_sql,
                         self.prefix.romax_mapping_variable_sql, self.prefix.romax_mapping_result_sql,
                         self.prefix.romax_mapping_action_sql]
        self.read_csv_into_sql(csv_path_list, sql_path_list)
        self.db.commit_it()

    def read_csv_into_sql(self, csv_path_list, sql_path_list):
        for csv_path, sql_path in zip(csv_path_list, sql_path_list):
            self.db.db_cursor.execute(f"Delete FROM {sql_path}")
            with open(csv_path, encoding='utf-8-sig') as csv_file_toread:
                csv_reader_readed = csv.reader(csv_file_toread, delimiter=';', quotechar='"')
                rows = [row for row in csv_reader_readed]
                col = rows[0]
                read_line = [dict(zip(col, row)) for row in rows[1:]]
                self.db.insertall_in_db(col, read_line, sql_path)
