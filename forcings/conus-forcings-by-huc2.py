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

Create VIC forcing files specific for one grid point, and organize the files by HUC2
'''


def process_year(y, output_dir):

  input_dir = '/rcfs/projects/godeeep/VIC/forcings/1_16_deg/CONUS_TGW_WRF_Historical_Year_Files/'

  print(f'Processing year {y}')

  start_time = time.time()
  forcing = xr.load_dataset(f'{input_dir}/tgw_forcing_d01_00625vic_{y}.nc')
  runtime = round((time.time() - start_time)/60, 2)
  print(f"Loading the dataset took {runtime} minutes")

  grid_ids = pd.read_csv('../data/grid_ids_conus.csv')

  # for h, huc2 in tqdm(huc2_shp.iterrows(), total=len(huc2_shp.geometry), desc=" huc2", position=0):
  for i, cell in grid_ids.iterrows():

    huc2_code = int(cell.huc2)
    lat = cell.lat
    lon = cell.lon

    point_forcing = forcing.sel(lat=slice(lat, lat), lon=slice(lon, lon))

    # make a subdirectory for each grid point
    point_dir = f'{output_dir}/{huc2_code:02}/{i+1:07}_{lon:0.5f}_{lat:0.5f}'
    os.makedirs(point_dir, exist_ok=True)
    forcing_fn = f'{point_dir}/forcings_16thdeg_{i+1:07}_{lon:0.5f}_{lat:0.5f}_{y}.nc'

    # skip over existing files
    if not os.path.exists(forcing_fn):
      # the tgw grid doesn't match the full extent, some points are missing
      if point_forcing.lon.shape[0] == 0 or point_forcing.lat.shape[0] == 0:
        continue
        # print(f'Grid cell')
      else:
        try:
          point_forcing.to_netcdf(forcing_fn)
        except KeyboardInterrupt:
          sys.exit()
        except:
          continue


if __name__ == "__main__":
  # output_dir = '/rcfs/projects/godeeep/VIC/forcings/1_16_deg/CONUS_TGW_WRF_Historical_Grid_Year_Files/'
  output_dir = '/rcfs/projects/godeeep/VIC/inputs_1_16_deg_by_huc2/'
  process_year(sys.argv[1], output_dir)
