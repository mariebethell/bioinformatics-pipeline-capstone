"""
Compiled node structures for backend Nextflow generation.

This module defines the small data objects used after a graph node has been
validated and compiled into an nf-core-ready pipeline stage.

`ModuleSpec` stores static metadata for each supported tool, such as the
process name, module path, output accessor, and whether the tool advances the
main data channel.

`CompiledNode` stores the per-node compiled result used during pipeline and
modules.config generation, including aliases, channel names, normalized args,
and rendered ext.args values.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ModuleSpec:
    tool: str
    process_name: str
    module_path: str
    publish_subdir: str
    output_accessor: str
    advances_primary_channel: bool


@dataclass
class CompiledNode:
    node_num: int
    tool: str
    module_path: str
    process_name: str
    alias: str
    input_channel: str
    output_channel: str
    output_accessor: str
    advances_primary_channel: bool
    normalized_args: dict = field(default_factory=dict)
    ext_args: str = ""
    ext_args2: str = ""
    publish_subdir: str = ""
    prefix_expr: str = '${meta.id}'


MODULE_SPECS: dict[str, ModuleSpec] = {
    "fastqc": ModuleSpec(
        tool="fastqc",
        process_name="FASTQC",
        module_path="./modules/nf-core/fastqc",
        publish_subdir="fastqc",
        output_accessor="out.zip",
        advances_primary_channel=False,
    ),
    "trimmomatic": ModuleSpec(
        tool="trimmomatic",
        process_name="TRIMMOMATIC",
        module_path="./modules/nf-core/trimmomatic",
        publish_subdir="trimmomatic",
        output_accessor="out.trimmed_reads",
        advances_primary_channel=True,
    ),
    "trinity": ModuleSpec(
        tool="trinity",
        process_name="TRINITY",
        module_path="./modules/nf-core/trinity",
        publish_subdir="trinity",
        output_accessor="out.transcript_fasta",
        advances_primary_channel=True,
    ),
}


def get_module_spec(tool: str) -> ModuleSpec:
    tool_key = (tool or "").lower()
    if tool_key not in MODULE_SPECS:
        raise KeyError(f"No nf-core module spec registered for tool '{tool}'")
    return MODULE_SPECS[tool_key]
