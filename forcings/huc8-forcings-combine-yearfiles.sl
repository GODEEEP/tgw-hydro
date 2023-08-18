#!/usr/bin/env /bin/bash

#SBATCH -p slurm
#SBATCH -N 1
#SBATCH --ntasks-per-node=34
#SBATCH -A GODEEEP
#SBATCH -t 48:00:00


module load intel/20.0.4
module load netcdf
module load openmpi

module load gcc/11.2.0
module load cdo

srun huc8-forcings-combine-yearfiles.sh

echo 'Really Done'
