#!/usr/bin/env /bin/bash

#SBATCH -p slurm
#SBATCH -N 1
#SBATCH --ntasks-per-node=32
#SBATCH -A GODEEEP
#SBATCH -t 00:01:00


srun huc8-forcings-combine-yearfiles.sh
