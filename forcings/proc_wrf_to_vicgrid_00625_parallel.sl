#!/usr/bin/env /bin/bash

#SBATCH -p slurm
#SBATCH -N 1
#SBATCH --ntasks-per-node=10
#SBATCH -A GODEEEP
#SBATCH -t 24:00:00

module load intel/20.0.4
module load netcdf
module load openmpi
module load python/miniconda3.9
source /share/apps/python/miniconda3.9/etc/profile.d/conda.sh
conda activate vic

srun proc_wrf_to_vicgrid_00625_parallel.sh
