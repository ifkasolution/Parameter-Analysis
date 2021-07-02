import mysql.connector


class new_connector():
    def __init__(self, dbconfig):
        self.dbconfig = dbconfig
        self.mydb = mysql.connector.connect(**self.dbconfig)
        self.mydb.autocommit = True
        self.db_cursor = self.mydb.cursor()

    def insertall_in_db(self, col_list, value_list_dict, to_table):
        insert_value = []
        value_holder = []
        for idx in range(len(col_list)):
            value_holder.append('%s')

        for each in value_list_dict:
            insert_row = []
            for eachkey in col_list:
                insert_row.append(each[eachkey])
            insert_value.append(tuple(insert_row.copy()))
        separator = ', '
        query_insert = "INSERT INTO " + to_table + " (" + separator.join(col_list) + ") values (" + separator.join(
            value_holder) + ")"
        self.db_cursor.executemany(query_insert, insert_value)

    def commit_it(self):
        self.db_cursor.close()


class db_connecotor:
    def __init__(self):

        self.dbconfig = {
            'host': "localhost",
            'user': "root",
            'passwd': "mysql",
            'database': "getriebe"
        }

    # """
    #         self.dbconfig = {
    #             'host': "ifka-database-2020.c2rbfs5fafu9.eu-central-1.rds.amazonaws.com",
    #             'user': "ifka-user",
    #             'passwd': "ifka?gogo123",
    #             'database': "getriebe"
    #         }
    #         """
    def build_connector(self):
        try:
            self.mydb = mysql.connector.connect(**self.dbconfig)
            self.db_cursor = self.mydb.cursor()
            _find_database = True
        except IOError:
            self.dbconfig.pop('database')
            self.mydb = mysql.connector.connect(**self.dbconfig)
            self.db_cursor = self.mydb.cursor()
            _find_database = False
        return _find_database

    def query_in_db(self, col_list, from_table, where_clause):
        separator = ', '
        name_list_all = separator.join(col_list)
        query_all_tests = "Select " + name_list_all + " FROM " + from_table + where_clause
        return self.execute_script_in_db(query_all_tests, col_list)

    def query_in_db_advanced(self, query):
        self.db_cursor.execute(query)
        all_row = self.db_cursor.fetchall()
        return all_row

    def query_in_db_with_script(self, with_col, with_from, with_clause, col_list, where_clause):
        separator = ', '
        with_col_all = separator.join(with_col)
        with_query = f"WITH with_table_temp AS ( SELECT {with_col_all} FROM {with_from} {with_clause} )"
        name_list_all = separator.join(col_list)
        query_all_tests = with_query + "Select " + name_list_all + " FROM with_table_temp " + where_clause
        self.execute_script_in_db(query_all_tests, col_list)

    def execute_script_in_db(self, query_script, col_list):
        global all_row
        for result in self.db_cursor.execute(query_script, multi=True):
            if result.with_rows:
                all_row = result.fetchall()
            else:
                print(".")
        query_result = []
        for each in all_row:
            query_result.append(dict(zip(col_list, each)))
        return query_result

    def insertall_in_db(self, col_list, value_list_dict, to_table):
        insert_value = []
        value_holder = []
        for idx in range(len(col_list)):
            value_holder.append('%s')

        for each in value_list_dict:
            insert_row = []
            for eachkey in col_list:
                insert_row.append(each[eachkey])
            insert_value.append(tuple(insert_row.copy()))
        separator = ', '
        query_insert = "INSERT INTO " + to_table + " (" + separator.join(col_list) + ") values (" \
                       + separator.join(value_holder) + ")"
        self.db_cursor.executemany(query_insert, insert_value)

    def insert_data_in_db(self, value_dict, to_table):
        insert_value = []
        value_holder = []
        separator = ', '
        col_list = list(value_dict.keys())
        row_num = len(value_dict[col_list[0]])
        for each in range(len(col_list)):
            value_holder.append('%s')
        query_insert = "INSERT INTO " + to_table + " (" + separator.join(col_list) + ") VALUES (" + separator.join(
            value_holder) + ")"
        for idx_row in range(row_num):
            insert_row = []
            for each in value_dict:
                insert_row.append(value_dict[each][idx_row])
            insert_value.append(tuple(insert_row.copy()))
        self.db_cursor.executemany(query_insert, insert_value)

    def insert_output_in_db(self, col_list, value_list_dict, to_table):
        insert_value = []
        value_holder = []
        for idx in range(len(col_list)):
            value_holder.append('%s')
        separator = ', '
        query_insert = "INSERT INTO " + to_table + " (" + separator.join(col_list) + ") VALUES (" + separator.join(
            value_holder) + ")"
        for each in value_list_dict:
            insert_row = []
            for eachkey in col_list:
                insert_row.append(each[eachkey])
            self.db_cursor.execute(query_insert, tuple(insert_row.copy()))

    def table_exist(self, table):
        self.db_cursor.execute("SHOW TABLES LIKE '{}';".format(table))
        c = self.db_cursor.fetchone()
        if c:
            return True
        else:
            return False

    def drop_table(self, table):
        self.db_cursor.execute("DROP TABLE IF EXISTS {};".format(table))

    def create_table(self, table, col):
        self.db_cursor.execute("CREATE TABLE IF NOT EXISTS {} ({})".format(table, ", ".join(col)))

    def commit_it(self):
        self.mydb.commit()


if __name__ == '__main__':
    db = db_connecotor()
    db.build_connector()
    # db.db_cursor.execute("Delete FROM romax_mapping.read_xml")
    # db.mydb.commit()
