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
        tool = 'fastqc'
        node_test = node_graph.create_node('bioinformatics_capstone.ToolNode', name=tool)
        node_test.build_widgets(tool)

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

# set of widgets 
TOOL_WIDGETS = { # note: QSlider, QCheckBox, QComboBox
    'fastqc' : [
        {'type': 'slider', 'name': 'thread_slider', 'label': 'Number of Threads: 1', 'default': 1, 'need_label': True },
        {'type': 'checkbox', 'name': 'quiet_check', 'label': 'Quiet', 'default': False, 'need_label': False },
        {'type': 'checkbox', 'name': 'nogroup_check', 'label': 'NoGroup', 'default': False, 'need_label': False },
        {'type': 'slider', 'name': 'kmers_slider', 'label': 'Kmer Length: 7', 'default': 7, 'need_label': True },
        {'type': 'text_entry', 'name': 'adapters_text_input', 'label': 'Adapters', 'default': None, 'need_label': False}, # paired with a checkbox below
        {'type': 'checkbox', 'name': 'adapters_checkbox', 'label': 'Set Adapters', 'default': False, 'need_label': False},
        {'type': 'text_entry', 'name': 'contaminants_text_input', 'label': 'Contaminants', 'default': None, 'need_label': False}, # paired with a checkbox below
        {'type': 'checkbox', 'name': 'contaminants_check', 'label': 'Set Contaminants', 'default': False, 'need_label': False},
        {'type': 'combo_box', 'name': 'file_format_combobox', 'label': 'File Format', 'default': 'fastq', 'need_label': True}
    ]
}

# Node responsible for representing a tool within the pipeline & its wrapper
class ToolNodeWrapper(NodeBaseWidget):
    def __init__(self, tool=None, parent=None):
        super().__init__(parent)

        self.widgets = {}
        self.mutable_labels = {}

        container = QtWidgets.QWidget()

        # sets font color for widget labels in the node
        container.setStyleSheet(
            """QLabel, QCheckBox{
            color: white;}
            """)

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
                widget.setReadOnly(True)
                widget.setMaximumHeight(30)

            elif w_type == 'combo_box':
                #bam, sam, fastq
                widget = QtWidgets.QComboBox()
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
        
        """ Just as an idea for later. Perhaps we could color code what are 'legal' connections, as in certain colors can only go to other colors. Just a thought"""
        self.add_input('input', color=(0, 255, 0))
        self.add_output('output', color=(0, 0, 255))
    
    def build_widgets(self, tool):
        self.wrapper = ToolNodeWrapper(tool, self.view)
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
    