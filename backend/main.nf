nextflow.enable.dsl=2

include { FASTQC } from 'backend/modules/stage_1_fastqc.nf'
include { TRIMMOMATIC } from 'backend/modules/stage_2_trimmomatic.nf'

workflow {
    read_ch = Channel.fromPath('C:/Users/Marie Bethell/projects/bioinformatics-pipeline-capstone/data/Test01_L001_R1_001.fastq')
    fastqc_1_out = FASTQC(read_ch)
    trimmomatic_2_out = TRIMMOMATIC(fastqc_1_out)
}
