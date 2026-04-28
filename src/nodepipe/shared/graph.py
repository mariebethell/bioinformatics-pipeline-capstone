from enum import Enum

class StageState(Enum):
    NEW = 0
    INIT = 1
    STOPPED = 2
    RUNNING = 3
    COMPLETED = 4
    ERROR = 5

class Node:
    def __init__(self, node_num, tool, args=None, inputs=None):
        self.node_num = node_num
        self.tool = tool
        self.args = args
        self.inputs = inputs
        self.outputs = {}
        self.prev_node: Node | None = None
        self.next_node: Node | None = None
        self.state = StageState.NEW
        

    def can_accept_input(self, in_type):
        """
        Sets the in_type attribute with the file type that can be processed by this tool.
    
        :param in_type: file extension that can be accepted, e.g. fastq
        """
        self.in_type = in_type

    def __str__(self):
        prev = self.prev_node.node_num if self.prev_node else None
        nxt = self.next_node.node_num if self.next_node else None

        return (
            f"Node {self.node_num}\n"
            f"Tool: {self.tool}\n"
            f"Arguments: {self.args}\n"
            f"Inputs: {self.inputs}\n"
            f"Outputs: {self.outputs}\n"
            f"Previous: {prev}\n"
            f"Next: {nxt}\n"
            f"State: {self.state.name}"
        )

class Graph:
    def __init__(self):
        self.nodes = {} # Dictionary of node num keys and Nodes. A dict automatically preserves the order of insertion since Python 3.7.
        self.next_id = 0

    def create_node(self, tool):
        node = Node(self.next_id, tool)
        self.nodes[self.next_id] = node
        self.next_id += 1
        return node

    def get_node(self, node_num) -> Node:
        return self.nodes[node_num]
    
    def get_first_node(self) -> Node:
        return next(iter((self.nodes).values()), None) # Returns first node or None if graph is empty.

    def add_node(self, node, prev=None, next=None):
        node.prev_node = prev
        node.next_node = next

        self.nodes[node.node_num] = node

    def connect(self, a: Node, b: Node):
        a.next_node = b
        b.prev_node = a

    def size(self):
        return len(self.nodes)
    
if __name__ == "__main__":
    graph = Graph()

    # Use create_node for auto numbering
    first = graph.create_node("FastQC")
    second = graph.create_node("Trimmomatic")
    third = graph.create_node("De Novo Transcriptome Assembly")

    graph.add_node(first)
    graph.add_node(second)
    graph.add_node(third)

    graph.connect(first, second)
    graph.connect(second, third)

    # Test getting node information
    for node in graph.nodes.values():
        print(node)
        print()