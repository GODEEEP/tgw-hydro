#!/usr/bin/env /bin/bash

#SBATCH -p slurm
#SBATCH -N 1
#SBATCH -A GODEEEP
#SBATCH -t 1:00:00
#SBATCH --ntasks-per-node=1

module load python/miniconda3.9
source /share/apps/python/miniconda3.9/etc/profile.d/conda.sh
conda activate vic

srun python -u check-mem.py 

echo 'Done'
