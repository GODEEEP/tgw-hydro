#!/usr/bin/env /bin/bash

#nfiles=$(ls -1q /rcfs/projects/godeeep/VIC/forcings/1_16_deg/CONUS_TGW_WRF_Historical/*.nc | wc -l)
#nfiles=208
#files_per_worker=$(expr 1 + ${nfiles} / ${SLURM_NTASKS})
#first=$(expr ${SLURM_PROCID} \* ${files_per_worker})
#last=$(expr ${first} + ${files_per_worker})
#last=$((last>nfiles ? nfiles : last))
#
#for i in $(seq $first $last)
#do
#  echo $i
#  #python huc8-forcings.py $i
#done


file_list=()
while IFS= read -r -d '' file; do
  file_list+=("$file")
done < <(find tgw-conus-forcings/ -maxdepth 1 -type f -print0)

nfiles=${#file_list[@]}
files_per_worker=$(( nfiles / SLURM_NTASKS + 1 ))  # +1 to ensure each worker gets at least one file

first=$(( SLURM_PROCID * files_per_worker ))
last=$(( first + files_per_worker ))

for ((i = first; i < last && i < nfiles; i++))
do
  # echo $SLURM_PROCID "${file_list[i]}"
  python huc8-forcings.py "${file_list[i]}"
done

echo 'Done'
