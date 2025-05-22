#!/bin/bash
module purge
module load python/miniconda3.9
source /share/apps/python/miniconda3.9/etc/profile.d/conda.sh
eval "$(conda shell.bash hook)"
conda activate vic

for y in $(seq 1992 1992)
do
    echo $y
    python -u subset_vicgrid_00625_byHUC2.py $y
done
echo Completed!