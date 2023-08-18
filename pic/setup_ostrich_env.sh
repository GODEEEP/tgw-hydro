module load intel/20.0.4
module load netcdf
module load openmpi
module load gcc/11.2.0
module load intelmpi/2020u4

export OMP_NUM_THREADS=64
export OMP_PROC_BIND=spread
export OMP_PLACES=threads
