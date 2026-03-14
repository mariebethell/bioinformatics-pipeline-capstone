"""
Trimmomatic tool configuration schema.

This defines the argument schema we use for validating and generating Trimmomatic commands within the pipeline backend.

Trimmomatic has global command options such as -threads and -summary But Trimmomatic also has ordered trimming steps that are appended to the end of the command (for example ILLUMINACLIP, LEADING, SLIDINGWINDOW, MINLEN)

Because step order matters in Trimmomatic, this schema is split into trimmomatic_global_arg_schema and trimmomatic_step_schemas.

Reference: https://github.com/usadellab/Trimmomatic
"""

trimmomatic_global_arg_schema = {
    "mode": {
        "type": str,
        "cli_flag": None,
        "min_value": None,
        "max_value": None,
        "allowed_values": ["SE", "PE"],
        "default": "SE",
        "nullable": False
    },

    "threads": {
      "type": int,
      "cli_flag": "-threads",
      "min_value": 0,
      "max_value": 128,
      "allowed_values": None,
      "default": 0,
      "nullable": False
    },

    "phred": {
        "type": str,
        "cli_flag": None,
        "min_value": None,
        "max_value": None,
        "allowed_values": ["33", "64"],
        "default": None,
        "nullable": True
    },

    "trimlog": {
        "type": str,
        "cli_flag": "-trimlog",
        "min_value": None,
        "max_value": None,
        "allowed_values": None,
        "default": None,
        "nullable": True
    },

    "summary": {
        "type": str,
        "cli_flag": "-summary",
        "min_value": None,
        "max_value": None,
        "allowed_values": None,
        "default": None,
        "nullable": True
    },

    "basein": {
        "type": str,
        "cli_flag": "-basein",
        "min_value": None,
        "max_value": None,
        "allowed_values": None,
        "default": None,
        "nullable": True
    },

    "baseout": {
        "type": str,
        "cli_flag": "-baseout",
        "min_value": None,
        "max_value": None,
        "allowed_values": None,
        "default": None,
        "nullable": True
    },

    "validate_pairs": {
        "type": bool,
        "cli_flag": "-validatePairs",
        "min_value": None,
        "max_value": None,
        "allowed_values": None,
        "default": False,
        "nullable": False
    },

    "compress_level": {
        "type": int,
        "cli_flag": "-compressLevel",
        "min_value": 1,
        "max_value": 9,
        "allowed_values": None,
        "default": None,
        "nullable": True
    },

    "compression_mode": {
        "type": str,
        "cli_flag": None,
        "min_value": None,
        "max_value": None,
        "allowed_values": ["stream", "block"],
        "default": None,
        "nullable": True
    },

    "quiet": {
        "type": bool,
        "cli_flag": "-quiet",
        "min_value": None,
        "max_value": None,
        "allowed_values": None,
        "default": False,
        "nullable": False
    },

    "version": {
        "type": bool,
        "cli_flag": "-version",
        "min_value": None,
        "max_value": None,
        "allowed_values": None,
        "default": False,
        "nullable": False
    },  
}

trimmomatic_step_schemas = {
    "illumina_clip": {
        "step_name": "ILLUMINACLIP",
        "ordered": True,
        "parameters": {
            "fasta_with_adapters": {
                "type": str,
                "position": 1,
                "min_value": None,
                "max_value": None,
                "allowed_values": None,
                "default": None,
                "nullable": False
            },

            "seed_mismatches": {
                "type": int,
                "position": 2,
                "min_value": 0,
                "max_value": None,
                "allowed_values": None,
                "default": None,
                "nullable": False
            },

            "palindrome_clip_threshold": {
                "type": int,
                "position": 3,
                "min_value": 0,
                "max_value": None,
                "allowed_values": None,
                "default": None,
                "nullable": False
            },

            "simple_clip_threshold": {
                "type": int,
                "position": 4,
                "min_value": 0,
                "max_value": None,
                "allowed_values": None,
                "default": None,
                "nullable": False
            },

            "min_adapter_length_palindrome": {
                "type": int,
                "position": 5,
                "min_value": 1,
                "max_value": None,
                "allowed_values": None,
                "default": 8,
                "nullable": True
            },

            "keep_both_reads": {
                "type": bool,
                "position": 6,
                "min_value": None,
                "max_value": None,
                "allowed_values": None,
                "default": False,
                "nullable": True
            },
        },
    },

    "leading": {
        "step_name": "LEADING",
        "ordered": True,
        "parameters": {
            "quality": {
                "type": int,
                "position": 1,
                "min_value": 0,
                "max_value": None,
                "allowed_values": None,
                "default": None,
                "nullable": False
            }
        }
    },

    "trailing": {
        "step_name": "TRAILING",
        "ordered": True,
        "parameters": {
            "quality": {
                "type": int,
                "position": 1,
                "min_value": 0,
                "max_value": None,
                "allowed_values": None,
                "default": None,
                "nullable": False
            }
        }
    },

    "head_crop": {
        "step_name": "HEADCROP",
        "ordered": True,
        "parameters": {
            "length": {
                "type": int,
                "position": 1,
                "min_value": 0,
                "max_value": None,
                "allowed_values": None,
                "default": None,
                "nullable": False
            }
        }
    },

    "tail_crop": {
        "step_name": "TAILCROP",
        "ordered": True,
        "parameters": {
            "length": {
                "type": int,
                "position": 1,
                "min_value": 0,
                "max_value": None,
                "allowed_values": None,
                "default": None,
                "nullable": False
            }
        }
    },

    "crop": {
        "step_name": "CROP",
        "ordered": True,
        "parameters": {
            "length": {
                "type": int,
                "position": 1,
                "min_value": 1,
                "max_value": None,
                "allowed_values": None,
                "default": None,
                "nullable": False
            }
        }
    },

    "sliding_window": {
        "step_name": "SLIDINGWINDOW",
        "ordered": True,
        "parameters": {
            "window_size": {
                "type": int,
                "position": 1,
                "min_value": 1,
                "max_value": None,
                "allowed_values": None,
                "default": None,
                "nullable": False
            },
            "required_quality": {
                "type": int,
                "position": 2,
                "min_value": 0,
                "max_value": None,
                "allowed_values": None,
                "default": None,
                "nullable": False
            }
        }
    },

    "max_info": {
        "step_name": "MAXINFO",
        "ordered": True,
        "parameters": {
            "target_length": {
                "type": int,
                "position": 1,
                "min_value": 1,
                "max_value": None,
                "allowed_values": None,
                "default": None,
                "nullable": False
            },
            "strictness": {
                "type": float,
                "position": 2,
                "min_value": 0.0,
                "max_value": 1.0,
                "allowed_values": None,
                "default": None,
                "nullable": False
            }
        }
    },

    "min_len": {
        "step_name": "MINLEN",
        "ordered": True,
        "parameters": {
            "length": {
                "type": int,
                "position": 1,
                "min_value": 1,
                "max_value": None,
                "allowed_values": None,
                "default": None,
                "nullable": False
            }
        }
    },

    "max_len": {
        "step_name": "MAXLEN",
        "ordered": True,
        "parameters": {
            "length": {
                "type": int,
                "position": 1,
                "min_value": 1,
                "max_value": None,
                "allowed_values": None,
                "default": None,
                "nullable": False
            }
        }
    },

    "avg_qual": {
        "step_name": "AVGQUAL",
        "ordered": True,
        "parameters": {
            "quality": {
                "type": int,
                "position": 1,
                "min_value": 0,
                "max_value": None,
                "allowed_values": None,
                "default": None,
                "nullable": False
            }
        }
    },

    "base_count": {
        "step_name": "BASECOUNT",
        "ordered": True,
        "parameters": {
            "bases": {
                "type": str,
                "position": 1,
                "min_value": None,
                "max_value": None,
                "allowed_values": None,
                "default": None,
                "nullable": False
            },

            "min_count": {
                "type": int,
                "position": 2,
                "min_value": 0,
                "max_value": None,
                "allowed_values": None,
                "default": None,
                "nullable": True
            },

            "max_count": {
                "type": int,
                "position": 3,
                "min_value": 0,
                "max_value": None,
                "allowed_values": None,
                "default": None,
                "nullable": True
            },
        }
    },
>>>>>>> e2e3619 (Added Trimmomatic global and step schema.)
}