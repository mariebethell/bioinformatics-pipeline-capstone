
"""
FastQC tool configuration shema.

This defines the argument schema we use for validating and generating fastQC commands
wihtin the pipeline backend. The schema describes each supported fastQC parameter,
including its expected type, CLI flag mapping, validation rules, and default values.

The schema is used to validate arguments recieved from the API, normalize tool config
values, and generate fastQC command line arguments for Nextflow stages.
"""
fastqc_arg_schema = {
    "threads": {
      "type": int,
      "cli_flag": "--threads",
      "min_value": 1,
      "max_value": 128,
      "allowed_values": None,
      "default": 1,
      "nullable": False
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
}