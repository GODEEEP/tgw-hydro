module load intel/20.0.4
module load netcdf
module load openmpi

# export MPICC=/share/apps/openmpi/4.1.0/intel/20.0.4/bin/mpicc
export OMP_NUM_THREADS=64
export OMP_PROC_BIND=spread
export OMP_PLACES=threads
