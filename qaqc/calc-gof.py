from numpy import mean, sum, corrcoef, std, sqrt, log1p
import numpy as np
import xarray as xr
import pandas as pd
from tqdm import tqdm
import os

"""
Compute goodness of fit (gof) metrics for calibrated VIC runs 

March 2024 
Cameron Bracken, cameron.bracken@pnnl.gov
"""

huc2 = '16'
begin_date_calib = pd.Timestamp('1981-01-01')
end_date_calib = pd.Timestamp('2000-12-31')

begin_date_valid = pd.Timestamp('2001-01-01')
end_date_valid = pd.Timestamp('2019-12-31')

# output monthly file names
obs_monthly_fn = f'/vast/projects/godeeep/VIC/mosart/grfr_huc{huc2:02}_8th_runoff_1980_2019_monthly.nc'
vic_monthly_fn = f'/vast/projects/godeeep/VIC/mosart/vic_huc{huc2:02}_8th_runoff_1979_2019_monthly.nc'


def nse(obs, pred):
  val = (1-(sum((obs-pred)**2)/sum((obs-mean(obs))**2)))
  # try:
  #   val = (1-(sum((obs-pred)**2)/sum((obs-mean(obs))**2)))
  # except KeyboardInterrupt:
  #   sys.exit()
  # except:
  #   val = 999
  return val


def kge(obs, pred):
  r = corrcoef(pred, obs)[0, 1]
  alpha = std(pred) / std(obs)
  beta = mean(pred) / mean(obs)
  gamma = alpha / beta
  return 1 - sqrt((r - 1) ** 2 + (beta - 1) ** 2 + (gamma - 1) ** 2)


print('Loading observed data')
# if not os.path.exists(obs_monthly_fn):
# load daily data 16the degree
runoff_obs_daily = xr.open_mfdataset('/rcfs/projects/godeeep/VIC/runoff/conus/*.nc')
runoff_obs_daily.load()
# convert to monthly
runoff_obs = runoff_obs_daily.resample(time='M').mean()
# clean up to save memory
del runoff_obs_daily
runoff_obs.to_netcdf(obs_monthly_fn)
# else:
#  runoff_obs = xr.load_dataset(obs_monthly_fn)

print('Loading VIC data')
# if not os.path.exists(vic_monthly_fn):
# load daily data 16the degree
runoff_vic_daily = xr.load_dataset(
    f'/vast/projects/godeeep/VIC/mosart/temp_VIC_runoff_gridded_16th_kge_huc{huc2:02}.nc')
# convert to monthly
runoff_vic = runoff_vic_daily.resample(time='M').mean()
del runoff_vic_daily
# clean up to save memory
runoff_vic.to_netcdf(vic_monthly_fn)
# else:
#  runoff_vic = xr.load_dataset(vic_monthly_fn)

print('Computing GoF metrics')
lons_vic = runoff_vic.lon
lats_vic = runoff_vic.lat
lons_obs = runoff_obs.lon
lats_obs = runoff_obs.lat

gof = (xr.full_like(runoff_vic.isel(time=0)
                    .rename({'OUT_RUNOFF': 'kge_calib', 'OUT_BASEFLOW': 'kge_valid'})
                    .drop(['time', 'OUT_EVAP', 'OUT_SWE']), np.nan))


for loni in tqdm(range(len(lons_vic))):
  for lati in range(len(lats_vic)):

    lon = float(lons_vic[loni])
    lat = float(lats_vic[lati])

    # if lon == -120.71875 and lat == 48.65625:
    #   break

    # print(runoff_vic.sel(lon=runoff_vic.lon==lon, lat = runoff_vic.lat==lat))
    runoff_vic_cell = runoff_vic['OUT_RUNOFF'].isel(lon=loni, lat=lati).squeeze() + \
        runoff_vic['OUT_BASEFLOW'].isel(lon=loni, lat=lati).squeeze()
    runoff_obs_cell = runoff_obs.sel(lon=slice(lon, lon), lat=slice(lat, lat))['ro'].squeeze()

    # calibration period
    runoff_vic_calib = runoff_vic_cell.where(
        runoff_vic_cell['time'] >= begin_date_calib, drop=True).where(
        runoff_vic_cell['time'] < end_date_calib, drop=True)
    runoff_obs_calib = runoff_obs_cell.where(
        runoff_obs_cell['time'] >= begin_date_calib, drop=True).where(
        runoff_obs_cell['time'] < end_date_calib, drop=True)

    # validation period
    runoff_vic_valid = runoff_vic_cell.where(
        runoff_vic_cell['time'] >= begin_date_valid, drop=True).where(
        runoff_vic_cell['time'] < end_date_valid, drop=True)
    runoff_obs_valid = runoff_obs_cell.where(
        runoff_obs_cell['time'] >= begin_date_valid, drop=True).where(
        runoff_obs_cell['time'] < end_date_valid, drop=True)

    # cant set single values with sel or isel, neeed to use .loc like so
    gof['kge_calib'].loc[dict(lat=lat, lon=lon)] = kge(runoff_vic_calib.to_numpy(), runoff_obs_calib.to_numpy())
    gof['kge_valid'].loc[dict(lat=lat, lon=lon)] = kge(runoff_vic_valid.to_numpy(), runoff_obs_valid.to_numpy())

gof.to_netcdf(f'gof_huc{huc2:02}.nc')
