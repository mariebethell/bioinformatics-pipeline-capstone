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

class ModelStub:
    """
    Model Stub class for storing Graphs instead of AppModel
    """
    def __init__(self):
        graph = Graph()

if __name__ == "__main__":
    user_id_str = "55761d01-6dbb-41a0-b4e2-a501af510697"
    user_id = uuid.UUID(user_id_str)

    model = ModelStub()
    command_dispatcher = CommandDispatcher(model, user_id)

    # Connect to server, which is docker container running locally
    server_ip = ipaddress.ip_address("127.0.0.1")
    command_dispatcher.connect(server_ip, 8000)

    # Create test graph and send new pipeline command
    graph = Graph()

    # Build nodes in insertion order
    input_node = graph.create_node("input")
    fastqc1 = graph.create_node("FastQC")
    trim = graph.create_node("Trimmomatic")
    fastqc2 = graph.create_node("FastQC")

    # Connect linearly
    graph.connect(input_node, fastqc1)
    graph.connect(fastqc1, trim)
    graph.connect(trim, fastqc2)

    # Test input uri
    project_directory = os.path.dirname(os.path.abspath(os.path.dirname(__file__)))
    input_uri = os.path.join(project_directory, "data", "Test01_L001_R1_001.fastq")

    command_dispatcher.new_pipeline(graph, input_uri)
