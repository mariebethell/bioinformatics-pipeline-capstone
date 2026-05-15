from __future__ import annotations
from enum import Enum

class StageState(Enum):
    NEW = 0
    INIT = 1
    STOPPED = 2
    RUNNING = 3
    COMPLETED = 4
    ERROR = 5

class Node:
    def __init__(self, node_num, tool, node_id=None, args=None, inputs=None):
        self.node_num = node_num
        self.tool = tool
        self.node_id = node_id # Used by the frontend only to hold ids of NodeGraphQT nodes
        self.args = args
        self.inputs = inputs
        self.outputs = {}
        self.prev_node: Node | None = None  # There should only ever be one previous Node, multiple inputs are not currently supported
        self.next_nodes: list[Node] = []    # A tool can be connected to multiple other tools.
        self.state = StageState.NEW
        
    def can_accept_input(self, in_type):
        """
        Sets the in_type attribute with the file type that can be processed by this tool.
    
        :param in_type: file extension that can be accepted, e.g. fastq
        """
        self.in_type = in_type

    def __str__(self):
        prev = self.prev_node.node_num if self.prev_node else None

        nxt_nodes = []
        if self.next_nodes:
            for node in self.next_nodes:
                if node:
                    nxt_nodes.append(node.node_num)

        return (
            f"Node {self.node_num}\n"
            f"Tool: {self.tool}\n"
            f"Arguments: {self.args}\n"
            f"Inputs: {self.inputs}\n"
            f"Outputs: {self.outputs}\n"
            f"Previous: {prev}\n"
            f"Next Nodes: {nxt_nodes}\n"
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
        return self.nodes.get(node_num)
    
    def get_first_node(self) -> Node:
        for node in self.nodes.values():
            if node.tool == "input":
                return node # If input node exists, return it as the first node
        
        return next(iter((self.nodes).values()), None) # If input node does not exsit, return first node that was inserted in the graph or None if graph is empty

    def add_node(self, node, prev=None, next=None):
        if prev is not None:
            node.prev_node = prev
        
        if next is not None:
            node.next_nodes.append(next)

        self.nodes[node.node_num] = node

    def connect(self, a: Node, b: Node):
        a.next_nodes.append(b)
        b.prev_node = a

    def size(self):
        return len(self.nodes)
    
if __name__ == "__main__":
    graph = Graph()

    # Use create_node for auto numbering
    input = graph.create_node("input")
    fastqc1 = graph.create_node("FastQC")
    trimmomatic = graph.create_node("Trimmomatic")
    fastqc2 = graph.create_node("FastQC")
    trinity = graph.create_node("De Novo Transcriptome Assembly")

    graph.add_node(input)
    graph.add_node(fastqc1)
    graph.add_node(trimmomatic)
    graph.add_node(fastqc2)
    graph.add_node(trinity)

    graph.connect(input, fastqc1)
    graph.connect(input, trimmomatic)
    graph.connect(trimmomatic, fastqc2)
    graph.connect(trimmomatic, trinity)

    # Test getting node information
    for node in graph.nodes.values():
        print(node)
        print()