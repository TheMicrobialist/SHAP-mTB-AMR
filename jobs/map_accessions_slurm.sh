#!/bin/bash
#SBATCH --cpus-per-task=8
#SBATCH --mem=8G
#SBATCH --time=08:30:00
#SBATCH --mail-type=FAIL
#SBATCH --mail-user=qp24@queensu.ca
#SBATCH -o %x.%j.out
#SBATCH -e %x.%j.err

module load StdEnv/2023

cd "$SLURM_SUBMIT_DIR"

chmod +x ../scripts/map_accession_to_run.sh

../scripts/map_accession_to_run.sh ../resistance_dataset/sra_accessions.txt ../resistance_dataset/run_accessions.txt 8