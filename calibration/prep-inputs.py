from shapely.geometry import shape, Point
import xarray as xr
import numpy as np
from pyogrio import read_dataframe
import pandas as pd
from tqdm import tqdm
import sys
import os
import time

'''
Author: Cameron Bracken 10-19-2023

Create VIC input files specific for one grid point
'''

grid_ids = pd.read_csv('../data/grid_ids_conus.csv')


def prep_forcings(lon, lat, input_dir, output_dir):

  years = range(1979, 2022+1)
  years = range(1980, 1980+1)

  for year in years:

    print(f'Subsetting forcings for {year}')
    start_time = time.time()
    forcing = xr.open_dataset(f'{input_dir}/tgw_forcing_d01_00625vic_{year}.nc')
    runtime = round((time.time() - start_time)/60, 2)
    print(f"Loading the forcing dataset took {runtime} minutes")

    start_time = time.time()
    point_forcing = forcing.sel(lat=slice(lat, lat), lon=slice(lon, lon))
    point_forcing.to_netcdf(f'{output_dir}/forcing_{year}.nc')
    runtime = round((time.time() - start_time)/60, 2)
    print(f"Subsetting the forcing dataset took {runtime} minutes")


def prep_runoff(lon, lat, input_dir, output_dir):

  years = range(1979, 2022+1)

  for year in years:

    print(f'Subsetting runoff for {year}')
    start_time = time.time()
    runoff = xr.open_dataset(f'{input_dir}/runoff_conus_16th_deg_{year}.nc')
    runtime = round((time.time() - start_time)/60, 2)
    print(f"Loading the runoff dataset took {runtime} minutes")

    start_time = time.time()
    point_runoff = runoff.sel(lat=slice(lat, lat), lon=slice(lon, lon))
    point_runoff.to_netcdf(f'{output_dir}/runoff_{year}.nc')
    runtime = round((time.time() - start_time)/60, 2)
    print(f"Subsetting the runoff dataset took {runtime} minutes")


def prep_domain(lon, lat, input_dir, output_dir):

  print(f'Subsetting domain')
  start_time = time.time()
  domain = xr.open_dataset(f'{input_dir}/domain.nc')
  runtime = round((time.time() - start_time)/60, 2)
  print(f"Loading the domain dataset took {runtime} minutes")

  start_time = time.time()
  point_domain = domain.sel(lat=slice(lat, lat), lon=slice(lon, lon))
  point_domain.to_netcdf(f'{output_dir}/domain.nc')
  runtime = round((time.time() - start_time)/60, 2)
  print(f"Subsetting the domain dataset took {runtime} minutes")


def prep_params(lon, lat, input_dir, output_dir):

  print(f'Subsetting params')
  start_time = time.time()
  params = xr.open_dataset(f'{input_dir}/namerica_params.nc')
  runtime = round((time.time() - start_time)/60, 2)
  print(f"Loading the params dataset took {runtime} minutes")

  start_time = time.time()
  point_params = params.sel(lat=slice(lat, lat), lon=slice(lon, lon))
  root_fract = point_params.root_fract
  for k in range(len(root_fract.veg_class)):
    # root fraction was throwing errors so renormalize
    root_fract[k, :] = root_fract[k, :]/sum(root_fract[k, :])
  point_params.to_netcdf(f'{output_dir}/params.nc')
  runtime = round((time.time() - start_time)/60, 2)
  print(f"Subsetting the params dataset took {runtime} minutes")


if __name__ == "__main__":

  point_id = int(sys.argv[1])

  forcing_input_dir = '/rcfs/projects/godeeep/VIC/forcings/1_16_deg/CONUS_TGW_WRF_Historical_Year_Files/'
  runoff_input_dir = '/rcfs/projects/godeeep/VIC/runoff/conus/'
  domain_input_dir = '/rcfs/projects/godeeep/VIC/params/'
  params_input_dir = '/rcfs/projects/godeeep/VIC/params/'

  output_dir = './input_files'

  lon = grid_ids.iloc[point_id].lon
  lat = grid_ids.iloc[point_id].lat

  prep_forcings(lon, lat, forcing_input_dir, output_dir)
  prep_runoff(lon, lat, runoff_input_dir, output_dir)
  prep_domain(lon, lat, domain_input_dir, output_dir)
  prep_params(lon, lat, params_input_dir, output_dir)
