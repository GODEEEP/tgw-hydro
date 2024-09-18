#!/bin/bash
#SBATCH --partition=slurm
#SBATCH --nodes=1
#SBTACH --ntasks=1
#SBATCH --cpus-per-task=64
#SBATCH --account=GODEEEP
#SBATCH --time=96:00:00
#SBATCH --job-name=mosartwmpy
#SBATCH --mail-type=ALL
#SBATCH --mail-user=youngjun.son@pnnl.gov

echo 'Loading modules'

module purge
module load python/miniconda3.9
source /share/apps/python/miniconda3.9/etc/profile.d/conda.sh
conda activate mosartwmpypip

echo 'Done loading modules'

ulimit -s unlimited

export NUMBA_NUM_THREADS=64
srun python -u run_mosartwmpy.py

echo 'Really Done'