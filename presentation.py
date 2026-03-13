# presentation layer
from PySide6 import QtWidgets
from NodeGraphQt import NodeGraph, BaseNode, NodeBaseWidget
from abc import ABC, abstractmethod

# handles what window is displayed to user
class AppFrame(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()

        # a top bar for navigating between the panels
        top_bar_layout = QtWidgets.QHBoxLayout()
        main_layout = QtWidgets.QVBoxLayout()

        top_bar_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # panel controllers
        self.home = HomeController(self)
        self.settings = SettingsController()
        self.workbench = PipelineWorkbenchVC(self)

        self.content = QtWidgets.QStackedWidget()

        # button dictionary
        btns = { 
            'Settings' : self.settings.init_view,
            'Home' : self.home.init_view,
            'Pipeline Workbench' : self.workbench.init_view
            }

        for label, func in btns.items():
            btn = QtWidgets.QPushButton(label)
            btn.clicked.connect(func)
            top_bar_layout.addWidget(btn)

        main_layout.addLayout(top_bar_layout, 0)
        main_layout.addWidget(self.content, 1)
        
        
        central = QtWidgets.QWidget()
        central.setLayout(main_layout)
        self.setCentralWidget(central)

        self.home.init_view()



#### PANEL SECTION ####

class PanelController():
    @abstractmethod
    def init_view(self):
        pass

    @abstractmethod # unsure if this method will be necessary.
    def close(self):
        pass


class HomeController(PanelController):
    def __init__(self, app):
        self.view = None
        self.app = app

    def init_view(self):
        if not self.view:
            self.view = HomeView()
            self.app.content.addWidget(self.view)
        
        self.app.content.setCurrentWidget(self.view)

    def show_documentation(self):
        pass

    def close(self):
        print("Closing Home")


class SettingsController(PanelController):
    pass


class PipelineWorkbenchVC(PanelController):
    def __init__(self, app):
        node_graph = NodeGraph()

        self.view = QtWidgets.QWidget()
        self.app = app

        node_graph.register_node(ToolNode)
        node_graph.register_node(InputNode)
        node_graph.register_node(OutputNode)

        # TODO figure out some way to make it so nodes cannot go off screen
        
        # populating with nodes (one test one for now)
        node_graph.add_node = node_graph.create_node('bioinformatics_capstone.ToolNode', name='tool')

        gr_widget = node_graph.widget
        
        
        btns = {
            'Save Preset' : self.save_preset,
            'Load Preset' : self.load_preset,
            'Run Pipeline' : self.run_pipeline,
            'Purge All Data' : self.purge_all_data
        }

        top_bar_layout = QtWidgets.QHBoxLayout()
        top_bar_layout.setContentsMargins(10, 10, 10, 10)

        for label, func in btns.items():
            btn = QtWidgets.QPushButton(label)
            btn.clicked.connect(func)
            top_bar_layout.addWidget(btn)

        layout = QtWidgets.QVBoxLayout(self.view)
        layout.setContentsMargins(10, 10, 10, 10)

        layout.addLayout(top_bar_layout)
        layout.addWidget(gr_widget)
    
    def save_preset(self):
        pass

    def load_preset(self):
        pass

    def run_pipeline(self):
        pass
    
    def purge_all_data(self):
        pass
        
    def new_pipeline(self):
        pass

    def init_view(self):       
        self.app.content.addWidget(self.view)
        self.app.content.setCurrentWidget(self.view)

    def close(self):
        print("closing")



#### VIEW SECTION ####

class HomeView(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        layout = QtWidgets.QVBoxLayout()

        welcome_text = "Home PAGE PLACEHOLDER !!" # placeholder
        self.welcome_label = QtWidgets.QLabel(welcome_text)

        # eventually use QTextEdit's setHTML to create a nicer, rich Home screen

        layout.addWidget(self.welcome_label)
        self.setLayout(layout)

class SettingsView():
    pass

#### NODE SECTION ####

# set of widgets 
# (a list of dictionaries which will contain the widget type, name, and label)
TOOL_WIDGETS = {
    "fastqc" : [
        {"type": "button", "name": "x", "label": "x"},
    ]
}

# Node responsible for representing a tool within the pipeline.
class ToolNode(BaseNode):
    __identifier__ = 'bioinformatics_capstone'
    NODE_NAME = "Tool"

    def __init__(self):
        super(ToolNode, self).__init__()


class DataNode(BaseNode):
    @property
    @abstractmethod
    def uri(self):
        pass

    @abstractmethod
    def check_format_against_consumer(self): # later function to check if two connected nodes are valid
        pass
# Node responsible for the accepting of data
class InputNode(DataNode):
    pass

# Node responsible for the exporting of data
class OutputNode(DataNode):
    pass



if __name__ == '__main__':
    app = QtWidgets.QApplication([])

    #gets user's screen size for resizing the window
    screen = app.primaryScreen()
    size = screen.size()
    scr_w = size.width()
    scr_h = size.height()


    window = AppFrame()

    # resizes it based on screen size (takes up 80%)
    width = int(scr_w * 0.8)
    height = int(scr_h * 0.8)
    window.setFixedHeight(height)
    window.setFixedWidth(width)

    # centers app at middle of screen
    window.move((scr_w - width) // 2, (scr_h - height) // 2)


    window.show()

    app.exec()
    