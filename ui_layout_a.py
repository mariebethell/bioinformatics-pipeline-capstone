from PySide6 import QtWidgets
from NodeGraphQt import NodeGraph, BaseNode, NodeBaseWidget

#basic widget for node
class TestNodeWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.button = QtWidgets.QPushButton('Send')

        layout = QtWidgets.QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        layout.addWidget(self.button)

#basic wrapper for test node
class TestNodeWidgetWrapper(NodeBaseWidget):
    def __init__(self, parent=None):
            super(TestNodeWidgetWrapper, self).__init__(parent)

            self.set_name ('input_widget')

            self.set_custom_widget(TestNodeWidget())

    def get_value(self):
        return None
    def set_value(self, value):
        pass

#basic node
class TestNode(BaseNode):
    __identifier__ = 'practice'
    NODE_NAME = "Practice"

    def __init__(self):
        super(TestNode, self).__init__()

        self.widget = TestNodeWidgetWrapper(self.view)
        self.add_custom_widget(self.widget)

        custom = self.widget.get_custom_widget()
        custom.button.clicked.connect(self.button_activity)


    def button_activity(self):
        print('button!\n')

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()

        main_layout = QtWidgets.QHBoxLayout() # this represents a main layout (for the graph)
        side_layout = QtWidgets.QVBoxLayout() # this represents the side layout

        main_layout.setContentsMargins(10, 10, 10, 10)

        side_layout.setContentsMargins(5, 5, 5, 5)

        graph = NodeGraph() # graph
        g_widget = graph.widget
        g_widget.setFixedSize(main_layout.get)

        self.terminal = QtWidgets.QTextEdit()
        self.terminal.setReadOnly(True)
        font = self.terminal.font()
        font.setFamily("Consolas")
        self.terminal.setFont(font)

        buttons = {'Save Preset' : self.save_preset,
                   'Load Preset' : self.load_preset,
                   'Stop Running' : self.stop_running}

        for text, func in buttons.items():
            btn = QtWidgets.QPushButton(text)
            btn.clicked.connect(func)
            side_layout.addWidget(btn)

        side_layout.addWidget(self.terminal, 1)
        graph.register_node(TestNode)

        graph.add_node = graph.create_node('practice.TestNode', name='test')
        side_layout.addStretch()

        main_layout.addLayout(side_layout)
        main_layout.addWidget(g_widget)
        widget = QtWidgets.QWidget()
        widget.setLayout(main_layout)
        self.setCentralWidget(widget)

    def save_preset(self):
        self.terminal.append('Saved!\n')

    def load_preset(self):
        self.terminal.append('Load!\n')

    def stop_running(self):
        self.terminal.append('Stopped!\n')


if __name__ == '__main__':
    app = QtWidgets.QApplication([])

    window = MainWindow()
    window.show()

    app.exec()
