#!/usr/bin/env /bin/bash

file_list=()
while IFS= read -r -d '' file; do
  file_list+=("$file")
done < <(find tgw-huc8-forcings/ -maxdepth 1 -type d -print0)

nfiles=${#file_list[@]}
files_per_worker=$(( nfiles / SLURM_NTASKS + 1 ))  # +1 to ensure each worker gets at least one file

first=$(( SLURM_PROCID * files_per_worker ))
last=$(( first + files_per_worker ))

for ((i = first; i < last && i < nfiles; i++))
do
  echo $SLURM_PROCID "${file_list[i]}"
  #./huc8-forcings-combine-yearfiles-one-basin.sh "${file_list[i]}" "${file_list[i]}"
done
