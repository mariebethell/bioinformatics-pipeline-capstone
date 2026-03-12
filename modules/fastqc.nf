process FASTQC {
    tag "$fqFile"

    publishDir "${params.outdir}/fastqc", mode: 'copy'

    input:
    path fqFile

    output:
    path "*_fastqc.zip"
    path "*_fastqc.html"

    script:
    """
    $projectDir/fastqc/FastQC/fastqc -t 32 $fqFile
    """
}