import networkx as nx
from numpy import sqrt



class draw_network():
    def __init__(self):


        self.color_dict = {}
        self.fixed_pos = {}
        self.edge_type = []
        self.edge_label = {}

    def add_edge(self, data):
        self.data = data
        self.color_dict = {}
        self.fixed_pos = {}
        self.nw = nx.Graph()
        for each_shaft in data.all_shafts:
            shaft_input_db = data.all_shafts[each_shaft]
            loacation = shaft_input_db['Position']
            self.color_dict[str(each_shaft)] = 0.2

        for each_gear in data.all_gears:
            shaft_info = str(data.all_gears[each_gear]['Part1ID'])
            self.nw.add_edge(shaft_info, str(each_gear), type='ShaftMount', weight=1)
            self.color_dict[str(each_gear)] = 1
            loacation = data.all_gears[each_gear]['Position']
            pos1 = sqrt(loacation[0] ** 2 + loacation[1] ** 2) * 2000
            pos2 = loacation[2] * 1000
            self.fixed_pos[str(each_gear)] = (pos1, pos2)


        for each_mesh in data.all_gear_mesh:
            mesh_info = data.all_gear_mesh[each_mesh]
            part1ID = str(mesh_info['Part1ID'])
            part2ID = str(mesh_info['Part2ID'])
            self.nw.add_edge(part1ID, part2ID, type='GearMesh', weight=1)

        for each_bearing in data.all_bearing:
            bearing_info = data.all_bearing[each_bearing]
            mount_on_inn = str(bearing_info['Part1ID'])
            mount_on_out = bearing_info['MountOn']
            self.nw.add_edge(str(each_bearing), mount_on_inn, type='ShaftMount', weight=1)
            if not mount_on_out == 'Ground':
                self.nw.add_edge(str(each_bearing), mount_on_out, type='ShaftMount', weight=1)
            self.color_dict[str(each_bearing)] = 2

        for each_loadpoint in data.all_loadpoint:
            loadpoint_info = data.all_loadpoint[each_loadpoint]
            mount_on = loadpoint_info['Part1ID']
            self.nw.add_edge(str(each_loadpoint), mount_on, type='ShaftMount', weight=1)
            self.color_dict[str(each_loadpoint)] = 3

        for each_clutch in data.all_clutch:
            clutch_mount = data.all_clutch[each_clutch]
            shaft_model_mount1 = str(clutch_mount['HalfClutch'][0]['Part1ID'])
            shaft_model_mount2 = str(clutch_mount['HalfClutch'][1]['Part1ID'])
            halfclutch1 = str(clutch_mount['HalfClutch'][0]['Part2ID'])
            halfclutch2 = str(clutch_mount['HalfClutch'][1]['Part2ID'])
            # self.nw.add_edge(halfclutch1, shaft_model_mount1, type='ShaftMount')
            # self.nw.add_edge(halfclutch2, shaft_model_mount2, type='ShaftMount')
            self.nw.add_edge(shaft_model_mount1, shaft_model_mount2, type='Clutch', weight=1)
            # self.color_dict[str(each_clutch)] = 4

        self.edge_type = []
        self.edge_label = {}
        for a, b in self.nw.edges:
            if self.nw[a][b]['type'] == "GearMesh":
                self.edge_type.append("dotted")
                self.edge_label[(a, b)] = "G"
            elif self.nw[a][b]['type'] == "Clutch":
                self.edge_type.append("dotted")
                self.edge_label[(a, b)] = "II"
            elif int(a) in data.all_bearing.keys() or int(b) in data.all_bearing.keys():
                self.edge_type.append("solid")
                self.edge_label[(a, b)] = "II"
            else:
                self.edge_type.append("solid")
                self.edge_label[(a, b)] = ""



        # pos =nx.kamada_kawai_layout(g,scale =1000)
        # pos_higher = {}
        y_off = 1.3  # offset on the y axis
        x_off = 1.3
        # for k, v in pos.items():
        #     pos_higher[k] = (v[0] * x_off, v[1] * y_off)

        # nx.draw_networkx_labels(g, pos_higher, Edge_dict, font_size=8)
        # nx.draw(g, pos, node_color=values, node_shape="s", node_size=40, style=edge_type, width=2)
        # plt.show()

    def show(self,ax):
        fixed_nodes = self.fixed_pos.keys()
        # pos = nx.spring_layout(self.nw, pos=self.fixed_pos, fixed=fixed_nodes)
        pos = nx.spring_layout(self.nw,k=0.15,iterations=30)
        color_values = [self.color_dict.get(node, 0) for node in self.nw.nodes()]
        nx.draw_networkx_edge_labels(self.nw, pos, edge_labels=self.edge_label, font_size = 12, ax = ax)
        nx.draw(self.nw, pos, node_color=color_values, with_labels= True,
                style=self.edge_type, font_color='white', width=2, ax = ax)

    def cal_path(self, Part1ID, Part2ID):
        path = nx.shortest_path(self.nw, source=str(Part1ID), target=str(Part2ID), weight='weight')
        return len(path)


if __name__ == '__main__':
    from All_prefix import prefix_info
    from My_DB_Connector import db_connecotor
    from Read_Database import readDb

    from PyQt5 import QtCore, QtWidgets
    import sys
    from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
    from matplotlib.figure import Figure
    import matplotlib
    import logging

    matplotlib.use('Qt5Agg')
    logging.getLogger('matplotlib.font_manager').disabled = True

    class MplCanvas(FigureCanvasQTAgg):
        def __init__(self, parent=None, width=8, height=6, dpi=100):
            fig = Figure(figsize=(width, height), dpi=dpi)
            self.axes = fig.add_subplot(111)
            super(MplCanvas, self).__init__(fig)


    class MainWindow(QtWidgets.QMainWindow):

        def __init__(self, *args, **kwargs):
            super(MainWindow, self).__init__(*args, **kwargs)

            # Create the maptlotlib FigureCanvas object,
            # which defines a single set of axes as self.axes.
            sc = MplCanvas(self, width=5, height=4, dpi=100)
            TestCaseID = ['1']
            prfix = prefix_info()
            db = db_connecotor()
            db.build_connector()
            input_table = prfix.db_tabels()
            data = readDb(prfix, db)
            data.read_all(input_table, TestCaseID)
            test = draw_network()
            test.add_edge(data)
            test.show(sc.axes)
            self.setCentralWidget(sc)

            self.show()


    app = QtWidgets.QApplication(sys.argv)
    w = MainWindow()
    app.exec_()


