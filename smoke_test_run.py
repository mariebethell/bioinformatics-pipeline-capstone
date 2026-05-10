import os

from shared.graph import Graph
from backend.tool_registry import ToolRegistry
from backend.pipeline_builder import NextflowPipeline

PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))

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

# One paired-end sample for the first smoke test
input_node.outputs = {
    "reads": [
        os.path.join(PROJECT_ROOT, "data", "Test01_L001_R1_001.fastq"),
        os.path.join(PROJECT_ROOT, "data", "Test01_L001_R2_001.fastq"),
    ]
}

# FastQC uses defaults
fastqc1.args = {}

# Trimmomatic needs an ordered steps list
trim.args = {
    "mode": "PE",
    "threads": 1,
    "steps": [
        {"name": "leading", "parameters": {"quality": 3}},
        {"name": "trailing", "parameters": {"quality": 3}},
        {"name": "sliding_window", "parameters": {"window_size": 4, "required_quality": 20}},
        {"name": "min_len", "parameters": {"length": 36}},
    ],
}

# Second FastQC also uses defaults
fastqc2.args = {}

registry = ToolRegistry()

pipeline = NextflowPipeline(
    graph=graph,
    tool_registry=registry,
    pipeline_script_path=os.path.join(PROJECT_ROOT, "main.nf"),
)

pipeline.run_pipeline()