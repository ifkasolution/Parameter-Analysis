from numpy import array, remainder, sign
from math import cos, degrees, pi, sqrt, acos, tan
import os


class readDb:
    """
    reading data from database, preparing for building model in adams

    input:
    prefix - from file All_prefix import all prefix definition
    db - from my db connector import db connector
    TestCaseID - selected test case to be evaluated

    output:
    self.all_data - include the dict of gear, gear mesh, shaft, bearing, load point, clutch
                    (Some of the values depend on the test case ID!)
    """

    def __init__(self, prefix, db_class):
        self.prefix = prefix
        self.db = db_class
        self.TestCase_info = {}
        self.TestCase = []
        self.all_shafts = {}
        self.all_gears = {}
        self.all_gear_mesh = {}
        self.all_bearing = {}
        self.all_load_point = {}
        self.all_clutch = {}
        self.db_table = None
        self.all_attributvalue = []
        self.all_attributeID = []
        self.all_type_unit = None
        self.all_attributename = None
        self.all_part_assembliesname = None

    def read_all(self, input_table, selected_id):
        self.db_table = input_table
        self.TestCase_info = {}
        self.TestCase = []
        self.all_shafts = {}
        self.all_gears = {}
        self.all_gear_mesh = {}
        self.all_bearing = {}
        self.all_load_point = {}
        self.all_clutch = {}
        self.read_testcase(selected_id)
        self.read_shaft_info()
        self.read_gear_info()
        self.read_bearing_info()
        self.read_loadpoint()
        self.read_clutch()

    def read_info_for_changing(self, input_list):
        for each in input_list:
            self.all_attributeID.append(each['PartAttributeID'])
            self.all_attributvalue.append(each['Attributevalue'])
        seperator = ','
        if len(input_list) > 1:
            text1 = "in "
        else:
            text1 = "="
        # reading of attributunit
        from_table = "(" + self.prefix.database + "." + self.prefix.Attribute_List + " inner join " + self.prefix.romax_mapping_unit_sql + " using (AttribUnit))"
        where_clause = " WHERE PartAttributeID " + text1 + '(' + seperator.join(
            str(i) for i in self.all_attributeID) + ')'
        self.all_type_unit = self.db.query_in_db(['AttribUnit_rmx_input', 'type'], from_table, where_clause)

        # reading of attributname
        from_table = "(" + self.prefix.database + "." + self.prefix.Attribute_List + " inner join " + self.prefix.romax_mapping_attribute_name_sql + " using (PartAttribName))"
        where_clause = " where PartAttributeID " + text1 + '(' + seperator.join(
            str(i) for i in self.all_attributeID) + ')'
        self.all_attributename = self.db.query_in_db(['PartAttribName_rmx_input'], from_table,
                                                     where_clause)
        # reading of partname and assembliesname
        from_table = "(" + self.prefix.database + "." + self.prefix.Attribute_List + " inner join " + self.prefix.Part_List + " using(PartID))"
        where_clause = " inner join " + self.prefix.assembly + " using (AssemID) where PartAttributeID " + text1 + '(' + seperator.join(
            str(i) for i in self.all_attributeID) + ')'
        self.all_part_assembliesname = self.db.query_in_db(['PartName', 'AssemName'], from_table, where_clause)

    def read_testcase(self, test_case_id):
        if test_case_id == '*':
            where_clause = " "
        else:
            seperator = ','
            where_clause = ' WHERE TestCaseID in (' + seperator.join(test_case_id) + ')'
        Testcase_name = ['TestCaseID', 'InputLoad', 'OutputLoad']
        Testcaseid_query = self.db.query_in_db(Testcase_name, self.prefix.Test_Plan, where_clause)
        for each in Testcaseid_query:
            self.TestCase.append(each['TestCaseID'])
            self.TestCase_info[int(each['TestCaseID'])] = {'InputLoad': each['InputLoad'],
                                                           'OutputLoad': each['OutputLoad']}

    def read_shaft_info(self):
        col_name = ['PartID', 'PartName', 'PartType']
        where_type = " WHERE PartType = 'Shaft'"
        all_results = self.db.query_in_db(col_name, self.db_table['PartList'], where_type)
        shaft_all = {}
        for each in all_results:
            shaft = {}
            col = ['PartAttribName', 'AttribValue', 'AttribIdx']
            where = " WHERE PartID = " + str(each['PartID']) + " AND PartAttribName " \
                                                               "in ('SectionsCount','AxisDirectionX','AxisDirectionY','AxisDirectionZ','OriginX','OriginY','OriginZ')"
            shaft_info = self.db.query_in_db(col, self.db_table['PartAttrib'], where)
            for each_info in shaft_info:
                shaft[each_info['PartAttribName']] = each_info['AttribValue']
            SectionsCount = int(shaft['SectionsCount'])
            shaft['Position'] = array([float(shaft['OriginX']), float(shaft['OriginY']),
                                       float(shaft['OriginZ'])])
            shaft['Dir'] = array([float(shaft['AxisDirectionX']), float(shaft['AxisDirectionY']),
                                  float(shaft['AxisDirectionZ'])])
            col = ['PartAttribName', 'AttribValue', 'AttribIdx']
            where = " WHERE PartID = " + str(each['PartID']) + " AND PartAttribName in " \
                                                               "('LeftDiameter','LeftBoreDiameter','LeftPosition','RightPosition')"
            shaft_info = self.db.query_in_db(col, self.db_table['PartAttrib'], where)
            for each_info in shaft_info:
                if not each_info['PartAttribName'] in shaft.keys():
                    shaft[each_info['PartAttribName']] = [0 for i in range(SectionsCount)]
                shaft[each_info['PartAttribName']][int(each_info['AttribIdx'])] = float(each_info['AttribValue'])
            shaft_all[each['PartID']] = shaft.copy()
        self.all_shafts = shaft_all
        print('Read shaft data done')

    def read_gear_info(self):
        col_name = ['PartID', 'PartName', 'PartType']
        where_type = " WHERE PartType = 'HelicalGear'"
        all_gears = self.db.query_in_db(col_name, self.db_table['PartList'], where_type)
        gear = {}
        for each_gear in all_gears:
            partID = each_gear['PartID']
            one_gear = {}
            gear_attri = ['NormalToothThicknessAtFinishedChamferDiameter', 'Hand', 'RootFilletRadius',
                          'TipDiameter', 'RootDiameter', 'BaseDiameter', 'FaceWidth',
                          'HelixAngle', 'NumberOfTeeth', 'NormalModule', 'FlankSurfaceRoughness', 'Lubricant',
                          'LubricantLevel', 'DedendumFactor', 'AddendumModCoeff', 'PressureAngle', 'Material']
            mount_type = 'GearMountDetailFeature'
            one_gear = self.read_part_attrib(partID, gear_attri, mount_type)
            one_gear['PartName'] = each_gear['PartName']
            one_gear['InitialAngel'] = 0
            one_gear['PartID'] = each_gear['PartID']
            file_path = self.prefix.CAD_file.format(one_gear['PartID'])
            one_gear['GearCAD'] = file_path
            gear[each_gear['PartID']] = one_gear.copy()
            material_col = ['AssemAttribName', 'AttribValue']
            material_where = " WHERE AssemAttribName in ('YoungsMod','Density')" \
                             " And AssemID = (SELECT AssemID From {} WHERE  AssemName = '{}') " \
                .format(self.db_table['AssemList'], gear[each_gear['PartID']]['Material'])
            material = self.db.query_in_db(material_col, self.db_table['AssemAttrib'], material_where)
            for each_material in material:
                gear[each_gear['PartID']][each_material['AssemAttribName']] = each_material['AttribValue']
            lubricant = gear[each_gear['PartID']]['Lubricant']
            col_lub = ['AssemAttribName', 'AttribValue']
            where = " WHERE AssemAttribName in ('KinematicViscosity1','KinematicViscosity2','Density') AND " \
                    " AssemID = (SELECT AssemID FROM {} WHERE AssemName = '{}' AND AssemType ='LubricantData')".format(
                self.prefix.assembly, lubricant)
            all_lub_data = self.db.query_in_db(col_lub, self.db_table['AssemAttrib'], where)
            for each_lub in all_lub_data:
                gear[each_gear['PartID']]['Lub' + each_lub['AssemAttribName']] = each_lub['AttribValue']
            gear[each_gear['PartID']]['InitialAngel'] = 0
            TestCase_gear = self.read_rmx_result(partID, ['MeshTangentialForce'])
            gear[each_gear['PartID']]['TestCase'] = TestCase_gear.copy()

        col2 = ['AssemID']
        where = " WHERE AssemType ='DetailedHelicalGearMesh'"
        mesh_info = {}
        allmesh = self.db.query_in_db(col2, self.db_table['AssemList'], where)
        for each in allmesh:
            col = ['AssemAttribName', 'AttribValue']
            where = " WHERE AssemID =" + str(each['AssemID']) + " AND AssemAttribName in ('Part1ID', 'Part2ID'," \
                                                                "'WorkingCentreDistance','TransverseContactRatio'," \
                                                                "'WorkingPressureAngle','WorkingFaceWidth')"
            mesh_info_db = self.db.query_in_db(col, self.db_table['AssemAttrib'], where)
            mesh_info_dict = {}
            for each_info in mesh_info_db:
                mesh_info_dict[each_info['AssemAttribName']] = each_info['AttribValue']
            # calculating rotaional angle
            gear_1 = gear[int(mesh_info_dict['Part1ID'])]
            gear_2 = gear[int(mesh_info_dict['Part2ID'])]
            delta_position = gear_2['Position'] - gear_1['Position']
            z = gear_2['NumberOfTeeth']
            initial_angle = degrees(acos(delta_position[1] / sqrt(delta_position[0] ** 2 + delta_position[1] ** 2)))
            if gear_2['Hand'] == 'left':
                dir_hand = -1
            else:
                dir_hand = 1
            beta = float(gear_2['HelixAngle'])
            m_n = float(gear_2['NormalModule']) * 1000  # in mm
            d = float(z) * m_n / cos(beta)
            dlta_beta = degrees(tan(beta) / d * 2 * dir_hand * delta_position[2] * 1000)
            if remainder(float(z), 2) == 0:
                gear_2['InitialAngel'] = gear_2['InitialAngel'] + \
                                         initial_angle * sign(delta_position[0]) + 360 / float(z) / 2 + dlta_beta
            else:
                gear_2['InitialAngel'] = gear_2['InitialAngel'] + initial_angle * sign(delta_position[0]) + dlta_beta
            mesh_info[each['AssemID']] = mesh_info_dict.copy()
            # self.read_rmx_result()
        self.all_gears = gear
        self.all_gear_mesh = mesh_info
        self.cal_gear_k_d()
        print('Read gear data done')

    def cal_gear_k_d(self):
        for each in self.all_gear_mesh:
            mesh = self.all_gear_mesh[each]
            pinion = int(mesh['Part1ID'])
            wheel = int(mesh['Part2ID'])
            eps_alfa = float(mesh['TransverseContactRatio'])
            b_gem = float(mesh['WorkingFaceWidth']) * 1E3  # in mm
            beta = float(self.all_gears[pinion]['HelixAngle'])  # in rad
            z1 = float(self.all_gears[pinion]['NumberOfTeeth'])
            z2 = float(self.all_gears[wheel]['NumberOfTeeth'])
            x1 = float(self.all_gears[pinion]['AddendumModCoeff'])
            x2 = float(self.all_gears[wheel]['AddendumModCoeff'])
            h_fp_s = float(self.all_gears[pinion]['DedendumFactor'])
            alfa_n = float(self.all_gears[pinion]['PressureAngle'])
            E1 = float(self.all_gears[pinion]['YoungsMod']) * 1E-6  # in N/mm2
            E2 = float(self.all_gears[wheel]['YoungsMod']) * 1E-6  # in N/mm2
            rho = [0, 0]
            d_a = [0, 0]
            d_f = [0, 0]
            d_b = [0, 0]
            d_m = [0, 0]
            theta = [0, 0]
            b = [0, 0]
            theta_test = [0, 0]
            rho[0] = float(self.all_gears[pinion]['Density'])  # in kg/m3
            rho[1] = float(self.all_gears[wheel]['Density'])  # in kg/m3
            d_a[0] = float(self.all_gears[pinion]['TipDiameter']) * 1000  # in mm
            d_f[0] = float(self.all_gears[pinion]['RootDiameter']) * 1000  # in mm
            d_a[1] = float(self.all_gears[wheel]['TipDiameter']) * 1000  # in mm
            d_f[1] = float(self.all_gears[wheel]['RootDiameter']) * 1000  # in mm
            d_b[0] = float(self.all_gears[pinion]['BaseDiameter']) * 1000  # in mm
            d_b[1] = float(self.all_gears[wheel]['BaseDiameter']) * 1000  # in mm
            b[0] = float(self.all_gears[pinion]['FaceWidth']) * 1000  # in mm
            b[1] = float(self.all_gears[wheel]['FaceWidth']) * 1000  # in mm3

            # Steifigkeit nach DIN 3990-1
            zn1 = z1 / (cos(beta)) ** 3
            zn2 = z2 / (cos(beta)) ** 3
            C_th = (0.04723 + 0.15551 / zn1 + 0.25791 / zn2 - 0.00635 * x1 - 0.11654 * x1 / zn1
                    - 0.00193 * x2 - 0.24188 * x2 / zn2 + 0.00529 * x1 ** 2 + 0.00182 * x2 ** 2) ** -1
            C_M = 0.8  # Correction factor
            C_R = 2 / 206000 * E1 * E2 / (E1 + E2)  # Shape factor
            C_B = (1 + 0.5 * (1.2 - h_fp_s)) * (1 - 0.02 * (20 - degrees(alfa_n)))  # Basic rack  profile factor
            C = C_th * C_M * C_R * C_B * cos(beta)  # in N/ mm miu m
            C_gamma = C * (0.75 * eps_alfa + 0.25)  # in N/ mm miu m
            C_gear = C_gamma * b_gem  # in N/ miu m
            C_gear = C_gear * 1E3  # Mesh stiffness  in N/ mm

            # Inertial in kg m^2
            Q = 0.8
            for i in [0, 1]:
                d_m[i] = (d_a[i] + d_f[i]) / 2
                theta[i] = 0.03125 * pi * d_m[i] ** 4 * b[i] * rho[i] * (
                        1 - Q ** 4) * 1e-15  # Trägkeitsmoment in kg m^2

            # Dämpfung der Verzahnung nach Lehr Maschinenelemente 2 von Berthold Schlecht Seite 604
            D_z = 0.05
            d_z = 2 * D_z * sqrt(
                C_gamma * b_gem * 1000 * theta[0] * theta[1] / (theta[0] + theta[1])) * 1000  # in Ns/mm
            mesh['ContactStiffness'] = C_gear
            mesh['ContactDamping'] = d_z

    def read_bearing_info(self):
        col_name = ['PartID', 'PartName', 'PartType']
        where_type = " WHERE PartType = 'Bearing'"
        all_results = self.db.query_in_db(col_name, self.db_table['PartList'], where_type)
        bearing_all = {}
        for each in all_results:
            Bearing = {}
            partID = each['PartID']

            col = ['AssemAttribName', 'AttribValue']
            where = " WHERE AssemAttribName = 'Part2ID' AND AssemID = (Select AssemID FROM {} " \
                    " WHERE AssemAttribName = 'Part1ID' AND AttribType ='HousingMountDetailFeature' " \
                    " AND AttribValue ={})".format(self.db_table['AssemAttrib'], partID)
            mount_info = self.db.query_in_db(col, self.db_table['AssemAttrib'], where)

            Bearing['MountOn'] = mount_info[0]['AttribValue']
            Bearing['PartName'] = each['PartName']
            col = ['PartAttribName', 'AttribValue']
            where = " WHERE PartAttribName in ('BearingData', 'Lubricant', 'LubricantLevel') " \
                    " AND PartID = {}".format(str(partID))
            bearing_query = self.db.query_in_db(col, self.db_table['PartAttrib'], where)
            for each in bearing_query:
                Bearing[each['PartAttribName']] = each['AttribValue']
            col_name = ['AssemType', 'AssemID']
            where = " WHERE AssemName = '{}'".format(Bearing['BearingData'])
            database = self.db.query_in_db(col_name, self.db_table['AssemList'], where)

            Bearing['BearingType'] = database[0]['AssemType'].replace('SSD', '')
            Bearing['BearingType'] = Bearing['BearingType'].replace('Data', '')
            col = ['AssemAttribName', 'AttribValue']
            attrib = ['Od', 'Bore', 'Width', 'StaticCapacity']
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
                self.db_table['AssemList'], lubricant)
            all_lub_data = self.db.query_in_db(col_lub, self.db_table['AssemAttrib'], where)
            for each_lub in all_lub_data:
                Bearing['Lub' + each_lub['AssemAttribName']] = each_lub['AttribValue']
            TestCase_bear = self.read_rmx_result(partID, ['RadialStiffness2D', 'AxialStiffness', 'RadialLoadMagnitude'])
            Bearing['TestCase'] = TestCase_bear.copy()
            bearing_all[partID] = Bearing.copy()
        self.all_bearing = bearing_all
        print('Read shaft data done')

    def read_loadpoint(self):
        col_name = ['PartID', 'PartName', 'PartType']
        where_type = " WHERE PartType = 'PowerLoad'"
        all_results = self.db.query_in_db(col_name, self.db_table['PartList'], where_type)
        loadpoint_all = {}
        for each in all_results:
            loadpoint = {}
            partID = each['PartID']
            loadpoint['PartName'] = each['PartName']
            # read attribute list and mount
            attribut = ['PolarInertia', 'TransverseInertia']
            loadpoint = self.read_part_attrib(partID, attribut, 'MountingDetailFeature')
            TestCase_bear = self.read_rmx_result(partID, ['Torque', 'Speed'])
            loadpoint['TestCase'] = TestCase_bear.copy()
            self.all_load_point[int(partID)] = loadpoint.copy()
        print('Read load data done')

    def read_clutch(self):
        col_name = ['AssemID', 'AssemName', 'AssemType']
        where_type = " WHERE AssemType = 'ClutchConnection'"
        all_results = self.db.query_in_db(col_name, self.db_table['AssemList'], where_type)
        closed_clutch = {}
        for each_test in self.TestCase:
            result_closeClutch = self.db.query_in_db(['ClosedClutch'], self.db_table['TestPlan'],
                                                     " WHERE TestCaseID = {}".format(each_test))
            closed_clutch[int(each_test)] = result_closeClutch[0]['ClosedClutch'].split(', ')
        clutch_all = {}
        for each in all_results:
            clutch = {}
            clutch['HalfClutch'] = []
            clutch['TestCase'] = {}
            AssemID = each['AssemID']
            clutch_state = {}
            for each_test in self.TestCase:
                clutch_state[int(each_test)] = False
                if str(AssemID) in closed_clutch[int(each_test)]:
                    clutch_state[int(each_test)] = True
            clutch['TestCase'] = clutch_state.copy()

            col_clutch = ['AssemAttribName', 'AttribValue']
            half_clutches_query = self.db.query_in_db(col_clutch, self.db_table['AssemAttrib'],
                                                      " WHERE AssemID = {}".format(AssemID))
            for result in half_clutches_query:
                one_clutch_id = result['AttribValue']
                one_clutch = self.read_part_attrib(one_clutch_id, [], 'MountingDetailFeature')
                clutch['HalfClutch'].append(one_clutch)
            self.all_clutch[int(AssemID)] = clutch.copy()
        print('Read clutch data done')

    def read_part_attrib(self, partID, attrib, mount_type):
        info_dic = {}
        if len(attrib) > 0:
            col = ['PartAttribName', 'AttribValue']
            seperator = "','"
            where = " WHERE PartID = " + str(partID) + " AND PartAttribName in ('" + seperator.join(attrib) + "')"
            info = self.db.query_in_db(col, self.db_table['PartAttrib'], where)
            for each in info:
                info_dic[each['PartAttribName']] = each['AttribValue']
        col = ['AssemAttribName', 'AttribValue']
        where = " WHERE AssemID = (Select AssemID FROM " + self.db_table['AssemAttrib'] + \
                " WHERE AssemAttribName = 'Part2ID' AND AttribType ='" + mount_type + "' AND AttribValue ='" + str(
            partID) + "')"
        mount_info = self.db.query_in_db(col, self.db_table['AssemAttrib'], where)
        for each in mount_info:
            info_dic[each['AssemAttribName']] = each['AttribValue']
        shaft_pos = self.all_shafts[int(info_dic['Part1ID'])]['Position']
        shaft_dir = self.all_shafts[int(info_dic['Part1ID'])]['Dir']
        Gear_pos_cor = shaft_pos + shaft_dir * float(info_dic['Offset'])
        info_dic['ShaftDir'] = shaft_dir
        info_dic['Position'] = Gear_pos_cor
        return info_dic

    def read_rmx_result(self, partID, resultName):
        col = ['TestCaseID', 'ResultName', 'ResultValue']
        sep = ','
        # resultName= ['RotationSpeed', 'RadialLoadMagnitude', 'Load3DZ']
        sep2 = "','"
        resultName_str = "'" + sep2.join(resultName) + "'"
        testCase = self.TestCase
        testCase_strings = [str(integer) for integer in testCase]
        where = " WHERE ResultName in ({}) " \
                "AND PartID = {} AND TestCaseID in ({})".format(resultName_str, partID, sep.join(testCase_strings))
        result = self.db.query_in_db(col, self.db_table['Output'], where)
        TestCasePart = {}
        for each_test in testCase:
            TestCasePart[int(each_test)] = {}
            for each in result:
                if each['TestCaseID'] == int(each_test):
                    TestCasePart[int(each_test)][each['ResultName']] = each['ResultValue']
        return TestCasePart


if __name__ == '__main__':
    from All_prefix import prefix_info
    from My_DB_Connector import db_connecotor

    pref = prefix_info()
    db = db_connecotor()
    eva = readDb(pref, db)
    eva.read_all(pref.db_tabels(), ['1'])
