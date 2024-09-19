#!/bin/bash
huc2=$(seq 1 18)

for h in ${huc2[@]}
do
    echo find /vast/projects/godeeep/VIC/calibration/$(printf "%02d" $h) -maxdepth 2 -type f -name params_updated.nc -print
    find /vast/projects/godeeep/VIC/calibration/$(printf "%02d" $h) -maxdepth 2 -type f -name params_updated.nc -print | wc -l

    echo find /vast/projects/godeeep/VIC/calibration/$(printf "%02d" $h) -maxdepth 2 -type f -name vic_runoff.1979-01-01.nc -print
    find /vast/projects/godeeep/VIC/calibration/$(printf "%02d" $h) -maxdepth 2 -type f -name vic_runoff.1979-01-01.nc -print | wc -l

    echo find /vast/projects/godeeep/VIC/future_projections/rcp45cooler/$(printf "%02d" $h) -type f -name vic_runoff.2018-01-01.nc -print
    find /vast/projects/godeeep/VIC/future_projections/rcp45cooler/$(printf "%02d" $h) -type f -name vic_runoff.2018-01-01.nc -print | wc -l

    echo find /vast/projects/godeeep/VIC/future_projections/rcp45hotter/$(printf "%02d" $h) -type f -name vic_runoff.2018-01-01.nc -print
    find /vast/projects/godeeep/VIC/future_projections/rcp45hotter/$(printf "%02d" $h) -type f -name vic_runoff.2018-01-01.nc -print | wc -l

    echo find /vast/projects/godeeep/VIC/future_projections/rcp85cooler/$(printf "%02d" $h) -type f -name vic_runoff.2018-01-01.nc -print
    find /vast/projects/godeeep/VIC/future_projections/rcp85cooler/$(printf "%02d" $h) -type f -name vic_runoff.2018-01-01.nc -print | wc -l

    echo find /vast/projects/godeeep/VIC/future_projections/rcp85hotter/$(printf "%02d" $h) -type f -name vic_runoff.2018-01-01.nc -print
    find /vast/projects/godeeep/VIC/future_projections/rcp85hotter/$(printf "%02d" $h) -type f -name vic_runoff.2018-01-01.nc -print | wc -l
done