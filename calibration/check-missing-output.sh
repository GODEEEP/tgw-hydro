#!/bin/bash
module load jq

key=08LD000
json_in=grid_ids_ca_group.json
csv_in=grid_ids_ca_check.csv
path_out=outputs/$key
check_file=vic_runoff.1979-01-01.nc

pts=$(jq .\"$key\" $json_in)
pts=${pts// /}  # remove space
pts=${pts//,/}  # remove ,
pts=${pts//\"/} # remove "
pts=${pts##[}   # remove [
pts=${pts%]}    # remove ]
pts=($pts)      # declare array

n=0
for i in ${pts[@]}
do
  hit_file=$(find $path_out/*$i*/mod0_calib/ -name $check_file | wc -l)
  echo $i:$hit_file '('$path_out/*$i*/mod0_calib/$check_file')'
  n=$(expr $n + $hit_file)
done
echo OK...$n/${#pts[@]}