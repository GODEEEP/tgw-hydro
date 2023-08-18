import xarray as xr
from pyogrio import read_dataframe
from tqdm import tqdm
import os
import sys

def subset_file(fn, output_dir):

  huc8_shp = read_dataframe("../data/HUC8_CONUS/HUC8_US.shp")

  for j, huc8 in tqdm(huc8_shp.iterrows()):

    huc8_code = huc8.HUC8

    huc8_dir = f'{output_dir}/{huc8_code}'
    if not os.path.exists(huc8_dir):
      os.mkdir(huc8_dir)

if __name__ == "__main__":
  output_dir = 'tgw-huc8-forcings-year'
  subset_file(sys.argv[1], output_dir)
