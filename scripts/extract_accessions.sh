#!/bin/bash

input=$1
output=$2

awk -F',' 'NR>1 {print $NF}' "$input" > "$output"

## Usage:
## scripts/extract_accessions.sh resistance_dataset/accessions_to_download.csv resistance_dataset/sra_accessions.txt