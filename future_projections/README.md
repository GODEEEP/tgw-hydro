# future_projections 

This directory contains scripts for extending future climate scenarios (eight different projections), including those for processing the TGW (https://tgw-data.msdlive.org/) forcings and running the VIC and mosartwmpy models. The scripts have been modified from those used for a historical climate scenario. Please refer to individual code files for details.
- rcp45cooler(2020-2059)
- rcp45cooler(2060-2099)
- rcp45hotter(2020-2059)
- rcp45hotter(2060-2099)
- rcp85cooler(2020-2059)
- rcp85cooler(2060-2099)
- rcp85hotter(2020-2059)
- rcp85hotter(2060-2099)

## Steps to reproduce
### forcing (YYYY: starting year) 
1. Download the TGW data (https://tgw-data.msdlive.org/) for future climate projections. Warning: this data is very large and will require an HPC system to process.
2. Update the 'wrf_dir' and 'out_dir' variables within `proc_wrf_to_vicgrid_00625_parallel_YYYY.py` to set input/output paths for Step 3.
3. Run `proc_wrf_to_vicgrid_00625_parallel_YYYY.sl` in an HPC system to process the forcings to prepare the VIC inputs.
4. Update the 'yearfile' and cdo paths within `conus-forcings-combine-yearfiles_YYYY.sh` to set input/output paths for Step 5.
5. Run `conus-forcings-combine-yearfiles_YYYY.sl` in an HPC system to combine the forcings into one file per year. 
6. Update the 'input_dir' and 'output_dir' variables within `conus-forcings-by-huc2_6h_rcpXX.py` to set input/output paths Step 7.
7. Run `conus-forcings-by-huc2_6h_rcpXX.sl` in an HPC system to output the forcings for one grid cell at a time, split by HUC2 region.

### VIC
1. Update the 'scenario' and 'huc2' variables within `conus-futureruns-by-huc2.sh` to set scenario/HUC2 paths for the VIC simulations.
2. Run `conus-futureruns-by-huc2.sl` in an HPC system to run the VIC model for one grid cell at a time, split by HUC2 region.

### mosartwmpy
1. Run `mosart/create_scenario_configs.py` to create the configuration files by HUC2/scenario for the mosartwmpy simulations.
2. Update the 'scenario', 'path_output', and 'timespan' within `mosart/create-mosart-runoff.py` to set scenario/output paths for Step 3. The 'timespan' variable may need to be splitted depending on the memory capacities of HPC nodes.
3. Run `mosart/create-mosart-runoff.sl` to merge the VIC simulated runoff by HUC2 region.
4. Update 'scenario' and 'huc2_idx' in `mosart/run-mosartwmpy.py` to set scenario/HUC2 paths for the mosartwmpy simulations.
5. Run `mosart/run-mosartwmpy.sl` in an HPC system to run the mosartwmpy model using the provided config files in `mosart/config`.

## Corresponding author: 

Cameron Bracken, cameron.bracken@pnnl.gov