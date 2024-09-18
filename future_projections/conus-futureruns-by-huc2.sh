#!/usr/bin/env /bin/bash

huc2=17

csv_in=../data/grid_ids_conus.csv
#scenario=rcp45cooler
#scenario=rcp45hotter
#scenario=rcp85cooler
scenario=rcp85hotter
path_out=/vast/projects/godeeep/VIC/future_projections/$scenario/$(printf "%02d" $huc2)

# huc2      n first_id last_id
# 01     5755        1    5755
# 02     7491     5756   13246
# 03    18192    13247   31438
# 04    24748    31439   56186
# 05    11200    56187   67386
# 06     2694    67387   70080
# 07    13883    70081   83963
# 08     6829    83964   90792
# 09     8074    90793   98866
# 10    38644    98867  137510
# 11    16464   137511  153974
# 12    11476   153975  165450
# 13    14443   165451  179893
# 14     7833   179894  187726
# 15    10623   187727  198349
# 16     9878   198350  208227
# 17    24923   208228  233150
# 18    11390   233151  244540

index=$((huc2-1))
first_ids=(1 5756 13247 31439 56187 67387 70081 83964 90793 98867 137511 153975 165451 179894 187727 198350 208228 233151)
total_points_array=(5755 7491 18192 24748 11200 2694 13883 6829 8074 38644 16464 11476 14443 7833 10623 9878 24923 11390)

first_id=${first_ids[$index]}
total_points=${total_points_array[$index]}

# echo "Running calibration for HUC2: $huc2"
# echo "First ID: $first_id"
# echo "Total Points: $total_points"

# total number of nodes used to run this job, defined in conus-futureruns-by-huc2.sl
total_nodes=$SLURM_JOB_NUM_NODES

start_id=$((SLURM_NODEID*total_points/total_nodes+first_id))
end_id=$((SLURM_NODEID*total_points/total_nodes+total_points/total_nodes-1+first_id))

if (( end_id >= total_points+first_id-1 )); then
  end_id=$((first_id+total_points-1))
fi

points=( $(seq $start_id $end_id) )

echo "HUC2 $huc2 NODE $SLURM_NODEID: points $start_id - $end_id"

export OMP_NUM_THREADS=1

~/bin/parallel --jobs 63 "python conus-futureruns-by-huc2.py $csv_in $scenario $path_out " ::: "${points[@]}"
