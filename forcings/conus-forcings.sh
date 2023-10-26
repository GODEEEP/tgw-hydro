#!/usr/bin/env /bin/bash

file_list=()
while IFS= read -r -d '' file; do
  file_list+=("$file")
done < <(find /rcfs/projects/godeeep/VIC/forcings/1_16_deg/CONUS_TGW_WRF_Historical/ -maxdepth 1 -type f -print0)

nfiles=${#file_list[@]}
files_per_worker=$(( nfiles / SLURM_NTASKS + 1 ))  # +1 to ensure each worker gets at least one file

first=$(( SLURM_PROCID * files_per_worker ))
last=$(( first + files_per_worker ))

for ((i = first; i < last && i < nfiles; i++))
do
  echo $SLURM_PROCID "${file_list[i]}" "HUC $1"
  python -u conus-forcings.py "${file_list[i]}" $1
done

echo "Done with HUC $1"

# for i in {1..18}; do
#   echo $i
# done