process TRIMMOMATIC {
    input:
        path READS
    output:
        path /work/stage_1
    script:
        """
        trimmomatic SE -threads 1 -trimlog /work/stage_1/sample1_trimmomatic_trimlog.txt -summary /work/stage_1/sample1_trimmomatic_summary.txt -compressLevel 1 /data/Test01-L001_R1_001.fastq /work/stage_1/sample1_trimmed.fastq.gz SLIDINGWINDOW:4:20
        """
}