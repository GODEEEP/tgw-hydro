from shapely.geometry import shape, Point
import xarray as xr
import numpy as np
from pyogrio import read_dataframe
from tqdm import tqdm
import sys
import os

'''Author: Cameron Bracken 10-18-2023

Create VIC input files specefic for one grid point, and organize the files by HUC2
'''

domain = xr.open_dataset('./namerica_domain.nc')
params = xr.open_dataset('/Volumes/data/tgw-hydro/params/namerica_params.nc')
huc2_shp = read_dataframe("../data/HUC2/HUC2.shp")

domain_dir = 'domains_conus_by_huc2'
param_dir = 'params_conus_by_huc2'

os.makedirs(domain_dir, exist_ok=True)
os.makedirs(param_dir, exist_ok=True)
for huc2_code in range(1, 18+1):
  os.makedirs(f'{domain_dir}/{huc2_code:02}', exist_ok=True)
  os.makedirs(f'{param_dir}/{huc2_code:02}', exist_ok=True)

for h, huc2 in tqdm(huc2_shp.iterrows(), total=len(huc2_shp.geometry), desc=" huc2", position=0):
  # huc8 = huc8_shp[huc8_shp.HUC8 == '10020001']
  huc2_code = huc2.huc2
  geometry = huc2.geometry
  bounds = geometry.bounds

  subdomain = domain.sel(lat=slice(bounds[1], bounds[3]), lon=slice(bounds[0], bounds[2]))
  subdomain_params = params.sel(lat=slice(bounds[1], bounds[3]), lon=slice(bounds[0], bounds[2]))

  for lon in tqdm(subdomain.lon, desc=" lon", position=1, leave=False):
    for lat in tqdm(subdomain.lat, desc=" lat", position=2, leave=False):

      # for i, huc8 in tqdm(huc8_shp.iterrows(), total=len(huc8_shp.geometry)):

      if not geometry.contains(Point(lon, lat)):
        continue
      else:
        # sys.exit("Error message")
        point_domain = subdomain.sel(lat=slice(lat, lat), lon=slice(lon, lon))
        point_params = subdomain_params.sel(lat=slice(lat, lat), lon=slice(lon, lon))
        # force the mask value to be 1, just in case, since we know we want to run this cell
        mask = point_domain.mask
        mask[0] = 1

        root_fract = point_params.root_fract

        for k in range(len(root_fract.veg_class)):
          # root fraction was throwing errors so renormalize
          root_fract[k, :] = root_fract[k, :]/sum(root_fract[k, :])

        point_domain['mask'] = mask
        point_params['mask'] = mask
        point_params['run_cell'] = mask
        point_params['root_fract'] = root_fract
        # ax = gpd.GeoSeries(geometry).plot()
        # subdomain.mask.plot(ax=ax)
        # gpd.GeoSeries(geometry).plot(ax=ax)

        ll_fn = f'{lon:0.5f}_{lat:0.5f}'
        point_domain.to_netcdf(f'{domain_dir}/{huc2_code:02}/domain_{ll_fn}.nc')
        point_params.to_netcdf(f'{param_dir}/{huc2_code:02}/params_{ll_fn}.nc')
