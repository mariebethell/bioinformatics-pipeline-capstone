from PySide6 import QtWidgets, QtCore
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
        self.settings = SettingsController(self)
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
    



def GraphGenerator():
    def from_workbench(node_list):
        pass

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
        self.view = HomeView()
        self.app.content.addWidget(self.view)
        
        self.app.content.setCurrentWidget(self.view)

    def show_documentation(self):
        pass

    def close(self):
        print('Closing Home')


class SettingsController(PanelController):
    def __init__(self, app):
        self.view = None
        self.app = app
    
    def init_view(self):
        self.view = SettingsView()
        self.app.content.addWidget(self.view)

        self.app.content.setCurrentWidget(self.view)

    def commit_changes(self):
        pass
    
# This is necessary as the NodesPaletteWidget only populates itself with registered nodes.
# However, we will only ever have 3 nodes registered (Tool, Input & Output) and it won't actually be populated with our tools, so this is a faux version of that
class NodeBrowser(QtWidgets.QWidget):
    def __init__(self, graph, parent=None):
        super().__init__(parent) #TODO, figure out some way to make it close when i close the window

        self.graph = graph
        layout = QtWidgets.QGridLayout()

        # gettin tools to create as buttons
        for tool in TOOL_WIDGETS:
            btn = QtWidgets.QPushButton('Create ' + tool + ' Node')

            # lambda necessary here to capture current value, passes it to create tool node
            btn.clicked.connect(
                lambda _, t=tool : self.create_tool_node(t)
                )
            layout.addWidget(btn)

        self.setLayout(layout)

    # interior function for creating a new tool node
    def create_tool_node(self, tool):
        node = self.graph.create_node('bioinformatics_capstone.ToolNode', name=tool, pos=(40, 40))
        node.build_widgets(tool)

        viewer = self.graph.viewer()
        center = viewer.mapToScene(viewer.viewport().rect().center())

        node.set_pos(center.x(), center.y())

        self.close() # closes after a user picks a tool

class PipelineWorkbenchVC(PanelController):
    def __init__(self, app):
        self.node_graph = NodeGraph()

        self.view = QtWidgets.QWidget()
        self.app = app

        self.node_graph.register_node(ToolNode)
        self.node_graph.register_node(InputNode)
        self.node_graph.register_node(OutputNode)

        self.tool_palette = None # this external window is responsible for holding the Node Browser window

        # TODO figure out some way to make it so nodes cannot go off screen

        gr_widget = self.node_graph.widget
        
        
        btns = {
            'Save Preset' : self.save_preset,
            'Load Preset' : self.load_preset,
            'Run Pipeline' : self.run_pipeline,
            'Purge All Data' : self.purge_all_data,
            'Node Browser' : self.node_browser
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
    
    def node_browser(self):
        if self.tool_palette is None:
                self.tool_palette = NodeBrowser(self.node_graph)
        self.tool_palette.show()

    def init_view(self):       
        self.app.content.addWidget(self.view)
        self.app.content.setCurrentWidget(self.view)

    def close(self):
        print('closing')



#### VIEW SECTION ####

class HomeView(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        layout = QtWidgets.QVBoxLayout()

        welcome_text = 'Home PAGE PLACEHOLDER !!' # placeholder
        self.welcome_label = QtWidgets.QLabel(welcome_text)

        # eventually use QTextEdit's setHTML to create a nicer, rich Home screen

        layout.addWidget(self.welcome_label)
        self.setLayout(layout)

class SettingsView(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        layout = QtWidgets.QVBoxLayout()

        placeholder_text = 'Settings placeholder !!'
        self.placeholder_label = QtWidgets.QLabel(placeholder_text)

        layout.addWidget(self.placeholder_label)
        self.setLayout(layout)

#### NODE SECTION ####
"""
Future idea and maybe a bit of a stretch goal but I wanted to record this here. I was thinking that perhaps one way to implement the ability to add
new nodes (atleast in the front end) is that I could store these widgets in a JSON or some other similar file, and make a separate window called
Node Builder where basically future devs could basically 'design' the node by dragging widgets to a blank node, and save it to the JSON, with the
added ability to share this tool JSON around so that others may import it. Might have to come back to this, but didn't want to lose this idea. - Max
"""
# a dictionary of a list for each tool, containing a dictionary of widget types where each tool will contain what type of widget it will have and the fields for each widget
TOOL_WIDGETS = {
    'fastqc' : [
        {'type': 'slider', 'name': 'thread_slider', 'label': 'Number of Threads: 1', 'default': 1, 'need_label': True },
        {'type': 'checkbox', 'name': 'quiet_check', 'label': 'Quiet', 'default': False, 'need_label': False },
        {'type': 'checkbox', 'name': 'nogroup_check', 'label': 'NoGroup', 'default': False, 'need_label': False },
        {'type': 'slider', 'name': 'kmers_slider', 'label': 'Kmer Length: 7', 'default': 7, 'need_label': True },
        {'type': 'text_entry', 'name': 'adapters_text_input', 'label': 'Adapters', 'default': None, 'need_label': False }, # paired with a checkbox below
        {'type': 'checkbox', 'name': 'adapters_checkbox', 'label': 'Set Adapters', 'default': False, 'need_label': False },
        {'type': 'text_entry', 'name': 'contaminants_text_input', 'label': 'Contaminants', 'default': None, 'need_label': False }, # paired with a checkbox below
        {'type': 'checkbox', 'name': 'contaminants_check', 'label': 'Set Contaminants', 'default': False, 'need_label': False },
        {'type': 'combo_box', 'name': 'file_format_combobox', 'label': 'File Format', 'default': 'fastq', 'need_label': True }
    ]
}


# Node responsible for representing a tool within the pipeline & its wrapper
class ToolNodeWrapper(NodeBaseWidget):
    def __init__(self, tool=None, parent=None, parent_node=None):
        super().__init__(parent)

        self.widgets = {}
        self.mutable_labels = {}

        self.parent_node = parent_node

        container = QtWidgets.QWidget()

        # sets font color for widget labels in the node
        container.setStyleSheet(
            """
            QLabel, QCheckBox{
            color: white;}
            """
            )

        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(0,0,0,0)

        # building widgets dynamically
        for widget_def in TOOL_WIDGETS[tool]:
            w_type = widget_def['type']
            w_label = widget_def['label']
            w_default = widget_def['default']
            w_name = widget_def['name']
            need_label = widget_def['need_label']

            widget = None

            if w_type == 'slider':
                widget = QtWidgets.QSlider(QtCore.Qt.Horizontal)

                if w_name == 'thread_slider':
                    widget.setMinimum(1)
                    widget.setMaximum(128)
                elif w_name == 'kmers_slider':
                    widget.setMinimum(1)
                    widget.setMaximum(20)
                
                widget.setValue(w_default)

                # lambda function passes in the current widget name and the value from the signal to update label
                widget.valueChanged.connect(
                    lambda value, name=w_name : self.update_label(name, value)
                    )

            elif w_type == 'checkbox':
                widget = QtWidgets.QCheckBox(w_label)

            elif w_type == 'text_entry':
                widget = QtWidgets.QPlainTextEdit()
                widget.setPlaceholderText(w_label)
                widget.setMaximumHeight(30)

            elif w_type == 'combo_box':
                #bam, sam, fastq
                widget = QtWidgets.QComboBox()
                if w_name == 'file_format_combobox':
                    widget.addItems(['fastq', 'sam', 'bam'])
            
            # if the widget was succesfully grabbed then it will add it
            if widget is not None:
                label = QtWidgets.QLabel(w_label)

                if need_label:
                    layout.addWidget(label)
                layout.addWidget(widget)


                self.widgets[w_name] = widget
                if w_type == 'slider':
                    self.mutable_labels[w_name] = label # tying mutable label to name of widget
            else:
                print("Error in Tool Node Wrapper! failed to get widget")
            
        # adds a delete button to the end of EVERY node (perhaps configure to be decoupled from ToolNode later)
        delete_btn = QtWidgets.QPushButton('Delete Node')
        delete_btn.clicked.connect(self.delete_node)
        delete_btn.setStyleSheet('background-color:red; color:white;')
        layout.addWidget(delete_btn)

        container.setLayout(layout)
        self.set_custom_widget(container)

    def get_value(self):
        values = {} # this set will contain the values returned, in order of: slider, checkboxes, strings, then combo box
        # if there is more sensible way to return it, PLEASE modify this.

        for name, widget in self.widgets.items():
            if isinstance(widget, QtWidgets.QSlider):
                values[name] = widget.value()
            elif isinstance(widget, QtWidgets.QCheckBox):
                values[name] = widget.isChecked()
            elif isinstance(widget, QtWidgets.QCheckBox):
                values[name] = widget.toPlainText()
            elif isinstance(widget, QtWidgets.QComboBox):
                values[name] = widget.currentText()
            else:
                values[name] = None

        print(values)

    def set_value(self, val_dict):
        for name, val, in val_dict.items():
            widget = self.widgets.get(name)

            if widget is None:
                continue
            if isinstance(widget, QtWidgets.QSlider):
                widget.setValue(val)
            elif isinstance(widget, QtWidgets.QCheckBox):
                widget.setChecked(val)
            elif isinstance(widget, QtWidgets.QCheckBox):
                widget.setPlainText(str(val))
            elif isinstance(widget, QtWidgets.QComboBox):
                index = widget.findText(str(val))
                if index >= 0:
                    widget.setCurrentIndex(index)
            
    def delete_node(self):
        if self.node is not None:
            graph = self.node.graph
            graph.delete_nodes([self.node])

    def update_label(self, w_name, val):
        label = self.mutable_labels.get(w_name)

        if w_name == "thread_slider":
            label.setText(f'Number of Threads: {val}')
        elif w_name == "kmers_slider":
            label.setText(f'Kmer Length: {val}')

class ToolNode(BaseNode):
    __identifier__ = 'bioinformatics_capstone'
    NODE_NAME = 'Tool'

    def __init__(self):
        super(ToolNode, self).__init__()
        self.wrapper = None
        
        """ 
        Just as an idea for later. Perhaps we could color code what are 'legal' connections, 
        as in certain colors can only go to other colors. Just a thought - Max
        """
        self.add_input('input', color=(0, 255, 0))
        self.add_output('output', color=(0, 0, 255))
    
    def build_widgets(self, tool):
        self.wrapper = ToolNodeWrapper(tool, self.view, self)
        self.add_custom_widget(self.wrapper)


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
    