#!/bin/bash
#SBATCH --partition=slurm
#SBATCH --nodes=4
#SBATCH --ntasks-per-node=1
##SBATCH --nodelist=dc[235-239]
#SBATCH --time=96:00:00
#SBATCH --account=CCHED
#SBATCH --job-name=VIC-Calib
#SBATCH --mail-type=ALL
#SBATCH --mail-user=youngjun.son@pnnl.gov

module purge
module load intel/20.0.4
module load intelmpi/2020u4
module load netcdf/4.8.0
module load gcc/11.2.0
#module load openmpi/4.1.4
module load python/miniconda3.9
source /share/apps/python/miniconda3.9/etc/profile.d/conda.sh
conda activate vic

srun --wait=0 run-calibration.sh

conda deactivate
