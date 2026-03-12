from enum import Enum

class StageState(Enum):
    NEW = 0,
    INIT = 1,
    STOPPED = 2,
    RUNNING = 3,
    COMPLETED = 4,
    ERROR = 5

class Node:
    def __init__(self, nodeNum):
        self.nodeNum = nodeNum
        self.tool = ""
        self.args = {}
        self.inputs = {}
        self.ouptuts = {}
        self.prevNode: Node
        self.nextNode: Node
        self.state = StageState.NEW

class Graph:
    def __init__(self):
        self.nodes = {} # Dictionary of node num keys and Nodes. A dict automatically preserves the order of insertion since Python 3.7.
    
    def getNode(self, nodeNum) -> Node:
        return self.nodes[nodeNum]
    
    def getFirstNode(self) -> Node:
        return next(iter((self.nodes).values()), None) # Returns first node or None if graph is empty.

    def addNode(self, node, prev, next):
        node.prevNode = prev
        node.nextNode = next

        self.nodes[node.nodeNum] = node
    
if __name__ == "__main__":
    first = Node(1)
    second = Node(2)

    graph = Graph()

    graph.addNode(first, None, second)
    graph.addNode(second, first, None)

    # Test getting node information
    print(graph.getFirstNode().nodeNum)
    print(graph.getNode(2).nodeNum)
