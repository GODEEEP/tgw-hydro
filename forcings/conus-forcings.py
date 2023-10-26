import xarray as xr
import pandas as pd
from pyogrio import read_dataframe
from tqdm import tqdm
import os
import glob
import time
import sys

"""
Author Cameron Bracken 10-24-2023

Slice out a single grid cell from processed tgw forcings. 
"""


def subset_file(fn, huc2, output_dir):

  start_time = time.time()

  grid_ids = pd.read_csv('../data/grid_ids_conus.csv')
  forcings = xr.load_dataset(fn)
  week = os.path.basename(fn)[24:34]
  huc2_code = f'{int(huc2):02}'

  huc2_grid_ids = grid_ids[grid_ids.huc2 == float(huc2)]

  print(f"Processing file {os.path.basename(fn)} HUC{huc2_code}")

  for i, cell in tqdm(huc2_grid_ids.iterrows(), total=huc2_grid_ids.shape[0]):
    # for i, cell in huc2_grid_ids.iterrows():

    # huc2 = int(cell.huc2)
    lon = cell.lon
    lat = cell.lat

    point_dir = f'{output_dir}/{huc2_code}/{i:07}_{lon:0.5f}_{lat:0.5f}'
    os.makedirs(point_dir, exist_ok=True)

    vic_forcing_fn = f'{point_dir}/forcings_tgw_16thdeg_{i:07}_{lon:0.5f}_{lat:0.5f}_{week}.nc'

    # skip over existing files
    if not os.path.exists(vic_forcing_fn):

      # chop out the grid cell
      point = forcings.sel(lat=slice(lat, lat), lon=slice(lon, lon))
      try:
        point.to_netcdf(vic_forcing_fn)
      except KeyboardInterrupt:
        sys.exit()
      except:
        continue
        # print(f'Error writing {vic_forcing_fn}')

  runtime = round((time.time() - start_time)/60, 2)
  print(f"Processing completed in {runtime} minutes for file {os.path.basename(fn)}")


if __name__ == "__main__":
  output_dir = '/rcfs/projects/godeeep/VIC/forcings/1_16_deg/CONUS_TGW_WRF_Historical_Grid/'
  subset_file(sys.argv[1], sys.argv[2], output_dir)
