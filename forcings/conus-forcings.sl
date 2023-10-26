#!/usr/bin/env /bin/bash

#SBATCH -p slurm
#SBATCH -N 18
#SBATCH -A GODEEEP
#SBATCH -t 48:00:00
#SBATCH --ntasks-per-node=64

# --ntasks-per-node=64
module load intel/20.0.4
module load netcdf
module load openmpi

module load python/miniconda3.9
source /share/apps/python/miniconda3.9/etc/profile.d/conda.sh
conda activate vic

# for i in {1..18}; do
#   srun -N 1 -n 64 conus-forcings.sh $i
# done
srun -N 1 conus-forcings.sh 1

echo 'Really Done'