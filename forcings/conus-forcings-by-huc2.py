from shapely.geometry import shape, Point
import xarray as xr
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

  start_time = time.time()
  forcing = xr.load_dataset(f'{input_dir}/tgw_forcing_d01_00625vic_{y}.nc')
  runtime = round((time.time() - start_time)/60, 2)
  print(f"Loading the dataset took {runtime} minutes")

  huc2_shp = read_dataframe("../data/HUC2/HUC2.shp")

  os.makedirs(output_dir, exist_ok=True)
  for huc2_code in range(1, 18+1):
    os.makedirs(f'{output_dir}/{huc2_code:02}', exist_ok=True)

  for h, huc2 in huc2_shp.iterrows():

    huc2_code = huc2.huc2

    print('Working on HUC', huc2_code, h, y)

    geometry = huc2.geometry
    bounds = geometry.bounds

    subdomain = forcing.sel(lat=slice(bounds[1], bounds[3]), lon=slice(bounds[0], bounds[2]))

    for lon in subdomain.lon:
      for lat in subdomain.lat:

        if not geometry.contains(Point(lon, lat)):
          continue
        else:
          # sys.exit("Error message")
          point_forcing = subdomain.sel(lat=slice(lat, lat), lon=slice(lon, lon))

          # make a subdirectory for each grid point
          ll = f'{lon:0.5f}_{lat:0.5f}'
          point_subdir = f'{output_dir}/{huc2_code:02}/{ll}'
          os.makedirs(point_subdir, exist_ok=True)
          forcing_fn = f'{point_subdir}/forcing_{ll}_{y}.nc'

          # skip over existing files
          if not os.path.exists(forcing_fn):
            point_forcing.to_netcdf(forcing_fn)


if __name__ == "__main__":
  output_dir = '/rcfs/projects/godeeep/VIC/forcings/1_16_deg/CONUS_TGW_WRF_Historical_Grid_Year_Files/'
  process_year(sys.argv[1], output_dir)
