import pytest
import uuid
import ipaddress
import time

from network.client.CommandDispatcher import CommandDispatcher

from shared import Command
from shared.CommandFactory import CommandFactory
from shared.graph import Graph, StageState, Node
from shared.APIStatus import APIStatus


class TestSockets:
    """
    Test harness to test websocket connection between client and server. Server must be running for tests to be performed
        - Connects to the server
        - Requests server to send test GraphUIUpdate over the websocket
        - Waits 5 seconds for the GraphUIUpdate to arrive

    """
    
    @staticmethod
    def test_pipeline_update():
        async_resp = []
        class model_stub():
            def update_presented_graph(self, updates):
                print(f"Received update: {updates}")
                async_resp.append(updates)


        model = model_stub()
        dispatcher = CommandDispatcher(model, uuid.uuid4()) # Random user ID for testing
        dispatcher.connect(ipaddress.ip_address("127.0.0.1"), 8000)

        time.sleep(1) # Wait for websocket connection to finish initializing

        pipeline_uuid = uuid.uuid4()
        dispatcher.trigger_websocket_test(pipeline_uuid)

        sleep_time = 0.250
        elapsedTime = 0
        while len(async_resp) == 0:
            if elapsedTime > 5:
                dispatcher.net_client.socket_worker
                raise TimeoutError("Test timed out waiting for async update")
            
            else:
                print(f"Waited {elapsedTime} seconds...")
            
            elapsedTime += sleep_time
            time.sleep(sleep_time)

        assert async_resp[0]["1"] == StageState.COMPLETED and async_resp[0]["2"] == StageState.RUNNING