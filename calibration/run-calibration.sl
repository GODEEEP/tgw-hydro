#!/bin/bash

#SBATCH -A godeeep
#SBATCH -N 15
#SBATCH --ntasks-per-node 1
#SBATCH -p slurm
#SBATCH -t 72:00:00
#SBATCH --job-name vic_calib

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

srun --wait=0 run-calibration.sh

conda deactivate
