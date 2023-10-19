#!/usr/bin/env /bin/bash

#SBATCH -p slurm
#SBATCH -N 1
#SBATCH --ntasks-per-node=1
#SBATCH -A GODEEEP
#SBATCH -t 48:00:00

module load python/miniconda3.9
source /share/apps/python/miniconda3.9/etc/profile.d/conda.sh
conda activate vic

module load gcc/11.2.0
module load intel/20.0.4
module load netcdf/4.8.0
module load openmpi/4.1.0
module load intelmpi/2020u4
module load cdo

# srun conus-forcings-by-huc2.sh

srun -N 1 -n 1 python conus-forcings-by-huc2.py 1980 &
# srun -N 1 -n 1 python conus-forcings-by-huc2.py 1981 &
# srun -N 1 -n 1 python conus-forcings-by-huc2.py 1982 &
# srun -N 1 -n 1 python conus-forcings-by-huc2.py 1983 &
# srun -N 1 -n 1 python conus-forcings-by-huc2.py 1984 &
# srun -N 1 -n 1 python conus-forcings-by-huc2.py 1985 &
# srun -N 1 -n 1 python conus-forcings-by-huc2.py 1986 &
# srun -N 1 -n 1 python conus-forcings-by-huc2.py 1987 &
# srun -N 1 -n 1 python conus-forcings-by-huc2.py 1988 &
# srun -N 1 -n 1 python conus-forcings-by-huc2.py 1989 &
# srun -N 1 -n 1 python conus-forcings-by-huc2.py 1990 &
# srun -N 1 -n 1 python conus-forcings-by-huc2.py 1991 &
# srun -N 1 -n 1 python conus-forcings-by-huc2.py 1992 &
# srun -N 1 -n 1 python conus-forcings-by-huc2.py 1993 &
# srun -N 1 -n 1 python conus-forcings-by-huc2.py 1994 &
# srun -N 1 -n 1 python conus-forcings-by-huc2.py 1995 &
# srun -N 1 -n 1 python conus-forcings-by-huc2.py 1996 &
# srun -N 1 -n 1 python conus-forcings-by-huc2.py 1997 &
# srun -N 1 -n 1 python conus-forcings-by-huc2.py 1998 &
# srun -N 1 -n 1 python conus-forcings-by-huc2.py 1999 &
# srun -N 1 -n 1 python conus-forcings-by-huc2.py 2000 &
# srun -N 1 -n 1 python conus-forcings-by-huc2.py 2001 &
# srun -N 1 -n 1 python conus-forcings-by-huc2.py 2002 &
# srun -N 1 -n 1 python conus-forcings-by-huc2.py 2003 &
# srun -N 1 -n 1 python conus-forcings-by-huc2.py 2004 &
# srun -N 1 -n 1 python conus-forcings-by-huc2.py 2005 &
# srun -N 1 -n 1 python conus-forcings-by-huc2.py 2006 &
# srun -N 1 -n 1 python conus-forcings-by-huc2.py 2007 &
# srun -N 1 -n 1 python conus-forcings-by-huc2.py 2008 &
# srun -N 1 -n 1 python conus-forcings-by-huc2.py 2009 &
# srun -N 1 -n 1 python conus-forcings-by-huc2.py 2010 &
# srun -N 1 -n 1 python conus-forcings-by-huc2.py 2011 &
# srun -N 1 -n 1 python conus-forcings-by-huc2.py 2012 &
# srun -N 1 -n 1 python conus-forcings-by-huc2.py 2013 &
# srun -N 1 -n 1 python conus-forcings-by-huc2.py 2014 &
# srun -N 1 -n 1 python conus-forcings-by-huc2.py 2015 &
# srun -N 1 -n 1 python conus-forcings-by-huc2.py 2016 &
# srun -N 1 -n 1 python conus-forcings-by-huc2.py 2017 &
# srun -N 1 -n 1 python conus-forcings-by-huc2.py 2018 &
# srun -N 1 -n 1 python conus-forcings-by-huc2.py 2019 &
# srun -N 1 -n 1 python conus-forcings-by-huc2.py 2020 &
# srun -N 1 -n 1 python conus-forcings-by-huc2.py 2021 &
# srun -N 1 -n 1 python conus-forcings-by-huc2.py 2022 &
wait 

echo 'Really Done'
