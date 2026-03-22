"""
Trimmomatic tool configuration schema.

This defines the argument schema we use for validating and generating Trimmomatic commands within the pipeline backend.

Trimmomatic has global command options such as -threads and -summary But Trimmomatic also has ordered trimming steps that are appended to the end of the command (for example ILLUMINACLIP, LEADING, SLIDINGWINDOW, MINLEN)

Because step order matters in Trimmomatic this module has two schema layers
1. arg_schema for flat golbal arguments
2. trimmimatic_step_schemas for ordered trimming steps

for compatability with current base.py helpers, arg_schema remains flat.
step schemas are attatched seperately for the final tool definition.

Reference: https://github.com/usadellab/Trimmomatic
"""

from tools.base import build_tool_def, validate_scalar_arg

tool_metadata = {
    "name": "trimmomatic",
    "display_name": "Trimmomatic",
    "category": "read_trimming",
    "supports_single_end": True,
    "supports_paired_end": True,
}

input_contract = {
    "accepted_formats": ["fastq", "fastq.gz"],
    "input_style": "single_or_paired_reads",
}

output_contract = {
    "produced_formats": ["fastq.gz", "txt"],
    "output_style": "trimmed_reads_bundle",
}

arg_schema = {
    "mode": {
        "type": str,
        "kind": "mode",
        "cli_flag": None,
        "min_value": None,
        "max_value": None,
        "allowed_values": ["SE", "PE"],
        "default": "SE",
        "nullable": False,
        "ui_expose": True,
        "managed_by_engine": False,
        "help_text": "Run Trimmomatic in single-end (SE) or paired-end (PE) mode.",
    },

    "threads": {
        "type": int,
        "kind": "option",
        "cli_flag": "-threads",
        "min_value": 1,
        "max_value": 128,
        "allowed_values": None,
        "default": 1,
        "nullable": False,
        "ui_expose": True,
        "managed_by_engine": False,
        "help_text": "Number of worker threads.",
    },

    "phred": {
        "type": str,
        "kind": "phred",
        "cli_flag": None,
        "min_value": None,
        "max_value": None,
        "allowed_values": ["33", "64"],
        "default": None,
        "nullable": True,
        "ui_expose": True,
        "managed_by_engine": False,
        "help_text": "Explicit quality score encoding. Rendered as -phred33 or -phred64.",
    },

    "trimlog": {
        "type": str,
        "kind": "option",
        "cli_flag": "-trimlog",
        "min_value": None,
        "max_value": None,
        "allowed_values": None,
        "default": None,
        "nullable": True,
        "ui_expose": False,
        "managed_by_engine": True,
        "help_text": "Trim log file path managed by the backend.",
    },

    "summary": {
        "type": str,
        "kind": "option",
        "cli_flag": "-summary",
        "min_value": None,
        "max_value": None,
        "allowed_values": None,
        "default": None,
        "nullable": True,
        "ui_expose": False,
        "managed_by_engine": True,
        "help_text": "Summary output file path managed by the backend.",
    },

    "validate_pairs": {
        "type": bool,
        "kind": "flag",
        "cli_flag": "-validatePairs",
        "min_value": None,
        "max_value": None,
        "allowed_values": None,
        "default": False,
        "nullable": False,
        "ui_expose": True,
        "managed_by_engine": False,
        "help_text": "Validate that paired-end reads stay synchronized.",
    },

    "compress_level": {
        "type": int,
        "kind": "option",
        "cli_flag": "-compressLevel",
        "min_value": 1,
        "max_value": 9,
        "allowed_values": None,
        "default": None,
        "nullable": True,
        "ui_expose": True,
        "managed_by_engine": False,
        "help_text": "Compression level for gzipped outputs.",
    },

    "compression_mode": {
        "type": str,
        "kind": "compression_mode",
        "cli_flag": None,
        "min_value": None,
        "max_value": None,
        "allowed_values": ["stream", "block"],
        "default": None,
        "nullable": True,
        "ui_expose": True,
        "managed_by_engine": False,
        "help_text": "Compression mode rendered as -compressStream or -compressBlock.",
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
                "nullable": False,
                "help_text": "Adapter FASTA file.",
            },

            "seed_mismatches": {
                "type": int,
                "position": 2,
                "min_value": 0,
                "max_value": None,
                "allowed_values": None,
                "default": None,
                "nullable": False,
                "help_text": "Maximum seed mismatches.",
            },

            "palindrome_clip_threshold": {
                "type": int,
                "position": 3,
                "min_value": 0,
                "max_value": None,
                "allowed_values": None,
                "default": None,
                "nullable": False,
                "help_text": "Palindrome clip threshold.",
            },

            "simple_clip_threshold": {
                "type": int,
                "position": 4,
                "min_value": 0,
                "max_value": None,
                "allowed_values": None,
                "default": None,
                "nullable": False,
                "help_text": "Simple clip threshold.",
            },

            "min_adapter_length_palindrome": {
                "type": int,
                "position": 5,
                "min_value": 1,
                "max_value": None,
                "allowed_values": None,
                "default": None,
                "nullable": True,
                "help_text": "Optional minimum adapter length for palindrome mode.",
            },

            "keep_both_reads": {
                "type": bool,
                "position": 6,
                "min_value": None,
                "max_value": None,
                "allowed_values": None,
                "default": None,
                "nullable": True,
                "help_text": "Optional boolean controlling whether both reads are kept.",
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
                "nullable": False,
                "help_text": "Trim leading bases below this quality.",
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
                "nullable": False,
                "help_text": "Trim trailing bases below this quality.",
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
                "nullable": False,
                "help_text": "Remove this many bases from the start of each read.",
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
                "nullable": False,
                "help_text": "Keep only up to this many bases from the start, trimming the tail.",
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
                "nullable": False,
                "help_text": "Crop reads to this maximum length.",
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
                "nullable": False,
                "help_text": "Sliding window size.",
            },
            "required_quality": {
                "type": int,
                "position": 2,
                "min_value": 0,
                "max_value": None,
                "allowed_values": None,
                "default": None,
                "nullable": False,
                "help_text": "Minimum average quality required in the window.",
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
                "nullable": False,
                "help_text": "Target read length.",
            },
            "strictness": {
                "type": float,
                "position": 2,
                "min_value": 0.0,
                "max_value": 1.0,
                "allowed_values": None,
                "default": None,
                "nullable": False,
                "help_text": "Strictness value between 0.0 and 1.0.",
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
                "nullable": False,
                "help_text": "Discard reads shorter than this length.",
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
                "nullable": False,
                "help_text": "Discard reads longer than this length.",
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
                "nullable": False,
                "help_text": "Discard reads with average quality below this value.",
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
                "nullable": False,
                "help_text": "Bases to count, for example N.",
            },

            "min_count": {
                "type": int,
                "position": 2,
                "min_value": 0,
                "max_value": None,
                "allowed_values": None,
                "default": None,
                "nullable": True,
                "help_text": "Optional minimum allowed count.",
            },

            "max_count": {
                "type": int,
                "position": 3,
                "min_value": 0,
                "max_value": None,
                "allowed_values": None,
                "default": None,
                "nullable": True,
                "help_text": "Optional maximum allowed count.",
            },
        }
    },
}

rules = [
    "Trimmomatic requires an ordered 'steps' list in node_args.",
    "SE mode expects one input read and one trimmed output file.",
    "PE mode expects two input reads and four output files.",
    "Optional step parameters must not skip earlier positional parameters.",
]

ui_schema = {
    "sections": {
        "basic": [
            "mode",
            "threads",
            "phred",
            "validate_pairs",
            "compress_level",
            "compression_mode",
        ],
        "advanced": [],
    },
    "custom_sections": {
        "steps": {
            "type": "ordered_step_list",
            "supported_steps": list(trimmomatic_step_schemas.keys()),
        }
    }
}

def _validate_trimmomatic_steps(steps: object) -> list[str]:
    """
    Validate the ordered Trimmomatic trimming steps.

    Expected shape:
    [
        {
            "name": "sliding_window",
            "parameters": {
                "window_size": 4,
                "required_quality": 20
            }
        },
        ...
    ]
    """
    errors = []

    if steps is None:
        return ["Trimmomatic requires a 'steps' list."]

    if not isinstance(steps, list):
        return ["'steps' must be a list."]

    if len(steps) == 0:
        return ["'steps' must contain at least one trimming step."]

    for index, step in enumerate(steps):
        step_prefix = f"steps[{index}]"

        if not isinstance(step, dict):
            errors.append(f"{step_prefix} must be a dictionary.")
            continue

        step_name = step.get("name")
        if step_name not in trimmomatic_step_schemas:
            errors.append(
                f"{step_prefix}.name must be one of "
                f"{list(trimmomatic_step_schemas.keys())}, got {step_name!r}."
            )
            continue

        parameters = step.get("parameters")
        if not isinstance(parameters, dict):
            errors.append(f"{step_prefix}.parameters must be a dictionary.")
            continue

        step_schema = trimmomatic_step_schemas[step_name]
        parameter_schema = step_schema["parameters"]

        for parameter_name in parameters:
            if parameter_name not in parameter_schema:
                errors.append(
                    f"Unknown parameter '{parameter_name}' for Trimmomatic step "
                    f"'{step_name}'."
                )

        ordered_parameters = sorted(
            parameter_schema.items(),
            key=lambda item: item[1]["position"]
        )

        seen_missing_optional = False

        for parameter_name, parameter_spec in ordered_parameters:
            value_provided = parameter_name in parameters

            if not value_provided:
                if not parameter_spec.get("nullable", False):
                    errors.append(
                        f"Missing required parameter '{parameter_name}' for "
                        f"Trimmomatic step '{step_name}'."
                    )
                else:
                    seen_missing_optional = True
                continue

            if seen_missing_optional:
                errors.append(
                    f"Optional parameters for Trimmomatic step '{step_name}' must "
                    f"be supplied in positional order without skipping earlier "
                    f"optional parameters."
                )

            errors.extend(
                validate_scalar_arg(
                    f"{step_prefix}.parameters.{parameter_name}",
                    parameters[parameter_name],
                    parameter_spec,
                )
            )

    return errors


def validate_trimmomatic_args(args: dict, context: dict | None = None) -> list[str]:
    """
    Validate Trimmomatic args against arg_schema plus ordered step rules.
    """
    errors = []

    if not isinstance(args, dict):
        return ["Arguments must be a dictionary."]

    for arg_name, value in args.items():
        if arg_name == "steps":
            continue

        if arg_name not in arg_schema:
            errors.append(f"Unknown Trimmomatic argument: '{arg_name}'.")
            continue

        errors.extend(validate_scalar_arg(arg_name, value, arg_schema[arg_name]))

    errors.extend(_validate_trimmomatic_steps(args.get("steps")))

    mode = args.get("mode", arg_schema["mode"]["default"])

    if mode == "SE" and args.get("validate_pairs"):
        errors.append("'validate_pairs' can only be used in PE mode.")

    return errors


def _render_trimmomatic_step(step: dict) -> str:
    """
    Render one Trimmomatic trimming step to CLI form.

    Example:
        {
            "name": "sliding_window",
            "parameters": {
                "window_size": 4,
                "required_quality": 20
            }
        }

    becomes:
        SLIDINGWINDOW:4:20
    """
    step_name = step["name"]
    step_schema = trimmomatic_step_schemas[step_name]
    parameter_schema = step_schema["parameters"]
    parameters = step["parameters"]

    ordered_parameters = sorted(
        parameter_schema.items(),
        key=lambda item: item[1]["position"]
    )

    rendered_values = []

    for parameter_name, parameter_spec in ordered_parameters:
        if parameter_name not in parameters:
            break

        value = parameters[parameter_name]

        if value is None:
            break

        if isinstance(value, bool):
            rendered_values.append(str(value).lower())
        else:
            rendered_values.append(str(value))

    return f"{step_schema['step_name']}:{':'.join(rendered_values)}"


def render_trimmomatic_command(
    node_args: dict,
    resolved_inputs: dict,
    resolved_outputs: dict,
) -> list[str]:
    """
    Build the Trimmomatic command as a list of CLI parts.

    resolved_inputs examples:
        SE:
            {"reads": ["/path/sample.fastq.gz"]}

        PE:
            {"reads": ["/path/sample_R1.fastq.gz", "/path/sample_R2.fastq.gz"]}

    resolved_outputs examples:
        SE:
            {
                "trimmed_reads": "/work/stage_1/sample_trimmed.fastq.gz",
                "summary": "/work/stage_1/trimmomatic_summary.txt",
                "trimlog": "/work/stage_1/trimmomatic_trimlog.txt",
            }

        PE:
            {
                "paired_read_1": "/work/stage_1/sample_R1_paired.fastq.gz",
                "unpaired_read_1": "/work/stage_1/sample_R1_unpaired.fastq.gz",
                "paired_read_2": "/work/stage_1/sample_R2_paired.fastq.gz",
                "unpaired_read_2": "/work/stage_1/sample_R2_unpaired.fastq.gz",
                "summary": "/work/stage_1/trimmomatic_summary.txt",
                "trimlog": "/work/stage_1/trimmomatic_trimlog.txt",
            }
    """
    parts = ["trimmomatic"]

    effective_args = {**node_args}

    if "summary" in resolved_outputs:
        effective_args["summary"] = resolved_outputs["summary"]

    if "trimlog" in resolved_outputs:
        effective_args["trimlog"] = resolved_outputs["trimlog"]

    mode = effective_args.get("mode", "SE")
    parts.append(mode)

    for arg_name, spec in arg_schema.items():
        if arg_name in {"mode", "phred", "compression_mode"}:
            continue

        value = effective_args.get(arg_name)

        if value is None:
            continue

        kind = spec["kind"]
        cli_flag = spec["cli_flag"]

        if kind == "flag":
            if value:
                parts.append(cli_flag)
        elif kind == "option":
            parts.extend([cli_flag, str(value)])

    phred = effective_args.get("phred")
    if phred is not None:
        parts.append(f"-phred{phred}")

    compression_mode = effective_args.get("compression_mode")
    if compression_mode == "stream":
        parts.append("-compressStream")
    elif compression_mode == "block":
        parts.append("-compressBlock")

    input_reads = resolved_inputs["reads"]

    if mode == "SE":
        if len(input_reads) != 1:
            raise ValueError("Trimmomatic SE mode requires exactly one input read.")
        parts.append(input_reads[0])
        parts.append(resolved_outputs["trimmed_reads"])

    elif mode == "PE":
        if len(input_reads) != 2:
            raise ValueError("Trimmomatic PE mode requires exactly two input reads.")
        parts.extend([input_reads[0], input_reads[1]])
        parts.extend([
            resolved_outputs["paired_read_1"],
            resolved_outputs["unpaired_read_1"],
            resolved_outputs["paired_read_2"],
            resolved_outputs["unpaired_read_2"],
        ])

    steps = effective_args.get("steps", [])
    if not steps:
        raise ValueError("Trimmomatic requires at least one trimming step.")

    for step in steps:
        parts.append(_render_trimmomatic_step(step))

    return parts


def resolve_trimmomatic_outputs(node_args: dict, context: dict) -> dict:
    """
    Resolve backend-managed Trimmomatic outputs.

    context example:
        {
            "stage_work_dir": "/work/pipeline_123/stage_1",
            "output_prefix": "sampleA"
        }
    """
    stage_work_dir = context["stage_work_dir"]
    output_prefix = context.get("output_prefix", "trimmomatic")

    mode = node_args.get("mode", "SE")

    outputs = {
        "summary": f"{stage_work_dir}/{output_prefix}_trimmomatic_summary.txt",
        "trimlog": f"{stage_work_dir}/{output_prefix}_trimmomatic_trimlog.txt",
    }

    if mode == "SE":
        outputs["trimmed_reads"] = (
            f"{stage_work_dir}/{output_prefix}_trimmed.fastq.gz"
        )
    else:
        outputs.update({
            "paired_read_1": f"{stage_work_dir}/{output_prefix}_R1_paired.fastq.gz",
            "unpaired_read_1": f"{stage_work_dir}/{output_prefix}_R1_unpaired.fastq.gz",
            "paired_read_2": f"{stage_work_dir}/{output_prefix}_R2_paired.fastq.gz",
            "unpaired_read_2": f"{stage_work_dir}/{output_prefix}_R2_unpaired.fastq.gz",
        })

    return outputs

trimmomatic_tool = build_tool_def(
    metadata=tool_metadata,
    input_contract=input_contract,
    output_contract=output_contract,
    arg_schema=arg_schema,
    rules=rules,
    ui_schema=ui_schema,
    validate_fn=validate_trimmomatic_args,
    render_command_fn=render_trimmomatic_command,
    resolve_outputs_fn=resolve_trimmomatic_outputs,
)

trimmomatic_tool["step_schemas"] = trimmomatic_step_schemas