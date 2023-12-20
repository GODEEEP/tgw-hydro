#!/bin/bash
#SBATCH --partition=shared
#SBATCH --nodes=1
#SBATCH --cpus-per-task=1
#SBATCH --account=GODEEEP
#SBATCH --time=6:00:00
#SBATCH --array=0-19
#SBATCH --job-name=VIC_calib
#SBATCH --mail-type=ALL
#SBATCH --mail-user=youngjun.son@pnnl.gov

echo 'Loading modules'

module purge
module load intel/20.0.4 openmpi/4.1.0 netcdf/4.8.0
module load gcc/11.2.0
module load jq
module load python/miniconda3.9
source /share/apps/python/miniconda3.9/etc/profile.d/conda.sh
conda activate vic

echo 'Done loading modules'

ulimit -s unlimited

key=08LD000 # '08LD000', '08FB002', '08MA001', '05CA000'
json_in=grid_ids_ca_group.json
csv_in=grid_ids_ca_check.csv
path_out=outputs/$key

pts=$(jq .\"$key\" $json_in)
pts=${pts// /}  # remove space
pts=${pts//,/}  # remove ,
pts=${pts//\"/} # remove "
pts=${pts##[}   # remove [
pts=${pts%]}    # remove ]
pts=($pts)      # declare array

n_pts=${#pts[@]} 
#pts_per_worker=$(expr 1 + $n_pts / $SLURM_ARRAY_TASK_COUNT)
#first=$(expr $SLURM_ARRAY_TASK_ID \* $pts_per_worker)
pts_per_worker=$(expr $n_pts / $SLURM_ARRAY_TASK_COUNT)
pts_remain=$(expr $n_pts \% $SLURM_ARRAY_TASK_COUNT)
add_first=$((SLURM_ARRAY_TASK_ID < pts_remain ? SLURM_ARRAY_TASK_ID: pts_remain))
add_last=$((SLURM_ARRAY_TASK_ID < pts_remain ? 1: 0))
first=$(expr $SLURM_ARRAY_TASK_ID \* $pts_per_worker + $add_first)
last=$(expr $first + $pts_per_worker - 1 + $add_last)
last=$((last >= n_pts ? n_pts - 1: last))

for i in $(seq $first $last)
do
  echo '############################################################'
  echo Beginning PROC $SLURM_ARRAY_TASK_ID [$first-$last]: ${pts[$i]} [$i]

  python run-calibration.py $csv_in ${pts[$i]} $path_out
  
  echo Completed PROC $SLURM_ARRAY_TASK_ID [$first-$last]: ${pts[$i]} [$i]
  echo '############################################################'
done

echo 'Really Done'
