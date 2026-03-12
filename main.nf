// Default parameter input
params.in = file('in/*.fastq.gz')
params.outdir = file('results')

process fastqc {
    publishDir "${params.outdir}/fastQC", mode: 'copy'

    input:
    path fqFile

    output:
    file "*_fastqc.{zip,html}"

    script:
    """
    "$projectDir/fastqc/FastQC/fastqc" -t 32 $fqFile
    """ 
}

/*
process trim {
    publishDir "results/trimmomatic"

    input:
    path fqFile

    output:
    path 'trim_*'

    script:
    """
    java -jar $projectDir/trimmomatic/trimmomatic-0.40.jar SE $fqFile trim_test.fq ILLUMINACLIP:TruSeq3-PE.fa:2:30:10 LEADING:3 TRAILING:3 SLIDINGWINDOW:4:15 MINLEN:36
    """ 
}
*/

// Workflow block
workflow {
    fqFiles = channel.of(params.in)       // Create a channel using parameter input
    fastqc(fqFiles)
    // trim(fqFiles)
}