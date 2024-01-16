import xesmf as xe
import xarray as xr
import os
# loading the xesmf package will throw an error if this path is not set
# os.environ['ESMFMKFILE'] = '/Users/brac840/miniforge3/envs/vic/lib/esmf.mk'

runoff_data_dir = '/Volumes/data/tgw-hydro/GRFR_runoff/global'
subset_output_dir = '/Volumes/data/tgw-hydro/GRFR_runoff/conus'
years = list(range(2000, 2019+1))

# domain including conus and most of canada
lon_slice = slice(-140, -55)
lat_slice = slice(20, 70)

na = xr.open_dataset('/Volumes/data/tgw-hydro/params/namerica_params.nc')
na_subset = na.sel(lon=lon_slice, lat=lat_slice)

for year in years:
  print(year)

  ro = xr.open_dataset(f'{runoff_data_dir}/RUNOFF_{year}.nc')

  # domain includes conus and canada
  ro_subset = ro.sel(lon=lon_slice, lat=lat_slice)

  # regrid to 1/16th (0.0625) degree from 0.05 degree (1/20th)
  regridder = xe.Regridder(ro_subset, na_subset, 'conservative')
  ro_regrid = regridder(ro_subset, keep_attrs=True)

  ro_regrid.to_netcdf(f'{subset_output_dir}/runoff_conus_16th_deg_{year}.nc')
