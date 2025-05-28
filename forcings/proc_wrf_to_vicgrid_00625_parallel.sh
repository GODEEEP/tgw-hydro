#!/usr/bin/env /bin/bash

nfiles=$(ls -1q /scratch/sony061/foresight/forcings/raw/hist/*.nc | wc -l)
files_per_worker=$(expr 1 + ${nfiles} / ${SLURM_NTASKS})
first=$(expr ${SLURM_PROCID} \* ${files_per_worker})
last=$(expr ${first} + ${files_per_worker})
last=$((last>nfiles ? nfiles : last))

for i in $(seq $first $last)
do
  python -u proc_wrf_to_vicgrid_00625_parallel.py $i
done
