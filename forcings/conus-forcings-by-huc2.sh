#!/usr/bin/env /bin/bash

# script to process each year of processed TGW forcing data and 
# combine them into one file per year, needs to be run as a slurm 
# job to run in parallel

start_year=$1
end_year=$2
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

python conus-forcings-by-huc2.py $year

echo "Worker $SLURM_PROCID has completed processing."