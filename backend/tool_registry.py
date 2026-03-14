from tools.fastqc import generate_fastqc_process

TOOL_REGISTRY = {
    "fastqc": generate_fastqc_process
}