nextflow.enable.dsl=2

params.input = [
    "/home/ethancode/capstone/bioinformatics-pipeline-capstone/data/Test01_L001_R1_001.fastq",
    "/home/ethancode/capstone/bioinformatics-pipeline-capstone/data/Test01_L001_R2_001.fastq"
]

include { FASTQC as FASTQC1 } from './backend/modules/nf-core/fastqc'
include { TRIMMOMATIC } from './backend/modules/nf-core/trimmomatic'
include { FASTQC as FASTQC2 } from './backend/modules/nf-core/fastqc'

workflow {

    reads_ch = Channel.fromPath(params.input, checkIfExists: true)
        .map { f ->
            def name = f.getName()

            def sample_id = name
                .replaceAll(/_R?1(_\d+)?\.(fastq|fq)(\.gz)?$/, '')
                .replaceAll(/_R?2(_\d+)?\.(fastq|fq)(\.gz)?$/, '')

            tuple(sample_id, f)
        }
        .groupTuple()
        .map { sample_id, files ->
            def files_list = files.toList()
            def r1 = files_list.find { it.getName() ==~ /.*_R?1(_\d+)?\.(fastq|fq)(\.gz)?$/ }
            def r2 = files_list.find { it.getName() ==~ /.*_R?2(_\d+)?\.(fastq|fq)(\.gz)?$/ }
            def meta = [ id: sample_id ]

            if (r1 && r2) {
                tuple(meta, [ r1, r2 ])
            } else {
                tuple(meta, files_list[0])
            }
        }

    FASTQC1(reads_ch)
    ch_fastqc1 = FASTQC1.out.zip

    TRIMMOMATIC(reads_ch)
    ch_trimmomatic = TRIMMOMATIC.out.trimmed_reads

    FASTQC2(ch_trimmomatic)
    ch_fastqc2 = FASTQC2.out.zip

}
