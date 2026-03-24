"""
Defines the argument schema used for validating and generating Trinity commands within
the pipeline backend.

Trinity is modeled as one top level assembly tool node. The backend doesnt expose inchworm,
Chrysalis, or butterfly as seperate graph subnodes.

Input read files are resolved from upstream artifacts, not stores as ordinary user editable args.
the output directory is managed by the backend.
"""

from tools.base import build_tool_def, validate_scalar_arg

tool_metadata = {
    "name": "trinity",
    "display_name": "Trinity",
    "category": "transcriptome_assembly",
    "supports_single_end": True,
    "supports_paired_end": True,
}

input_contract = {
    "accepted_formats": ["fastq", "fastq.gz", "fq", "fq.gz", "fasta", "fa"],
    "input_style": "single_or_paired_read_sets",
}

output_contract = {
    "produced_formats": ["fasta"],
    "output_style": "trinity_assembly_dir",
}

arg_schema = {
    "seq_type": {
        "type": str,
        "kind": "option",
        "cli_flag": "--seqType",
        "min_value": None,
        "max_value": None,
        "allowed_values": ["fq", "fa"],
        "default": "fq",
        "nullable": False,
        "ui_expose": True,
        "managed_by_engine": False,
        "help_text": "Input sequence type: fq for FASTQ, fa for FASTA.",
    },

    "cpu": {
        "type": int,
        "kind": "option",
        "cli_flag": "--CPU",
        "min_value": 1,
        "max_value": 128,
        "allowed_values": None,
        "default": 1,
        "nullable": False,
        "ui_expose": True,
        "managed_by_engine": False,
        "help_text": "Maximum number of CPU threads to use.",
    },

    "max_memory": {
        "type": str,
        "kind": "option",
        "cli_flag": "--max_memory",
        "min_value": None,
        "max_value": None,
        "allowed_values": None,
        "default": "14G",
        "nullable": False,
        "ui_expose": True,
        "managed_by_engine": False,
        "help_text": "Maximum memory to allocate, for example 14G or 50G.",
    },

    "output": {
        "type": str,
        "kind": "option",
        "cli_flag": "--output",
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

rules = [
    "Provide either paired-end reads or single-end reads.",
    "Do not mix paired and single-end inputs in the basic trinity node.",
    "The trinity output directory is back-end managed",
]

ui_schema = {
    "sections": {
        "basic": ["seq_type", "cpu", "max_memory"],
        "advanced": [],
    }
}


def validate_trinity_args(args: dict, context: dict | None = None) -> list[str]:
    """
    Validate Trinity args against the flat arg schema.

    Input-read wiring is validated separately during command rendering, because
    read files come from resolved_inputs rather than node_args.
    """
    errors = []

    if not isinstance(args, dict):
        return ["Arguments must be a dictionary."]

    for arg_name, value in args.items():
        if arg_name not in arg_schema:
            errors.append(f"Unknown Trinity argument: '{arg_name}'.")
            continue

        errors.extend(validate_scalar_arg(arg_name, value, arg_schema[arg_name]))

    return errors

def render_trinity_command(
    node_args: dict,
    resolved_inputs: dict,
    resolved_outputs: dict,
) -> list[str]:
    """
    Build the Trinity command as a list of CLI parts.

    resolved_inputs examples:

        Paired-end:
            {
                "left_reads": [
                    "/path/sampleA_R1.fastq.gz",
                    "/path/sampleB_R1.fastq.gz",
                ],
                "right_reads": [
                    "/path/sampleA_R2.fastq.gz",
                    "/path/sampleB_R2.fastq.gz",
                ],
            }

        Single-end:
            {
                "single_reads": [
                    "/path/sampleA.fastq.gz",
                    "/path/sampleB.fastq.gz",
                ]
            }

    resolved_outputs example:
        {
            "outdir": "/work/pipeline_123/stage_2/sampleA_trinity_out_dir",
            "assembly_fasta": "/work/pipeline_123/stage_2/sampleA_trinity_out_dir/Trinity.fasta",
        }
    """
    parts = ["Trinity"]

    effective_args = {**node_args}
    effective_args["output"] = resolved_outputs["outdir"]

    for arg_name, spec in arg_schema.items():
        value = effective_args.get(arg_name)

        if value is None:
            continue

        kind = spec["kind"]
        cli_flag = spec["cli_flag"]

        if kind == "option":
            parts.extend([cli_flag, str(value)])

    left_reads = resolved_inputs.get("left_reads", [])
    right_reads = resolved_inputs.get("right_reads", [])
    single_reads = resolved_inputs.get("single_reads", [])

    has_paired = bool(left_reads) or bool(right_reads)
    has_single = bool(single_reads)

    if has_paired and has_single:
        raise ValueError(
            "Trinity input resolution cannot mix paired-end and single-end reads "
            "in the basic node configuration."
        )

    if has_paired:
        if not left_reads or not right_reads:
            raise ValueError(
                "Trinity paired-end mode requires both 'left_reads' and 'right_reads'."
            )

        if len(left_reads) != len(right_reads):
            raise ValueError(
                "Trinity paired-end mode requires the same number of left and right read files."
            )

        parts.extend(["--left", ",".join(left_reads)])
        parts.extend(["--right", ",".join(right_reads)])

    elif has_single:
        parts.extend(["--single", ",".join(single_reads)])

    else:
        raise ValueError(
            "Trinity requires either paired-end reads or single-end reads."
        )

    return parts

def resolve_trinity_outputs(node_args: dict, context: dict) -> dict:
    """
    Resolve backend-managed Trinity outputs.

    context example:
        {
            "stage_work_dir": "/work/pipeline_123/stage_2",
            "output_prefix": "sampleA"
        }
    """
    stage_work_dir = context["stage_work_dir"]
    output_prefix = context.get("output_prefix", "trinity")

    outdir = f"{stage_work_dir}/{output_prefix}_trinity_out_dir"

    return {
        "outdir": outdir,
        "assembly_fasta": f"{outdir}/Trinity.fasta",
    }


trinity_tool = build_tool_def(
    metadata=tool_metadata,
    input_contract=input_contract,
    output_contract=output_contract,
    arg_schema=arg_schema,
    rules=rules,
    ui_schema=ui_schema,
    validate_fn=validate_trinity_args,
    render_command_fn=render_trinity_command,
    resolve_outputs_fn=resolve_trinity_outputs,
)
