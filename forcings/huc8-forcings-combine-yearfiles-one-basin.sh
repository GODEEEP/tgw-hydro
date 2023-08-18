#!/bin/bash 

indir=$1
outdir=$2
first=1979
last=2022
for i in $(seq $first $last)
do
  echo ${i} `basename $1`
  cdo -w -P 10 cat ${indir}*${i}*.nc ${outdir}tgw_forcings_d01_00625vic_${i}_tmp.nc
  cdo -w -P 10 shifttime,-1hour ${outdir}tgw_forcings_d01_00625vic_${i}_tmp.nc ${outdir}tgw_forcing_d01_00625vic_${i}.nc
  rm ${outdir}tgw_forcings_d01_00625vic_${i}_tmp.nc
done
