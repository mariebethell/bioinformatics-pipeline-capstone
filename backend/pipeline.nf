nextflow.enable.dsl=2

params.input = [
    "./shared-data/input-files/Test01_L001_R1_001.fastq"
]

include { TRIMMOMATIC } from './backend/modules/nf-core/trimmomatic'

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

            def r1s = files.findAll { it.name ==~ /.*_R?1(_\d+)?\.(fastq|fq)(\.gz)?$/ }.sort()
            def r2s = files.findAll { it.name ==~ /.*_R?2(_\d+)?\.(fastq|fq)(\.gz)?$/ }.sort()

            if (r1s && r2s) {
                def meta = [ id: sample_id, single_end: false ]
                tuple(meta, [ r1s, r2s ])
            } else {
                def meta = [ id: sample_id, single_end: true ]
                tuple(meta, files[0])
            }
        }


    TRIMMOMATIC(reads_ch)
    ch_trimmomatic = TRIMMOMATIC.out.trimmed_reads

}
