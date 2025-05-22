#!/usr/bin/env /bin/bash

# script to process each year of processed TGW forcing data and 
# combine them into one file per year, needs to be run as a slurm 
# job to run in parallel

start_year=1980
end_year=2019
years=()

for ((year = start_year; year <= end_year; year++))
do
  years+=($year)
done

nyears=${#years[@]}

# Make sure SLURM_NTASKS is set appropriately in your Slurm environment
if [ -z "$SLURM_NTASKS" ]; then
  echo "SLURM_NTASKS is not set. Please run this script in a Slurm job."
  exit 1
fi

# Calculate the index of the year to be processed by this worker
worker_index=$((SLURM_PROCID % nyears))
year=${years[worker_index]}

echo "Worker $SLURM_PROCID is processing year: $year"

yearfile="/people/sony061/tmp/foresight/forcings/tgw_wrf_historic_${year}_00625vic.nc"

if [ ! -f "$yearfile" ]; then
  echo "Processing year $year: $yearfile"
  cdo -w cat "/people/sony061/tmp/foresight/forcings/scratch/tgw_wrf_historic_6hourly_${year}-*_00625vic.nc" "$yearfile"
  echo "Year $year processing complete"
else
  echo "Year $year: $yearfile already exists. Skipping."
fi

echo "Worker $SLURM_PROCID has completed processing."
