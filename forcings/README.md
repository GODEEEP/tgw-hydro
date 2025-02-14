# forcings 

This directory contains scripts to process the TGW (https://tgw-data.msdlive.org/) forcings for the VIC model. Please refer to indivdual code files for details. 

## Steps to reproduce
1. Download the TGW data (https://tgw-data.msdlive.org/). Warning: this data is very large and will require an HPC system to process.
2. Run `make-point-dirs.py` to create directories for each grid cell. 
3. Run the `proc_wrf_to_vicgrid_00625_parallel.py` script to process the forcings to prepare the VIC inputs, slurm files are provided for an HPC system. 
4. Run `conus-forcings-combine-yearfiles.sl` in an HPC system to combine the forcings into one file per year. 
5. Run `conus-forcings-by-huc2.py` to output the forcings for one grid cell at a time, split by HUC2 region. 

## Corresponding author: 

Cameron Bracken, cameron.bracken@pnnl.gov