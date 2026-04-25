from uuid import UUID
import ipaddress

from network.client.CommandDispatcher import CommandDispatcher

from shared.Command import *
from shared.APIStatus import APIStatus

from tests.conftest import BaseCmdTest


user_uuid = uuid.uuid4()
dispatcher = CommandDispatcher(None, user_uuid) # We don't need the model for this test since we're not testing the websocket
dispatcher.connect(ipaddress.ip_address('127.0.0.1'), 8000)


class TestNetworkingSystems(BaseCmdTest):
    """
    Test harness to test all networking layers. Server must be running for tests to be performed
        !!! Server must be configured to run the testing SessionManager stub !!!
        - Connects to the server
        - Attempts to run most commands, checks if result was as expected according to hardcoded test values in SessionManager stub

    """
    
    @staticmethod
    def test_cmd_new_pipeline(build_graph):
        expected_params = {"PIPELINE_ID": UUID('7d44c86f-2a0d-4ea8-84d4-542c341ec7f4'), "STATUS": APIStatus.SUCCESS}

        resp = dispatcher.new_pipeline(build_graph, "some/uri/path")
        assert TestNetworkingSystems.compare_param_to_cmd(expected_params, resp)

    @staticmethod
    def test_cmd_get_pipeline(build_graph):
        pipeline_id = UUID('7d44c86f-2a0d-4ea8-84d4-542c341ec7f4')
        expected_params = {"GRAPH": build_graph, "STATUS": APIStatus.SUCCESS}

        resp = dispatcher.get_pipeline(pipeline_id)
        assert TestNetworkingSystems.compare_param_to_cmd(expected_params, resp)

    @staticmethod
    def test_cmd_modify_pipeline_params():
        pipeline_id = UUID('7d44c86f-2a0d-4ea8-84d4-542c341ec7f4')
        expected_params = {'STATUS': APIStatus.SUCCESS}

        resp = dispatcher.revise_stage_params(pipeline_id, 1, {'some_arg': 'some_val'})
        assert TestNetworkingSystems.compare_param_to_cmd(expected_params, resp)

    @staticmethod
    def test_cmd_run_pipeline():
        pipeline_id = UUID('7d44c86f-2a0d-4ea8-84d4-542c341ec7f4')
        expected_params = {'STATUS': APIStatus.SUCCESS}

        resp = dispatcher.run_pipeline(pipeline_id)
        assert TestNetworkingSystems.compare_param_to_cmd(expected_params, resp)

    @staticmethod
    def test_cmd_stop_pipeline():
        pipeline_id = UUID('7d44c86f-2a0d-4ea8-84d4-542c341ec7f4')
        expected_params = {'STATUS': APIStatus.SUCCESS}

        resp = dispatcher.stop_pipeline(pipeline_id)
        assert TestNetworkingSystems.compare_param_to_cmd(expected_params, resp)

    @staticmethod
    def test_cmd_rerun_stage():
        pipeline_id = UUID('7d44c86f-2a0d-4ea8-84d4-542c341ec7f4')
        expected_params = {'STATUS': APIStatus.SUCCESS}

        resp = dispatcher.rerun_from_stage(pipeline_id, 2)
        assert TestNetworkingSystems.compare_param_to_cmd(expected_params, resp)

    @staticmethod
    def test_cmd_get_download(build_graph):
        pipeline_id = UUID('7d44c86f-2a0d-4ea8-84d4-542c341ec7f4')
        expected_params = {"URI": 'some/dir/relative/to/bindmount', "STATUS": APIStatus.SUCCESS}

        resp = dispatcher.get_result_data_uri(pipeline_id, 1)
        assert TestNetworkingSystems.compare_param_to_cmd(expected_params, resp)