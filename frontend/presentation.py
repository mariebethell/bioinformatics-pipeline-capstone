from datetime import date, datetime
import json
import re
from pathlib import Path
from platform import node
from PySide6 import QtWidgets, QtCore
from NodeGraphQt import NodeGraph, BaseNode, NodeBaseWidget
from abc import ABC, abstractmethod
from shared.graph import Graph
from backend.pipeline_builder import PipelineFactory
from backend.tool_registry import ToolRegistry

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

#what this does right now is generate a dictionary based on the outputs 
""""
class GraphGenerator():
    def __init__(self, graph=None):
        input = graph.get_node_by_name('Input')
        self.graph_outline = None
        file_uri = input.get_value()

        if file_uri:
            self.graph_outline = { 'input' : {'file_uri': file_uri} }
            self.from_workbench(input)
        else:
            print("ERROR: Input File must have a FASTQ file input to run the pipeline!") # create some warning window that pops up if there is no URI/no input file

    def from_workbench(self, input_node):

        curr = input_node

        while True:
            connections = curr.connected_output_nodes() # gets all the connected output nodes in the form of a dictionary: {port object : list of nodes}
            if not connections: # handles if there are no connections
                break
            
            (_, nodes), = connections.items()

            if not nodes: # if the node list is empty
                break
            
            node = nodes[0]
            
            self.graph_outline.update({node.tool : node.get_value()})

            curr = node

        return self.graph_outline
"""

# New GraphGenerator class that converts node graph to backend graph data structure
class GraphGenerator():
    def __init__(self, qt_graph):
        self.qt_graph = qt_graph
        self.graph = Graph()
        self.node_map = {}  # maps Qt nodes to backend nodes

        input = self.qt_graph.get_node_by_name('Input')
        file_uri = input.get_value()

        if not file_uri:
            print("ERROR: Input File must have a FASTQ file input to run the pipeline!") # create some warning window that pops up if there is no URI/no input file

    def from_workbench(self):
        # create backend nodes
        for qt_node in self.qt_graph.all_nodes():
            if isinstance(qt_node, InputNode):
                tool = "input"
            elif isinstance(qt_node, ToolNode):
                tool = qt_node.tool
            else:
                continue

            node = self.graph.create_node(tool)
            if isinstance(qt_node, InputNode):
                node.outputs = {
                    "reads": qt_node.get_value()
                }
                node.args = {}  # input nodes don’t have args
            else:
                node.args = qt_node.get_value()

            self.node_map[qt_node] = node

        # connect nodes
        for qt_node in self.qt_graph.all_nodes():
            connections = qt_node.connected_output_nodes()

            for _, connected_nodes in connections.items():
                for target in connected_nodes:
                    self.graph.connect(
                        self.node_map[qt_node],
                        self.node_map[target]
                    )

        return self.graph

#### PANEL SECTION ####

class PanelController():
    """
    Abstract class for all Panel Controllers, which has a init_view method required
    """
    @abstractmethod
    def init_view(self):
        pass

    @abstractmethod # unsure if this method will be necessary.
    def close(self):
        pass


class HomeController(PanelController):
    """
    This is the Home Page of the App, which will describe 
    """
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
    """
    This is the Settings Page's controller where commands to change the app will be passed through.
    """
    def __init__(self, app):
        self.view = None
        self.app = app
    
    def init_view(self):
        self.view = SettingsView()
        self.app.content.addWidget(self.view)

        self.app.content.setCurrentWidget(self.view)

    def commit_changes(self):
        pass
    
class NodeBrowser(QtWidgets.QDialog): 
    """
    This is a small window responsible for allowing the user to create new tool/data nodes.
    Creating a dedicated NodeBrowser class bypasses the limitation brought on by our lack of registering new tool nodes.
    """
    def __init__(self, graph, parent=None):
        super().__init__(parent) #TODO, figure out some way to make it close when i close the window

        self.graph = graph
        layout = QtWidgets.QGridLayout()

        # gettin tools to create as buttons
        for tool in NODE_WIDGETS:
            btn = QtWidgets.QPushButton('Create ' + tool + ' Node')

            # lambda necessary here to capture current value, passes it to create tool node
            btn.clicked.connect(
                lambda _, t=tool : self.create_tool_node(t)
                )
            layout.addWidget(btn)

        input_btn = QtWidgets.QPushButton('Create input Node')
        output_btn = QtWidgets.QPushButton('Create output Node')

        input_btn.clicked.connect(self.create_input_node)
        output_btn.clicked.connect(self.create_output_node)

        layout.addWidget(input_btn)
        layout.addWidget(output_btn)

        self.setLayout(layout)

    # interior function for creating a new tool node
    def create_tool_node(self, tool, non_tool=False):
        
        self.node = ToolNode(tool)

        self.graph.add_node(self.node)

        viewer = self.graph.viewer()
        center = viewer.mapToScene(viewer.viewport().rect().center())

        self.node.set_pos(center.x(), center.y())

        self.close() # closes after a user picks a tool
    
    def create_input_node(self):
        node = self.graph.create_node('bioinformatics_capstone.InputNode', name='Input', pos=(40,40))
        
        self.close()

    
    def create_output_node(self):
        pass
        

class SaveWindow(QtWidgets.QDialog):
    """
    A window which will allow the user to specify a name for their saved file.
    """
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle('Save Pipeline')

        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(0,0,0,0)

        self.input = QtWidgets.QLineEdit()
        self.input.setPlaceholderText('Enter Filename Here (or None to name it as a generic)')
        self.input.setMaximumHeight(30)

        btn = QtWidgets.QPushButton('Save')
        btn.clicked.connect(self.accept) # when the button is clicked, it closes the dialog and sends an Accepted exit code

        layout.addWidget(self.input)
        layout.addWidget(btn)

        self.setLayout(layout)
    
    def save_name(self):
        filename = self.input.text()

        filename = filename.replace(' ', '_')

        # uses regex to keep only valid characters by
        filename = re.sub(r'[^a-zA-Z0-9._-]', '', filename)

        filename = filename.strip('. ')

        return filename

class PipelineWorkbenchVC(PanelController):
    def __init__(self, app):
        self.node_graph = NodeGraph()

        self.view = QtWidgets.QWidget()
        self.app = app

        self.pipeline_uuid = None

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

            if label == 'Run Pipeline': # flag to make the run pipeline button green
                btn.setStyleSheet('background-color: green; color: white;')
            
            top_bar_layout.addWidget(btn)

        layout = QtWidgets.QVBoxLayout(self.view)
        layout.setContentsMargins(10, 10, 10, 10)

        layout.addLayout(top_bar_layout)

        layout.addWidget(gr_widget)
    
    def save_preset(self):  
        # syncing all nodes
        for node in self.node_graph.all_nodes():
            if isinstance(node, ToolNode):
                if node.wrapper:
                    node.set_property('tool_data', node.get_value())

        # opens a dialog for the user to input a name
        save_dialog = SaveWindow(parent=self.app)
        
        if save_dialog.exec() == QtWidgets.QDialog.Accepted:
            filename = save_dialog.save_name()

            if not filename:
                filename = 'pipeline'

                timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
                filename = f'pipeline_{timestamp}.json'

            dir = Path(__file__).parent
            dir = dir / 'presets'

            if not dir.exists():
                dir.mkdir(exist_ok=True)

            preset_path = dir / filename


            self.node_graph.save_session(str(preset_path))

            # now need to manually remove junk property generated by adding the custom widget to ToolNode
            try:
                with open(preset_path, 'r') as file:
                    data = json.load(file)

                if 'nodes' in data:
                    for _, node_info in data['nodes'].items():
                        if 'custom' in node_info:
                            node_info['custom'].pop('_delete', None) # deletes junk property in the custom field for the node info
                
                with open(preset_path, 'w') as file:
                    json.dump(data, file, indent=2)

            except:
                print('Error in save_preset when deleting junk property')
            
            print(f'Succesfully saved as {filename}')
        else:
            print('Save Preset cancelled by user.')
    def load_preset(self):
        file_dialog = QtWidgets.QFileDialog()

        file_dialog.setWindowTitle('Open Pipeline JSON')
        file_dialog.setNameFilter('*pipeline*.json') # only looks for files with 'pipeline' in the name

        file_dialog.setFileMode(QtWidgets.QFileDialog.FileMode.ExistingFile) # forces the user to get an existing file
        file_dialog.setViewMode(QtWidgets.QFileDialog.ViewMode.Detail)

        if file_dialog.exec():
            path = file_dialog.selectedFiles()[0]
            self.node_graph.load_session(path)

    def run_pipeline(self):
        graph = GraphGenerator(self.node_graph)
        graph = graph.from_workbench()

        input_node = graph.get_first_node()
        if (graph.get_node(input_node.node_num).tool != "input"):
            print("ERROR: First node must be an input node with a FASTQ file input to run the pipeline!")
            return
        else:
            print(input_node.outputs)
            input_folder = input_node.outputs["reads"]["reads"][0] # gets the file URI of the input node's reads, which is the input folder for the pipeline

        for node_num, node in graph.nodes.items():
            print(f"Node {node_num}: tool={node.tool}, args={node.args}")

        pipeline_factory = PipelineFactory()
        pipeline = pipeline_factory.build_pipeline("nextflow", graph, input_folder, ToolRegistry(), pipeline_script_path="backend/pipeline.nf")
        # pipeline.run_pipeline()
        
    def purge_all_data(self):
        pass
        
    def new_pipeline(self):
        pass
    
    def node_browser(self):
        if self.tool_palette is None:
                self.tool_palette = NodeBrowser(self.node_graph, parent=self.app)
        self.tool_palette.show()

    def init_view(self):       
        self.app.content.addWidget(self.view)
        self.app.content.setCurrentWidget(self.view)

    def close(self):
        print('closing')



#### VIEW SECTION ####

class HomeView(QtWidgets.QWidget):
    """
    This is the Home Page's view, which will display a place to log in to their OneDrive account
    as well as see information about the system
    """
    def __init__(self):
        super().__init__()
        layout = QtWidgets.QVBoxLayout()

        welcome_text = 'Home PAGE PLACEHOLDER !!' # placeholder
        self.welcome_label = QtWidgets.QLabel(welcome_text)

        # eventually use QTextEdit's setHTML to create a nicer, rich Home screen

        layout.addWidget(self.welcome_label)
        self.setLayout(layout)

class SettingsView(QtWidgets.QWidget):
    """
    This is the Setting Page's view, which actually displays information to the user to change app-wide settings
    """
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
# perhaps find a way to get the tool's version to display in the node to the user

# widget definitions to increase readability and make it easier to add widgets
#TODO add tooltips to each widget

def slider_widget(name, label, default=1, min=1, max=1):
    return {'type': 'slider', 'name': name, 'label': f'{label}: {default}', 'label_template': f'{label}: {{}}', 'default': default, 'need_label': True, 'min': min, 'max': max }
def checkbox_widget(name, label): 
    return {'type': 'checkbox', 'name': name, 'label': label, 'default': False, 'need_label': False}
def text_entry_widget(name, label, nullable=False):
    return {'type': 'text_entry', 'name': name, 'label': label, 'default': None, 'need_label': False, 'nullable': nullable } 
def combo_box_widget(name, label, default=None, items=[], nullable=False):
    return {'type': 'combo_box', 'name': name, 'label': label, 'default': default, 'need_label': True, 'items': items, 'nullable': nullable}





# common widgets
threads_slider = slider_widget('threads', 'Number of Threads', 1, max=128)
quiet_check = checkbox_widget('quiet', 'Quiet')
NODE_WIDGETS = {
    'fastqc' : [
        threads_slider,
        quiet_check,
        checkbox_widget('nogroup', 'NoGroup'),
        slider_widget('kmers', 'Kmers Length', 7, max=20),
        text_entry_widget('adapters', 'Adapters', True), 
        text_entry_widget('contaminants', 'Contaminants', True),
        combo_box_widget('format', 'File Format', items=['fastq', 'sam', 'bam'])
    ],
    #TRIMMOMATIC WIDGET NOTES
    # arg(type, default, vals)
    # notes:
    # 
    # _global argument widgets
    # mode(str, 'SE', SE OR PE) dropdown
    # threads(int, 0, 0-128) slider
    # phred(str, None, 33 or 64) dropdown, nullable
    # trimlog(str, None) checkbox? nullable 
    # summary(str, None) checkbox? nullable
    # basein(str, None) checkbox? nullable
    # baseout(str, None) checkbox? nullable
    # validate_pairs(bool, false) checkbox
    # compress_level(int, 1, 1-9) slider
    # compression_mode(str, None, stream or block) dropdown, nullable needs checkbox
    # quiet(bool, false) checkbox
    # version unnecessary?
    # step argument widgets
    # will have to ask Ethan if this is the right way to go about it
    # 
    # _illumina clip widgets, in order of position
    # illumina clip checkbox?
    # fasta_with_adapters(str, None) checkbox?
    # seed_mismatches(int, None) checkbox? 
    # palindrome_clip_threshold(int, None) checkbox?
    # simple_clip_threshold(int, None) checkbox?
    # min_adapter_length_palindrome(int, 8, 1-inf) slider? or text entry? nullable needs check box
    # keep_both_reads (bool, False) checkbox nullable
    #
    #
    # leading(int, None, 0-inf) text entry
    # trailing(int, None, 0-inf) text entry
    # head_crop(int, None, 0-inf) text entry
    # tail_crop(int, None 0-inf) text entry
    # crop(int, None, 1-inf) text entry
    # 
    # _sliding window widgets, order of pos
    # window_size(int, None, 1-inf) text entry
    # required_quality(int, None, 0-inf) text entry
    #
    # _max_info widgets, order of pos
    # parameters(int, None, 1) text entry
    # strictness(float, 0.0, 0.0-1.0) slider
    #
    # min_len(int, None, 1-inf) text entry
    # max_len(int, None, 1-inf) text entry
    # avg_qual(int, None, 1-inf) text entry
    #
    # _base_count widgets, in order of pos
    # bases(str, None, None) checkbox?
    # min_count(int, None, 0-inf) text entry nullable
    # max_count(int, None, 0-inf) text entry nullable

    #order: type, name, label, default, need_label, extra*
    #sliders and combo boxes need labels
    # nullable checkboxes always after parent widget in dictionary order
    'trimmomatic' : [
        threads_slider,
        combo_box_widget('mode', 'Mode', items=['SE', 'PE']),
        combo_box_widget('phred', 'Phred', items=['33', '64'], nullable=True),
        checkbox_widget('trimlog', 'Trimlog'),
        checkbox_widget('summary', 'Summary'),
        checkbox_widget('basein', 'Basein'),
        checkbox_widget('baseout', 'Baseout'),
        checkbox_widget('validate_pairs', 'Validate Pairs'),
        slider_widget('compress_level', 'Compression Level', max=9),
        combo_box_widget('compression_mode', 'Compression Mode', items=['stream', 'block'], nullable=True),
        quiet_check
        #illumina clip
        
    ]
}

# TODO come back to
# WIDGET_FACTORY = {
#     'slider' : create_slider,
#     'text_entry' : create_text_entry,
#     'combo_box' : create_combo_box,
#     'checkbox' : create_checkbox,
# }


# Node responsible for representing a tool within the pipeline & its wrapper
#TODO Tooltips
class ToolNodeWrapper(NodeBaseWidget):
    def __init__(self, tool=None, parent=None):
        super().__init__(parent)
        
        self.tool = tool
        
        self.widgets = {}

        self.mutable_labels = {}
        
        self.nullable_checks = {} # certain widgets can be nullable. this dictionary maps checkboxes to the nullable widgets

        if not tool:
            return

        container = QtWidgets.QWidget()

        # sets font color for widget labels in the node
        container.setStyleSheet(
            """
            QLabel, QCheckBox{
            color: white; }
            """
            )

        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(0,0,0,0)

        # building widgets dynamically
        # NOTE i might come back to this, i feel like its kind of sloppy but gets the job done. i like kenneth's original suggestion of a factory, but will have to see later
        # for now this works
        for widget_def in NODE_WIDGETS[tool]:
            # gathering fields for widget definition
            w_type = widget_def['type']
            w_name = widget_def['name']
            w_label = widget_def['label']

            # flags
            need_label = widget_def.get('need_label', False)
            w_default = widget_def.get('default', None)
            w_label_template = widget_def.get('label_template')
            nullable = widget_def.get('nullable', False)


            widget = None

            if w_type == 'slider': 
                widget = QtWidgets.QSlider(QtCore.Qt.Horizontal)
                
                widget.setMinimum(widget_def['min'])
                widget.setMaximum(widget_def['max'])
                
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
                widget = QtWidgets.QComboBox()
                widget.addItems(widget_def['items'])
            
            # if the widget was succesfully grabbed then it will add it
            if widget is not None:
                label = QtWidgets.QLabel(w_label)

                if need_label:
                    layout.addWidget(label)

                if nullable:
                    checkbox = QtWidgets.QCheckBox()
                    checkbox.setChecked(False)

                    widget.setEnabled(False)
                    checkbox.toggled.connect(widget.setEnabled)

                    label = QtWidgets.QLabel('Enable ' + w_label)
                    nullable_space = QtWidgets.QHBoxLayout()

                    nullable_space.addWidget(checkbox)
                    nullable_space.addWidget(label)
                    nullable_space.addWidget(widget)

                    layout.addLayout(nullable_space)

                    self.nullable_checks[w_name] = checkbox
                else: 
                    layout.addWidget(widget)
                self.widgets[w_name] = widget
                if w_type == 'slider':
                    self.mutable_labels[w_name] = (label, w_label_template) # tying mutable label to name of widget
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
            checkbox = self.nullable_checks.get(name)  

            #checks if both the checkbox exists and if it is not checked 
            if checkbox and not checkbox.isChecked():
                continue

            if isinstance(widget, QtWidgets.QSlider):
                values[name] = widget.value()
            elif isinstance(widget, QtWidgets.QCheckBox):
                if(widget.isChecked()): # will not append to list
                    values[name] = widget.isChecked()
            elif isinstance(widget, QtWidgets.QTextEdit):
                values[name] = widget.toPlainText()
            elif isinstance(widget, QtWidgets.QComboBox):
                values[name] = widget.currentText()
            else:
                values[name] = None
        # return values
        #print(f'{self.tool} outputs: {values}')
        #return {self.tool : values}
        return values

    def set_value(self, val_dict):
        for name, val, in val_dict.items():
            widget = self.widgets.get(name)

            if widget is None:
                continue
            if isinstance(widget, QtWidgets.QSlider):
                widget.setValue(val)
            elif isinstance(widget, QtWidgets.QCheckBox):
                widget.setChecked(val)
            elif isinstance(widget, QtWidgets.QTextEdit):
                widget.setPlainText(str(val))
            elif isinstance(widget, QtWidgets.QComboBox):
                index = widget.findText(str(val))
                if index >= 0:
                    widget.setCurrentIndex(index)
            
    def delete_node(self): # TODO add a warning pop up for deleting a node
        if self.node is not None:
            graph = self.node.graph
            graph.delete_nodes([self.node])

    def update_label(self, w_name, val):
        data = self.mutable_labels.get(w_name)

        if not data:
            print("Problem getting mutable label & template")
        
        label, template = data

        if template:
            label.setText(template.format(val))
        

class ToolNode(BaseNode):
    __identifier__ = 'bioinformatics_capstone'
    NODE_NAME = 'Tool'

    def __init__(self, tool=None):
        super(ToolNode, self).__init__()
        self.wrapper = None

        self.tool = tool
        self.cache = None

        self.create_property('tool_type', None)
        self.create_property('tool_data', {})
        
        #only builds if we have a tool so when we load the session, it skips it
        if tool:
            self.build_widgets(tool)
       
        """ 
        Just as an idea for later. Perhaps we could color code what are 'legal' connections, 
        as in certain colors can only go to other colors. Just a thought - Max
        """
        self.add_input('input', color=(0, 255, 0))
        self.add_output('output', color=(0, 0, 255))
    
    def build_widgets(self, tool):
        if not tool or self.wrapper is not None:
                return

        self.tool = tool
        self.wrapper = ToolNodeWrapper(tool, self.view)
        self.set_property('tool_type', tool)
        
        self.wrapper.set_name('_delete') # junk
        #self.set_property('tool_data', self.wrapper.get_value())
        self.add_custom_widget(self.wrapper)

        if self.cache:
            self.wrapper.set_value(self.cache)
            self.cache = None
        else:
            existing_data = self.get_property('tool_data')
            if existing_data:
                self.wrapper.set_value(existing_data)
            else:
                self.model.set_property('tool_data', self.wrapper.get_value())


    def set_property(self, name, val, push_undo=True):
        super(ToolNode, self).set_property(name, val, push_undo=push_undo)

        if name == 'tool_type' and val:
            if not self.wrapper:
                self.build_widgets(val)

        elif name == 'tool_data' and val:
            if self.wrapper:
                self.wrapper.set_value(val)


    def on_input_connected(self, in_port, out_port):
        super(ToolNode, self).on_input_connected(in_port, out_port)

        t_type = self.get_property('tool_type')
        if t_type and not self.wrapper:
            self.build_widgets(t_type)

    def get_value(self):
        return self.wrapper.get_value() if self.wrapper else {}


class DataNode(BaseNode):
    def __init__(self):
        super(DataNode, self).__init__()
        self.uri = None


    @abstractmethod
    def check_format_against_consumer(self): # later function to check if two connected nodes are valid
        pass

class InputNodeWrapper(NodeBaseWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.uri = None

        container = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout()
        
        # self.label = QtWidgets.QLabel("No file selected")

        btn = QtWidgets.QPushButton('Input FASTQ File')
        btn.clicked.connect(self.open_file)

        layout.addWidget(btn)
        # layout.addWidget(self.label)

        container.setLayout(layout)
        self.set_custom_widget(container)

    def open_file(self):
        file_dialog = QtWidgets.QFileDialog()
        file_dialog.setNameFilter('*.fastq')

        if file_dialog.exec():
            files = file_dialog.selectedFiles()
            if files:
                self.uri = files[0]
                # self.label.setText(self.uri)

    def get_value(self):
        if not self.uri:
            return {}
        return {"reads": [self.uri]}

    def set_value(self, val):
        pass

# Node responsible for the accepting of data
class InputNode(DataNode):
    __identifier__ = 'bioinformatics_capstone'
    NODE_NAME = 'Input'

    def __init__(self):
        super().__init__()
        self.add_output('output', color=(0,255, 0))

        self.wrapper = InputNodeWrapper(self.view)

        self.wrapper.set_name('input_data')
        self.add_custom_widget(self.wrapper)

    def get_value(self):
        return self.wrapper.get_value()

    

# Node responsible for the exporting of data
# maybe it'd just be better if each tool node was able to export data once it was done processing?
class OutputNode(DataNode):
    __identifier__ = 'bioinformatics_capstone'
    NODE_NAME = 'Output'

    def __init__(self):
        super().__init__()
        self.add_input('input', color=(0,0,255))

        # self.wrapper = None
        # self.add_custom_widget(self.wrapper)



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
    