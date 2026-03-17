"""

"""

trinity_core_arg_schema = {
    "seq_type": {
        "type": str,
        "cli_flag": "--seqType",
        "allowed_values": ["fq", "fa"],
        "default": "fq",
        "nullable": False,
    },

    "cpu": {
        "type": int,
        "cli_flag": "--CPU",
        "min_value": 1,
        "max_value": 128,
        "default": 1,
        "nullable": False,
    },

    "max_memory": {
        "type": str,
        "cli_flag": "--max_memory",
        "default": "14G",
        "nullable": False,
    },

    "output": {
        "type": str,
        "cli_flag": "--output",
        "default": None,
        "nullable": True,
    },

    "left": {
        "type": str,
        "cli_flag": "--left",
        "default": None,
        "nullable": True,
    },

    "right": {
        "type": str,
        "cli_flag": "--right",
        "default": None,
        "nullable": True,
    },

    "single": {
        "type": str,
        "cli_flag": "--single",
        "default": None,
        "nullable": True,
    },
}