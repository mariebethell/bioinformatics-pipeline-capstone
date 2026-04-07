process FASTQC {
    input:
        path READS
    output:
        path /work/stage_0
    script:
        """
        fastqc --threads 1 --kmers 7 --format fastq --outdir /work/stage_0 /data/Test01-L001_R1_001.fastq
        """
}