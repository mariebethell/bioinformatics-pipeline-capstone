# a base program implementing nodegraphqt

# had to grab PySide6 which has everything from the Qt 6.0+ framework
# wasn't specified in the documentation for NodeGraphQt (unless I missd it)
# https://pypi.org/project/PySide6/


# apparently NodeGraphQt is not compatible with python 3.12+
# have to rollback to 3.11.9
# reinstalled dependencies to 3.11.9 (globally, idk if that'll be a problem)

from PySide6 import QtWidgets 
from NodeGraphQt import NodeGraph, BaseNode, NodeBaseWidget

# this is a custom widget we will be adding to the node
# this widget contains a line for the user to enter text, and a button to send the text to the following node
class InputWidget(QtWidgets.QWidget):

        def __init__(self, parent=None):
                super(InputWidget, self).__init__(parent)
                
                self.line_edit = QtWidgets.QLineEdit() # line edit is a text box where you can enter a string

                self.btn_send = QtWidgets.QPushButton('Send') # push button for sending the word

                layout = QtWidgets.QHBoxLayout(self)
                layout.setContentsMargins(0, 0, 0, 0)

                layout.addWidget(self.line_edit)
                layout.addWidget(self.btn_send)

# this wrapper is what connects the widget to the node, as the widgets are just Qt and nodes are a part of NodeGraphQt
class InputWidgetWrapper(NodeBaseWidget):
        def __init__(self, parent=None):
                super(InputWidgetWrapper, self).__init__(parent)

                self.set_name ('input_widget')
 
                self.set_custom_widget(InputWidget())
        

        def get_value(self):
                widget = self.get_custom_widget()
                return widget.line_edit.text()
        
        def set_value(self, value):
                widget = self.get_custom_widget()
                widget.line_edit.setText(value)

# these are the nodes provided by NodeGraphQt
# this is the node responsible for getting the user's input text
class InputNode(BaseNode):
        #unique identifier, what this does is that it defines the namespace for a node
        __identifier__ = "practice.nodes"

        NODE_NAME = 'Input Node' # initial name

        def __init__(self):
                super(InputNode, self).__init__()

                self.add_output('out') #add output

                self.widget = InputWidgetWrapper(self.view)
                self.add_custom_widget(self.widget)

                #connect button signal
                custom = self.widget.get_custom_widget()
                custom.btn_send.clicked.connect(self.send)

        def send(self):
                # get text
                val = self.widget.get_value()

                out_port = self.output(0) # get output port

                #get connected ports (in this case only ever one)
                for port in out_port.connected_ports():
                        node = port.node()
                        if hasattr(node, "receive"):
                                node.receive(val)

# this is the widget for the output text, containing a combo box of three languages to select from, as well as a text to display the translated word
class OutputWidget(QtWidgets.QWidget):
        def __init__(self, parent=None):
                super(OutputWidget, self).__init__(parent)
                
                #add qcombo box
                self.lang_combo = QtWidgets.QComboBox()
                self.lang_combo.addItems(['japanese', 'chinese', 'thai'])

                self.label = QtWidgets.QLabel('...') #Qtextedit better for long text, this is fine for normal text
                self.label.setWordWrap(True)

                self.label.setStyleSheet("color: red;")
                
                self.label.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.MinimumExpanding)
                
                #size is controlled by the widget, as the node will expand to it (i was having an issue of the text exceeding the width of the node, this fixed it)
                self.setMinimumWidth(200)

                layout = QtWidgets.QHBoxLayout(self)
                layout.setContentsMargins(0, 0, 0, 0)

                layout.addWidget(self.label)
                layout.addWidget(self.lang_combo)

class OutputWidgetWrapper(NodeBaseWidget):
        def __init__(self, parent=None):
                super(OutputWidgetWrapper, self).__init__(parent)

                self.set_name('output_widget')
                self.set_custom_widget(OutputWidget())

        def get_value(self):
                widget = self.get_custom_widget()
                return widget.label.text()
        def set_value(self, value):
                widget = self.get_custom_widget()
                widget.label.setText(str(value))
        def get_language(self): # gets the value from the combo box
                widget = self.get_custom_widget()
                return widget.lang_combo.currentText()

def translate(word, lang): # function to ""translate""" from english to languages
        word = word.lower()

        if word == 'hello': # the only word it supports!
                if lang == 'japanese':
                        return 'konnichiwa'
                elif lang == 'chinese':
                        return 'nihao'
                elif lang == 'thai':
                        return 'sawatdee'
        else:
                return '!?'
        


# this is the node responsible for displaying the translated text to the user, as well as where the user will select a language
class OutputNode(BaseNode):
        __identifier__ = "practice.nodes"

        NODE_NAME = 'Output Node'

        def __init__(self):
                super(OutputNode, self).__init__()

                self.add_input('in', color=(0, 180, 0))

                self.widget = OutputWidgetWrapper(self.view)
                self.add_custom_widget(self.widget)
                

                self._last_data = None # responsible for storing the previous word translated

                # connecting dropdown change signal
                # so when the text is changed in the dropdown, it calls update
                custom = self.widget.get_custom_widget()
                custom.lang_combo.currentTextChanged.connect(self.update)


        def receive(self, data):
                self._last_data = data # gets the original data from the text box
                self.update()

        def update(self):
                if not self._last_data:
                        return
                
                lang = self.widget.get_language()
                result = translate(self._last_data, lang)
                self.widget.set_value(result)





if __name__ == '__main__':
        app = QtWidgets.QApplication()

        graph = NodeGraph()

        graph.register_node(InputNode)
        graph.register_node(OutputNode)

        graph_widget = graph.widget
        graph_widget.show()

        node_a = graph.create_node('practice.nodes.InputNode', name='Input Node (Only Hello)')
        node_b = graph.create_node('practice.nodes.OutputNode', name='Translator Node', pos=(200, 200))

        #node_a.set_output(0, node_b.input(0)) # you can automatically specify if a node is connected to the other

        app.exec()
