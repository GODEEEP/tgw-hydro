import xarray as xr
import glob
import os

huc2 = 17
input_dir = 'input/runoff'
pp_dir = f'{input_dir}/{huc2}_pp'
os.makedirs(pp_dir, exist_ok=True)

nc_files = glob.glob(f'{input_dir}/{huc2}/*.nc')
nc_files.sort()

for nc_file in nc_files:
  ds = xr.load_dataset(nc_file)
