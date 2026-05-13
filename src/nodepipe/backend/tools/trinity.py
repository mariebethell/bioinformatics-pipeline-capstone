"""
Defines the argument schema used for validating and generating Trinity commands within
the pipeline backend.

Trinity is modeled as one top level assembly tool node. The backend doesnt expose inchworm,
Chrysalis, or butterfly as seperate graph subnodes.

Input read files are resolved from upstream artifacts, not stores as ordinary user editable args.
the output directory is managed by the backend.
"""

from backend.tools.base import build_tool_def, validate_scalar_arg

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
        "default": None,
        "nullable": True,
        "ui_expose": False,
        "managed_by_engine": True,
        "help_text": "CPU resources are handled by the nf-core Trinity module / Nextflow config.",
    },

    "max_memory": {
        "type": str,
        "kind": "option",
        "cli_flag": "--max_memory",
        "min_value": None,
        "max_value": None,
        "allowed_values": None,
        "default": None,
        "nullable": True,
        "ui_expose": False,
        "managed_by_engine": True,
        "help_text": "Maximum memory is handled by the nf-core Trinity module / Nextflow config.",
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
        "basic": ["seq_type"],
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
    resolve_outputs_fn=resolve_trinity_outputs,
)
