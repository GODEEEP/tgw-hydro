import os
# loading the xesmf package will throw an error if this path is not set
os.environ['ESMFMKFILE'] = '/people/sony061/.conda/envs/xesmf_env/lib/esmf.mk'
import xesmf as xe
import xarray as xr

runoff_data_dir = '/people/sony061/tmp/foresight/runoff'
subset_output_dir = '/people/sony061/tmp/foresight/runoff'
years = list(range(1995, 1995+1))

# domain including conus and most of canada
lon_slice = slice(-140, -55)
lat_slice = slice(20, 70)

na = xr.open_dataset('/people/sony061/tmp/foresight/domain/namerica_params.nc')
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
