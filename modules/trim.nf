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