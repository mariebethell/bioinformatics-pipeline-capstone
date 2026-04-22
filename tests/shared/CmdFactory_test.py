import pytest
import uuid

from shared import Command
from shared.CommandFactory import CommandFactory
from shared.graph import Graph, StageState, Node
from shared.APIStatus import APIStatus

"""
Test harness to test CommandFactory, Command, and Serializer
    - Spawns all structurally different Command types using a predefined param block and graph, then...
        - Checks if Command is valid
        - Checks if Command properly copied param data
        - Checks if Command is properly serialized
        - Checks if Command is properly deserialized
        
    - Tests rejection of bad or missing parameters when constructing a new Command
    - Tests rejection of bad or missing JSON strings while deserializing
    - Tests runtime coercion of Response type from Response derivatives during JSON deserialization
        - This occurs when the server returns an error

"""


@pytest.fixture
def build_graph() -> Graph:
    g = Graph()

    n1 = g.create_node("tool 1")
    n2 = g.create_node("tool 2")
    n3 = g.create_node("tool 3")

    g.connect(n1, n2)
    g.connect(n2, n3)
    
    return g

@pytest.fixture
def client_connect():
    params = {
        "user_uuid": uuid.uuid4()
    }
    
    cmd = CommandFactory.new_command(Command.ClientConnect, params=params)
    
    return (cmd, params)

@pytest.fixture    
def client_connect_resp():
    params = {
        "STATUS": APIStatus.SUCCESS,
        "ACTIVE_PIPELINE_UUID": uuid.uuid4()
    }
    
    cmd = CommandFactory.new_command(Command.ClientConnectResponse, params=params)
    
    return (cmd, params)

@pytest.fixture
def get_pipeline():
    params = {
        "user_uuid": uuid.uuid4(),
        "pipeline_id": uuid.uuid4()
    }
    
    cmd = CommandFactory.new_command(Command.GetPipeline, params=params)
    
    return (cmd, params)
    
@pytest.fixture    
def get_pipeline_resp(build_graph):
    params = {
        "STATUS": APIStatus.SUCCESS,
        "GRAPH": build_graph
    }
    
    cmd = CommandFactory.new_command(Command.GetPipelineResponse, params=params)
    
    return (cmd, params)
    
@pytest.fixture
def new_pipeline(build_graph):
    params = {
        "user_uuid": uuid.uuid4(),
        "input_uri": "/some/path",
        "graph": build_graph
    }
    
    cmd = CommandFactory.new_command(Command.NewPipeline, params=params)
    
    return (cmd, params)
    
@pytest.fixture    
def new_pipeline_resp():
    params = {
        "STATUS": APIStatus.SUCCESS,
        "PIPELINE_ID": uuid.uuid4(),
        "ERROR_INFO": APIStatus.ERR_UNKNOWN
    }
    
    cmd = CommandFactory.new_command(Command.NewPipelineResponse, params=params)
    
    return (cmd, params)
    
@pytest.fixture
def modify_params():
    params = {
        "user_uuid": uuid.uuid4(),
        "pipeline_id": uuid.uuid4(),
        "node_num": 0,
        "new_args": {"some_arg_name": "some_arg_value"}
    }
    
    cmd = CommandFactory.new_command(Command.ModifyPipelineParams, params=params)
    
    return (cmd, params)
    
@pytest.fixture
def run_pipeline():
    params = {
        "user_uuid": uuid.uuid4(),
        "pipeline_id": uuid.uuid4()
    }
    
    cmd = CommandFactory.new_command(Command.RunPipeline, params=params)
    
    return (cmd, params)
    
@pytest.fixture    
def run_pipeline_resp():
    params = {
        "STATUS": APIStatus.SUCCESS,
        "ERROR_INFO": APIStatus.ERR_BAD_PIPELINE_ID
    }
    
    cmd = CommandFactory.new_command(Command.RunPipelineResponse, params=params)
    
    return (cmd, params)
    
@pytest.fixture
def stop_pipeline():
    params = {
        "user_uuid": uuid.uuid4(),
        "pipeline_id": uuid.uuid4()
    }
    
    cmd = CommandFactory.new_command(Command.StopPipeline, params=params)
    
    return (cmd, params)
    
@pytest.fixture
def rerun_stage():
    params = {
        "user_uuid": uuid.uuid4(),
        "pipeline_id": uuid.uuid4(),
        "node_num": 2
    }
    
    cmd = CommandFactory.new_command(Command.RerunStage, params=params)
    
    return (cmd, params)
    
@pytest.fixture
def get_download():
    params = {
        "user_uuid": uuid.uuid4(),
        "pipeline_id": uuid.uuid4(),
        "node_num": 1
    }
    
    cmd = CommandFactory.new_command(Command.GetArtifactDownload, params=params)
    
    return (cmd, params)
    
@pytest.fixture    
def get_download_resp():
    params = {
        "STATUS": APIStatus.SUCCESS,
        "URI": "/some/uri"
    }
    
    cmd = CommandFactory.new_command(Command.GetArtifactDownloadResponse, params=params)
    
    return (cmd, params)
    
@pytest.fixture
def graph_ui_update():
    params = {
        "PIPELINE_ID": uuid.uuid4(),
        "UPDATES": {0: StageState.COMPLETED, 1: StageState.INIT, 2: StageState.NEW}
    }
    
    cmd = CommandFactory.new_command(Command.GraphUIUpdate, params=params)
    
    return (cmd, params)

@pytest.fixture
def on_stage_complete():
    params = {
        "pipeline_id": uuid.uuid4(),
        "stage_num": 3
    }
    
    cmd = CommandFactory.new_command(Command.OnStageComplete, params=params)
    
    return (cmd, params)
    
@pytest.fixture
def on_pipeline_error():
    params = {
        "pipeline_id": uuid.uuid4(),
        "stage_num": 1,
        "error": APIStatus.ERR_INVALID_TOOL
    }
    
    cmd = CommandFactory.new_command(Command.OnPipelineError, params=params)
    
    return (cmd, params)
    

class TestSerializer: # Also tests CommandFactory and Command
    @staticmethod
    def deep_compare_objs(obj1, obj2) -> bool:
        if type(obj1) is not type(obj2):
            print(f"Deep comparison failed because obj1 type is {type(obj1)} but obj2 type is {type(obj2)}")
            return False;
            
        if obj1 is None:
            return True
            
        if obj1 is obj2:
            return True
            
        if (obj1 == obj2):
            return True
            
        if isinstance(obj1, Node):
            # Manually check equality for Nodes to prevent infinite loops
            if not TestSerializer.deep_compare_objs(obj1.node_num, obj2.node_num):
                print(f"Deep comparison failed because nodes nums were not equal")
                return False
                
            elif not TestSerializer.deep_compare_objs(obj1.tool, obj2.tool):
                print(f"Deep comparison failed because nodes tools were not equal")
                return False
                
            elif not TestSerializer.deep_compare_objs(obj1.args, obj2.args):
                print(f"Deep comparison failed because nodes args were not equal")
                return False
                
            elif not TestSerializer.deep_compare_objs(obj1.inputs, obj2.inputs):
                print(f"Deep comparison failed because nodes inputs were not equal")
                return False
                
            elif (obj1.prev_node.node_num if obj1.prev_node else None) != (obj2.prev_node.node_num if obj2.prev_node else None):
                print(f"Deep comparison failed because node prev_nodes were not equal")
                return False
                
            elif (obj1.next_node.node_num if obj1.next_node else None) != (obj2.next_node.node_num if obj2.next_node else None):
                print(f"Deep comparison failed because nodes next_nodes were not equal")
                return False
                
            elif not TestSerializer.deep_compare_objs(obj1.state, obj2.state):
                print(f"Deep comparison failed because nodes state were not equal")
                return False
                
            elif not TestSerializer.deep_compare_objs(obj1.outputs, obj2.outputs):
                print(f"Deep comparison failed because nodes outputs were not equal")
                return False
                
            else:
                return True
            
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
            return False;
            
        for field, obj1Val in obj1Vars.items():
            obj2Val = obj2Vars.get(field, ValueError)
            
            if obj2Val is ValueError:
                print(f"Deep comparison failed because obj2 was missing field {field} in obj1")
                return False
                
            if not TestSerializer.deep_compare_objs(obj1Val, obj2Val):
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
                    
                if not TestSerializer.deep_compare_objs(val, cmdVal):
                    print(f"Param comparison failed for command {type(cmd)} because parameter value and cmd field value were not equal")
                    return False
                    
                return True
                
            except Exception as e:
                print(f"Param comparison failed due to exception {e}")
                return False
             
    @staticmethod
    def ser_deser_compare(cmd: Command) -> bool:
        cmd_json = CommandFactory.serialize_command(cmd)
        print(cmd_json)
        reconstruct = CommandFactory.deserialize_command(type(cmd), cmd_json)
        
        return TestSerializer.deep_compare_objs(cmd, reconstruct)
       
    @staticmethod
    def cmd_test_logic(cmd_param_tuple) -> bool:
        cmd = cmd_param_tuple[0]
        params = cmd_param_tuple[1]
        
        try:
            if not TestSerializer.compare_param_to_cmd(params, cmd):
                print("Test failed due to param to cmd comparison failure")
                return False
            
            if not TestSerializer.ser_deser_compare(cmd):
                print("Test failed due to serialization deserialization comparison failure")
                return False
                
        except Exception as e:
            print(f"Test for Command type failed due to exception: {e}")
            return False
            
        return True
        
    
    @staticmethod
    def test_client_connect(client_connect):
        assert TestSerializer.cmd_test_logic(client_connect)
        
    @staticmethod
    def test_client_connect_resp(client_connect_resp):
        assert TestSerializer.cmd_test_logic(client_connect_resp)
        
    @staticmethod
    def test_get_pipeline(get_pipeline):
        assert TestSerializer.cmd_test_logic(get_pipeline)
        
    @staticmethod
    def test_get_pipeline_resp(get_pipeline_resp):
        assert TestSerializer.cmd_test_logic(get_pipeline_resp)
        
    @staticmethod
    def test_new_pipeline(new_pipeline):
        assert TestSerializer.cmd_test_logic(new_pipeline)
        
    @staticmethod
    def test_new_pipeline_resp(new_pipeline_resp):
        assert TestSerializer.cmd_test_logic(new_pipeline_resp)
        
    @staticmethod
    def test_modify_params(modify_params):
        assert TestSerializer.cmd_test_logic(modify_params)
        
    @staticmethod
    def test_run_pipeline(run_pipeline):
        assert TestSerializer.cmd_test_logic(run_pipeline)
        
    @staticmethod
    def test_run_pipeline_resp(run_pipeline_resp):
        assert TestSerializer.cmd_test_logic(run_pipeline_resp)
        
    @staticmethod
    def test_stop_pipeline(stop_pipeline):
        assert TestSerializer.cmd_test_logic(stop_pipeline)
        
    @staticmethod
    def test_rerun_stage(rerun_stage):
        assert TestSerializer.cmd_test_logic(rerun_stage)
        
    @staticmethod
    def test_get_download(get_download):
        assert TestSerializer.cmd_test_logic(get_download)
        
    @staticmethod
    def test_get_download_resp(get_download_resp):
        assert TestSerializer.cmd_test_logic(get_download_resp)
        
    @staticmethod
    def test_graph_ui_update(graph_ui_update):
        assert TestSerializer.cmd_test_logic(graph_ui_update)
        
    @staticmethod
    def test_on_stage_complete(on_stage_complete):
        assert TestSerializer.cmd_test_logic(on_stage_complete)
        
    @staticmethod
    def test_on_pipeline_error(on_pipeline_error):
        assert TestSerializer.cmd_test_logic(on_pipeline_error)
        
    @staticmethod
    def test_bad_params(build_graph):
        paramsNone = {
            "user_uuid": None,
            "pipeline_id": uuid.uuid4(),
            "node_num": 1
        }
        
        paramsMissing = {
            "pipeline_id": uuid.uuid4(),
            "node_num": 1
        }
        
        try:
            with pytest.raises(TypeError):
                cmd = CommandFactory.new_command(str, params=None) # Not a Command
                raise RuntimeError("CommandFactory did not raise an exception when it should have")
            
        except TypeError:
            pass; # Passed, move on to next test
            
        except Exception as e:
            print(f"Test test_bad_params failed on invalid Command type test due to exception: {e}")
            assert False # Failed
    
        try:
            with pytest.raises(ValueError):
                cmd = CommandFactory.new_command(Command.GetArtifactDownload, params=None)
                raise RuntimeError("CommandFactory did not raise an exception when it should have")
            
        except ValueError:
            pass; # Passed, move on to next test
            
        except Exception as e:
            print(f"Test test_bad_params failed on params=None test due to exception: {e}")
            assert False
            
        try:
            with pytest.raises(ValueError):
                cmd = CommandFactory.new_command(Command.GetArtifactDownload, params=paramsNone)
                raise RuntimeError("CommandFactory did not raise an exception when it should have")
            
        except ValueError:
            pass; # Passed, move on to next test
            
        except Exception as e:
            print(f"Test test_bad_params failed on params=paramsNone test due to exception: {e}")
            assert False
            
        try:
            with pytest.raises(ValueError):
                cmd = CommandFactory.new_command(Command.GetArtifactDownload, params=paramsMissing)
                raise RuntimeError("CommandFactory did not raise an exception when it should have")
            
        except ValueError:
            pass; # Passed, move on to next test
            
        except Exception as e:
            print(f"Test test_bad_params failed on params=paramsMissing test due to exception: {e}")
            assert False
            
        assert True
        
    @staticmethod
    def test_bad_json(build_graph):
        try:
            with pytest.raises(ValueError):
                cmd = CommandFactory.deserialize_command(Command.NewPipeline, '{"input_uri": "/some/path", "graph": {"nodes": {"0": {"node_num": 0, "tool": "tool 1", "args": null, "inputs": null, "outputs": {}, "prev_node": null, "next_node": null, "state": 0, "prev_id": null, "next_id": 1}, "1": {"node_num": 1, "tool": "tool 2", "args": null, "inputs": null, "outputs": {}, "prev_node": null, "next_node": null, "state": 0, "prev_id": 0, "next_id": 2}, "2": {"node_num": 2, "tool": "tool 3", "args": null, "inputs": null, "outputs": {}, "prev_node": null, "next_node": null, "state": 0, "prev_id": 1, "next_id": null}}, "next_id": 3}, "timestamp": "2026-04-13T19:36:03.806247"}')
                raise RuntimeError("CommandFactory did not raise an exception when it should have")
            
        except ValueError:
            pass; # Passed, move on to next test
            
        except Exception as e:
            print(f"Test test_bad_json failed on missing param field test due to exception: {e}")
            assert False
            
        try:
            with pytest.raises(TypeError):
                cmd = CommandFactory.deserialize_command(Command.NewPipeline, '{"user_uuid": "3f4deaa9-2b33-4831-989f-41793f0c40a2", "input_uri": "/some/path", "graph": "not a graph", "timestamp": "2026-04-13T19:36:03.806247"}')
                raise RuntimeError("CommandFactory did not raise an exception when it should have")
            
        except ValueError:
            pass; # Passed, move on to next test
            
        except Exception as e:
            print(f"Test test_bad_json failed on incorrect param field type test due to exception: {e}")
            assert False
            
        try:
            with pytest.raises(ValueError):
                cmd = CommandFactory.deserialize_command(Command.NewPipeline, "")
                raise RuntimeError("CommandFactory did not raise an exception when it should have")
            
        except ValueError:
            pass; # Passed, move on to next test
            
        except Exception as e:
            print(f"Test test_bad_json failed on empty string test due to exception: {e}")
            assert False
            
        try:
            with pytest.raises(ValueError):
                cmd = CommandFactory.deserialize_command(Command.NewPipeline, "{}")
                raise RuntimeError("CommandFactory did not raise an exception when it should have")
            
        except ValueError:
            pass; # Passed, move on to next test
            
        except Exception as e:
            print(f"Test test_bad_json failed on empty json test due to exception: {e}")
            assert False
            
        try:
            with pytest.raises(TypeError):
                cmd = CommandFactory.deserialize_command(Command.NewPipeline, None)
                raise RuntimeError("CommandFactory did not raise an exception when it should have")
            
        except ValueError:
            pass; # Passed, move on to next test
            
        except Exception as e:
            print(f"Test test_bad_json failed on None json parameter test due to exception: {e}")
            assert False
        
        assert True
        
    @staticmethod
    def test_response_base_coercion():
        params = {'STATUS': APIStatus.ERR_INVALID_GRAPH}
        cmd = CommandFactory.new_command(Command.Response, params)
        cmdJson = CommandFactory.serialize_command(cmd)
        
        coercedResponse = CommandFactory.deserialize_command(Command.NewPipelineResponse, cmdJson)
        
        if type(coercedResponse) is not Command.Response: # Deserializer should have realized that server returned an error type (Response) and
            assert False                                  #     ignore the given type
            
        assert True