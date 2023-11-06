import xarray as xr
import pandas as pd
from tqdm import tqdm
import sys
import os
import time

'''
Author: Cameron Bracken 10-27-2023

Create VIC domain and param files for each grid point, and organize the files by HUC2
'''


def process(output_dir):

  print(f'Processing domain and params')
  start_time = time.time()

  domain = xr.load_dataset('/rcfs/projects/godeeep/VIC/params/namerica_domain.nc')
  params = xr.load_dataset('/rcfs/projects/godeeep/VIC/params/namerica_params.nc')
  grid_ids = pd.read_csv('../data/grid_ids_conus.csv')
  runtime = round((time.time() - start_time)/60, 2)
  print(f"Loading the datasets took {runtime} minutes")

  # for i, cell in tqdm(grid_ids.iterrows(), total=grid_ids.shape[0]):
  for n, cell in tqdm(grid_ids.iterrows(), total=grid_ids.shape[0]):

    i = int(cell.id)
    huc2_code = int(cell.huc2)
    lat = cell.lat
    lon = cell.lon

    point_domain = domain.sel(lat=slice(lat, lat), lon=slice(lon, lon))
    point_params = params.sel(lat=slice(lat, lat), lon=slice(lon, lon))

    mask = point_domain.mask
    # make sure the mask is set properly
    # mask[0] = 1

    root_fract = point_params.root_fract

    for k in range(len(root_fract.veg_class)):
      # root fraction was throwing errors so renormalize
      root_fract[k, :] = root_fract[k, :]/sum(root_fract[k, :])

    # point_domain['mask'] = mask
    point_params['mask'] = mask
    point_params['run_cell'] = mask
    point_params['root_fract'] = root_fract

    # make a subdirectory for each grid point
    point_dir = f'{output_dir}/{huc2_code:02}/{i:07}_{lon:0.5f}_{lat:0.5f}'
    os.makedirs(point_dir, exist_ok=True)
    domain_fn = f'{point_dir}/domain_{i:07}_{lon:0.5f}_{lat:0.5f}.nc'
    params_fn = f'{point_dir}/params_{i:07}_{lon:0.5f}_{lat:0.5f}.nc'

    # skip over existing files
    # if not os.path.exists(domain_fn):
    point_domain.to_netcdf(domain_fn)

    # if not os.path.exists(params_fn):
    point_params.to_netcdf(params_fn)

  runtime = round((time.time() - start_time)/60/60, 2)
  print(f"Processing completed in {runtime} hours")


if __name__ == "__main__":
  output_dir = '/rcfs/projects/godeeep/VIC/inputs_1_16_deg_by_huc2/'
  process(output_dir)
