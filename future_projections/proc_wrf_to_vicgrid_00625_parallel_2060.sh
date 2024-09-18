#!/usr/bin/env /bin/bash

nfiles=$(ls -1q /rcfs/projects/godeeep/shared_data/tgw_wrf/rcp85cooler_2060_2099/hourly/*.nc | wc -l)
files_per_worker=$(expr 1 + ${nfiles} / ${SLURM_NTASKS})
first=$(expr ${SLURM_PROCID} \* ${files_per_worker})
last=$(expr ${first} + ${files_per_worker})
last=$((last>nfiles ? nfiles : last))

for i in $(seq $first $last)
do
  python -u proc_wrf_to_vicgrid_00625_parallel_2060.py $i
done
