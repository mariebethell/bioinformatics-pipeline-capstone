"""
This file contains code for the node based GUI built using PySide6 and NodeGraphQt.
"""

from PySide6 import QtWidgets
from NodeGraphQt import NodeGraph, BaseNode, NodeBaseWidget, NodesPaletteWidget
import subprocess
from pathlib import Path

# FastQC custom nodes and widget
# Each node needs a Node class, Widget class, and Widget wrapper class
class FastQCWidget(QtWidgets.QWidget):
    # Widgets are the buttons, dropdowns, and other UI features that can be added to node.
    # The FastQC Widget includes a button to select the directory, a label for the selected directory, and a button for running the node.
    def __init__(self, parent=None):
        super(FastQCWidget, self).__init__(parent) # Inherit from the QWidget class

        # Define a horizontal layout
        layout = QtWidgets.QHBoxLayout()
        layout.setContentsMargins(0,0,0,0)
        self.setLayout(layout)

        self.label = QtWidgets.QLabel("No folder selected") # Default text for directory, will be changed later when directory is selected
        self.label.setWordWrap(True)
                
        self.label.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.MinimumExpanding)

        self.setMinimumWidth(200)
        
        layout.addWidget(self.label)

        self.button = QtWidgets.QPushButton("Select Directory")
        layout.addWidget(self.button)

        self.run_button = QtWidgets.QPushButton("Run")
        layout.addWidget(self.run_button)

class FastQCWidgetWrapper(NodeBaseWidget):
    def __init__(self, parent=None):
        super(FastQCWidgetWrapper, self).__init__(parent) # Inherit from the NodeBaseWidget class

        self.set_name('fastqc_widget')
        self.set_custom_widget(FastQCWidget())

    def get_value(self):
        return self.get_custom_widget().label.text()

    def set_value(self, value):
        self.get_custom_widget().label.setText(value)
        
class FastQCNode(BaseNode):
    __identifier__ = "practice.nodes"

    NODE_NAME = "FastQCNode"

    def __init__(self):
        super(FastQCNode, self).__init__()

        self.set_layout_direction(0)
        self.add_output('out')

        self.widget = FastQCWidgetWrapper(self.view)
        self.add_custom_widget(self.widget)

        self.custom_widget = self.widget.get_custom_widget()

        self.custom_widget.button.clicked.connect(self.select_directory) # The method select_directory can be passed in as an argument
        self.custom_widget.run_button.clicked.connect(self.run_fastqc)

    def select_directory(self):
        """
        Opens directory selection dialog and updates the label to the selected directory.
        """
        try:
            directory = QtWidgets.QFileDialog.getExistingDirectory(None, "Select Folder", "")

            if directory:
                self.custom_widget.label.setText(f"Selected directory: {directory}")
            else:
                self.custom_widget.label.setText("Selection cancelled")
        except Exception as e:
            print("Directory selection error:", e)

    def run_fastqc(self):
        project_dir = Path(__file__).resolve().parent
        # Test
        result = subprocess.run(["wsl", "nextflow", "main.nf"], cwd=project_dir, capture_output=True, text=True)
        
        # Print the output
        print("STDOUT:", result.stdout)
        print("STDERR:", result.stderr)

if __name__ == '__main__':
        app = QtWidgets.QApplication()

        graph = NodeGraph()
        graph.register_node(FastQCNode)

        graph_widget = graph.widget
        graph_widget.show()

        fastqc_node = graph.create_node('practice.nodes.FastQCNode', name="FastQC Node", pos=(200, 350))

        app.exec()
        #node_a.set_output(0, node_b.input(0)) # you can automatically specify if a node is connected to the other

        