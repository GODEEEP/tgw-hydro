import xarray as xr
from glob import glob
import os
import json
import numpy as np
import pandas as pd
import xarray as xr
from time import time
from datetime import timedelta

huc2 = 17
#scenario = 'rcp45cooler'
#scenario = 'rcp45hotter'
#scenario = 'rcp85cooler'
scenario = 'rcp85hotter'

start = time()

path = f'/vast/projects/godeeep/VIC/future_projections/mosart/{scenario}'
os.makedirs(path, exist_ok=True)
# set a path for outputs
#path_output = f'{path}/mosart_{scenario}_huc{huc2:02}_8th_runoff_2018_2038.nc'
#path_output = f'{path}/mosart_{scenario}_huc{huc2:02}_8th_runoff_2039_2059.nc'
#path_output = f'{path}/mosart_{scenario}_huc{huc2:02}_8th_runoff_2060_2079.nc'
path_output = f'{path}/mosart_{scenario}_huc{huc2:02}_8th_runoff_2080_2099.nc'
print(f'Outputting to file {path_output}')

xr.set_options(keep_attrs=True)

# set a time period to generate MOSART runoff inputs
#timespan = [pd.Timestamp('2018-01-01'), pd.Timestamp('2038-12-31')]
#timespan = [pd.Timestamp('2039-01-01'), pd.Timestamp('2059-12-31')]
#timespan = [pd.Timestamp('2060-01-01'), pd.Timestamp('2079-12-31')]
timespan = [pd.Timestamp('2080-01-01'), pd.Timestamp('2099-12-31')]
resolution_runoff = 1/16  # runoff resolution
resolution_MOSART = 1/8  # target resolution

# set a path for the MOSART domain
path_domain = 'mosart_conus_nldas_grid.nc'
ds_domain = xr.open_dataset(path_domain, decode_coords='all')

# set a path for runoff netcdf files
# read ./[path_vicout]/[list_groups]/**/mod0_calib/[runoff_filename]
vic_output_dir = f'/vast/projects/godeeep/VIC/future_projections/{scenario}/{huc2:02}/'
calb_dirs = glob(f'{vic_output_dir}/*')

print('Finding output files')
nc_fns = []
for calb_dir in calb_dirs:
  fn = glob(f'{calb_dir}/vic*.nc')
  # print(fn)
  if fn != []:
    nc_fns.append(fn[0])

# create lons and lats (runoff: 1/16th degree, MOSART: 1/8th degree)
west = ds_domain['lon'].min().values - resolution_MOSART / 2
east = ds_domain['lon'].max().values + resolution_MOSART / 2
south = ds_domain['lat'].min().values - resolution_MOSART / 2
north = ds_domain['lat'].max().values + resolution_MOSART / 2
lons_runoff = np.arange(west + resolution_runoff / 2, east + resolution_runoff / 2, resolution_runoff)
lats_runoff = np.arange(south + resolution_runoff / 2, north + resolution_runoff / 2, resolution_runoff)
lons_MOSART = ds_domain['lon'].sortby('lon').values
lats_MOSART = ds_domain['lat'].sortby('lat').values

# load the MOSART domain for area-weighted average of runoffs
da_area = ds_domain['area']
da_area_16th = da_area.interp(lon=lons_runoff, lat=lats_runoff) / 4

print('Loading data')

# load xarray datasets from simulated runoffs
#path_temp = f'{path}/temp_VIC_runoff_gridded_16th_kge_huc{huc2:02}.nc'
path_temp = path_output.replace('.nc', '.nctemp')
# saving temporary file may take a huge space depending on the number of grid cells
if not os.path.isfile(path_temp):
  ds_runoff = xr.open_mfdataset(nc_fns, chunks={'time': -1}, decode_coords='all', parallel=True)
  ds_runoff = (ds_runoff
               .where(ds_runoff['time'] >= timespan[0], drop=True)
               .where(ds_runoff['time'] <= timespan[1], drop=True)
               .load())
  ds_runoff = ds_runoff.reindex({'lat': lats_runoff, 'lon': lons_runoff})
  ds_runoff.to_netcdf(path_temp)
else:
  ds_runoff = xr.load_dataset(path_temp)

print("Loading took:", str(timedelta(seconds=np.round(time() - start))))

# for y in range(timespan[0].year, timespan[1].year+1):
#   print(f'\t{y}')
#   # load xarray datasets from simulated runoffs
#   path_temp = f'/vast/projects/godeeep/VIC/temp_VIC_runoff_gridded_16th_kge_huc{huc2}.nc'
#   # saving temporary file may take a huge space depending on the number of grid cells
#   if not os.path.isfile(path_temp):
#     for y in range(timespan[0].year, timespan[1].year):
#       ds_runoff = xr.open_mfdataset(nc_fns, chunks={'time': -1}, decode_coords='all', parallel=True)
#       ds_runoff = (ds_runoff
#                   .where(ds_runoff['time'] >= pd.Timestamp(f'{y}-01-01'), drop=True)
#                   .where(ds_runoff['time'] < pd.Timestamp(f'{y}-12-31'), drop=True)
#                   .load())
#       ds_runoff = ds_runoff.reindex({'lat': lats_runoff, 'lon': lons_runoff})
#       ds_runoff.to_netcdf(path_temp)
#   # else: ds_runoff = xr.load_dataset(path_temp)

print('Regridding data')

ds_runoff_coarsen = (ds_runoff.drop_vars('time_bnds') * da_area_16th).coarsen(lat=2, lon=2).sum() / da_area
# ds_runoff_coarsen.to_netcdf(path_output)

# for y in range(timespan[0].year, timespan[1].year+1):
#   print(f'\t{y}')
#   path_temp = f'/scratch/godeeep/temp_VIC_runoff_gridded_16th_kge_huc{huc2}_{y}.nc'
#   runoff_year = xr.load_dataset(path_temp)
#   # coarsen runoff datasets from 1/16th degree into 1/8th degree (area-weighted)
#   runoff_year_coarsen = (runoff_year.drop_vars('time_bnds') * da_area_16th).coarsen(lat=2, lon=2).sum() / da_area
#   runoff_year_coarsen.to_netcdf(f'/scratch/godeeep/temp_coursen_VIC_runoff_gridded_16th_kge_huc{huc2}_{y}.nc')

# ds_runoff_coarsen = xr.open_mfdataset(f'/scratch/godeeep/temp_coursen_VIC_runoff_gridded_16th_kge_huc{huc2}_*.nc',
#                                       chunks={'time': -1}, decode_coords='all', parallel=True)

# check if the upscaling (2 times) creates the desired lon and lat
print("check if the coarsen 'lon' is the same to the expected: {}".format(
    np.array_equal(ds_runoff_coarsen['lon'], lons_MOSART)))
print("check if the coarsen 'lat' is the same to the expected: {}".format(
    np.array_equal(ds_runoff_coarsen['lat'], lats_MOSART)))

# select only surface runoff and baseflow
drop_vars = list(ds_runoff_coarsen.data_vars)
for var in ['OUT_RUNOFF', 'OUT_BASEFLOW']:
  drop_vars.remove(var)
  ds_runoff_coarsen[var] = ds_runoff_coarsen[var] / (24 * 60 * 60)  # conversion from mm/day into mm/s
  ds_runoff_coarsen[var].attrs['units'] = 'mm/s'
ds_runoff_coarsen = ds_runoff_coarsen.drop_vars(drop_vars)

print('Writing data')
# rename the variable names and generate the MOSART runoff input
ds_runoff_coarsen = ds_runoff_coarsen.rename({'OUT_RUNOFF': 'QOVER', 'OUT_BASEFLOW': 'QDRAI'})
#ds_runoff_coarsen.to_netcdf(path_output)

huc2_output_dir = os.path.join(path, f'{huc2:02}')
os.makedirs(huc2_output_dir, exist_ok=True)

start_year = int(ds_runoff_coarsen['time.year'].min())
end_year = int(ds_runoff_coarsen['time.year'].max())

print('Outputting month files')
for year in range(start_year, end_year+1):
  for month in range(1, 12+1):
    print(year, month)
    ds_runoff_my = ds_runoff_coarsen.sel(
        time=(ds_runoff_coarsen['time.month'] == month) & (ds_runoff_coarsen['time.year'] == year))
    ds_runoff_my.to_netcdf(os.path.join(huc2_output_dir, f'mosart_{scenario}_huc{huc2:02}_8th_runoff_{year}_{month:02}.nc'))


print("Postprocessing took:", str(timedelta(seconds=np.round(time() - start))))
if os.path.isfile(path_temp): os.remove(path_temp)
print('Done.')
