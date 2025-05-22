#!/bin/bash
#SBATCH --partition=shared
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
##SBATCH --nodelist=dc239
#SBATCH --time=12:00:00
#SBATCH --account=CCHED
#SBATCH --job-name=VIC
#SBATCH --mail-type=ALL
#SBATCH --mail-user=youngjun.son@pnnl.gov

module purge
module load intel/20.0.4 intelmpi/2020u4 netcdf/4.8.0

cd /rcfs/projects/cched/test/VIC-CCSM/06
mpirun -np 16 ./vic_image_impi.exe -g config.txt >& run_vic.log
echo Completed!
