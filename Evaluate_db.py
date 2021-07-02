

class evaluation_db():
    def __init__(self, pref, db):
        # ---------------Initializing----------------------------------------------------
        self.prefix = pref
        self.db = db

    def run(self, tables, TestCaseid='*'):
        testid=[]
        if TestCaseid == '*':
            where_clause = " "
        else:
            seperator = ','
            where_clause = ' WHERE TestCaseID in (' + seperator.join(TestCaseid) + ')'
        Testcase_name = ['TestCaseID', 'InputLoad', 'OutputLoad']
        Testcaseid_query = self.db.query_in_db(Testcase_name, self.prefix.Test_Plan, where_clause)
        for each in Testcaseid_query:
            testid.append(str(each['TestCaseID']))
        self.initialize_table(tables)
        self.rmx_output_evalutaion(tables, testid)
        self.pv_output_evalution(tables, testid)
        self.db.mydb.commit()

    def initialize_table(self, db_table):
        self.db.db_cursor.execute("CREATE TABLE IF NOT EXISTS " + db_table['Eva'] + " "
                                     "(EvaID INT AUTO_INCREMENT PRIMARY KEY, "
                                     "TestCaseID INT, "
                                     "PartID INT, "
                                     "PartName VARCHAR(255), "
                                     "EvaluationName VARCHAR(255), "
                                     "EvaluationValue VARCHAR(255), "
                                     "EvaluationUnit VARCHAR(20), "
                                     "EvaluationInfo VARCHAR(255), "
                                     "RomaxID VARCHAR(100))")

        DELETE_rows = "Delete FROM " + db_table['Eva']
        self.db.db_cursor.execute(DELETE_rows)

    def rmx_output_evalutaion(self, db_table, TestCassIDs):
        to_evaluate1 = {}
        to_evaluate2 = {}

        # to_evaluate1.update({"MaxBend": [" ResultName in ('BendingLeft','BendingRight')", "Lifetime"],
        #                      "MaxTension": [" ResultName in ('TensionLeft','TensionRight')","Lifetime"],
        #                      "MaxTorsion": [" ResultName in ('TorsionLeft','TorsionRight')","Lifetime"]})
        # self.max_OnePart(to_evaluate1, db_table, TestCassIDs)
        to_evaluate1.update({"ShaftSafetyFactor": ["ResultName = 'ShaftSafetyFactor'", "Lifetime"]})
        self.equalto(to_evaluate1, db_table, TestCassIDs)
        to_evaluate2.update({"BendingDamage": ["ResultName = 'BendingDamage' ", "Lifetime"],
                             "BendingStress": ["ResultName = 'BendingStress' ", "Lifetime"],
                             "ContactDamage": ["ResultName = 'ContactDamage' ", "Lifetime"],
                             "ContactStress": ["ResultName = 'ContactStress' ", "Lifetime"],
                             "SafetyFactorInBending": ["ResultName = 'SafetyFactorInBending'", "Lifetime"],
                             "SafetyFactorInContact": ["ResultName = 'SafetyFactorInContact'", "Lifetime"]})
        for each in to_evaluate2:
            to_evaluate2[each][0] = to_evaluate2[each][0] + f" AND (PartID, TestCaseID) in (SELECT PartID, TestCaseID " \
                f"FROM {db_table['Output']} WHERE ResultName = 'Torque' AND abs(CAST(ResultValue AS DECIMAL(30, 1)))>1)"

        to_evaluate2.update({"IsoLifeSec": [" ResultName ='IsoLifeSec'", "Lifetime"],
                             "IsoDamage" : [" ResultName ='IsoDamage'", "Lifetime"]})
        self.equalto(to_evaluate2, db_table, TestCassIDs)

    def pv_output_evalution(self, db_table, TestCassIDs):
        to_evaluate = {"PowerLoss": ["ResultType = 'PowerLoss'", "PowerLoss"]}
        self.sum_OnePart(to_evaluate, db_table, TestCassIDs)

    def adams_output_evalution(self, db_table, TestCassIDs):
        to_evaluate = {"MaxTE": ["ResultName = 'MaxTE'", "NVH"],
                       "Kv": ["ResultName = 'Kv'", "NVH"]}
        self.equalto(to_evaluate, db_table, TestCassIDs)

    def equalto(self, to_evaluate, db_table, TestCassIDs):
        IDs = ", ".join(TestCassIDs)
        for key in to_evaluate:
            insert_eva = f" INSERT INTO {db_table['Eva']} " \
                         f" (EvaID,TestCaseID, PartID, PartName,EvaluationUnit,EvaluationName,EvaluationValue, EvaluationInfo) "\
                         f" SELECT ResultID,TestCaseID,PartID,PartName, ResultUnit,'{key}' , ResultValue , '{to_evaluate[key][1]}'"\
                         f" FROM {db_table['Output']}" \
                         f" WHERE {to_evaluate[key][0]} AND TestCaseID in ({IDs}) " +  \
                         f" group by TestCaseID,PartID;"
            self.db.db_cursor.execute(insert_eva)


    def max_OnePart (self, to_evaluate, db_table, TestCassIDs):
        IDs = ", ".join(TestCassIDs)
        for key in to_evaluate:
            insert_eva = f" INSERT INTO {db_table['Eva']} " \
                         f" (EvaID,TestCaseID, PartID, PartName,EvaluationUnit,EvaluationName,EvaluationValue, EvaluationInfo) "\
                         f" SELECT ResultID,TestCaseID,PartID,PartName, ResultUnit,'{key}', max(abs(CAST(ResultValue AS DECIMAL(40, 6)))),'{to_evaluate[key][1]}'"\
                         f" FROM {db_table['Output']}" \
                         f" WHERE {to_evaluate[key][0]} AND TestCaseID in ({IDs}) " +  \
                         f" group by TestCaseID,PartID;"
            self.db.db_cursor.execute(insert_eva)


    def sum_OnePart (self, to_evaluate, db_table, TestCassIDs):
        IDs = ", ".join(TestCassIDs)
        for key in to_evaluate:
            insert_eva = f" INSERT INTO {db_table['Eva']} " \
                             f" (EvaID,TestCaseID, PartID, PartName,EvaluationUnit,EvaluationName,EvaluationValue, EvaluationInfo) " \
                             f" SELECT ResultID,TestCaseID,PartID,PartName, ResultUnit,'{key}', sum(abs(CAST(ResultValue AS DECIMAL(40, 6)))), '{to_evaluate[key][1]}'" \
                             f" FROM {db_table['Output']}" \
                             f" WHERE {to_evaluate[key][0]} AND TestCaseID in ({IDs}) " + \
                         f" group by TestCaseID,PartID;"
            self.db.db_cursor.execute(insert_eva)






if __name__ == '__main__':
    from All_prefix import prefix_info
    from My_DB_Connector import db_connecotor
    pref= prefix_info()
    db = db_connecotor()
    db.build_connector()
    eva = evaluation_db(pref, db)
    tables = pref.db_tabels_temp()
    ids = ['1']
    eva.run(pref.db_tabels_temp())
    # eva.evaTable(pref.db_tabels())



