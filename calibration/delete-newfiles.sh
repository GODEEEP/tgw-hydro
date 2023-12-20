#!/bin/bash

#module purge
module load jq

basin="00"
key=08LD000
json_in=grid_ids_ca_group.json
csv_in=grid_ids_ca_check.csv
path_ctr=/people/sony061/projects/godeeep/VIC/inputs_1_16_deg_by_huc2/$basin

pts=$(jq .\"$key\" $json_in)
pts=${pts// /}  # remove space
pts=${pts//,/}  # remove ,
pts=${pts//\"/} # remove "
pts=${pts##[}   # remove [
pts=${pts%]}    # remove ]
pts=($pts)      # declare array

cd $path_ctr
for p in "${pts[@]}"
do
  find . -name "forcings_6h_16thdeg_$p*" -delete
  echo $path_ctr...forcings_6h_16thdeg_$p*
  find . -name "runoff_concat_16thdeg_$p*" -delete
  echo $path_ctr...runoff_concat_16thdeg_$p*
done