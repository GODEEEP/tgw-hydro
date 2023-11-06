#!/bin/bash 

module load python/miniconda3.9
source /share/apps/python/miniconda3.9/etc/profile.d/conda.sh
conda activate vic

module load gcc/11.2.0
module load openmpi/4.1.4

module load intel/20.0.4
module load intelmpi/2020u4
module load netcdf/4.8.0

module load cdo

export OMP_NUM_THREADS=1
#export OMP_PROC_BIND=spread
#export OMP_PLACES=threads