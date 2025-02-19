#!/usr/bin/env /bin/bash

#SBATCH -p slurm
#SBATCH -N 1
#SBATCH --ntasks-per-node=44
#SBATCH -A GODEEEP
#SBATCH -t 24:00:00


module load intel/20.0.4
module load netcdf
module load openmpi

module load gcc/11.2.0
module load cdo

srun conus-forcings-combine-yearfiles_2060.sh

echo 'Really Done'
