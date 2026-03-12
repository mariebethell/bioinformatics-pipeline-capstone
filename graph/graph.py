from enum import Enum

class StageState(Enum):
    NEW = 0,
    INIT = 1,
    STOPPED = 2,
    RUNNING = 3,
    COMPLETED = 4,
    ERROR = 5

class Node:
    def __init__(self, node_num, tool):
        self.node_num = node_num
        self.tool = tool
        self.args = {}
        self.inputs = {}
        self.outputs = {}
        self.prev_node: Node
        self.next_node: Node
        self.state = StageState.NEW

    def can_accept_input(self, in_type):
        """
        Sets the in_type attribute with the file type that can be processed by this tool.
    
        :param in_type: file extension that can be accepted, e.g. fastq
        """
        self.in_type = in_type

    def to_string(self):
        print(f"Node number: {self.node_num}")
        print(f"Tool: {self.tool}")
        print(f"Arguments: {self.args}")
        print(f"Inputs: {self.inputs}")
        print(f"Outputs: {self.outputs}")
        if (self.prev_node != None):
            print(f"Previous node: {self.prev_node.node_num}, {self.prev_node.tool}")
        if (self.next_node != None):
            print(f"Next node: {self.next_node.node_num}, {self.next_node.tool}")
        print(f"Current State: {self.state}")

class Graph:
    def __init__(self):
        self.nodes = {} # Dictionary of node num keys and Nodes. A dict automatically preserves the order of insertion since Python 3.7.
    
    def get_node(self, node_num) -> Node:
        return self.nodes[node_num]
    
    def get_first_node(self) -> Node:
        return next(iter((self.nodes).values()), None) # Returns first node or None if graph is empty.

    def add_node(self, node, prev=None, next=None):
        node.prev_node = prev
        node.next_node = next

        self.nodes[node.node_num] = node

    def size(self):
        return len(self.nodes)
    
if __name__ == "__main__":
    graph = Graph()

    first = Node(graph.size(), "FastQC")
    first.can_accept_input("fastq")
    graph.add_node(first)

    second = Node(graph.size(), "Trimmomatic")
    second.can_accept_input("fastq")
    graph.add_node(second)

    first.next_node = second
    second.prev_node = first

    # Test getting node information
    print(graph.get_first_node().to_string())
    print()
    print(graph.get_node(1).to_string())
