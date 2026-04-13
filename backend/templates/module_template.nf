process TOOL_NAME {
    input:
        path "READS"
    output:
        path "OUTPUT"
    script:
        """
        "COMMAND"
        """
}