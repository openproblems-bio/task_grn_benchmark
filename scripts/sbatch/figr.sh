#!/bin/bash
#SBATCH --job-name=figr
#SBATCH --time=48:00:00
#SBATCH --output=logs/%j.out
#SBATCH --error=logs/%j.err
#SBATCH --mail-type=END
#SBATCH --mail-user=jalil.nourisa@gmail.com
#SBATCH --cpus-per-task=20
#SBATCH --mem=250G


singularity run ../../images/figr Rscript src/methods/multi_omics/figr/script.R 
