nextflow.enable.dsl=2

params.input = [
    "../data/Test01_L001_R1_001.fastq",
    "../data/Test01_L001_R2_001.fastq",
    "../data/Test02_L001_R1_001.fastq",
    "../data/Test02_L001_R2_001.fastq"
]

include { FASTQC as FASTQC1 } from './modules/nf-core/fastqc/main'
include { TRIMMOMATIC } from './modules/nf-core/trimmomatic/main'
include { FASTQC as FASTQC2 } from './modules/nf-core/fastqc/main'

workflow {

    reads_ch = Channel.fromPath(params.input, checkIfExists: true)
        .map { f ->
        def name = f.getName()

        def sample_id = name
            .replaceAll(/_R?1(_\d+)?\.fastq$/, '')
            .replaceAll(/_R?2(_\d+)?\.fastq$/, '')

        tuple(sample_id, f  )
        }
        .groupTuple()
        .map { sample_id, files ->

            def files_list = files.toList()

            def r1 = files_list.find { it.getName() ==~ /.*_R?1(_\d+)?\.fastq$/ }
            def r2 = files_list.find { it.getName() ==~ /.*_R?2(_\d+)?\.fastq$/ }

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
