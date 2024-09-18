#!/bin/bash
huc2=$(seq 1 18)

for h in ${huc2[@]}
do
    echo /vast/projects/godeeep/VIC/future_projections/mosart/rcp45cooler/$(printf "%02d" $h)
    ls /vast/projects/godeeep/VIC/future_projections/mosart/rcp45cooler/$(printf "%02d" $h)/ | wc -l
    ls -la /vast/projects/godeeep/VIC/future_projections/mosart/rcp45cooler/$(printf "%02d" $h)/mosart_rcp45cooler_huc$(printf "%02d" $h)_8th_runoff_2038_12.nc
    ls -la /vast/projects/godeeep/VIC/future_projections/mosart/rcp45cooler/$(printf "%02d" $h)/mosart_rcp45cooler_huc$(printf "%02d" $h)_8th_runoff_2059_12.nc
    ls -la /vast/projects/godeeep/VIC/future_projections/mosart/rcp45cooler/$(printf "%02d" $h)/mosart_rcp45cooler_huc$(printf "%02d" $h)_8th_runoff_2079_12.nc
    ls -la /vast/projects/godeeep/VIC/future_projections/mosart/rcp45cooler/$(printf "%02d" $h)/mosart_rcp45cooler_huc$(printf "%02d" $h)_8th_runoff_2099_12.nc

    echo /vast/projects/godeeep/VIC/future_projections/mosart/rcp45hotter/$(printf "%02d" $h)
    ls /vast/projects/godeeep/VIC/future_projections/mosart/rcp45hotter/$(printf "%02d" $h)/ | wc -l
    ls -la /vast/projects/godeeep/VIC/future_projections/mosart/rcp45hotter/$(printf "%02d" $h)/mosart_rcp45hotter_huc$(printf "%02d" $h)_8th_runoff_2038_12.nc
    ls -la /vast/projects/godeeep/VIC/future_projections/mosart/rcp45hotter/$(printf "%02d" $h)/mosart_rcp45hotter_huc$(printf "%02d" $h)_8th_runoff_2059_12.nc
    ls -la /vast/projects/godeeep/VIC/future_projections/mosart/rcp45hotter/$(printf "%02d" $h)/mosart_rcp45hotter_huc$(printf "%02d" $h)_8th_runoff_2079_12.nc
    ls -la /vast/projects/godeeep/VIC/future_projections/mosart/rcp45hotter/$(printf "%02d" $h)/mosart_rcp45hotter_huc$(printf "%02d" $h)_8th_runoff_2099_12.nc

    echo /vast/projects/godeeep/VIC/future_projections/mosart/rcp85cooler/$(printf "%02d" $h)
    ls /vast/projects/godeeep/VIC/future_projections/mosart/rcp85cooler/$(printf "%02d" $h)/ | wc -l
    ls -la /vast/projects/godeeep/VIC/future_projections/mosart/rcp85cooler/$(printf "%02d" $h)/mosart_rcp85cooler_huc$(printf "%02d" $h)_8th_runoff_2038_12.nc
    ls -la /vast/projects/godeeep/VIC/future_projections/mosart/rcp85cooler/$(printf "%02d" $h)/mosart_rcp85cooler_huc$(printf "%02d" $h)_8th_runoff_2059_12.nc
    ls -la /vast/projects/godeeep/VIC/future_projections/mosart/rcp85cooler/$(printf "%02d" $h)/mosart_rcp85cooler_huc$(printf "%02d" $h)_8th_runoff_2079_12.nc
    ls -la /vast/projects/godeeep/VIC/future_projections/mosart/rcp85cooler/$(printf "%02d" $h)/mosart_rcp85cooler_huc$(printf "%02d" $h)_8th_runoff_2099_12.nc

    echo /vast/projects/godeeep/VIC/future_projections/mosart/rcp85hotter/$(printf "%02d" $h)
    ls /vast/projects/godeeep/VIC/future_projections/mosart/rcp85hotter/$(printf "%02d" $h)/ | wc -l
    ls -la /vast/projects/godeeep/VIC/future_projections/mosart/rcp85hotter/$(printf "%02d" $h)/mosart_rcp85hotter_huc$(printf "%02d" $h)_8th_runoff_2038_12.nc
    ls -la /vast/projects/godeeep/VIC/future_projections/mosart/rcp85hotter/$(printf "%02d" $h)/mosart_rcp85hotter_huc$(printf "%02d" $h)_8th_runoff_2059_12.nc
    ls -la /vast/projects/godeeep/VIC/future_projections/mosart/rcp85hotter/$(printf "%02d" $h)/mosart_rcp85hotter_huc$(printf "%02d" $h)_8th_runoff_2079_12.nc
    ls -la /vast/projects/godeeep/VIC/future_projections/mosart/rcp85hotter/$(printf "%02d" $h)/mosart_rcp85hotter_huc$(printf "%02d" $h)_8th_runoff_2099_12.nc
done

echo
echo
echo
echo find /vast/projects/godeeep/VIC/future_projections/mosart/runs/ -maxdepth 2 -type f -name *2099_12.nc -print
find /vast/projects/godeeep/VIC/future_projections/mosart/runs/ -maxdepth 2 -type f -name *2099_12.nc -print