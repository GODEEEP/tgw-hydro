import sys, os, glob
import numpy as np
import pandas as pd
import xarray as xr

xr.set_options(keep_attrs = True)

#scn = sys.argv[1]
#year_begin = int(sys.argv[2])
#year_end = int(sys.argv[3])
scn, year_begin, year_end = 'hist', 1992, 1992
#scn, year_begin, year_end = 'rcp85hotter', 2019, 2059

dict_map = {
#   destination key: source key
    'hist': 'historical',
    'rcp45cooler': 'rcp45cooler',
    'rcp45hotter': 'rcp45hotter',
    'rcp85cooler': 'rcp85cooler',
    'rcp85hotter': 'rcp85hotter',
}

path_files = '/scratch/sony061/foresight/forcings/hist/tgw_wrf_{scn_map}_6hourly_{year}-*_00625vic.nc'
path_out = '/scratch/sony061/foresight/forcings/hist/tgw_wrf_{scn}_{year}_00625vic.nc'

for year in range(year_begin, year_end + 1):
    print(f'Processing {year}...')
    fs = glob.glob(path_files.format(scn = scn, scn_map = dict_map[scn], year = year - 1)) + glob.glob(path_files.format(scn = scn, scn_map = dict_map[scn], year = year)) + glob.glob(path_files.format(scn = scn, scn_map = dict_map[scn], year = year + 1))
    fs.sort()

    with xr.open_mfdataset(fs, combine = 'by_coords', parallel = True) as ds:
        t = pd.date_range(pd.Timestamp(year = year, month = 1, day = 1), pd.Timestamp(year = year + 1, month = 1, day = 1), freq = '6h', inclusive = 'left')
        if t[0] in ds['time']: ds_iter = ds.sel(time = t)
        elif year == year_begin:
            print(f'Warning: No {t[0].strftime("%Y%m%dT%H:%M")} Exists - Duplicate {t[1].strftime("%Y%m%dT%H:%M")}!')
            ds_iter = ds.sel(time = [t[1]] + list(t[1:])).assign_coords(time = t) # duplicate if the first time step does not exist
        ds_iter['time'].encoding.update({'units': f'hours since {year}-01-01T00:00:00'})
        ds_iter.to_netcdf(path_out.format(scn = scn, year = year))