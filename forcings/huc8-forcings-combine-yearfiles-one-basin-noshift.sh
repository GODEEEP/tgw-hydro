#!/bin/bash 

indir=$1
outdir=$2
first=1979
last=2022
huc8=`basename $1`
for i in $(seq $first $last)
do
  yearfile=${outdir}/tgw_forcing_d01_00625vic_${huc8}_${i}.nc
  tmp_yearfile=${outdir}/tgw_forcings_d01_00625vic_${huc8}_${i}_tmp.nc
  
  if [ ! -f $yearfile ]; then
    echo $SLURM_PROCID ${i} ${huc8} $indir $outdir
    cdo -w cat ${indir}/forcings_${huc8}_${i}*.nc $yearfile
    #cdo -w shifttime,-1hour $tmp_yearfile $yearfile
    #rm $tmp_yearfile
  fi
done
