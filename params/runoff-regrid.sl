#!/bin/bash
#SBATCH --partition=shared
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
##SBATCH --nodelist=dc241
#SBATCH --time=96:00:00
#SBATCH --account=CCHED
#SBATCH --job-name=RunoffRegrid
#SBATCH --mail-type=ALL
#SBATCH --mail-user=youngjun.son@pnnl.gov

module load python/miniconda3.9
source /share/apps/python/miniconda3.9/etc/profile.d/conda.sh
conda activate xesmf_env

python -u runoff-regrid.py

conda deactivate