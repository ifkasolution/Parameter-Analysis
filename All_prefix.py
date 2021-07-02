import os
import sys


class prefix_info:
    def __init__(self):
        if getattr(sys, 'frozen', False):
            # we are running in a bundle
            frozen = 'ever so'
            bundle_dir = sys._MEIPASS
        else:
            # we are running in a normal Python environment
            bundle_dir = os.path.dirname(os.path.abspath(__file__))
        self.dir = bundle_dir

        self.Batch_Input_Name = bundle_dir + '\Tool\\batch_input.xml'
        self.Batch_Output_Name = bundle_dir + '\Tool\\batch_output.xml'
        self.Batch_Log_Name = bundle_dir + '\Tool\\batch_protocol.log'
        self.Outputfile = bundle_dir + '\Tool\\output.xml'
        self.simulation_outputfile = bundle_dir + '\RMX\\simoutput'
        self.refresh_xml = bundle_dir + '\Tool\\refresh_input.xml'
        self.refresh_output = bundle_dir + '\Tool\\refresh_output.xml'
        self.refresh_log = bundle_dir + '\Tool\\refresh_protocol.log'
        self.refresh_file = bundle_dir + '\Tool\\Getriebe.ssd'
        self.SA = bundle_dir + '\\SA'
        self.refresh = bundle_dir + '\\Tool\\refresh'

        self.Software_Name = 'C:\Program Files (x86)\RomaxSoftware\RomaxDESIGNER R17\winrxd.exe'
        self.rmx_server = "C:\Program Files (x86)\RomaxSoftware\RomaxDESIGNER R17\RomaxSocketInterface.exe"
        self.rmx_shutdown = bundle_dir + "/Tool/batch-shutdown.xml"
        self.last_time = bundle_dir + '/Tool//lasttime.csv'

        self.conf_file = bundle_dir + '\Tool\\ifka.ini'
        self.conf_data = {"rmx": {"software": "", "server": "",
                                  "modelName": "", "modelPath": ""},
                          "adams": {"software": "", "error": "", "hmax": "",
                                    "motion_step": "", "endTime": "", "steps": ""}}
        self.database = "getriebe"
        self.rmx_map = "romax_mapping"

        self.romax_mapping_read_xml_sql = f'{self.rmx_map}.read_xml'
        self.romax_mapping_output_xml_sql = f'{self.rmx_map}.output_xml'
        self.romax_mapping_attribute_name_sql = f'{self.rmx_map}.attribute_name'
        self.romax_mapping_unit_sql = f'{self.rmx_map}.unit'
        self.romax_mapping_variable_sql = f'{self.rmx_map}.batch_variable'
        self.romax_mapping_result_sql = f'{self.rmx_map}.batch_result'
        self.romax_mapping_action_sql = f'{self.rmx_map}.batch_action'

        self.romax_mapping_read_xml_csv = bundle_dir + '\Tool\\csv\\import.csv'
        self.romax_mapping_output_xml_csv = bundle_dir + '\Tool\\csv\\output.csv'
        self.romax_mapping_variable_csv = bundle_dir + '\\Tool\\csv\\variable.csv'
        self.romax_mapping_result_csv = bundle_dir + '\\Tool\\csv\\result.csv'
        self.romax_mapping_action_csv = bundle_dir + '\\Tool\\csv\\action.csv'

        self.rmx_file = bundle_dir + '\RMX\Getriebe624_v2.ssd'
        self.Gearbox_name = 'Getriebe'
        self.output = 'Simulation_Output'
        self.output_temp = 'Simulation_Output_Temp'
        self.ifka_eva = 'Evaluation_Data'
        self.ifka_eva_temp = 'Evaluation_Data_Temp'
        self.ifka_testcase = 'IFKA_TestCases'
        self.ifka_testcase_output = 'IFKA_TestCases_output'
        self.ifka_testcase_output_temp = 'IFKA_TestCases_output_temp'
        self.assembly = 'Assembly'
        self.part_list = 'part_list'
        self.Attribute_List = 'Attribute_List'
        self.Assem_Attribute_List = 'Assem_Attribute_List'
        self.assembly_temp = 'Assembly_temp'
        self.part_list_temp = 'part_list'
        self.test_plan_temp = 'test_plan_temp'
        self.Attribute_List_temp = 'Attribute_List'
        self.Assem_Attribute_List_temp = 'Assem_Attribute_List_temp'


        self.ShaftAssembly = 'ShaftAssembly'
        self.HelicalGearSet = 'HelicalGearset'
        self.ClutchPair = 'ClutchPair'
        self.HelicalGear = 'HelicalGear'
        self.ClutchConnection = 'ClutchConnection'
        self.DetailedHelicalGearMesh = 'DetailedHelicalGearMesh'
        self.HousingMountDetail = 'HousingMountDetail'
        self.GearMountDetail = 'GearMountDetail'
        self.MountingDetail = 'MountingDetail'
        self.BearingMountDetail = 'BearingMountDetail'
        self.Shaft = 'Shaft'
        self.Bearing = 'Bearing'
        self.PowerLoad = 'PowerLoad'
        self.Clutch = 'Clutch'
        self.Databas = ['LubricantData', 'ShaftMaterialData', 'GearMaterialData',
                        'NeedleRollerBearingData', 'RadialBallBearingData', 'CylindricalRollerBearingData',
                        'SurfaceTreatmentData']

        self.Attribute_List = 'Attribute_List'
        self.ShaftCoordination = 'ShaftCoordination'
        self.Part_List = 'Part_List'
        self.Assembly = 'Assembly'
        self.Assem_Attribute_List = 'Assem_Attribute_List'

        self.Test_Plan = 'Test_Plan'
        self.Attribute_List_temp = 'Attribute_List_temp'
        self.Part_List_temp = 'Part_List_temp'
        self.Assembly_temp = 'Assembly_temp'
        self.Assem_Attribute_List_temp = 'Assem_Attribute_List_temp'
        self.Test_Plan_temp = 'Test_Plan_temp'

        self.CAD_folder = bundle_dir + '\CAD'
        self.CAD_file = bundle_dir + r"\CAD\Part_{}.stl"

        self.Adams_Path = r"C:\Program Files\MSC.Software\Adams\\2020\common\mdi.bat"
        self.Adams_Result_Table = 'ADAMS_Result_TestCase'
        self.Adams_Result_Table_temp = 'ADAMS_Result_TestCase_temp'

        self.Eva_Log = 'eva_log'

        # for debug
        self.simulation_outputfile_debug = bundle_dir + "\\RMX\\simoutput_for_debug.xml"
        self.gear_gesamt = bundle_dir + "\\Tool\\Gear_gesamt.xml"

        # Batch running
        self.variable_listname='variable_list'
        self.result_listname = 'result_list'
        self.action_listname = 'action_list'
        self.output_path_listname = 'output_path_list'

    def Assembly_list(self):
        assem_type = {self.ShaftAssembly: [self.Bearing, self.PowerLoad, self.Shaft],
                      self.HelicalGearSet: [self.HelicalGear], self.ClutchPair: [self.Clutch]}
        return assem_type

    def Connection(self):
        Connection = [self.ClutchConnection, self.DetailedHelicalGearMesh, self.HousingMountDetail,
                      self.GearMountDetail, self.MountingDetail, self.BearingMountDetail]
        return Connection

    def db_tabels(self):
        db_tabel = {'EvaCase': self.ifka_testcase_output, 'Eva': self.ifka_eva, 'Output': self.output,
                    'TestPlan': self.Test_Plan, 'AssemAttrib': self.Assem_Attribute_List,
                    'PartAttrib': self.Attribute_List, 'PartList': self.Part_List, 'AssemList': self.Assembly}
        # Do not change the order of the dict!
        return db_tabel

    def db_tabels_temp(self):
        db_tabel = {'EvaCase': self.ifka_testcase_output_temp, 'Eva': self.ifka_eva_temp, 'Output': self.output_temp,
                    'TestPlan': self.test_plan_temp, 'AssemAttrib': self.Assem_Attribute_List_temp,
                    'PartAttrib': self.Attribute_List_temp, 'PartList': self.Part_List_temp,
                    'AssemList': self.Assembly_temp}  # Do not change the order of the list!
        return db_tabel

    def generating_refresh(self):
        batch_line = f"""
        <ParametricModification file="{self.refresh_file}">

        </ParametricModification>
        """
        with open(self.refresh_xml, "w+") as f:
            f.write(batch_line)
