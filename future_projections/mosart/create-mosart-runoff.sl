#!/bin/bash

#SBATCH -A godeeep
#SBATCH -N 1
#SBATCH -p shared
##SBATCH -p slurm
#SBATCH -w dc220
##SBATCH -w dc[025,045,098,188,031,220]
#SBATCH -t 168:00:00
#SBATCH --cpus-per-task=4
#SBATCH --job-name mosart-inputs

module purge
# module load python/miniconda4.12
# source /share/apps/python/miniconda4.12/etc/profile.d/conda.sh
module load intel/20.0.4
module load intelmpi/2020u4
module load netcdf/4.8.0
module load gcc/11.2.0
module load openmpi/4.1.4
module load python/miniconda3.9
source /share/apps/python/miniconda3.9/etc/profile.d/conda.sh
conda activate vic

srun python -u create-mosart-runoff.py

conda deactivate
