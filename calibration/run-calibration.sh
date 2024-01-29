#!/usr/bin/env /bin/bash

key=17
csv_in=../data/grid_ids_conus.csv
path_out=/rcfs/projects/godeeep/VIC/calibration/$key 

# total number of points to process
total_points=24923
# start and end ids of huc2 17 - columbia 
first_id=208228
# last_id=233150

# total number of nodes used to run this job, defined in q.sl
total_nodes=$SLURM_JOB_NUM_NODES

start_id=$((SLURM_NODEID*total_points/total_nodes+first_id))
end_id=$((SLURM_NODEID*total_points/total_nodes+total_points/total_nodes-1+first_id))

if (( end_id >= total_points+first_id-1 )); then
  end_id=$((first_id+total_points-1))
fi

points=( $(seq $start_id $end_id) )

echo "NODE $SLURM_NODEID: points $start_id - $end_id"

export OMP_NUM_THREADS=1

/rcfs/projects/im3/gnuparallel/bin/parallel --jobs 48 "python run-calibration.py $csv_in $path_out " ::: "${points[@]}"