# params 

This directory contains scripts to process the VIC model grid and parameters from the VICGlobal dataset (https://zenodo.org/records/5038653). Please refer to each code file for more details. 

## Steps to reproduce
1. Download the GRFR and VICGlobal (north america) data. 
2. Run `runoff-subset-by-huc2.py` to generate runoff subsets for each HUC2 basin for calibration. 
3. Run `param-subset-by-huc2.py` to subset the VICGlobal parames for each VIC gridcell. 

## Corresponding author: 

Cameron Bracken, cameron.bracken@pnnl.gov