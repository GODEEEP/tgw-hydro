from shapely.geometry import shape, Point
import xarray as xr
import numpy as np
from pyogrio import read_dataframe
from tqdm import tqdm
import sys
import os

'''
Author: Cameron Bracken 10-19-2023

Create runoff files specific for one grid point, and organize the files by HUC2
'''


f = open("grid_ids_conus.csv", "a")
f.write(f"huc2,id,lon,lat\n")

output_dir = '.'
input_dir = '/Volumes/data/tgw-hydro/GRFR_runoff/conus'

runoff = xr.load_dataset(f'{input_dir}/runoff_conus_16th_deg_1980.nc')

huc2_shp = read_dataframe("../data/HUC2/HUC2.shp").sort_values('huc2')

count = 0
for h, huc2 in tqdm(huc2_shp.iterrows(), total=len(huc2_shp.geometry), desc=" huc2", position=0):

  huc2_code = huc2.huc2

  # print('Working on HUC', huc2_code, h, y)

  geometry = huc2.geometry
  bounds = geometry.bounds

  # carve out a box around the HUC2 for speed
  subdomain = runoff.sel(lat=slice(bounds[1], bounds[3]), lon=slice(bounds[0], bounds[2]))

  for lon in tqdm(subdomain.lon, desc=" lon", position=1, leave=False):
    for lat in tqdm(subdomain.lat, desc=" lat", position=2, leave=False):

      if not geometry.contains(Point(lon, lat)):
        continue
      else:
        count += 1
        f.write(f"{huc2_code},{count},{lon.to_dict()['data']},{lat.to_dict()['data']}\n")

f.close()
