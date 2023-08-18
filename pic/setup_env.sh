module load intel/20.0.4
module load netcdf
module load openmpi

module load gcc/11.2.0
module load cdo

module load python/miniconda3.9
source /share/apps/python/miniconda3.9/etc/profile.d/conda.sh
conda activate vic

# export MPICC=/share/apps/openmpi/4.1.0/intel/20.0.4/bin/mpicc
