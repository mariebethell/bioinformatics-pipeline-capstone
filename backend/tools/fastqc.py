
"""
FastQC tool configuration shema.

This defines the argument schema we use for validating and generating fastQC commands
wihtin the pipeline backend. The schema describes each supported fastQC parameter,
including its expected type, CLI flag mapping, validation rules, and default values.

The schema is used to validate arguments recieved from the API, normalize tool config
values, and generate fastQC command line arguments for Nextflow stages.\

This links to a page that briefly explains each tool https://home.cc.umanitoba.ca/~psgendb/doc/fastqc.help
"""

from tools.base import build_tool_def, validate_scalar_arg

tool_metadata = {
    "name" : "fastqc",
    "display_name" : "FastQC",
    "category" : "quality_control",
    "supports_single_end" : "True",
    "supports_paired_end" : "True",
}

input_contract = {
    "accepted_formats": ["fastq", "fast.gz", "sam", "bam"],
    "input_style": "one_or_many_files",
}

output_contract = {
    "produced_formats": ["html", "zip"],
    "output_style": "fastqc_report_bundle",
}



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
      "ui_expose": True,
      "managed_by_engine": False,
      "help_text": "Number of FastQC worker threads.",

    },

    "quiet": {
      "type": bool,
      "cli_flag": "--quiet",
      "min_value": None,
      "max_value": None,
      "allowed_values": None,
      "default": False,
      "nullable": False
    },

    "nogroup": {
      "type": bool,
      "cli_flag": "--nogroup",
      "min_value": None,
      "max_value": None,
      "allowed_values": None,
      "default": False,
      "nullable": False
    },

    "kmers": {
      "type": int,
      "cli_flag": "--kmers",
      "min_value": 1,
      "max_value": 20,
      "allowed_values": None,
      "default": None,
      "nullable": True
    },

    "adapters": {
      "type": str,
      "cli_flag": "--adapters",
      "min_value": None,
      "max_value": None,
      "allowed_values": None,
      "default": None,
      "nullable": True
    },

    "contaminants": {
      "type": str,
      "cli_flag": "--contaminants",
      "min_value": None,
      "max_value": None,
      "allowed_values": None,
      "default": None,
      "nullable": True
    },
    
    "limits": {
        "type": str,
        "cli_flag": "--limits",
        "min_value": None,
        "max_value": None,
        "allowed_values": None,
        "default": None,
        "nullable": True
    },

    "format": {
      "type": str,
      "cli_flag": "--format",
      "min_value": None,
      "max_value": None,
      "allowed_values": ["bam","sam","fastq"],
      "default": None,
      "nullable": True
    },

    "extract": {
        "type": bool,
        "cli_flag": "--extract",
        "min_value": None,
        "max_value": None,
        "allowed_values": None,
        "default": None,
        "nullable": True
    },

    "version": {
        "type": bool,
        "cli_flag": "--version",
        "min_value": None,
        "max_value": None,
        "allowed_values": None,
        "default": None,
        "nullable": True
    },

    "help": {
        "type": bool,
        "cli_flag": "--help",
        "min_value": None,
        "max_value": None,
        "allowed_values": None,
        "default": None,
        "nullable": True
    },

    "outdir": {
        "type": str,
        "cli_flag": "--outdir",
        "min_value": None,
        "max_value": None,
        "allowed_values": None,
        "default": None,
        "nullable": True
    },
}