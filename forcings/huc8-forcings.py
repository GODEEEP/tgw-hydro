import xarray as xr
from pyogrio import read_dataframe
from tqdm import tqdm
import os
import glob
import time
import sys

def subset_file(fn, output_dir):

  start_time = time.time()

  huc8_shp = read_dataframe("../data/HUC8_CONUS/HUC8_US.shp")
  forcings = xr.open_dataset(fn)
  week = os.path.basename(fn)[24:34]

  #print(week)
  
  #for i, huc8 in tqdm(huc8_shp.iterrows(), total=len(huc8_shp.geometry), desc=week):
  for j, huc8 in huc8_shp.iterrows():

    
    huc8_code = huc8.HUC8
    geometry = huc8.geometry
    bounds = geometry.bounds
    
    huc8_dir = f'{output_dir}/{huc8_code}'
    if not os.path.exists(huc8_dir):
      os.mkdir(huc8_dir)

    vic_forcing_fn = f'{huc8_dir}/forcings_{huc8_code}_{week}.nc'
    # skip over existing files 
    if not os.path.exists(vic_forcing_fn):

      # chop out the huc8 
      subdomain = forcings.sel(lat=slice(bounds[1], bounds[3]), lon=slice(bounds[0], bounds[2]))    
      subdomain.to_netcdf(vic_forcing_fn)

      #print(vic_forcing_fn)

  runtime = round((time.time() - start_time)/60, 2)
  print(f"Processing completed in {runtime} minutes for file {os.path.basename(fn)}")

if __name__ == "__main__":
  output_dir = 'tgw-huc8-forcings'
  subset_file(sys.argv[1], output_dir)
