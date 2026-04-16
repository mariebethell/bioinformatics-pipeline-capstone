"""
Salmon tool configuration for nf-core module composition.

This version is for the newer architecture where our backend builds
a custom pipeline out of nf-core modules.

this file describes:
- what Salmon is
- what parameters the UI can expose
- how those parameters map to pipeline params
- how the pipeline builder can include/call the Salmon module
"""

from backend.tools.base import build_tool_def, validate_scalar_arg


tool_metadata = {
    "name": "salmon",
    "display_name": "Salmon",
    "category": "transcript_quantification",
    "supports_single_end": True,
    "supports_paired_end": True,

    # new fields for nf-core-based composition
    "module_source": "nf-core",
    "module_name": "salmon",
    "include_name": "SALMON",
}


input_contract = {
    "accepted_formats": [
        "fastq", "fastq.gz", "fq", "fq.gz",
        "fasta", "fa", "fasta.gz", "fa.gz",
        "sam", "bam", "cram",
    ],
    "input_style": "multi_input_bundle",
}


output_contract = {
    "produced_formats": ["sf", "json", "tsv", "dir"],
    "output_style": "salmon_stage_dir",
}


arg_schema = {
    "command": {
        "type": str,
        "min_value": None,
        "max_value": None,
        "allowed_values": ["index", "quant"],
        "default": "quant",
        "nullable": False,
        "ui_expose": True,
        "help_text": "Run Salmon in index or quant mode.",

        "nf_param": "salmon_command",
    },

    "threads": {
        "type": int,
        "min_value": 1,
        "max_value": 128,
        "allowed_values": None,
        "default": 1,
        "nullable": False,
        "ui_expose": True,
        "help_text": "Number of worker threads.",

        "nf_param": "salmon_threads",
    },

    "lib_type": {
        "type": str,
        "min_value": None,
        "max_value": None,
        "allowed_values": None,
        "default": "A",
        "nullable": True,
        "ui_expose": True,
        "help_text": "Library type for quant mode. Use A for auto-detect.",

        "nf_param": "salmon_lib_type",
    },

    "k": {
        "type": int,
        "min_value": 1,
        "max_value": None,
        "allowed_values": None,
        "default": 31,
        "nullable": True,
        "ui_expose": True,
        "help_text": "k-mer size for index mode.",

        "nf_param": "salmon_k",
    },

    "seq_bias": {
        "type": bool,
        "min_value": None,
        "max_value": None,
        "allowed_values": None,
        "default": False,
        "nullable": False,
        "ui_expose": True,
        "help_text": "Enable sequence-specific bias correction.",

        "nf_param": "salmon_seq_bias",
    },

    "gc_bias": {
        "type": bool,
        "min_value": None,
        "max_value": None,
        "allowed_values": None,
        "default": False,
        "nullable": False,
        "ui_expose": True,
        "help_text": "Enable GC bias correction.",

        "nf_param": "salmon_gc_bias",
    },

    "num_bootstraps": {
        "type": int,
        "min_value": 0,
        "max_value": None,
        "allowed_values": None,
        "default": None,
        "nullable": True,
        "ui_expose": True,
        "help_text": "Number of bootstrap samples to compute in quant mode.",

        "nf_param": "salmon_num_bootstraps",
    },
}


rules = [
    "Salmon index mode requires a transcript FASTA input.",
    "Salmon quant mode requires an index plus reads.",
    "Automatic library type detection can be requested with lib_type = 'A'.",
]


ui_schema = {
    "sections": {
        "basic": [
            "command",
            "threads",
            "lib_type",
            "seq_bias",
            "gc_bias",
        ],
        "advanced": [
            "k",
            "num_bootstraps",
        ],
    }
}


def validate_salmon_args(args: dict, context: dict | None = None) -> list[str]:
    """
    Validate Salmon args against arg_schema.

    Even if nextflow_schema.json handles validation later,
    this is still useful for catching bad UI/API input early.
    """
    errors = []

    if not isinstance(args, dict):
        return ["Arguments must be a dictionary."]

    for arg_name, value in args.items():
        if arg_name not in arg_schema:
            errors.append(f"Unknown Salmon argument: '{arg_name}'.")
            continue

        errors.extend(validate_scalar_arg(arg_name, value, arg_schema[arg_name]))

    command = args.get("command", arg_schema["command"]["default"])

    if command == "index":
        if "lib_type" in args and args.get("lib_type") not in (None, "A"):
            errors.append("'lib_type' is only meaningful for Salmon quant mode.")
        if args.get("seq_bias"):
            errors.append("'seq_bias' is only meaningful for Salmon quant mode.")
        if args.get("gc_bias"):
            errors.append("'gc_bias' is only meaningful for Salmon quant mode.")
        if args.get("num_bootstraps") is not None:
            errors.append("'num_bootstraps' is only meaningful for Salmon quant mode.")

    if command == "quant":
        # k mainly belongs to index mode
        if "k" in args and args.get("k") is not None:
            errors.append("'k' is only meaningful for Salmon index mode.")

    return errors


def build_salmon_param_map(node_args: dict) -> dict:
    """
    Convert node args into pipeline param values.

    Example:
        {"command": "quant", "threads": 8, "lib_type": "A"}

    becomes:
        {
            "salmon_command": "quant",
            "salmon_threads": 8,
            "salmon_lib_type": "A"
        }
    """
    params = {}

    for arg_name, spec in arg_schema.items():
        if arg_name not in node_args:
            continue

        nf_param = spec.get("nf_param")
        if nf_param is None:
            continue

        params[nf_param] = node_args[arg_name]

    return params


def build_salmon_schema_fields() -> dict:
    """
    Build JSON-schema-like field definitions for nextflow_schema.json generation.
    """
    schema_fields = {}

    for arg_name, spec in arg_schema.items():
        nf_param = spec.get("nf_param")
        if nf_param is None:
            continue

        if spec["type"] is int:
            json_type = "integer"
        elif spec["type"] is bool:
            json_type = "boolean"
        else:
            json_type = "string"

        field = {
            "type": json_type,
            "description": spec.get("help_text", ""),
        }

        if spec.get("default") is not None:
            field["default"] = spec["default"]

        if spec.get("allowed_values") is not None:
            field["enum"] = spec["allowed_values"]

        schema_fields[nf_param] = field

    return schema_fields


def build_salmon_config_defaults() -> dict:
    """
    Build default param values for nextflow.config generation.
    """
    defaults = {}

    for arg_name, spec in arg_schema.items():
        nf_param = spec.get("nf_param")
        if nf_param is None:
            continue

        defaults[nf_param] = spec.get("default")

    return defaults


def build_salmon_workflow_call(
    input_channel: str = "reads_ch",
    index_channel: str = "salmon_index_ch",
) -> str:
    """
    Return the workflow call string for the Salmon nf-core module.

    For now this keeps the same simplified style as the FastQC example.
    The pipeline builder can choose which call to use depending on whether
    this node is being used for index or quant mode.
    """
    include_name = tool_metadata["include_name"]
    return (
        "if (params.salmon_command == 'index') {\n"
        f"    {include_name}(transcripts_ch)\n"
        "}\n"
        "else {\n"
        f"    {include_name}({input_channel}, {index_channel})\n"
        "}"
    )


salmon_tool = build_tool_def(
    metadata=tool_metadata,
    input_contract=input_contract,
    output_contract=output_contract,
    arg_schema=arg_schema,
    rules=rules,
    ui_schema=ui_schema,
    validate_fn=validate_salmon_args,
)

# Attach helper functions used by the newer pipeline builder
salmon_tool["build_param_map"] = build_salmon_param_map
salmon_tool["build_schema_fields"] = build_salmon_schema_fields
salmon_tool["build_config_defaults"] = build_salmon_config_defaults
salmon_tool["build_workflow_call"] = build_salmon_workflow_call