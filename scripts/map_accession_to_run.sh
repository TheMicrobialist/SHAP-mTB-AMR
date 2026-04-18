#!/bin/bash

input=$1
output=$2

while read id; do
  curl -s "https://www.ebi.ac.uk/ena/portal/api/search?result=read_run&query=sample_accession=$id&fields=run_accession&format=tsv" | tail -n +2
  curl -s "https://www.ebi.ac.uk/ena/portal/api/search?result=read_run&query=secondary_sample_accession=$id&fields=run_accession&format=tsv" | tail -n +2
done < $input | sort -u > $output