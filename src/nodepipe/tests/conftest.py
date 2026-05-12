import pytest
from uuid import UUID

from shared import Command
from shared.CommandFactory import CommandFactory
from shared.graph import Node, Graph

@pytest.fixture
def build_graph() -> Graph:
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
    
    return graph


class BaseCmdTest:
    @staticmethod
    def deep_compare_objs(obj1, obj2) -> bool:
        if type(obj1) is not type(obj2):
            print(f"Deep comparison failed because obj1 type is {type(obj1)} but obj2 type is {type(obj2)}")
            return False
            
        if obj1 is None:
            return True
            
        if obj1 is obj2:
            return True
            
        if (obj1 == obj2):
            return True
            
        if isinstance(obj1, Node):
            # Manually check equality for Nodes to prevent infinite loops
            if not BaseCmdTest.deep_compare_objs(obj1.node_num, obj2.node_num):
                print("Deep comparison failed because nodes nums were not equal")
                return False
                
            elif not BaseCmdTest.deep_compare_objs(obj1.tool, obj2.tool):
                print("Deep comparison failed because nodes tools were not equal")
                return False
                
            elif not BaseCmdTest.deep_compare_objs(obj1.args, obj2.args):
                print("Deep comparison failed because nodes args were not equal")
                return False
                
            elif not BaseCmdTest.deep_compare_objs(obj1.inputs, obj2.inputs):
                print("Deep comparison failed because nodes inputs were not equal")
                return False
                
            elif (obj1.prev_node.node_num if obj1.prev_node else None) != (obj2.prev_node.node_num if obj2.prev_node else None):
                print("Deep comparison failed because node prev_nodes were not equal")
                return False
                
            elif not BaseCmdTest.deep_compare_objs(obj1.state, obj2.state):
                print("Deep comparison failed because nodes state were not equal")
                return False
                
            elif not BaseCmdTest.deep_compare_objs(obj1.outputs, obj2.outputs):
                print("Deep comparison failed because nodes outputs were not equal")
                return False

            elif (len(obj1.next_nodes) != len(obj2.next_nodes)):
                print("Deep comparison failed because next node arrays were of different lengths")
                return False
            
            for idx in range(len(obj1.next_nodes)):
                if not BaseCmdTest.deep_compare_objs(obj1.next_nodes[idx], obj2.next_nodes[idx]):
                    print("Deep comparison failed because next node arrays did not match")
                    return False
                
            return True
            
        if isinstance(obj1, UUID):
            return obj1 == obj2
            
        obj1Vars = None
        obj2Vars = None
        
        if isinstance(obj1, dict):
            obj1Vars = obj1
            obj2Vars = obj2

        else:
            try:
                obj1Vars = vars(obj1)
                obj2Vars = vars(obj2)
                
            except TypeError:
                raise NotImplementedError(f"Objects of type {type(obj1)} are not supported by deep_compare_objs")
            
                    
        if len(obj1Vars) != len(obj2Vars):
            print(f"Deep comparison failed because obj1 has {len(obj1Vars)} fields but obj2 has {len(obj2Vars)} fields")
            return False
            
        for field, obj1Val in obj1Vars.items():
            obj2Val = obj2Vars.get(field, ValueError)
            
            if obj2Val is ValueError:
                print(f"Deep comparison failed because obj2 was missing field {field} in obj1")
                return False
                
            if not BaseCmdTest.deep_compare_objs(obj1Val, obj2Val):
                return False
                
        return True
    
    @staticmethod
    def compare_param_to_cmd(params: dict, cmd: Command) -> bool:
        for field, val in params.items():
            try:
                cmdVal = getattr(cmd, field, ValueError)
                
                if cmdVal is ValueError:
                    print(f"Param comparison failed for command {type(cmd)} because Command is missing field: {field}")
                    return False
                    
                if not BaseCmdTest.deep_compare_objs(val, cmdVal):
                    print(f"Param comparison failed for command {type(cmd)} because parameter value and cmd field value were not equal")
                    return False
                    
                return True
                
            except Exception as e:
                print(f"Param comparison failed due to exception {e}")
                return False
             
    @staticmethod
    def ser_deser_compare(cmd: Command.Command) -> bool:
        cmd_json = CommandFactory.serialize_command(cmd)
        print(cmd_json)
        reconstruct = CommandFactory.deserialize_command(type(cmd), cmd_json)
        
        return BaseCmdTest.deep_compare_objs(cmd, reconstruct)