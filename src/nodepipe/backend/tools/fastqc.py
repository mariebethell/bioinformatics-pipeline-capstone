"""
FastQC tool definition for the backend tool registry.

This module describes the FastQC tool in the format expected by
`ToolRegistry`. It defines metadata, accepted inputs, expected outputs,
argument schema/defaults, UI grouping, validation, and backend-managed output
metadata.

The schema keeps CLI flag information for each supported FastQC option, but
nf-core argument string rendering is handled later by
`modules_config_builder.py`.

This links to a page that briefly explains each tool https://home.cc.umanitoba.ca/~psgendb/doc/fastqc.help
"""

from backend.tools.base import build_tool_def, validate_scalar_arg

tool_metadata = {
    "name": "fastqc",
    "display_name" : "FastQC",
    "category" : "quality_control",
    "supports_single_end" : True,
    "supports_paired_end" : True,
}

input_contract = {
    "accepted_formats": ["fastq", "fastq.gz", "sam", "bam"],
    "input_style": "one_or_many_files",
}

output_contract = {
    "produced_formats": ["html", "zip"],
    "output_style": "fastqc_report_bundle",
}


"""
Backend-supported FastQC arguments.

`ui_expose` should match the options currently shown in the frontend node.
Some backend-supported options are kept here for validation/default support
even though the user does not currently control them through the UI.
"""
arg_schema = {
    "threads": {
      "type": int,
      "kind": "option",
      "cli_flag": "--threads",
      "min_value": 1,
      "max_value": 128,
      "allowed_values": None,
      "default": 1,
      "nullable": False,
      "ui_expose": False,
      "managed_by_engine": True,
      "help_text": "Number of FastQC worker threads.",

    },

    "quiet": {
        "type": bool,
        "kind": "flag",
        "cli_flag": "--quiet",
        "min_value": None,
        "max_value": None,
        "allowed_values": None,
        "default": False,
        "nullable": False,
        "ui_expose": False,
        "managed_by_engine": False,
        "help_text": "Suppress progress output.",
    },

    "nogroup": {
        "type": bool,
        "kind": "flag",
        "cli_flag": "--nogroup",
        "min_value": None,
        "max_value": None,
        "allowed_values": None,
        "default": False,
        "nullable": False,
        "ui_expose": True,
        "managed_by_engine": False,
        "help_text": "Disable grouping of bases for long reads.",
    },

    "kmers": {
        "type": int,
        "kind": "option",
        "cli_flag": "--kmers",
        "min_value": 1,
        "max_value": 20,
        "allowed_values": None,
        "default": None,
        "nullable": True,
        "ui_expose": True,
        "managed_by_engine": False,
        "help_text": "K-mer size for k-mer content analysis.",
    },

    "adapters": {
        "type": str,
        "kind": "option",
        "cli_flag": "--adapters",
        "min_value": None,
        "max_value": None,
        "allowed_values": None,
        "default": None,
        "nullable": True,
        "ui_expose": True,
        "managed_by_engine": False,
        "help_text": "Path to an adapters file.",
    },

    "contaminants": {
        "type": str,
        "kind": "option",
        "cli_flag": "--contaminants",
        "min_value": None,
        "max_value": None,
        "allowed_values": None,
        "default": None,
        "nullable": True,
        "ui_expose": True,
        "managed_by_engine": False,
        "help_text": "Path to a contaminants file.",
    },
    
    "limits": {
        "type": str,
        "kind": "option",
        "cli_flag": "--limits",
        "min_value": None,
        "max_value": None,
        "allowed_values": None,
        "default": None,
        "nullable": True,
        "ui_expose": False,
        "managed_by_engine": False,
        "help_text": "Path to a custom limits file.",
    },

    "format": {
        "type": str,
        "kind": "option",
        "cli_flag": "--format",
        "min_value": None,
        "max_value": None,
        "allowed_values": ["bam", "sam", "fastq"],
        "default": None,
        "nullable": True,
        "ui_expose": True,
        "managed_by_engine": False,
        "help_text": "Force the input format.",
    },

    "extract": {
        "type": bool,
        "kind": "flag",
        "cli_flag": "--extract",
        "min_value": None,
        "max_value": None,
        "allowed_values": None,
        "default": False,
        "nullable": False,
        "ui_expose": False,
        "managed_by_engine": False,
        "help_text": "Extract the output zip after FastQC runs.",
    },

    "outdir": {
        "type": str,
        "kind": "option",
        "cli_flag": "--outdir",
        "min_value": None,
        "max_value": None,
        "allowed_values": None,
        "default": None,
        "nullable": True,
        "ui_expose": False,
        "managed_by_engine": True,
        "help_text": "Output directory managed by the backend.",
    },
}

rules = []

ui_schema = {
    "sections": {
        "basic": ["nogroup", "format"],
        "advanced": ["kmers", "adapters", "contaminants"],
    }
}

def validate_fastqc_args(args: dict, context: dict | None = None) -> list[str]:
    """
    Validate FastQC args against arg_schema
    """
    errors = []

    for arg_name, value in args.items():
      if arg_name not in arg_schema:
          errors.append(f"Unknown FastQC argument: '{arg_name}'.")
          continue
      
      errors.extend(validate_scalar_arg(arg_name, value, arg_schema[arg_name]))

    return errors



def resolve_fastqc_outputs(node_args: dict, context: dict) -> dict:
    """
    Resolve backend-managed FastQC output metadata.

    FastQC output paths are managed by the pipeline backend/Nextflow layer, so
    this function records the stage work directory for downstream pipeline
    bookkeeping.
    """
    return {
        "outdir": context["stage_work_dir"]
    }


fastqc_tool = build_tool_def(
    metadata = tool_metadata,
    input_contract=input_contract,
    output_contract=output_contract,
    arg_schema=arg_schema,
    rules=rules,
    ui_schema=ui_schema,
    validate_fn=validate_fastqc_args,
    resolve_outputs_fn=resolve_fastqc_outputs,
)