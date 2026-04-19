from __future__ import annotations

from typing import Iterable

from backend.compiled_node import CompiledNode


INDENT = " " * 4


def _coerce_bool(value) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y", "on"}
    return bool(value)


def _groovy_single_quote(value: str) -> str:
    escaped = str(value).replace("\\", "\\\\").replace("'", "\\'")
    return f"'{escaped}'"


def _join_flags(parts: Iterable[str]) -> str:
    return " ".join(part.strip() for part in parts if part and str(part).strip())


def _maybe_flag(flag: str, enabled) -> str:
    return flag if _coerce_bool(enabled) else ""


def _maybe_option(flag: str, value, suffix: str = "") -> str:
    if value is None or value == "":
        return ""
    return f"{flag} {value}{suffix}" if not flag.endswith(":") else f"{flag}{value}{suffix}"


def _normalize_step_name(name: str) -> str:
    return (name or "").strip().lower().replace("-", "_").replace(" ", "_")


def _collect_trimmomatic_steps(args: dict) -> list[dict]:
    explicit_steps = args.get("steps")
    if isinstance(explicit_steps, list) and explicit_steps:
        return explicit_steps

    synthesized_steps: list[dict] = []

    def add_step(step_name: str, parameters: dict):
        filtered = {k: v for k, v in parameters.items() if v not in (None, "")}
        if filtered:
            synthesized_steps.append({"name": step_name, "parameters": filtered})

    add_step(
        "illuminaclip",
        {
            "fasta_with_adapters": args.get("fasta_with_adapters"),
            "seed_mismatches": args.get("seed_mismatches"),
            "palindrome_clip_threshold": args.get("palindrome_clip_threshold"),
            "simple_clip_threshold": args.get("simple_clip_threshold"),
            "min_adapter_length_palindrome": args.get("min_adapter_length_palindrome"),
            "keep_both_reads": args.get("keep_both_reads"),
        },
    )
    add_step("leading", {"quality": args.get("leading")})
    add_step("trailing", {"quality": args.get("trailing")})
    add_step("headcrop", {"length": args.get("head_crop")})
    add_step("tailcrop", {"length": args.get("trail_crop") or args.get("tail_crop")})
    add_step("crop", {"length": args.get("crop")})
    add_step(
        "sliding_window",
        {
            "window_size": args.get("sliding_window_size") or args.get("window_size"),
            "required_quality": args.get("required_quality"),
        },
    )
    add_step(
        "maxinfo",
        {
            "target_length": args.get("target_length"),
            "strictness": args.get("strictness"),
        },
    )
    add_step("minlen", {"length": args.get("min_len")})
    add_step("maxlen", {"length": args.get("max_len")})
    add_step("avgqual", {"quality": args.get("avg_qual")})
    add_step(
        "basecount",
        {
            "bases": args.get("bases"),
            "min_count": args.get("min_count"),
            "max_count": args.get("max_count"),
        },
    )
    return synthesized_steps


def _render_trimmomatic_step(step: dict) -> str:
    name = _normalize_step_name(step.get("name"))
    params = step.get("parameters", {}) or {}

    if name == "illuminaclip":
        tokens = [
            params.get("fasta_with_adapters"),
            params.get("seed_mismatches"),
            params.get("palindrome_clip_threshold"),
            params.get("simple_clip_threshold"),
        ]
        optional = []
        if params.get("min_adapter_length_palindrome") not in (None, ""):
            optional.append(params.get("min_adapter_length_palindrome"))
        if params.get("keep_both_reads") not in (None, ""):
            optional.append("true" if _coerce_bool(params.get("keep_both_reads")) else "false")
        values = [str(token) for token in tokens if token not in (None, "")] + [str(token) for token in optional]
        return f"ILLUMINACLIP:{':'.join(values)}" if values else ""

    if name == "leading":
        return f"LEADING:{params.get('quality')}" if params.get("quality") not in (None, "") else ""
    if name == "trailing":
        return f"TRAILING:{params.get('quality')}" if params.get("quality") not in (None, "") else ""
    if name == "headcrop":
        return f"HEADCROP:{params.get('length')}" if params.get("length") not in (None, "") else ""
    if name == "tailcrop":
        return f"TAILCROP:{params.get('length')}" if params.get("length") not in (None, "") else ""
    if name == "crop":
        return f"CROP:{params.get('length')}" if params.get("length") not in (None, "") else ""
    if name == "sliding_window":
        window_size = params.get("window_size")
        required_quality = params.get("required_quality")
        if window_size in (None, "") or required_quality in (None, ""):
            return ""
        return f"SLIDINGWINDOW:{window_size}:{required_quality}"
    if name == "maxinfo":
        target_length = params.get("target_length")
        strictness = params.get("strictness")
        if target_length in (None, "") or strictness in (None, ""):
            return ""
        return f"MAXINFO:{target_length}:{strictness}"
    if name == "minlen":
        return f"MINLEN:{params.get('length')}" if params.get("length") not in (None, "") else ""
    if name == "maxlen":
        return f"MAXLEN:{params.get('length')}" if params.get("length") not in (None, "") else ""
    if name == "avgqual":
        return f"AVGQUAL:{params.get('quality')}" if params.get("quality") not in (None, "") else ""
    if name == "basecount":
        bases = params.get("bases")
        min_count = params.get("min_count")
        max_count = params.get("max_count")
        if bases in (None, ""):
            return ""
        tokens = [str(bases)]
        if min_count not in (None, ""):
            tokens.append(str(min_count))
        if max_count not in (None, ""):
            tokens.append(str(max_count))
        return f"BASECOUNT:{':'.join(tokens)}"

    return ""


def build_fastqc_ext_args(args: dict) -> str:
    return _join_flags(
        [
            _maybe_flag("--quiet", args.get("quiet")),
            _maybe_flag("--nogroup", args.get("nogroup")),
            _maybe_option("--kmers", args.get("kmers")),
            _maybe_option("--adapters", args.get("adapters")),
            _maybe_option("--contaminants", args.get("contaminants")),
            _maybe_option("--limits", args.get("limits")),
            _maybe_option("--format", args.get("format")),
            _maybe_flag("--extract", args.get("extract")),
            args.get("extra_args", ""),
        ]
    )


def build_trimmomatic_ext_args(args: dict) -> str:
    compression_mode = (args.get("compression_mode") or "").lower()
    phred = args.get("phred")
    if phred not in (None, ""):
        phred = f"-phred{phred}"
    return _join_flags(
        [
            phred or "",
            _maybe_flag("-validatePairs", args.get("validate_pairs") or args.get("validatePairs")),
            _maybe_option("-compressLevel", args.get("compress_level")),
            "-compressStream" if compression_mode == "stream" else "",
            "-compressBlock" if compression_mode == "block" else "",
            args.get("extra_args", ""),
        ]
    )


def build_trimmomatic_ext_args2(args: dict) -> str:
    steps = _collect_trimmomatic_steps(args)
    return _join_flags(_render_trimmomatic_step(step) for step in steps)


def build_trinity_ext_args(args: dict) -> str:
    max_memory = args.get("max_memory")
    max_memory_part = ""
    if max_memory not in (None, ""):
        max_memory_str = str(max_memory)
        max_memory_part = f"--max_memory {max_memory_str if max_memory_str.upper().endswith('G') else max_memory_str + 'G'}"

    return _join_flags(
        [
            _maybe_option("--seqType", args.get("seq_type")),
            _maybe_option("--CPU", args.get("cpu")),
            max_memory_part,
            args.get("extra_args", ""),
        ]
    )


def build_ext_args_for_tool(tool: str, args: dict) -> str:
    tool_key = (tool or "").lower()
    if tool_key == "fastqc":
        return build_fastqc_ext_args(args)
    if tool_key == "trimmomatic":
        return build_trimmomatic_ext_args(args)
    if tool_key == "trinity":
        return build_trinity_ext_args(args)
    return _join_flags([args.get("extra_args", "")])


def build_ext_args2_for_tool(tool: str, args: dict) -> str:
    tool_key = (tool or "").lower()
    if tool_key == "trimmomatic":
        return build_trimmomatic_ext_args2(args)
    return ""


def render_modules_config_block(node: CompiledNode) -> str:
    lines = [f"{INDENT}withName: '{node.alias}' {{"]

    if node.ext_args:
        lines.append(f"{INDENT * 2}ext.args = {_groovy_single_quote(node.ext_args)}")
    if node.ext_args2:
        lines.append(f"{INDENT * 2}ext.args2 = {_groovy_single_quote(node.ext_args2)}")

    lines.append(f"{INDENT * 2}ext.prefix = {{ \"{node.prefix_expr}\" }}")
    lines.extend(
        [
            f"{INDENT * 2}publishDir = [",
            f"{INDENT * 3}path: {{ \"${{params.outdir}}/{node.publish_subdir}\" }},",
            f"{INDENT * 3}mode: params.publish_dir_mode,",
            f"{INDENT * 3}saveAs: {{ filename -> filename.equals('versions.yml') ? null : filename }}",
            f"{INDENT * 2}]",
            f"{INDENT}}}",
        ]
    )
    return "\n".join(lines)


def render_modules_config(nodes: list[CompiledNode]) -> str:
    blocks = [
        "/*",
        " * Auto-generated nf-core module overrides.",
        " * Each block is compiled from a normalized pipeline node.",
        " */",
        "",
        "process {",
        "",
        f"{INDENT}publishDir = [",
        f"{INDENT * 2}path: {{ \"${{params.outdir}}/${{task.process.tokenize(':')[-1].toLowerCase()}}\" }},",
        f"{INDENT * 2}mode: params.publish_dir_mode,",
        f"{INDENT * 2}saveAs: {{ filename -> filename.equals('versions.yml') ? null : filename }}",
        f"{INDENT}]",
    ]

    for node in nodes:
        blocks.append("")
        blocks.append(render_modules_config_block(node))

    blocks.append("}")
    blocks.append("")
    return "\n".join(blocks)
