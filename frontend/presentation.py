import sys
[sys.path.append(i) for i in ['.', '..']] # Tells Python to search for modules in the parent directories.

from datetime import date, datetime
import json
import re
from collections import deque
import threading
from pathlib import Path
from platform import node
from PySide6 import QtWidgets, QtCore, QtWebEngineWidgets
from NodeGraphQt import NodeGraph, BaseNode, NodeBaseWidget
from NodeGraphQt.qgraphics.node_base import NodeItem
from abc import ABC, abstractmethod
from shared.graph import Graph
from backend.pipeline_builder import PipelineFactory
from backend.tool_registry import ToolRegistry


app = QtWidgets.QApplication([])
class AppFrame(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle('NodePipe: Bioinformatics Pipeline System')

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
        if not input:
            print("ERROR: Input Node must exist within the graph to run the pipeline!")
            return

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



class SettingsController(PanelController):
    """
    This is the Settings Page's controller where commands to change the app will be passed through.
    """
    def __init__(self, app):
        self.view = None
        self.app = app
    
    def init_view(self):
        self.view = SettingsView()
        self.view.save_requested.connect(self.change_app_resolution)
        self.app.content.addWidget(self.view)

        self.app.content.setCurrentWidget(self.view)

    def change_app_resolution(self, size_str):
        try:
            w, h = map(int, size_str.split('x'))

            self.app.setFixedSize(w, h)
        except:
            print('Error when trying to change screen size.')


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
            if '_' in tool: # if the widget is paired
                continue
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
        viewer = self.graph.viewer()
        center = viewer.mapToScene(viewer.viewport().rect().center())

        if tool == 'bwa': # special case for paired node (bwa only)
            self._create_bwa_nodes(center)
        else: # default case
            self.node = ToolNode(tool)
            self.graph.add_node(self.node)
            self.node.set_pos(center.x(), center.y())
        
        self.graph.clear_selection()
        self.close() # closes after a user picks a tool

    def _create_bwa_nodes(self, center):
        x, y = center.x(), center.y()

        index_node = ToolNode('bwa_index')
        mem_node = ToolNode('bwa_mem')

        self.graph.add_node(index_node)
        self.graph.add_node(mem_node)

        index_node.set_pos(x-150, y)
        mem_node.set_pos(x+150, y)

        # getting output port and input port for index and mem
        out_port = index_node.output(0)
        in_port = mem_node.input(0)

        out_port.connect_to(in_port)

        out_port.lock()
        in_port.lock()



    
    def create_input_node(self):
        self.graph.create_node('bioinformatics_capstone.InputNode', name='Input', pos=(40,40))
        self.graph.clear_selection()
        self.close()

    
    def create_output_node(self):
        self.graph.create_node('bioinformatics_capstone.OutputNode', name='Output Checkpoint', pos=(40,40))
        self.graph.clear_selection()
        self.close()

class PipelineWorkbenchVC(PanelController):
    """
    The View-Control portion of the Pipeline Workbench which includes various subfeatures:
    Saving/Loading a Preset, Running the Pipeline, Browsing/Creating Nodes, Purging All Data within the pipeline, and the NodeGraph suite
    """
    def __init__(self, app):
        self.node_graph = NodeGraph()

        self.update_queue = deque(maxlen=100)
        self.update_lock = threading.Lock()




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
            'Node Browser' : self.node_browser,
            'Create New Pipeline' : self.new_pipeline
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
        save_dialog = self.PopupWindow(parent=self.app, type='save')

        if save_dialog.exec() == QtWidgets.QDialog.Accepted:
            raw = save_dialog.save_name()

            if not raw: # generic name including pipeline
                timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
                filename = f'pipeline_{timestamp}.json'
            else:
                clean = raw.replace('.json', '')
                filename = f'{clean}_pipeline.json'

            presets_dir = Path(__file__).parent.absolute() / 'presets'
            presets_dir.mkdir(parents=True, exist_ok=True)

            # ensures that pipeline is added to the filename, so when searching for a file it only looks for things named pipeline
            preset_path = presets_dir / filename

            print(f'Saving to preset path: {preset_path}')

            try:
                self._unlock_bwa_ports()
                self.node_graph.save_session(str(preset_path))
            except:
                print('Problem when saving the session.')

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
            self._unlock_bwa_ports()
            self.node_graph.load_session(path)

    def _unlock_bwa_ports(self):
        for node in self.node_graph.all_nodes():
            if not isinstance(node, ToolNode):
                continue

            if node.tool == 'bwa_index':
                for port in node.output_ports():
                    port.unlock()
            elif node.tool == 'bwa_mem':
                for port in node.input_ports():
                    port.unlock()
    
    def enqueue_update(self, update):
        with self.update_lock:
            self.update_queue.append(update)

    def run_pipeline(self):
        graph = GraphGenerator(self.node_graph)
        graph = graph.from_workbench()


        input_node = graph.get_first_node()
        if not input_node: 
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
        if not self.node_graph.all_nodes():
            print('Empty Node Graph, skipping new pipeline')
            return
        
        warning_dialog = self.PopupWindow(parent=self.app, type='warn', warn_msg='Warning! This will Delete the Current Pipeline!', btn_label='Create New Pipeline')
        if warning_dialog.exec() == QtWidgets.QDialog.Accepted:
            self._unlock_bwa_ports()
            self.node_graph.clear_session()
    
    def node_browser(self):
        if self.tool_palette is None:
                self.tool_palette = NodeBrowser(self.node_graph, parent=self.app)
        self.tool_palette.show()

    def init_view(self):       
        self.app.content.addWidget(self.view)
        self.app.content.setCurrentWidget(self.view)

    def close(self):
        print('closing')

    class PopupWindow(QtWidgets.QDialog):
        """
        An inner class to PipelineWorkbenchVC that allows for multiple different types of popup windows:
        Saving Dialog, Warning Messages
        """

        def __init__(self, parent=None, type=None, warn_msg=None, btn_label=None):
            if not type:
                print('Error in PopupWindow, Type not specified')

            else:
                super().__init__(parent)
                layout = QtWidgets.QVBoxLayout()
                layout.setContentsMargins(5, 5, 5, 5)

                widgets = []

                if type == 'save': # if the popup window is a save window
                    self.setWindowTitle('Save Pipeline')
                    self.input = QtWidgets.QLineEdit()
                    self.input.setPlaceholderText('Enter Filename Here (or None to name it as a generic)')
                    self.input.setMaximumHeight(30)

                    btn = QtWidgets.QPushButton('Save')
                    btn.clicked.connect(self.accept) # when the button is clicked, it closes the dialog and sends an Accepted exit code

                    widgets.append(self.input)
                    widgets.append(btn)
                
                elif type == 'warn':
                    self.setWindowTitle('Warning')
                    label = QtWidgets.QLabel(warn_msg)
                    label.setStyleSheet(
                        """
                        color:red;
                        """
                    )

                    btn = QtWidgets.QPushButton(btn_label)
                    btn.clicked.connect(self.accept)

                    widgets.append(label)
                    widgets.append(btn)
                
                # adds widgets based on window type to the window
                for widget in widgets:
                    layout.addWidget(widget)

                self.setLayout(layout)
                

        def save_name(self):
            filename = self.input.text()

            filename = filename.replace(' ', '_')

            # uses regex to keep only valid characters by
            filename = re.sub(r'[^a-zA-Z0-9._-]', '', filename)

            filename = filename.strip('. ')

            return filename




#### VIEW SECTION ####

#### view styles for text ####

title_text="""
color:white;
font-size:30px;
font-weight:bold;
"""
header_text = """
color: white;
font-size:24px;
font-weight:bold;
"""
body_text = """
color:white;
font-size:16px;
"""
onedrive_text_false ="""
color:red;
font-size:18px;
font-weight:bold;
"""

onedrive_text_true ="""
color:green;
font-size:18px;
font-weight:bold;
"""

link_text = """
font-size:12px;
font-weight:bold
"""
class HomeView(QtWidgets.QWidget):
    """
    This is the Home Page's view, which will display a place to log in to their OneDrive account
    as well as see information about the system
    """
    def __init__(self):
        super().__init__()

        container = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(container)
        layout.setContentsMargins(0,0,0,0)
        layout.setSpacing(2)
        container.setStyleSheet('background-color: #3D3D3D;')
        
        ### TITLE SECTION ###

        title = QtWidgets.QLabel('NodePipe')
        title.setStyleSheet(title_text)
        title.setAlignment(QtCore.Qt.AlignCenter)

        self.onedrive_status = QtWidgets.QLabel('Not logged in to OneDrive! Data will not be saved.')
        self.onedrive_status.setStyleSheet(onedrive_text_false)
        self.onedrive_status.setAlignment(QtCore.Qt.AlignCenter)
        
        #onedrive = QtWidgets.QLabel('OneDrive PlaceHolder')
        #onedrive.setAlignment(QtCore.Qt.AlignCenter)
        
        ## ONEDRIVE SUBSECTION ##
        self.onedrive_container = QtWidgets.QGroupBox('OneDrive Access')
        self.onedrive_container.setStyleSheet('color:white; font-weight:bold')
        self.onedrive_container.setMaximumHeight(600)
        self.onedrive_container.setMaximumWidth(450)
        self.onedrive_container.setAlignment(QtCore.Qt.AlignCenter)

        self.web_view = QtWebEngineWidgets.QWebEngineView()
        web_settings = self.web_view.settings()
        web_settings.setAttribute(web_settings.WebAttribute.JavascriptCanOpenWindows, True)

        od_cont_layout = QtWidgets.QVBoxLayout()
        od_cont_layout.addWidget(self.web_view)
        self.onedrive_container.setLayout(od_cont_layout)

        login_url = 'https://login.microsoftonline.com/common/oauth2/v2.0/authorize'
        self.web_view.setUrl(QtCore.QUrl(login_url))


        spacer = QtWidgets.QSpacerItem(100, 100)

        ### CHANGELOG SECTION ###

        version = 0 # get from somewhere else later.. 
        changelog_title = QtWidgets.QLabel(f'What\'s New In Version: {version}')
        changelog_title.setStyleSheet(header_text)
        changelog_title.setAlignment(QtCore.Qt.AlignCenter)

        changelog_text = QtWidgets.QLabel('Changelog')
        changelog_text.setStyleSheet(body_text)
        changelog_text.setAlignment(QtCore.Qt.AlignCenter)

        ### WELCOME SECTION ###

        welcome_title = QtWidgets.QLabel('Welcome to NodePipe!')
        welcome_title.setStyleSheet(title_text)
        welcome_title.setAlignment(QtCore.Qt.AlignCenter)

        welcome_text = QtWidgets.QLabel('To get started, head to the Pipeline Workbench and create a NodeGraph!')
        welcome_text.setStyleSheet(body_text)
        welcome_text.setAlignment(QtCore.Qt.AlignCenter)

        ### DOCUMENTATION SECTION ###

        link = '<a href="https://github.com/mariebethell/bioinformatics-pipeline-capstone"><span style="color:#FFA100;">See Our Documentation</span></a>'
        documentation_link = QtWidgets.QLabel(link)
        documentation_link.setStyleSheet(link_text)
        documentation_link.setAlignment(QtCore.Qt.AlignCenter)
        documentation_link.setOpenExternalLinks(True)

        layout.addWidget(title)
        layout.addWidget(self.onedrive_status)
        layout.addWidget(self.onedrive_container, alignment=QtCore.Qt.AlignCenter)
        #layout.addItem(spacer)
        
        layout.addWidget(changelog_title)
        layout.addWidget(changelog_text)
        layout.addItem(spacer)

        layout.addWidget(welcome_title)
        layout.addWidget(welcome_text)
        layout.addItem(spacer)

        layout.addStretch(1)
        layout.addWidget(documentation_link)
        container.setLayout(layout)

        outer_layout = QtWidgets.QVBoxLayout()
        outer_layout.addWidget(container)
        
        self.setLayout(outer_layout)






class SettingsView(QtWidgets.QWidget):
    """
    This is the Setting Page's view, which actually displays information to the user to change app-wide settings
    """

    save_requested = QtCore.Signal(str)
    def __init__(self):
        super().__init__()

        container = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(container)
        layout.setContentsMargins(0,0,0,0)
        layout.setSpacing(2)
        container.setStyleSheet('background-color: #3D3D3D;')
        
        ### TITLE SECTION ###
        title = QtWidgets.QLabel('NodePipe Settings')
        title.setStyleSheet(title_text)
        title.setAlignment(QtCore.Qt.AlignCenter)

        ### SETTINGS SECTION ###
        window_size_label = QtWidgets.QLabel('Change App Size')
        window_size_label.setStyleSheet(body_text)
        window_size_label.setAlignment(QtCore.Qt.AlignCenter)

        self.window_size_combo = QtWidgets.QComboBox()

        self.window_size_combo.setStyleSheet('background-color: white; color:black;')
        self.window_size_combo.addItems(self._get_screen_sizes())
        self.window_size_combo.setMinimumContentsLength(100)

        

        self.done_btn = QtWidgets.QPushButton('Save Changes')
        self.done_btn.setStyleSheet(
            'background-color: green; color: white;'
            )
        self.done_btn.clicked.connect(self._on_save_clicked)
        
        layout.addWidget(window_size_label)
        layout.addWidget(self.window_size_combo, alignment=QtCore.Qt.AlignCenter)
        
        layout.addWidget(self.done_btn, alignment=QtCore.Qt.AlignCenter)

        outer_layout = QtWidgets.QVBoxLayout()
        outer_layout.addWidget(container)

        self.setLayout(outer_layout)
        
    def _get_screen_sizes(self):
        screen = app.primaryScreen()
        size = screen.size()
        scr_w = size.width()
        scr_h = size.height()
        
        mod = 0.5 # screen size modifier
    

        sizes = []

        # appending screen sizes up to 100% of the user's screen size (from 50%)
        while mod <= 0.8:
            w = int(scr_w * mod)
            h = int(scr_h * mod)

            sizes.append(f'{w}x{h}')
            mod += 0.1

        return sizes   
    
    def _on_save_clicked(self):
        selected_size = self.window_size_combo.currentText()
        self.save_requested.emit(selected_size)



#### NODE SECTION ####

# a dictionary of a list for each tool, containing a dictionary of widget types where each tool will contain what type of widget it will have and the fields for each widget

# widget definitions to increase readability and make it easier to add widgets
#TODO add tooltips to each widget

def slider_widget(name, label, nullable=False, default=1, min=1, max=1, section=None):
    return {'type': 'slider', 'name': name, 'label': f'{label}: {default}', 'label_template': f'{label}: {{}}', 'default': default, 'need_label': True, 'min': min, 'max': max, 'nullable' : nullable, 'section' : section }
def checkbox_widget(name, label, section=None): 
    return {'type': 'checkbox', 'name': name, 'label': label, 'default': False, 'need_label': False, 'section' : section }
def text_entry_widget(name, label, nullable=False, section=None):
    return {'type': 'text_entry', 'name': name, 'label': label, 'default': None, 'need_label': False, 'nullable': nullable, 'section' : section } 
def combo_box_widget(name, label, default=None, items=[], nullable=False, section=None):
    return {'type': 'combo_box', 'name': name, 'label': label, 'default': default, 'need_label': True, 'items': items, 'nullable': nullable, 'section' : section }
def num_input_widget(name, label, step=1, default=1, nullable=False, min=1, max=100, section=None):
    return {'type': 'num_input', 'name': name, 'label': label, 'step' : step, 'default': default, 'need_label': True, 'min': min, 'max': max, 'nullable' : nullable, 'section' : section }

# common widgets
threads_slider = slider_widget('threads', 'Number of Threads', min=1, max=128)
quiet_check = checkbox_widget('quiet', 'Quiet')

SECTION_CONFIGS = {
"""
A dictionary of sub section configs for tools that require them
"""
    'trimmomatic': {
        'ILLUMINACLIP': {'label': 'Illumina Clip'},
        'LEADING': {'label': 'Leading'},
        'TRAILING': {'label': 'Trailing'},
        'HEADCROP': {'label': 'Head Crop'},
        'TAILCROP': {'label': 'Tail Crop'},
        'CROP': {'label': 'Crop'},
        'SLIDINGWINDOW': {'label': 'Sliding Window'},
        'MAXINFO': {'label': 'Max Info'},
        'MINLEN': {'label': 'Min Length'},
        'MAXLEN': {'label': 'Max Length'},
        'AVGQUAL': {'label': 'Avg Quality'},
        'BASECOUNT': {'label': 'Base Count'}
    }
}

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
    'trimmomatic' : [
        threads_slider,
        combo_box_widget('mode', 'Mode', items=['SE', 'PE']),
        combo_box_widget('phred', 'Phred', items=['33', '64'], nullable=True),
        #checkbox_widget('trimlog', 'Trimlog'),
        #checkbox_widget('summary', 'Summary'),
        #checkbox_widget('basein', 'Basein'),
        #checkbox_widget('baseout', 'Baseout'),
        checkbox_widget('validate_pairs', 'Validate Pairs'),
        slider_widget('compress_level', 'Compression Level', max=9),
        combo_box_widget('compression_mode', 'Compression Mode', items=['stream', 'block'], nullable=True),
        quiet_check,

        # illumina clip
        text_entry_widget('fasta_with_adapters', 'FASTA File Path (CHANGE LATER TO FILE UPLOAD!)', section='ILLUMINACLIP'),
        num_input_widget('seed_mismatches', 'Maximum Seed Mismatches', section='ILLUMINACLIP'),
        num_input_widget('palindrome_clip_threshold', 'Palindrome Clip Threshold', section='ILLUMINACLIP'),
        num_input_widget('simple_clip_threshold', 'Simple Clip Threshold', section='ILLUMINACLIP'),
        num_input_widget('min_adapter_length_palindrome', 'Min Adapter Length', nullable=True, section='ILLUMINACLIP'),
        checkbox_widget('keep_both_reads', 'Keep Both Reads?', section='ILLUMINACLIP'),

        # leading
        num_input_widget('leading', 'Trim Leading Below: ', section='LEADING'),

        # trailing
        num_input_widget('trailing', 'Trim Trailing Below: ', section='TRAILING'),

        # head_crop
        num_input_widget('head_crop', 'Crop # from start of read:', section='HEADCROP'),

        # tail_crop
        num_input_widget('trail_crop', 'Trim tail', section='TAILCROP'),

        # crop
        num_input_widget('crop', 'Crop reads to this length: ', section='CROP'),

        # sliding window
        num_input_widget('sliding_window_size', 'Sliding Window Size: ', section='SLIDINGWINDOW'),
        num_input_widget('required_quality', 'Minimum average quality required in the window: ', section='SLIDINGWINDOW'),

        # max info
        num_input_widget('target_length', 'Target read length: ', section='MAXINFO'),
        slider_widget('strictness', 'Strictness value', default=0, min=0, max=1, section='MAXINFO'),

        # min_len, max_len, avg_qual
        num_input_widget('min_len', 'Discard reads shorter than this length: ', section='MINLEN'),
        num_input_widget('max_len', 'Discard reads longer than this length: ', section='MAXLEN'),
        num_input_widget('avg_qual', 'Discard reads with average quality below: ', section='AVGQUAL'),

        # base_count widgets
        text_entry_widget('bases', 'Bases to count: ', section='BASECOUNT'),
        num_input_widget('min_count', 'Minimum allowed count: ', nullable=True, section='BASECOUNT'),
        num_input_widget('max_count', 'Maximum allowed count: ', nullable=True, section='BASECOUNT')
        
    ],

    'trinity' : [
        combo_box_widget('seq_type', 'Sequence Type', items=['fq', 'fa']),
        slider_widget('cpu', "Number of CPU Threads", max=128),
        slider_widget('max_memory', 'Memory to Use (GB)', max=32)
    ],

    'bwa' : [], # empty as we need widgets for its two sub nodes
    'bwa_index' : [

    ],
    'bwa_mem' : [

    ]
}


# Node responsible for representing a tool within the pipeline & its wrapper
#TODO Tooltips
class ToolNodeWrapper(NodeBaseWidget):
    """
    This is the Tool Node's wrapper, responsible for the saving and retrieving of data within the ToolNode.
    The wrapper also handles self-deletion
    """
    def __init__(self, tool=None, parent=None):
        super().__init__(parent)
        
        self.tool = tool
        
        # inner storage
        self.widgets = {}
        self.mutable_labels = {}
        self.nullable_checks = {} # certain widgets can be nullable. this dictionary maps checkboxes to the nullable widgets

        self.substep_defs = []
        self.substep_vals = {}
        self.section_states = {}


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

        layout = QtWidgets.QVBoxLayout(container)
        layout.setContentsMargins(0,0,0,0)

        node_title = QtWidgets.QLabel(self.tool)
        node_title.setAlignment(QtCore.Qt.AlignCenter)
        node_title.setStyleSheet('color: orange; font-size:24px; font-weight:bold;')
        layout.addWidget(node_title)


        # building widgets dynamically
        for widget_def in NODE_WIDGETS[tool]:
            # if it is a substep, we save it for the substep dialog and continue
            section = widget_def.get('section')
            if section:
                self.substep_defs.append(widget_def)
                continue
            
            # building widgets by passing in the layout so the helper knows where to build widgets and passing in the update label callback in case a label needs to be updated
            widget, checkbox, label = self.build_widget_from_def(widget_def, layout, self.update_label)

            if widget:
                name = widget_def['name']
                self.widgets[name] = widget

                # if a checkbox exists, there is a nullable space
                if checkbox:
                    self.nullable_checks[name] = checkbox
                
                # if a label exists and the widget is a slider, we create an extra mutable label for it
                if label and widget_def['type'] == 'slider':
                    self.mutable_labels[name] = (label, widget_def.get('label_template'))

        # button creation section
        # add a button for a substep page if one needs to be made
        if self.substep_defs:
            substep_btn = QtWidgets.QPushButton('Configure Substeps')
            substep_btn.setStyleSheet('background-color: orange;')
            substep_btn.clicked.connect(self.open_substeps)
            layout.addWidget(substep_btn) 

               
        # adds a delete button to the end of EVERY node 
        delete_btn = QtWidgets.QPushButton('Delete Node')
        delete_btn.clicked.connect(self.delete_node)
        delete_btn.setStyleSheet('background-color:red; color:white;')
        layout.addWidget(delete_btn)

        container.setLayout(layout)
        self.set_custom_widget(container)


    @staticmethod
    def build_widget_from_def(widget_def, parent_layout, update_callback=None, widget_section=None):
        """
        Helper static function to build widgets in both the wrapper and subset dialog,
        given a layout and widget definition
        """
        w_type = widget_def['type']
        w_name = widget_def['name']
        w_label = widget_def['label']
        w_default = widget_def.get('default', None)
        nullable = widget_def.get('nullable', False)
        need_label = widget_def.get('need_label', False)

        widget = None
        checkbox = None
        label = None

        if w_type == 'slider': 
                widget = QtWidgets.QSlider(QtCore.Qt.Horizontal)
                
                widget.setMinimum(widget_def['min'])
                widget.setMaximum(widget_def['max'])
                
                widget.setValue(w_default)


                # lambda function passes in the current widget name and the value from the signal to update label
                widget.valueChanged.connect(
                    lambda value : update_callback(w_name, value)
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

        elif w_type == 'num_input':
            widget = QtWidgets.QSpinBox()

            widget.setMinimum(widget_def['min'])
            widget.setMaximum(widget_def['max'])

            widget.setSingleStep(widget_def['step'])
            widget.setValue(w_default)
            

        # handling widget layout
        if widget:
            # creates a space of widgets that are nullable by a checkbox (default nulled)
            if nullable:
                checkbox = QtWidgets.QCheckBox()
                
                widget.setEnabled(False)
                checkbox.toggled.connect(widget.setEnabled)

                label = QtWidgets.QLabel('Enable ' + w_label)
                nullable_space = QtWidgets.QHBoxLayout()
                nullable_space.addWidget(checkbox)
                nullable_space.addWidget(label)
                nullable_space.addWidget(widget)

                parent_layout.addLayout(nullable_space)
            else:
                if need_label:
                    label = QtWidgets.QLabel(w_label)
                    parent_layout.addWidget(label)
                parent_layout.addWidget(widget)


            return widget, checkbox, label
        

    def open_substeps(self):
        dialog = self.SubstepDialog(self.tool, self.substep_defs, None)

        # filling dialog with values(!) stored in the wrapper
        for name, widget in dialog.widgets.items():
            if name in self.substep_vals:
                existing_val = self.substep_vals[name]

                # setting values in the dialog's widgets from existing values
                if isinstance(widget, QtWidgets.QSlider) or isinstance(widget, QtWidgets.QSpinBox):
                    widget.setValue(int(existing_val))
                elif isinstance(widget, QtWidgets.QCheckBox):
                    widget.setChecked(bool(existing_val))
                elif isinstance(widget, QtWidgets.QPlainTextEdit):
                    widget.setPlainText(str(existing_val))
                elif isinstance(widget, QtWidgets.QComboBox):
                    index = widget.findText(str(existing_val))
                    if index >= 0:
                        widget.setCurrentIndex(index)

        for section, data in dialog.sections.items():
            if section in self.section_states:
                data['checkbox'].setChecked(self.section_states[section])
                data['layout'].parentWidget().setEnabled(self.section_states[section])

        if dialog.exec() == QtWidgets.QDialog.Accepted:

            # saving widget values
            for name, widget in dialog.widgets.items():
                if isinstance(widget, QtWidgets.QSlider) or isinstance(widget, QtWidgets.QSpinBox):
                    self.substep_vals[name] = widget.value()
                elif isinstance(widget, QtWidgets.QCheckBox):
                    self.substep_vals[name] = widget.isChecked()
                elif isinstance(widget, QtWidgets.QPlainTextEdit):
                    self.substep_vals[name] = widget.toPlainText()
                elif isinstance(widget, QtWidgets.QComboBox):
                    self.substep_vals[name] = widget.currentText()

            # storing section states
            self.section_states = {
                section: data['checkbox'].isChecked()
                for section, data in dialog.sections.items()
            }

            # retaining nullable widgets
            for name, check in dialog.nullable_checks.items():
                self.nullable_checks[name] = check

    def get_value(self):
        values = {} # this set will contain the values returned, in order of: slider, checkboxes, strings, then combo box
        # if there is more sensible way to return it, PLEASE modify this.

        for name, item in self.widgets.items():

            # if it is already a value (from a closed dialog) it is simply used
            if not isinstance(item, QtWidgets.QWidget):
                # if it is a disabled nullable item
                if name in self.nullable_checks and self.nullable_checks[name] is False:
                    continue
                values[name] = item
                continue
            
            # otherwise it is a widget
            widget = item


            #checks if both the checkbox exists and if it is not checked 
            checkbox = self.nullable_checks.get(name) 

            if isinstance(checkbox, QtWidgets.QCheckBox) and not checkbox.isChecked():
                continue
            elif checkbox is False:
                continue

            if isinstance(widget, QtWidgets.QSlider) or isinstance(widget, QtWidgets.QSpinBox):
                values[name] = widget.value()
            elif isinstance(widget, QtWidgets.QCheckBox):
                if(widget.isChecked()): # will not append to list
                    values[name] = widget.isChecked()
            elif isinstance(widget, QtWidgets.QPlainTextEdit):
                values[name] = widget.toPlainText()
            elif isinstance(widget, QtWidgets.QComboBox):
                values[name] = widget.currentText()
            else:
                values[name] = None

        #values.update(self.substep_vals)

        for name, val in self.substep_vals.items():
            widget_def = next((w for w in self.substep_defs if w['name'] == name), None)

            if widget_def:
                section = widget_def.get('section')

                if section:
                    if not self.section_states.get(section, False):
                        continue
            
            values[name] = val

        return values

    def set_value(self, val_dict):
        for name, val, in val_dict.items():
            widget = self.widgets.get(name)

            if widget is None:
                continue
            if isinstance(widget, QtWidgets.QSlider) or isinstance(widget, QtWidgets.QSpinBox):
                widget.setValue(val)
            elif isinstance(widget, QtWidgets.QCheckBox):
                widget.setChecked(val)
            elif isinstance(widget, QtWidgets.QPlainTextEdit):
                widget.setPlainText(str(val))
            elif isinstance(widget, QtWidgets.QComboBox):
                index = widget.findText(str(val))
                if index >= 0:
                    widget.setCurrentIndex(index)
            
    def delete_node(self): 
        if self.node is not None:
            warning_dialog = PipelineWorkbenchVC.PopupWindow(parent=None, type='warn', warn_msg=f'Warning! \nAll unsaved {self.tool} data and parameters will be lost!', btn_label=f'Delete {self.tool} Node')
            if warning_dialog.exec() == QtWidgets.QDialog.Accepted:
                if self.tool == 'bwa_index':
                    self.node.output(0).unlock()
                elif self.tool == 'bwa_mem':
                    self.node.input(0).unlock()
                graph = self.node.graph
                graph.delete_nodes([self.node])

    def update_label(self, w_name, val):
        data = self.mutable_labels.get(w_name)

        if not data:
            print("Problem getting mutable label & template")
        
        label, template = data

        if template:
            label.setText(template.format(val))

    class SubstepDialog(QtWidgets.QDialog):
        """
        An inner class for nodes who have substeps to have a separate window for optional parameters
        Ideally, this would be a part of the node but NodeGraphQt has limitations on node resizing (as the system itself is not very dynamic..)
        so this is a temporary solution.
        """
        def __init__(self, title, widgets_def, parent=None):
            super().__init__(parent)

            self.setWindowTitle(f'{title} Settings')
            self.setMinimumWidth(400)

            layout = QtWidgets.QGridLayout(self)
            layout.setContentsMargins(5,5,5,5)
            layout.setHorizontalSpacing(10)
            layout.setVerticalSpacing(8)

            self.widgets = {}
            self.nullable_checks = {}
            self.mutable_labels = {}
            self.sections = {}
            section_layouts = {}

            tool_sections = SECTION_CONFIGS.get(title, {})

            section_layouts = {}

            row = 0

            for widget_def in widgets_def:
                section = widget_def.get('section')

                # section handling
                if section:
                    if section not in section_layouts:
                        section_container = QtWidgets.QWidget()
                        section_box = QtWidgets.QVBoxLayout(section_container)
                        section_box.setContentsMargins(5,5,5,5)

                        section_container.setStyleSheet('background-color: #E3E3E3;')

                        config = tool_sections.get(section, {})
                        sec_label = config.get('label', section)
        

                        checkbox = QtWidgets.QCheckBox(f'Enable {sec_label}')
                        checkbox.setChecked(False)


                        
                        inner_widget = QtWidgets.QWidget()
                        inner_layout = QtWidgets.QHBoxLayout(inner_widget)
                        inner_widget.setLayout(inner_layout)
                        inner_widget.setEnabled(False)

                        def make_toggle(w):
                            return lambda state: w.setEnabled(state)
                        
                        checkbox.toggled.connect(make_toggle(inner_widget))

                        section_box.addWidget(checkbox)
                        section_box.addWidget(inner_widget)

                        layout.addWidget(section_container, row, 0, 1, 2)
                        row += 1

                        self.sections[section] = {
                            'checkbox' : checkbox,
                            'layout' : inner_layout
                        }

                        section_layouts[section] = inner_layout
                    
                    parent_layout = section_layouts[section]
                else:
                    parent_layout = None
                
                # building widgets
                widget, checkbox, label = ToolNodeWrapper.build_widget_from_def(widget_def, parent_layout, self.update_label_local)

                if widget:
                    w_name = widget_def['name']
                    self.widgets[w_name] = widget

                    if checkbox:
                        self.nullable_checks[w_name] = checkbox
                    
                    if label and widget_def['type'] == 'slider':
                        self.mutable_labels[w_name] = (label, widget_def.get('label_template'))
                    
                    if not section:
                        layout.addWidget(label if label else QtWidgets.QLabel(''), row, 0)
                        layout.addWidget(widget, row, 1)
                        row += 1
                
            self.done_btn = QtWidgets.QPushButton('Save Changes')
            self.done_btn.setStyleSheet(
                'background-color: green; color: white;'
            )
            self.done_btn.clicked.connect(self.accept)
            layout.addWidget(self.done_btn, row, 0, 1, 2)
    
        def update_label_local(self, w_name, val):
            data = self.mutable_labels.get(w_name)

            if not data:
                print('Problem getting mutable label & template in SubstepDialog')
            
            label, template = data

            if template:
                label.setText(template.format(val))
            
        def toggle_section(self, layout, enabled):
            for idx in range(layout.count()):
                item = layout.itemAt(idx)

                if item.widget():
                    item.widget().setEnabled(enabled)
                elif item.layout():
                    self.toggle_section(item.layout(), enabled)
                

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

        # rebuilds widgets for tools when loading a preset, as loading the preset sends an input connected signal
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

        btn = QtWidgets.QPushButton('Input FASTQ File')
        btn.clicked.connect(self.open_file)

        layout.addWidget(btn)

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
                if self.node: # updating node property so the uri gets saved
                    self.node.set_property('file_uri', self.uri)

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

        self.create_property('file_uri', '')

        self.wrapper = InputNodeWrapper(self.view)

        self.wrapper.set_name('input_data')
        self.add_custom_widget(self.wrapper)

    def get_value(self):
        uri = self.get_property('file_uri')
        return {"reads" : [uri]} if uri else {}
        #return self.wrapper.get_value()

    def set_property(self, name, val, push_undo=True):
        super(InputNode, self).set_property(name, val, push_undo)
        if name == 'file_uri' and self.wrapper:
            self.wrapper.uri = val

    

class OutputNodeWrapper(NodeBaseWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.uri = None
        self.dataTimestamp = None
        self.dataName = None
        self.is_available = False

        self.tool = None

        container = QtWidgets.QWidget()
        container.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
        layout = QtWidgets.QVBoxLayout()


        self.tool_label = QtWidgets.QLabel('Connected Tool: None')
        self.data_label = QtWidgets.QLabel('Data Name: None')
        self.timestamp_label = QtWidgets.QLabel('Timestamp: None')
        

    
        

        dl_button = QtWidgets.QPushButton('Download Results')
        dl_button.setStyleSheet('background-color: green; color: white;')
        dl_button.clicked.connect(self.download_data)
        

        purge_button = QtWidgets.QPushButton('Purge Data')
        purge_button.setStyleSheet('background-color: red; color:white;')
        purge_button.clicked.connect(self._purge_data)

        stats_button = QtWidgets.QPushButton('View Stats')
        stats_button.setStyleSheet('background-color: orange; color:white')
        stats_button.clicked.connect(self.view_stats)

        for label in [self.tool_label, self.data_label, self.timestamp_label]:
            label.setStyleSheet('color:white; font-weight:bold;')
            layout.addWidget(label, alignment=QtCore.Qt.AlignCenter)

        for button in [dl_button, purge_button, stats_button]:
            button.setEnabled(False)
            layout.addWidget(button, alignment=QtCore.Qt.AlignCenter)

        container.setLayout(layout)
        self.set_custom_widget(container)


    def download_data(self):
        pass

    def open_data(self):
        pass

    def view_stats(self):
        pass
    
    def _update(self, uri):
        pass

    def _purge_data(self):
        pass

    def _update_tool_label(self, tool):
        self.tool = tool
        self.tool_label.setText(f'Connected Tool: {tool}')

    def get_value(self):
        pass

    def set_value(self, val):
        pass
class OutputNode(DataNode):
    __identifier__ = 'bioinformatics_capstone'
    NODE_NAME = 'Output Checkpoint'

    def __init__(self):
        super().__init__()
        self.add_input('input', color=(0,0,255))

        self.wrapper = OutputNodeWrapper(self.view)
        self.wrapper.set_name('output_data')

        self.add_custom_widget(self.wrapper)


    def on_input_connected(self, in_port, out_port):
        super().on_input_connected(in_port, out_port)

        src_node = out_port.node()

        if hasattr(src_node, 'tool'):
            self.wrapper._update_tool_label(src_node.tool)
        else:
            pass


    def on_input_disconnected(self, in_port, out_port):
        super().on_input_disconnected(in_port, out_port)

        self.wrapper._update_tool_label('None')

        



if __name__ == '__main__':


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
    