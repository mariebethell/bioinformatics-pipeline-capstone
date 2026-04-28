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

PROJECT_ROOT = os.path.abspath(os.path.dirname(os.path.dirname((__file__))))

if __name__ == "__main__":
    user_id_str = "55761d01-6dbb-41a0-b4e2-a501af510697"
    user_id = uuid.UUID(user_id_str)

    command_dispatcher = CommandDispatcher(None, user_id)

    # Connect to server, which is docker container running locally
    server_ip = ipaddress.ip_address("127.0.0.1")
    command_dispatcher.connect(server_ip, 8000)

    # Create test graph and send new pipeline command
    g = Graph()

    n1 = g.create_node("input")
    n1.outputs = {
        "reads": [
            os.path.join(PROJECT_ROOT, "data", "Test01_L001_R1_001.fastq"),
            os.path.join(PROJECT_ROOT, "data", "Test01_L001_R2_001.fastq"),
        ]
    }
    n1.args = {}  # input nodes don’t have args

    n2 = g.create_node("fastqc")
    n2.args = {} # Use defaults
    # n3 = g.create_node("output")

    g.connect(n1, n2)
    # g.connect(n2, n3)

    # Test input uri
    project_directory = os.path.dirname(os.path.abspath(os.path.dirname(__file__)))
    input_uri = os.path.join(project_directory, "data", "Test01_L001_R1_001.fastq")

    # Create new pipeline
    new_pipeline_resp = command_dispatcher.new_pipeline(g, "./shared-data/test1")
    print(f"new_pipeline_resp:\n{new_pipeline_resp}\n")

    # Get created pipeline
    get_pipeline_resp = command_dispatcher.get_pipeline(new_pipeline_resp.PIPELINE_ID)
    print(f"get_pipeline_resp:\n{get_pipeline_resp}\n")

    # Run pipeline
    run_pipeline_resp = command_dispatcher.run_pipeline(new_pipeline_resp.PIPELINE_ID)
    print(f"run_pipeline_resp:\n{run_pipeline_resp}\n")