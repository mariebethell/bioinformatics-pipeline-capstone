import pytest

from uuid import UUID
import ipaddress

from network.client.CommandDispatcher import CommandDispatcher

from shared.Command import *
from shared.CommandFactory import CommandFactory
from shared.APIStatus import APIStatus
from shared.graph import Graph

from tests.conftest import BaseCmdTest

@pytest.fixture
def test_graph() -> Graph:
    g = Graph()

    n1 = g.create_node("input")
    n2 = g.create_node("fastqc")
    n2.args = {'threads': 1, 'format': 'fastq'}
    n3 = g.create_node("output")

    g.connect(n1, n2)
    g.connect(n2, n3)
    
    return g


user_uuid = uuid.uuid4()
dispatcher = CommandDispatcher(None, user_uuid) # We don't need the model for this test since we're not testing the websocket
dispatcher.connect(ipaddress.ip_address('127.0.0.1'), 8000)


class TestNetworkingSystems(BaseCmdTest):
    """
    Test harness to test the entire server. Server must be running for tests to be performed
        !!! Server must be configured to run the testing SessionManager stub !!!
        - Connects to the server
        - Attempts to run a sequence of commands to check if the server acts as expected

    """
    
    @staticmethod
    def test_cmd_new_pipeline(test_graph):

        resp = dispatcher.new_pipeline(test_graph, "./shared-data/test1")

        # For debugging
        respStr = CommandFactory.serialize_command(resp)
        print(f"Server returned: {respStr}")

        assert resp.STATUS == APIStatus.SUCCESS