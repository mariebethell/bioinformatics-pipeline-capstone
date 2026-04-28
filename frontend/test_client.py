"""
Test program to imitate presentation layer and test pipeline manager on backned.
"""

import uuid
import ipaddress
import os
import sys
[sys.path.append(i) for i in ['.', '..']] # Tells Python to search for modules in the parent directories.

from network.client.CommandDispatcher import CommandDispatcher
from shared.graph import Graph
from shared.CommandFactory import CommandFactory

class ModelStub:
    """
    Model Stub class for storing Graphs instead of AppModel
    """
    def __init__(self):
        graph = Graph()

if __name__ == "__main__":
    user_id_str = "55761d01-6dbb-41a0-b4e2-a501af510697"
    user_id = uuid.UUID(user_id_str)

    # model = ModelStub()
    command_dispatcher = CommandDispatcher(None, user_id)

    # Connect to server, which is docker container running locally
    server_ip = ipaddress.ip_address("127.0.0.1")
    command_dispatcher.connect(server_ip, 8000)

    # Create test graph and send new pipeline command
    g = Graph()

    n1 = g.create_node("input")
    n2 = g.create_node("fastqc")
    n2.args = {'threads': 1, 'format': 'fastq'}
    n3 = g.create_node("output")

    g.connect(n1, n2)
    g.connect(n2, n3)

    # Test input uri
    project_directory = os.path.dirname(os.path.abspath(os.path.dirname(__file__)))
    input_uri = os.path.join(project_directory, "data", "Test01_L001_R1_001.fastq")

    resp = command_dispatcher.new_pipeline(g, "./shared-data/test1")

    respStr = CommandFactory.serialize_command(resp)
    print(f"Server returned: {respStr}")