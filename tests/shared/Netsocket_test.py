import pytest
import uuid
import ipaddress

from network.client.CommandDispatcher import CommandDispatcher

from shared import Command
from shared.CommandFactory import CommandFactory
from shared.graph import Graph, StageState, Node
from shared.APIStatus import APIStatus


class TestSockets:
    @staticmethod
    def test_pipeline_update():
        class model_stub():
            def update_presented_graph(self, updates):
                print(f"Received update: {updates}")

        model = model_stub()
        dispatcher = CommandDispatcher(model, uuid.uuid4()) # Random user ID for testing
        dispatcher.connect(ipaddress.ip_address("127.0.0.1"), 8000)

        pipeline_uuid = uuid.uuid4()
        dispatcher.trigger_websocket_test(pipeline_uuid)

