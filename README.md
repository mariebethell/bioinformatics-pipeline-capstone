# CS 490 Bioinformatics Pipeline Project
## Purpose
This software seeks to implement a modular bioinformatics pipeline tailored to analyzing host-microbiome interactions in non-model organisms, such as coral, jellyfish, and agriculturally relevant pest insects with a primary focus on how these interactions are influenced by climate change.
 
Currently, the Biology Department at CSUSM does not utilize most of the data it generates due to the time required to execute tools and the inability to easily configure existing pipelines. The software seeks to address this by being a modular, flexible system that will assist researchers and students currently working in the lab.

# Frontend
The front end is implemented using NodeGraphQT.

# Backend
The backend is written in Python and NextFlow.

# External tools
- FastQC
- Trimmomatic
- QIIME2
- DADA2
- Trinity
- HISAT2
- Salmon
- DESeq2
- InterProScan
- eggNOG