from glob import glob
import xarray as xr

forcing_files = glob('input_files/forcings_16thdeg*')
forcing_files.sort()

for file in forcing_files:

  print(file)

  forcing_hourly = xr.load_dataset(file, chunks=-1)
  # forcing_hourly.chunks()

  for v in forcing_hourly.data_vars:
    if 'time' in forcing_hourly[v].dims:
      forcing_hourly[v].encoding['chunksizes'] = (len(forcing_hourly['time']), 1, 1)

  forcing_hourly.to_netcdf('input_files/forcing_hourly_'+file.split('_')[-1])

  tosum = forcing_hourly.PRECIP
  tosum_daily = tosum.resample(time='6H',).sum()

  tomean = forcing_hourly[['T2', 'PSFC', 'SWDOWN', 'GLW', 'VP', 'WSPEED']]
  tomean_daily = tomean.resample(time='6H').mean()

  tomean_daily['PRECIP'] = tosum_daily

  for v in tomean_daily.data_vars:
    if 'time' in tomean_daily[v].dims:
      tomean_daily[v].encoding['chunksizes'] = (len(tomean_daily['time']), 1, 1)

  tomean_daily.to_netcdf('input_files/forcing_daily_'+file.split('_')[-1])
