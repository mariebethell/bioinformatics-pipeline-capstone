include { FASTQC } from 'backend\modules\stage_1_fastqc.nf'
include { TRIMMOMATIC } from 'backend\modules\stage_2_trimmomatic.nf'
workflow {
    read_ch = Channel.fromPath('C:/Users/Marie Bethell/projects/bioinformatics-pipeline-capstone/data/Test01_L001_R1_001.fastq')
    FASTQC(read_ch)
    TRIMMOMATIC(read_ch)
}
