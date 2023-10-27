#!/usr/bin/env /bin/bash

#SBATCH --partition=shared
#SBATCH --nodes=1
#SBATCH --cpus-per-task=12
#SBATCH --ntasks-per-node=1
#SBATCH --account=GODEEEP
#SBATCH --time=48:00:00

echo 'Loading modules'

module load python/miniconda3.9
source /share/apps/python/miniconda3.9/etc/profile.d/conda.sh
conda activate vic

module load gcc/11.2.0
module load intel/20.0.4
module load netcdf/4.8.0
module load openmpi/4.1.0
module load intelmpi/2020u4
module load cdo

echo 'Done loading modules'

srun python -u huc2-subset-params-domain.py

echo 'Really Done'