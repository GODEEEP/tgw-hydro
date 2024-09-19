#!/usr/bin/env /bin/bash

# script to process each year of processed TGW forcing data and 
# combine them into one file per year, needs to be run as a slurm 
# job to run in parallel

start_year=2020
end_year=2059
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

#yearfile="/vast/projects/godeeep/VIC/forcing/conus_tgw_1_16_deg_rcp45cooler_2020_year_files/tgw_forcing_d01_00625vic_${year}.nc"
#yearfile="/vast/projects/godeeep/VIC/forcing/conus_tgw_1_16_deg_rcp45hotter_2020_year_files/tgw_forcing_d01_00625vic_${year}.nc"
#yearfile="/vast/projects/godeeep/VIC/forcing/conus_tgw_1_16_deg_rcp85cooler_2020_year_files/tgw_forcing_d01_00625vic_${year}.nc"
yearfile="/vast/projects/godeeep/VIC/forcing/conus_tgw_1_16_deg_rcp85hotter_2020_year_files/tgw_forcing_d01_00625vic_${year}.nc"

if [ ! -f "$yearfile" ]; then
  echo "Processing year $year: $yearfile"
  #cdo -w cat "/vast/projects/godeeep/VIC/forcing/conus_tgw_1_16_deg_rcp45cooler_2020/tgw_wrf_rcp45cooler_hourly_${year}*.nc" "$yearfile"
  #cdo -w cat "/vast/projects/godeeep/VIC/forcing/conus_tgw_1_16_deg_rcp45hotter_2020/tgw_wrf_rcp45hotter_hourly_${year}*.nc" "$yearfile"
  #cdo -w cat "/vast/projects/godeeep/VIC/forcing/conus_tgw_1_16_deg_rcp85cooler_2020/tgw_wrf_rcp85cooler_hourly_${year}*.nc" "$yearfile"
  cdo -w cat "/vast/projects/godeeep/VIC/forcing/conus_tgw_1_16_deg_rcp85hotter_2020/tgw_wrf_rcp85hotter_hourly_${year}*.nc" "$yearfile"
  echo "Year $year processing complete"
else
  echo "Year $year: $yearfile already exists. Skipping."
fi

echo "Worker $SLURM_PROCID has completed processing."
