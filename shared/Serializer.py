import json
import copy
import inspect
import datetime
import uuid
import ipaddress

from typing import Type, get_args, ForwardRef
from types import UnionType

from shared import Command
from shared import graph
from shared import APIStatus


class Serializer:
    """
    Class which handles conversion and reconstruction of Commands to and from JSON strings

    """

    @staticmethod
    def serialize_command(cmd: Command.Command) -> str:
        """
        Attempts to clone and isolate field data in the given command into a dictionary and serialize the dictionary into a JSON string
            - Automatically converts custom datatypes and enums into more primitive versions which may be serialized
            - Graphs have their Nodes converted into SerializeableNode objects which have no memory references between objects

        Args:
            cmd (Command): The command to clone and serialize into JSON

        Returns:
            A JSON string containing the field data from the given Command

        Raises:
            TypeError if a field in the Command does not match the type specified in the Command's annotations
            ValueError if Command annotation definition is malformed (fix it in Command.py)
            ValueError if timestamp is not an ISO string

        """

        proto_obj = {}

        polymorphs = cmd.__class__.__mro__[:-1] # Get tuple of self's type and all ancestors types. Last element is always object, which is cut off
        for desc_type in polymorphs:
            for field, annotation in inspect.get_annotations(desc_type).items():
                annotations = get_args(annotation)

                sub_obj = copy.deepcopy(getattr(cmd, field, None)) # Should be impossible for it to return None because an annotation exists at all

                # Check if annotation actually has any metadata before trying to access them
                if (annotations.count == 0):
                    # Let json.dumps handle it as a regular obj later
                    proto_obj[field] = sub_obj

                sub_obj_type = annotations[0] # Type metadata SHOULD always be at the front
                if isinstance(sub_obj_type, ForwardRef):
                    sub_obj_type = Serializer._unforward_ref(sub_obj_type)

                if (sub_obj_type is Command.Nullable):
                    raise ValueError(f"Command type {type(cmd)} has malformed annotations for field {field}. First annotation should be object type, not Nullable")
                
                if (type(sub_obj) is not sub_obj_type and sub_obj is not None):
                    raise TypeError(f"Actual field type does not match specified type by annotation for command {type(cmd)}, field {field}. Expected type {sub_obj_type} but got {type(sub_obj)}")

                if sub_obj is not None:
                    if sub_obj_type is graph.Graph:
                        ser_graph = Serializer._serializify_graph(sub_obj)
                        proto_obj[field] = ser_graph

                    elif sub_obj_type is graph.Node:
                        ser_node = SerializableNode.copy_construct(sub_obj)
                        proto_obj[field] = vars(ser_node)

                    elif sub_obj_type is uuid.UUID:
                        proto_obj[field] = str(sub_obj)

                    elif sub_obj_type is APIStatus.APIStatus:
                        proto_obj[field] = sub_obj.value # is int

                    elif sub_obj_type is datetime.datetime:
                        proto_obj[field] = sub_obj.isoformat()

                    elif sub_obj_type is ipaddress.IPv4Address or sub_obj_type is ipaddress.IPv6Address:
                        proto_obj[field] = str(sub_obj)

                    else:
                        proto_obj[field] = sub_obj # Deep copy from earlier makes this safe

        return json.dumps(proto_obj)
    
    @staticmethod
    def deserialize(obj_type: Type, json_string: str):
        """
        Attempts to parse a JSON string and coerce it into the specified type
            - Contains special logic for handing Command subtypes
                - Validates command structure to ensure that they are complete/not malformed
            - Automatically converts serialized Graphs and Nodes into their proper types

        Args:
            obj_type (Type): The type to interpret the JSON string as
            json_string (string): The JSON string to parse

        Returns:
            An object of obj_type containing the data held within the JSON string
                - In some situations the server may return Response instead of the requested obj_type. In those
                    cases, this method will return an object of type Response instead of obj_type!

        Raises:
            TypeError if the fields in the JSON have the incorrect type for the fields within the specified Type
            ValueError if the JSON is missing data which is required by the specified Type

        """

        raw_obj = json.loads(json_string)

        if issubclass(obj_type, Command.Command):
            proto_cmd = obj_type()

            cmd_annotations = {}
            polymorphs = proto_cmd.__class__.__mro__[:-1] # Get tuple of self's type and all ancestors types. Last element is always object, which is cut off
            for desc_type in polymorphs:
                cmd_annotations = cmd_annotations | inspect.get_annotations(desc_type)

            # Copy all incoming data into empty command, validate to check if command is malformed
            for field, val in raw_obj.items():
                expected_field_type = None
                try:
                    annotations = get_args(cmd_annotations[field])
                    if len(annotations) > 0:
                        wip_field_type = annotations[0] # First annotation should be type
                        if wip_field_type is Command.Nullable:
                            print(f"WARNING: First annotation for field {field} in command type {obj_type} should be a type, but is Nullable! Dev fix this in Command.py!")

                        else:
                            expected_field_type = wip_field_type

                except KeyError:
                    pass # Let expected_field_type be None, we will use default case later if so

                if isinstance(expected_field_type, ForwardRef):
                    expected_field_type = Serializer._unforward_ref(expected_field_type)
                
                # Reconstruct Nodes, Graphs into their proper types
                reconstructedVal = val
                if expected_field_type is graph.Graph:
                    reconstructedVal = Serializer._deserializify_graph(val)

                elif expected_field_type is graph.Node:
                    raise TypeError("Unexpected Node object at depth 1 of deserialized object. Nodes should only exist within a graph, pass node number instead")
                
                elif expected_field_type is APIStatus.APIStatus:
                    reconstructedVal = APIStatus.APIStatus(val)

                elif expected_field_type is uuid.UUID:
                    reconstructedVal = uuid.UUID(val)

                elif expected_field_type is datetime.datetime:
                    reconstructedVal = datetime.datetime.fromisoformat(val)

                elif expected_field_type is UnionType:
                    for type_option in expected_field_type:
                        if type_option is ipaddress.IPv4Address or type_option is ipaddress.IPv6Address:
                            reconstructedVal = ipaddress.ip_address(val)
                            break

                # else assume val is already good to go

                if (hasattr(proto_cmd, field)):
                    setattr(proto_cmd, field, reconstructedVal)

                else:
                    print(f"WARNING: Deserializer given field which does not exist in target object type. Field: {field}, target type: {obj_type}")

            if not proto_cmd.validate():
                try:
                    return Serializer._coerce_resp_to_base(proto_cmd) # Server may have returned base Response type in case of error
                
                except ValueError: # Coerce throws ValueError if cast was unsuccessful
                    raise ValueError("Given JSON was invalid for the given command type") # Point of this is to give more specific details even though exception type is the same
            
            return proto_cmd

        else:
            #TODO cast to given type, but low priority
            return raw_obj
        
    @staticmethod
    def _coerce_resp_to_base(resp: Command.Response):
        """
        Under certain situations, the server may return a Response containing an error status instead of the requested Response derivative type
            This method allows the Serializer to handle those situations by attempting to narrow the scope of deserialization to just the fields
            required by the base Response type so it can return that instead

        Args:
            resp (Response): An invalid Response derivative to attempt to narrow into a base Response

        Returns:
            A Response object containing copied fields from the given invalid Response

        Raises:
            ValueError if the given Response object did not contain enough valid data to make a valid base Response object
        
        """

        proto_base_resp = Command.Response()
        for field in vars(proto_base_resp).keys():
            val = getattr(resp, field, None)
            setattr(proto_base_resp, field, val)

        if not proto_base_resp.validate():
            raise ValueError("Could not cast to Response type")
        
        return proto_base_resp

    @staticmethod
    def _serializify_graph(graph: graph.Graph) -> dict: # Dict contains fields within the graph type
        """
        Accepts a Graph and isolates all of the data stored within it. Data is cloned into a Dictionary which may be used later to reconstruct
            the Graph using _deserializify_graph
            - Cloned data is used by the Serializer during the serialization process
            - Converts Nodes within the graph into SerializableNodes on the fly

        Args:
            graph (Graph): The graph to dump into a serializable Dictionary

        Returns:
            Dictionary containing all the data stored within the graph, with some mutations to support serialization (Nodes converted to SerializableNodes, etc.)

        """

        # Walk the graph, serializify all nodes
        proto_graph = {'nodes': {}, 'next_id': 0}
        if len(graph.nodes) == 0: 
            return proto_graph

        proto_graph['next_id'] = graph.next_id

        cur_node = graph.nodes[0]
        while cur_node is not None:
            ser_node = SerializableNode.copy_construct(cur_node)
            proto_graph['nodes'][ser_node.node_num] = vars(ser_node)

            cur_node = cur_node.next_node

        return proto_graph
    
    @staticmethod
    def _deserializify_graph(graph_data: dict) -> graph.Graph:
        """
        Accepts a dictionary containing all data required to reconstruct a graph object and constructs a new Graph containing that data
            - Used by Serializer whenever it encounters a field within a Command which it knows should be a Graph type

        Args:
            graph_data (Dictionary): A dictionary containing all the fields necessary to construct a Graph
        
        Returns:
            Graph containing a clone of all the data in the given dictionary

        Raises:
            ValueError if the supplied dict does not supply enough data to populate a Graph object
            ValueError if there is an incongruity between node_nums assigned to nodes and the node_num stored within that node
            ValueError if Node data is malformed
            ValueError if Node neighbor references are dangling
            TypeError if a field in the supplied dict has the incorrect type for the field it seeks to populate in the Graph

        """

        required_keys = {'nodes', 'next_id'}
        if len(required_keys.intersection(graph_data.keys())) != len(required_keys):
            raise ValueError("Given graph data lacks required data to reconstruct Graph datastructure")
        
        proto_next_id = graph_data['next_id']
        if type(proto_next_id) is not int:
            raise TypeError(f"Given graph data has incorrect type for next_id. Expected int, got {type(proto_next_id)}")

        proto_graph = graph.Graph()
        proto_graph.next_id = proto_next_id

        proto_nodes = {}
        for ser_node_num, ser_node in graph_data['nodes'].items():
            if int(ser_node_num) != ser_node['node_num']:
                raise ValueError(f"Serializified Graph has mismatch between actual node num and node num specified in node dict key. Key: {ser_node_num}, actual: {ser_node['node_num']}. Dev debug _serializify_graph in Serializer.py")

            if (not SerializableNode.validate_data_dict_shape(ser_node)):
                raise ValueError("Node data in graph to deserializify is malformed")
            
            #Move data over to proper Node object
            proto_node = graph.Node(ser_node_num, ser_node['tool'])
            for field, rawval in ser_node.items():
                val = rawval

                #Convert raw int back to enum if needed
                if field == 'state' and type(val) is not graph.StageState:
                    if type(val) is not int:
                        raise TypeError(f"Node data has invalid StageState value type. Expected int, got {type(val)}")
                    val = graph.StageState(rawval)

                setattr(proto_node, field, val)

            proto_nodes[proto_node.node_num] = proto_node

        #Reconnect references between nodes
        for node in proto_nodes.values():
            try:
                node.prev_node = proto_nodes.get(node.prev_id)
                node.next_node = proto_nodes.get(node.next_id)

            except KeyError:
                raise ValueError("Serialized graph has nodes which refer to invalid neighbor nodes")
            
            #Remove extra data which was used in the deserialization process
            for field in SerializableNode.NEW_FIELDS:
                try:
                    delattr(node, field)

                except Exception:
                    try:
                        print(f"WARNING: While deserializifying graph, reconstructed Node already had temporary data removed somehow. Node contents: {json.dumps(node)}")

                    except Exception:
                        print("WARNING: While deserializifying graph, reconstructed Node already had temporary data removed somehow")

        proto_graph.nodes = proto_nodes
        return proto_graph
    
    def _unforward_ref(ref: ForwardRef) -> Type:
        """
        Converts type reference strings to actual type references
            - This is necessary because the Annotation library struggles to find our modules if I directly reference them

        Args:
            ref (ForwardRef): The ForwardRef to convert to a type reference

        Returns:
            The Type object which the ForwardRef refers to

        """

        return ref._evaluate(globals(), locals(), recursive_guard=frozenset()) # TODO find a less nasty way to deal with forward type refs
        
    

class SerializableNode(graph.Node):
    """
    A specialized version of Node which supports data serialization. 
        - This is done by converting memory references to index references and by unwrapping enums

        Used by the Serializer. Nodes are converted to this type during serialization and back during deserialization

    """

    STRIPPED_FIELDS = {'l_idx', 'r_idx'} # These fields are removed from the base Node class
    NEW_FIELDS = {'prev_id', 'next_id'} # These fields are added to the base Node class
    # Above two fields are used during object validation

    def __init__(self):
        # All fields get populated later   
        super().__init__(None, None)     
        self.state = None
        self.prev_id = None
        self.next_id = None

    @staticmethod
    def copy_construct(original_node: graph.Node):
        """
        Constructs a SerializableNode which contains a clone of all information stored in the given Node
            - SerializableNode is not dependent on the original node

        Args:
            original_node (Node): The Node to copy against

        Returns:
            SerializableNode containing a copy of the given Node's data

        Raises:
            TypeError if passed in an object which is not a Node

        """

        if type(original_node) is not graph.Node:
            raise TypeError("Input must be a Node")

        ser_node = SerializableNode()

        # Need to remove dependency on memory references to send over net
        l_idx = original_node.prev_node.node_num if original_node.prev_node is not None else None
        r_idx = original_node.next_node.node_num if original_node.next_node is not None else None

        # Make copies to avoid runtime dependencies on original
        ser_node.node_num = original_node.node_num
        ser_node.tool = original_node.tool
        ser_node.args = copy.deepcopy(original_node.args)
        ser_node.inputs = copy.deepcopy(original_node.inputs)
        ser_node.outputs = copy.deepcopy(original_node.outputs)

        ser_node.prev_id = l_idx # is int
        ser_node.next_id = r_idx # is int
        ser_node.state = original_node.state.value # is int

        return ser_node
    
    @staticmethod
    def validate_data_dict_shape(data: dict) -> bool:
        """
        Inspects a dictionary to see if it contains the required data to populate a SerializableNode
            - This is used to protect the system from malformed data or data injection

        Args:
            data (Dictionary): The dictionary which should be validated

        Returns:
            Bool which is True if the dictionary has the correct shape, False if it should be rejected

        """

        test_ser_node = SerializableNode()
        expected_fields = SerializableNode.STRIPPED_FIELDS.difference(vars(test_ser_node).keys())

        unexpected_fields = expected_fields.difference(data.keys())
        if unexpected_fields != SerializableNode.STRIPPED_FIELDS: # Be tolerant of incomplete node conversion
            return False # Reject, malformed data
        
        return True