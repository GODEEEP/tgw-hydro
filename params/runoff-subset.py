from shapely.geometry import shape, Point
import xarray as xr
import pandas as pd
import numpy as np
from pyogrio import read_dataframe
from tqdm import tqdm
import sys
import os
import time

'''
Author: Cameron Bracken 10-19-2023

Create runoff files specific for one grid point, and organize the files by HUC2
'''


def process_year(y, output_dir):

  print(f'Processing year {y}')
  start_time = time.time()

  input_dir = '/rcfs/projects/godeeep/VIC/runoff/conus/'
  runoff = xr.load_dataset(f'{input_dir}/runoff_conus_16th_deg_{y}.nc')
  # grid_ids = pd.read_csv('../data/grid_ids_conus_bad.csv')
  grid_ids = pd.read_csv('../data/grid_ids_conus_bad.csv')

  # for i, cell in tqdm(grid_ids.iterrows(), total=grid_ids.shape[0]):
  for count, cell in grid_ids.iterrows():

    huc2_code = int(cell.huc2)
    lat = cell.lat
    lon = cell.lon
    i = int(cell.id)
    # print(huc2_code, lat, lon)

    point_forcing = runoff.sel(lat=slice(lat, lat), lon=slice(lon, lon))

    # make a subdirectory for each grid point
    point_dir = f'{output_dir}/{huc2_code:02}/{i:07}_{lon:0.5f}_{lat:0.5f}'
    os.makedirs(point_dir, exist_ok=True)
    runoff_fn = f'{point_dir}/runoff_16thdeg_{i:07}_{lon:0.5f}_{lat:0.5f}_{y}.nc'

    # skip over existing files
    if not os.path.exists(runoff_fn):
      point_forcing.to_netcdf(runoff_fn)

    # remove the concat file if it exists
    concat_fn = f'{point_dir}/runoff_concat_16thdeg_{i:07}_{lon:0.5f}_{lat:0.5f}_1979-2019.nc'
    if os.path.exists(concat_fn):
      os.unlink(concat_fn)

  runtime = round((time.time() - start_time)/60, 2)
  print(f"Processing completed in {runtime} minutes for file {input_dir}/runoff_conus_16th_deg_{y}.nc")


if __name__ == "__main__":
  output_dir = '/vast/projects/godeeep/VIC/inputs_1_16_deg_by_huc2/'
  process_year(sys.argv[1], output_dir)
  # years = range(1979, 2019+1)
  # for year in years:
  # process_year(year, output_dir)
