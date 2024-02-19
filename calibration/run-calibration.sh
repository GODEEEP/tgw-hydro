#!/usr/bin/env /bin/bash

# huc2=17
huc2=18

csv_in=../data/grid_ids_conus.csv
path_out=/vast/projects/godeeep/VIC/calibration/$huc2 

# huc2      n first_id
# <chr> <int>    <dbl>
# 01     5755        1
# 02     7491     5756
# 03    18192    13247
# 04    24748    31439
# 05    11200    56187
# 06     2694    67387
# 07    13883    70081
# 08     6829    83964
# 09     8074    90793
# 10    38644    98867
# 11    16464   137511
# 12    11476   153975
# 13    14443   165451
# 14     7833   179894
# 15    10623   187727
# 16     9878   198350
# 17    24923   208228
# 18    11390   233151

# total number of points to process
# x = pd.read_csv('data/grid_ids_conus.csv')
# x[x.huc2==key].shape[0]
# total_points=24923
total_points=11390 # 18
# start and end ids of huc2 17 - columbia 
# first_id=208228
first_id=233151 # 18
# last_id=233150

# total number of nodes used to run this job, defined in run-calibration.sl
total_nodes=$SLURM_JOB_NUM_NODES

start_id=$((SLURM_NODEID*total_points/total_nodes+first_id))
end_id=$((SLURM_NODEID*total_points/total_nodes+total_points/total_nodes-1+first_id))

if (( end_id >= total_points+first_id-1 )); then
  end_id=$((first_id+total_points-1))
fi

points=( $(seq $start_id $end_id) )

echo "NODE $SLURM_NODEID: points $start_id - $end_id"

export OMP_NUM_THREADS=1

/rcfs/projects/im3/gnuparallel/bin/parallel --jobs 63 "python run-calibration.py $csv_in $path_out " ::: "${points[@]}"
