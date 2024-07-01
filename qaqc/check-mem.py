import requests
import xarray as xr
import time
import humanize
import os
import psutil

start_time = time.time()
x = xr.load_dataset('/vast/projects/godeeep/conus_tgw_1_16_deg_historical_year_files/tgw_forcing_d01_00625vic_1980.nc')
runtime = round((time.time() - start_time)/60, 2)
print(f"Loading the dataset took {runtime} minutes")

print('Memory usage: ',humanize.naturalsize(psutil.Process(os.getpid()).memory_info().rss))

