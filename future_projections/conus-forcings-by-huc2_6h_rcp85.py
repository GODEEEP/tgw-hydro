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
xr.set_options(keep_attrs = True)

def process_year(y, input_dir, output_dir):

  print(f'Processing year {y}')

  start_time = time.time()
  forcing = xr.load_dataset(f'{input_dir}/tgw_forcing_d01_00625vic_{y}.nc')

  # Y.Son: only 6-hourly time-step required
  forcing_6h = forcing.resample(time='6H').mean()
  forcing_6h['PRECIP'] = forcing['PRECIP'].resample(time='6H').sum(skipna = False)
  
  runtime = round((time.time() - start_time)/60, 2)
  print(f"Loading the dataset took {runtime} minutes")

  grid_ids = pd.read_csv('../data/grid_ids_conus.csv')

  # for h, huc2 in tqdm(huc2_shp.iterrows(), total=len(huc2_shp.geometry), desc=" huc2", position=0):
  #for n, cell in tqdm(grid_ids.iterrows()):
  for n, cell in grid_ids.iterrows():
    print(f'{n + 1}/{len(grid_ids)}')

    i = int(cell.id)
    huc2_code = int(cell.huc2)
    lat = cell.lat
    lon = cell.lon

    point_forcing = forcing_6h.sel(lat=slice(lat, lat), lon=slice(lon, lon))

    # Y.Son: added for rechunking to save storage
    # reference: https://github.com/Ouranosinc/xscen/pull/379/files/92ba3a57c2c6c2a80db2226769fdbc36b218c42e
    for var in list(point_forcing.data_vars.keys()):
      point_forcing[var].encoding.pop('original_shape', None)
      if len(point_forcing[var].shape) > 0:
        point_forcing[var].encoding['chunksizes'] = point_forcing[var].shape
    point_forcing.encoding = {'unlimited_dims': ['time']}

    # make a subdirectory for each grid point
    point_dir = f'{output_dir}/{huc2_code:02}/{i:07}_{lon:0.5f}_{lat:0.5f}'
    os.makedirs(point_dir, exist_ok=True)
    #forcing_fn = f'{point_dir}/forcings_16thdeg_{i:07}_{lon:0.5f}_{lat:0.5f}_{y}.nc'
    forcing_fn = f'{point_dir}/forcings_6h_16thdeg_{i:07}_{lon:0.5f}_{lat:0.5f}_{y}.nc' # Y.Son: only 6-hourly time-step required

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
  # output_dir = '/rcfs/projects/godeeep/VIC/inputs_1_16_deg_by_huc2/'
  #output_dir = '/vast/projects/godeeep/VIC/future_projections/conus_tgw_1_16_deg_rcp85cooler/'
  output_dir = '/vast/projects/godeeep/VIC/future_projections/conus_tgw_1_16_deg_rcp85hotter/'
  #input_dir = '/vast/projects/godeeep/VIC/forcing/conus_tgw_1_16_deg_rcp85cooler_year_files/'
  input_dir = '/vast/projects/godeeep/VIC/forcing/conus_tgw_1_16_deg_rcp85hotter_year_files/'
  process_year(sys.argv[1], input_dir, output_dir)

