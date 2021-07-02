import matlab.engine
import os
from All_prefix import prefix_info
from datetime import datetime
from My_DB_Connector import db_connecotor
from numpy import array,pi,cos


class mlab_fun():
    def __init__(self,prefix,db):
        self.eng=matlab.engine.start_matlab()
        self.eng.addpath( os.path.abspath(os.getcwd())+'\MATLAB',nargout=0)
        self.db = db
        self.prefix =prefix
        self.gear_mesh = []
        self.gear = {}
        self.bearing = {}
        self.formatted_date =''
        self.db_table = self.prefix.db_tabels()
        # self.output = self.prefix.output

    def pv_Sim(self, tempOrNot, TestCaseid='*'):
        print('Launching Matlab----------')
        if tempOrNot == 0:
            self.db_table = self.prefix.db_tabels()
        else:
            self.db_table = self.prefix.db_tabels_temp()

        now = datetime.now()
        self.formatted_date = now.strftime('%Y-%m-%d')
        if TestCaseid == '*':
            where_clause = " "
        else:
            seperator = ','
            where_clause = ' WHERE TestCaseID in (' + seperator.join(TestCaseid) + ')'
        Testcase_name = ['TestCaseID', 'RomaxPath']
        Testcaseid_query = self.db.query_in_db(Testcase_name, self.prefix.Test_Plan, where_clause)
        testCaseAll = []
        for each in Testcaseid_query:
            testCaseAll.append(each['TestCaseID'])
        self.read_db(testCaseAll)
        output = []
        output = output + self.gear_mesh_loss()
        output = output + self.gear_churn_loss()
        output = output + self.gear_wind_loss()
        output = output + self.bearing_loss()
        Colm_to_insert = ["TestCaseID", "PartID", "PartName", "ResultName",
                          "ResultValue", "ResultUnit", "ResultType", "UpdateDATE"]
        self.db.insertall_in_db(Colm_to_insert, output,  self.db_table['Output'])
        self.db.mydb.commit()
        print('Writing Matlab data to DB----------')



    def read_db(self,testCase):
        self.all_shafts=self.read_shaft_info()
        col_name = ['PartID', 'PartName', 'PartType']
        where_type = " WHERE PartType = 'HelicalGear'"
        all_gears = self.db.query_in_db(col_name, self.db_table['PartList'], where_type)
        gear = {}
        for each_gear in all_gears:
            partID = each_gear['PartID']
            mount = {}
            gear_attri = [ 'TipDiameter', 'RootDiameter', 'BaseDiameter', 'FaceWidth',
                           'HelixAngle', 'NumberOfTeeth', 'NormalModule','FlankSurfaceRoughness','Lubricant','LubricantLevel']
            mount_type = 'GearMountDetailFeature'
            mount = self.read_part_attrib(partID, gear_attri, mount_type)
            mount['PartName'] = each_gear['PartName']
            mount['InitialAngel'] = 0
            gear[each_gear['PartID']] = mount.copy()
            lubricant = gear[each_gear['PartID']]['Lubricant']
            col_lub = ['AssemAttribName', 'AttribValue']
            where = " WHERE AssemAttribName in ('KinematicViscosity1','KinematicViscosity2','Density') AND " \
                    " AssemID = (SELECT AssemID FROM {} WHERE AssemName = '{}' AND AssemType ='LubricantData')".format(self.prefix.assembly,lubricant)
            all_lub_data = self.db.query_in_db(col_lub,self.db_table['AssemAttrib'],where)
            for each_lub in all_lub_data:
                gear[each_gear['PartID']]['Lub'+each_lub['AssemAttribName']]=each_lub['AttribValue']
            TestCase_gear = {}
            for each in testCase:
                temper_query = self.db.query_in_db(['Temperature'],self.db_table['TestPlan']," WHERE TestCaseID ="+str(each))
                TestCase_gear[each]={'Temperature':temper_query[0]['Temperature']}
            col=['TestCaseID','ResultName','ResultValue']
            sep = ','
            testCase_strings = [str(integer) for integer in testCase]
            where =" WHERE ResultName in ('Torque', 'Speed') AND PartID = {} AND TestCaseID in ({})".format(partID,sep.join(testCase_strings))
            result = self.db.query_in_db(col, self.db_table['Output'], where)
            for each in result:
                TestCase_gear[int(each['TestCaseID'])][each['ResultName']]=each['ResultValue']
            gear[each_gear['PartID']]['TestCase'] = TestCase_gear
        col2 = ['AssemID']
        where = " WHERE AssemType ='DetailedHelicalGearMesh'"
        mesh_info = []
        allmesh = self.db.query_in_db(col2, self.db_table['AssemList'], where)
        for each in allmesh:
            col = ['AssemAttribName', 'AttribValue']
            where = " WHERE AssemID =" + str(each['AssemID']) + " AND AssemAttribName in ('Part1ID', 'Part2ID'," \
                                            "'WorkingCentreDistance','WorkingPressureAngle','WorkingFaceWidth')"
            mesh_info_db = self.db.query_in_db(col, self.db_table['AssemAttrib'], where)
            mesh_info_dict={}
            for each_info in mesh_info_db:
                mesh_info_dict[each_info['AssemAttribName']] = each_info['AttribValue']
            mesh_info.append(mesh_info_dict.copy())
        self.gear =gear
        self.gear_mesh = mesh_info
        # Bearing query
        col_name = ['PartID', 'PartName', 'PartType']
        where_type = " WHERE PartType = 'Bearing'"
        all_results = self.db.query_in_db(col_name, self.db_table['PartList'], where_type)
        bearing_all = {}
        for each in all_results:
            Bearing = {}
            partID = each['PartID']
            Bearing['PartName']=each['PartName']
            col = ['PartAttribName','AttribValue']
            where  = " WHERE PartAttribName in ('BearingData', 'Lubricant', 'LubricantLevel') " \
                     " AND PartID = {}".format(str(partID))
            bearing_query = self.db.query_in_db(col, self.db_table['PartAttrib'], where)
            for each in bearing_query:
                Bearing[each['PartAttribName']]=each['AttribValue']
            col_name = ['AssemType','AssemID']
            where = " WHERE AssemName = '{}'".format(Bearing['BearingData'])
            database = self.db.query_in_db(col_name,self.db_table['AssemList'],where)
            Bearing['BearingType'] = database[0]['AssemType'].replace('SSD', '')
            Bearing['BearingType'] = Bearing['BearingType'].replace('Data', '')
            col = ['AssemAttribName', 'AttribValue']
            attrib = ['Od', 'Bore', 'Width','StaticCapacity']
            seperator = "','"
            where = " WHERE AssemID = " + str(database[0]['AssemID']) + " AND AssemAttribName in ('" + seperator.join(
                attrib) + "')"
            info = self.db.query_in_db(col, self.db_table['AssemAttrib'], where)
            for each in info:
                Bearing[each['AssemAttribName']] = each['AttribValue']
            Bearing.update(self.read_part_attrib(partID, [], 'BearingMountFeature'))
            lubricant = Bearing['Lubricant']
            col_lub = ['AssemAttribName', 'AttribValue']
            where = " WHERE AssemAttribName in ('KinematicViscosity1','KinematicViscosity2','Density') AND " \
                    " AssemID = (SELECT AssemID FROM {} WHERE AssemName = '{}' AND AssemType ='LubricantData')".format(
                self.prefix.assembly, lubricant)
            all_lub_data = self.db.query_in_db(col_lub, self.db_table['AssemAttrib'], where)
            for each_lub in all_lub_data:
                Bearing['Lub' + each_lub['AssemAttribName']] = each_lub['AttribValue']
            TestCase_bear = {}
            for each in testCase:
                temper_query = self.db.query_in_db(['Temperature'], self.db_table['TestPlan'],
                                                   " WHERE TestCaseID =" + str(each))
                TestCase_bear[each] = {'Temperature': temper_query[0]['Temperature']}
            col = ['TestCaseID', 'ResultName', 'ResultValue']
            sep = ','
            testCase_strings = [str(integer) for integer in testCase]
            where = " WHERE ResultName in ('RotationSpeed','RadialLoadMagnitude', 'Load3DZ') " \
                    "AND PartID = {} AND TestCaseID in ({})".format(partID,sep.join(testCase_strings))
            result = self.db.query_in_db(col, self.db_table['Output'], where)
            for each in result:
                TestCase_bear[int(each['TestCaseID'])][each['ResultName']] = each['ResultValue']
            Bearing['TestCase'] = TestCase_bear
            bearing_all[partID] = Bearing.copy()
        self.bearing= bearing_all
        # print ('bearing info',bearing_all)
        # return bearing_all


    def read_shaft_info(self):
        col_name = ['PartID', 'PartName', 'PartType']
        where_type = " WHERE PartType = 'Shaft'"
        all_results = self.db.query_in_db(col_name, self.db_table['PartList'], where_type)
        shaft_all={}
        for each in all_results:
            shaft = {}
            col = ['PartAttribName', 'AttribValue','AttribIdx']
            where = " WHERE PartID = " + str(each['PartID'])+ " AND PartAttribName " \
                    "in ('SectionsCount','AxisDirectionX','AxisDirectionY','AxisDirectionZ','OriginX','OriginY','OriginZ')"
            shaft_info = self.db.query_in_db(col, self.db_table['PartAttrib'], where)
            for each_info in shaft_info:
                shaft [each_info ['PartAttribName']] = each_info ['AttribValue']
            SectionsCount = int(shaft['SectionsCount'])
            shaft ['Position'] = array([float(shaft ['OriginX']), float(shaft ['OriginY']),
                                           float(shaft ['OriginZ'])])
            shaft ['Dir'] = array([float(shaft ['AxisDirectionX'] ), float(shaft ['AxisDirectionY']),
                                      float(shaft ['AxisDirectionZ'])])
            col = ['PartAttribName', 'AttribValue', 'AttribIdx']
            where = " WHERE PartID = " + str(each ['PartID']) + " AND PartAttribName in " \
                   "('LeftDiameter','LeftBoreDiameter','LeftPosition','RightPosition')"
            shaft_info = self.db.query_in_db(col, self.db_table['PartAttrib'], where)
            for each_info in shaft_info:
                if not each_info['PartAttribName'] in shaft.keys():
                    shaft[each_info['PartAttribName']] =[0 for i in range(SectionsCount)]
                shaft [each_info ['PartAttribName']][int(each_info ['AttribIdx'])] = float(each_info ['AttribValue'])
            shaft_all[each['PartID']] = shaft.copy()
        return shaft_all

    def read_part_attrib(self,partID,attrib,mount_type):
        info_dic={}
        if len(attrib) > 0:
            col = ['PartAttribName', 'AttribValue']
            seperator = "','"
            where = " WHERE PartID = " + str(partID) + " AND PartAttribName in ('" + seperator.join(attrib) + "')"
            info = self.db.query_in_db(col, self.db_table['PartAttrib'], where)
            for each in info:
                info_dic [each ['PartAttribName']] = each ['AttribValue']
        col = ['AssemAttribName', 'AttribValue']
        where = " WHERE AssemID = (Select AssemID FROM " + self.prefix.Assem_Attribute_List + \
                " WHERE AssemAttribName = 'Part2ID' AND AttribType ='"+ mount_type+"' AND AttribValue ='" + str(partID) + "')"
        mount_info = self.db.query_in_db(col, self.db_table['AssemAttrib'], where)
        for each in mount_info:
            info_dic [each ['AssemAttribName']] = each ['AttribValue']
        shaft_pos = self.all_shafts[int(info_dic['Part1ID'])]['Position']
        shaft_dir = self.all_shafts[int(info_dic['Part1ID'])]['Dir']
        Gear_pos_cor = shaft_pos + shaft_dir * float(info_dic ['Offset'])
        info_dic ['ShaftDir'] = shaft_dir
        info_dic ['Position'] = Gear_pos_cor
        return info_dic

    def gear_mesh_loss(self):
        output=[]
        for each in self.gear_mesh:
            gear = {}
            gear['a']   = float(each['WorkingCentreDistance'])*1000
            gear['z1']  = float(self.gear[int(each['Part1ID'])]['NumberOfTeeth'])
            gear['z2']  = float(self.gear[int(each['Part2ID'])]['NumberOfTeeth'])
            gear['da1'] = float(self.gear[int(each['Part1ID'])]['TipDiameter'])*1000
            gear['df1'] = float(self.gear[int(each['Part1ID'])]['RootDiameter'])*1000
            gear['da2'] = float(self.gear[int(each['Part2ID'])]['TipDiameter'])*1000
            gear['df2'] = float(self.gear[int(each['Part2ID'])]['RootDiameter'])*1000
            gear['m']   = float(self.gear[int(each['Part1ID'])]['NormalModule'])*1000
            gear['beta'] = float(self.gear[int(each['Part1ID'])]['HelixAngle'])/2/pi*360
            gear['ra']  = float(self.gear[int(each['Part1ID'])]['FlankSurfaceRoughness'])*10**6
            gear['aw']  = float(each['WorkingPressureAngle'])/2/pi*360
            gear['b']   = float(each['WorkingFaceWidth'])*1000
            nue1 = float(self.gear[int(each['Part1ID'])]['LubKinematicViscosity1'])*10**6
            nue2 = float(self.gear[int(each['Part1ID'])]['LubKinematicViscosity2'])*10**6
            Rho = float(self.gear[int(each['Part1ID'])]['LubDensity'])
            testcase = self.gear[int(each['Part1ID'])]['TestCase']
            for each_test in testcase:
                T = testcase[each_test]['Torque']
                n = float(testcase[each_test]['Speed'])*60
                temprature = float(testcase[each_test]['Temperature'])
                voil = self.visko(float(temprature-273.15),nue1,nue2)
                result = self.eng.mesh_Kahraman(gear, float(voil), float(Rho), float(n), float(T), nargout= 2)
                Pv = result[0]
                value_to_insert = {}
                value_to_insert['TestCaseID'] = each_test
                value_to_insert['PartID'] = int(each['Part1ID'])
                value_to_insert['PartName'] =self.gear[int(each['Part1ID'])]['PartName']
                value_to_insert['ResultName'] = 'GearMeshPowerLoss'
                value_to_insert['ResultValue'] = Pv
                value_to_insert['ResultUnit'] = 'W'
                value_to_insert['ResultType'] = 'PowerLoss'
                value_to_insert['UpdateDATE'] = self.formatted_date
                output.append(value_to_insert.copy())
        # print('GearMesh',output)
        return output

    def gear_churn_loss(self):
        output=[]
        for each in self.gear:
            gear = {}
            gear['z1']   = float(self.gear[each]['NumberOfTeeth'])
            gear['da1']  = float(self.gear[each]['TipDiameter'])*1000
            gear['df1']  = float(self.gear[each]['RootDiameter'])*1000
            gear['m']    = float(self.gear[each]['NormalModule'])*1000
            gear['beta'] = float(self.gear[each]['HelixAngle'])/2/pi*360
            gear['b']    = float(self.gear[each]['FaceWidth']) * 1000
            gear['d1']   = gear['z1']*gear['m']/cos(gear['beta']/360*2*pi)
            for each_mesh in self.gear_mesh:
                if each_mesh['Part1ID'] == str(each) or each_mesh['Part2ID'] == str(each):
                    gear['aw'] = float(each_mesh['WorkingPressureAngle'])/2/pi*360
            gear['he1']  = -1 * float(self.gear[each]['LubricantLevel']) * 1000 \
                            + self.gear[each]['Position'][1] * 1000 \
                            + gear['d1'] / 2

            if gear['he1'] < 0:
                gear['he1'] =float(0)
            nue1 = float(self.gear[each]['LubKinematicViscosity1']) * 10 ** 6
            nue2 = float(self.gear[each]['LubKinematicViscosity2']) * 10 ** 6
            Rho = float(self.gear[each]['LubDensity'])
            testcase = self.gear[each]['TestCase']
            Vol = 0.0013
            for each_test in testcase:
                n = float(testcase[each_test]['Speed']) * 60
                temprature = float(testcase[each_test]['Temperature'])
                voil = self.visko(float(temprature - 273.15), nue1, nue2)
                result = self.eng.Blank_Changenet(self.numb_change(gear), float(voil), float(Rho),float(Vol), float(n), nargout= 2)
                Pv = result[0]
                value_to_insert = {}
                value_to_insert['TestCaseID'] = each_test
                value_to_insert['PartID'] = each
                value_to_insert['PartName'] = self.gear[each]['PartName']
                value_to_insert['ResultName'] = 'GearChurningPowerLoss'
                value_to_insert['ResultValue'] = Pv
                value_to_insert['ResultUnit'] = 'W'
                value_to_insert['ResultType'] = 'PowerLoss'
                value_to_insert['UpdateDATE'] = self.formatted_date
                output.append(value_to_insert.copy())
        # print  ('churning',output)
        return output

    def gear_wind_loss(self):
        output=[]
        for each in self.gear:
            gear = {}
            value_to_insert = {}
            gear['da1']  = float(self.gear[each]['TipDiameter'])*1000
            gear['m']    = float(self.gear[each]['NormalModule'])*1000
            gear['b']    = float(self.gear[each]['FaceWidth']) * 1000
            testcase = self.gear[each]['TestCase']
            for each_test in testcase:
                n = float(testcase[each_test]['Speed']) * 60
                result = self.eng.Windage_Townsend(self.numb_change(gear), float(n), nargout= 1)
                Pv = result
                value_to_insert['TestCaseID'] = each_test
                value_to_insert['PartID'] = each
                value_to_insert['PartName'] = self.gear[each]['PartName']
                value_to_insert['ResultName'] = 'GearWindagePowerLoss'
                value_to_insert['ResultValue'] = Pv
                value_to_insert['ResultUnit'] = 'W'
                value_to_insert['ResultType'] = 'PowerLoss'
                value_to_insert['UpdateDATE'] = self.formatted_date
                output.append(value_to_insert.copy())
        # print  ('Windage',output)
        return output


    def bearing_loss(self):
        output=[]
        for each in self.bearing:
            bearing={}
            value_to_insert={}
            bearing['BearingType'] =self.bearing[each]['BearingType']
            bearing['D'] = float(self.bearing[each]['Od']) * 1000
            bearing['d'] = float(self.bearing[each]['Bore']) * 1000
            bearing['C0'] = float(self.bearing[each]['StaticCapacity'])
            bearing['Br'] =float(self.bearing[each]['Width'])*1000
            testcase = self.bearing[each]['TestCase']
            bearing['H_bearing'] = -1 * float(self.bearing[each]['LubricantLevel']) * 1000 \
                                   + self.bearing[each]['Position'][1] * 1000 \
                                   + bearing['D'] / 2
            nue1 = float(self.bearing[each]['LubKinematicViscosity1']) * 10 ** 6
            nue2 = float(self.bearing[each]['LubKinematicViscosity2']) * 10 ** 6
            for each_test in testcase:
                Fa = testcase[each_test]['RadialLoadMagnitude']
                Fr = testcase[each_test]['Load3DZ']
                n = float(testcase[each_test]['RotationSpeed']) * 60
                temprature = float(testcase[each_test]['Temperature'])
                voil = self.visko(float(temprature - 273.15), nue1, nue2)
                result = self.eng.Bearing_Skf(self.numb_change(bearing),float(n),float(voil),float(Fa),float(Fr), nargout= 5)
                Pv = result[0]
                value_to_insert['TestCaseID'] = each_test
                value_to_insert['PartID'] = each
                value_to_insert['PartName'] = self.bearing[each]['PartName']
                value_to_insert['ResultName'] = 'BearingPowerLoss'
                value_to_insert['ResultValue'] = Pv
                value_to_insert['ResultUnit'] = 'W'
                value_to_insert['ResultType'] = 'PowerLoss'
                value_to_insert['UpdateDATE'] = self.formatted_date
                output.append(value_to_insert.copy())
        # print("Bearing",output)
        return output

    def visko(self,t,nue1,nue2):
        result = self.eng.visko(t,nue1,nue2)
        return result

    def test_connection(self,test_input):
        return self.eng.test_connection(test_input)



    def numb_change(self,dict_input):
        dict_output = {}
        for each in dict_input:
            try:
                float(dict_input[each])
                dict_output[each]=float(dict_input[each])
            except ValueError:
                dict_output[each]= dict_input[each]
        return dict_output

if __name__ == '__main__':
    prfix= prefix_info()
    db = db_connecotor()
    db.build_connector()
    mlab= mlab_fun(prfix,db)
    # T = 20.0
    # n = 2200.0
    # voil = 6.4
    # rho = 843.0
    # Vol = 0.0003
    mlab.test_connection(1)
    mlab.pv_Sim(1,[str(1),str(2),str(3),str(4)])
    # mlab.read_db([1,2,3])
    # mlab.gear_mesh_loss()
    # mlab.gear_churn_loss()
    # mlab.gear_wind_loss()
    # mlab.bearing_loss()

