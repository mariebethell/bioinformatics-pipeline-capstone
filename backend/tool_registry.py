"""
Central registry for backend tool definitions.

This module is the bridge between graph nodes and tool schema modules.

Responsibilities are storing the cononical mapping of tool keys -> tool_dif dictionaries.
normalizing tool names coming from the UI/graph layer. Exposing helper functions for validation,
defaults, output resolution and command rendering.
"""

from tols.base import get_default_args
from tools.fastqc import fastqc_tool
from tools.trimmomatic import trimmomatic_tool

TOOL_REGISTRY = {
    "fastqc": generate_fastqc_process
}

# cannonical registry: backend key -> tool definition
tool_registry = {
    "fastqc": fastqc_tool,
    "trimmomatic": trimmomatic_tool,
    #"trinity": trinity_tool 
}

