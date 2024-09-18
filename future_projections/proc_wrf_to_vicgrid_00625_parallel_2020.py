"""
Name: proc_wrf_to_vicgrid_00625.py
Author: Dan Broman, PNNL
Description: Processes WRF data to 1_16 deg. daily for use with VIC
Comments: grid defs (proj strings) are hard coded
variable names, units, and selections are hard coded
parallelized by Travis Thurber
see associated sh and sl scripts

modified by Cameron Bracken 9 Aug 2023 to process the full period 1979-2022
modified by Cameron Bracken 27 Oct 2023 to extend the grid to include as much of canada as possible
"""

import xarray as xr
import rioxarray
import salem
import math
import numpy as np
import time
import glob
import os
import sys

yearstart = 2020
yearend = 2059
filesubinit = '2020-01-01'


def method(i: int = 1):

  # set dir for source wrf data
  #wrf_dir = '/rcfs/projects/godeeep/shared_data/tgw_wrf/rcp45cooler_2020_2059/hourly/'
  #wrf_dir = '/rcfs/projects/godeeep/shared_data/tgw_wrf/rcp45hotter_2020_2059/hourly/'
  #wrf_dir = '/rcfs/projects/godeeep/shared_data/tgw_wrf/rcp85cooler_2020_2059/hourly/'
  wrf_dir = '/rcfs/projects/godeeep/shared_data/tgw_wrf/rcp85hotter_2020_2059/hourly/'

  # set dir for processed data
  # out_dir = '/qfs/projects/godeeep/VIC/forcings/1_16_deg/CONUS_TGW_WRF_Historical/'
  #out_dir = '/vast/projects/godeeep/VIC/forcing/conus_tgw_1_16_deg_rcp45cooler_2020/'
  #out_dir = '/vast/projects/godeeep/VIC/forcing/conus_tgw_1_16_deg_rcp45hotter_2020/'
  #out_dir = '/vast/projects/godeeep/VIC/forcing/conus_tgw_1_16_deg_rcp85cooler_2020/'
  out_dir = '/vast/projects/godeeep/VIC/forcing/conus_tgw_1_16_deg_rcp85hotter_2020/'

  # set label to append to output files
  file_label = '00625vic'

  """
  wrf data dir must have either data from the start of the WRF simulation period or
  an 'init' file prior to the desired time window to back out incremental
  precipitation from total accumulated precipitation
  """
  # set init file flag [0: false, 1: true]
  init_file_flag = 1 if i == 0 else 0

  """
  flag indicates whether first netCDF file in dir is from the start of the WRF
  simulation period [0: false] or an 'init' file [1: true] to back out
  incremental precipitation. If false, data are written out for first file
  """

  # build file list
  # file_list = glob.glob("{0}/*{1}*.nc".format(wrf_dir, year_sel))
  # file_list.sort()
  # nfile = len(file_list)

  # build file list (subset of files)
  file_list = glob.glob("{0}/*{1}*.nc".format(wrf_dir, filesubinit))
  # print('file list: ', file_list)
  for yr in range(yearstart, yearend+1):
    file_list_tmp = glob.glob("{0}/*{1}*.nc".format(wrf_dir, yr))
    file_list = file_list + file_list_tmp

  file_list.sort()
  # print('file list: ', file_list)
  nfile = len(file_list)

  # construct the 1/16 degree grid
  lat = np.arange(24.03125, 56.03125, 0.0625)
  lon = np.arange(-129.96875, -65.09375, 0.0625)

  # subset forcings
  subset_flag = False
  subset_dir = 'pnw/'
  # bounding box (only needed if subset_flag == True)
  min_lat = 41.09375
  max_lat = 52.84375
  min_lon = -124.90625
  max_lon = -109.84375

  wrf_file = file_list[i]

  # read in 'init' file
  if init_file_flag == 1 and i == 0:
    return

  # read in prior file for precipitation if past first file
  if i > 0:
    wrf_file_prior = file_list[i-1]

    # open dataset
    wrf_data_initprecip = salem.open_wrf_dataset(wrf_file_prior)[['RAINC', 'RAINSH', 'RAINNC']].drop(['lat', 'lon'])

    # set coordinate system
    wrf_data_initprecip.rio.write_crs(
        '+proj=lcc +lat_0=40.0000076293945 +lon_0=-97 +lat_1=30 +lat_2=45 +x_0=0 +y_0=0 +R=6370000 +units=m +no_defs', inplace=True
    ).rio.set_spatial_dims(
        x_dim='west_east',
        y_dim='south_north',
        inplace=True,
    ).rio.write_coordinate_system(inplace=True)

  # read in file to process
  if (init_file_flag == 0 and i == 0) or (i > 0):

    start_time = time.time()

    # open dataset
    wrf_data = salem.open_wrf_dataset(
        wrf_file)[['Q2', 'T2', 'PSFC', 'U10', 'V10', 'RAINC', 'RAINSH', 'RAINNC', 'SWDOWN', 'GLW']].drop(['lat', 'lon'])

    # set coordinate system
    wrf_data.rio.write_crs(
        '+proj=lcc +lat_0=40.0000076293945 +lon_0=-97 +lat_1=30 +lat_2=45 +x_0=0 +y_0=0 +R=6370000 +units=m +no_defs', inplace=True
    ).rio.set_spatial_dims(
        x_dim='west_east',
        y_dim='south_north',
        inplace=True,
    ).rio.write_coordinate_system(inplace=True)

    # create placeholder vars to hold computed incremental precipitation
    wrf_data = wrf_data.assign(RAINC_INC=wrf_data['RAINC'] * 0)
    wrf_data.RAINC_INC.attrs['units'] = 'mm'
    wrf_data.RAINC_INC.attrs['description'] = 'INCREMENTAL TOTAL CUMULUS PRECIPITATION'
    wrf_data = wrf_data.assign(RAINSH_INC=wrf_data['RAINSH'] * 0)
    wrf_data.RAINSH_INC.attrs['units'] = 'mm'
    wrf_data.RAINSH_INC.attrs['description'] = 'INCREMENTAL SHALLOW CUMULUS PRECIPITATION'
    wrf_data = wrf_data.assign(RAINNC_INC=wrf_data['RAINNC'] * 0)
    wrf_data.RAINNC_INC.attrs['units'] = 'mm'
    wrf_data.RAINNC_INC.attrs['description'] = 'INCREMENTAL TOTAL GRID SCALE PRECIPITATION'

    # loop through time slices and compute incremental precipitation
    ntime = wrf_data.sizes['time']
    for ts in range(0, ntime-1):
      # special case if processing first file from WRF simulation (first time step)
      if ts == 0 and i == 0:
        wrf_data.RAINC_INC[ts, :, :] = wrf_data.RAINC.isel(time=ts)
        wrf_data.RAINSH_INC[ts, :, :] = wrf_data.RAINSH.isel(time=ts)
        wrf_data.RAINNC_INC[ts, :, :] = wrf_data.RAINNC.isel(time=ts)
      # if processing any file except for the first and on the first time step
      elif ts == 0 and i > 1:
        wrf_data.RAINC_INC[ts, :, :] = wrf_data.RAINC.isel(time=ts) - wrf_data_initprecip.RAINC.isel(time=-1)
        wrf_data.RAINSH_INC[ts, :, :] = wrf_data.RAINSH.isel(time=ts) - wrf_data_initprecip.RAINSH.isel(time=-1)
        wrf_data.RAINNC_INC[ts, :, :] = wrf_data.RAINNC.isel(time=ts) - wrf_data_initprecip.RAINNC.isel(time=-1)
      # if processing any time step except for the first
      elif ts > 0:
        wrf_data.RAINC_INC[ts, :, :] = wrf_data.RAINC.isel(time=ts) - wrf_data.RAINC.isel(time=ts-1)
        wrf_data.RAINSH_INC[ts, :, :] = wrf_data.RAINSH.isel(time=ts) - wrf_data.RAINSH.isel(time=ts-1)
        wrf_data.RAINNC_INC[ts, :, :] = wrf_data.RAINNC.isel(time=ts) - wrf_data.RAINNC.isel(time=ts-1)

    # create a template dataset with 1/8 degree grid
    wrf_data_wgs84 = xr.Dataset(coords={'time': wrf_data.time.values, 'y': lat, 'x': lon, })
    wrf_data_wgs84.rio.write_crs(
        'EPSG:4326', inplace=True
    ).rio.set_spatial_dims(
        x_dim='x',
        y_dim='y',
        inplace=True,
    ).rio.write_coordinate_system(inplace=True)

    # reproject each var
    for var in list(wrf_data.data_vars):
      wrf_data_wgs84[var] = wrf_data[var].rio.reproject_match(wrf_data_wgs84, resampling=1, nodata=np.NaN)

    # close datasets
    wrf_data_initprecip.close()
    wrf_data.close()

    # compute vars

    # compute total precipitation
    wrf_data_wgs84 = wrf_data_wgs84.assign(
        PRECIP=wrf_data_wgs84['RAINC_INC'] + wrf_data_wgs84['RAINSH_INC'] + wrf_data_wgs84['RAINNC_INC'])
    wrf_data_wgs84.PRECIP.attrs['units'] = 'mm/step'
    wrf_data_wgs84.PRECIP.attrs['description'] = 'TOTAL PRECIPITATION'

    # compute wind speed from component winds
    wrf_data_wgs84 = wrf_data_wgs84.assign(WSPEED=np.sqrt(wrf_data_wgs84['U10']**2 + wrf_data_wgs84['V10']**2))
    wrf_data_wgs84.WSPEED.attrs['units'] = 'm s-1'
    wrf_data_wgs84.WSPEED.attrs['description'] = 'WIND SPEED at 10 M'

    # compute vapor pressure
    wrf_data_wgs84 = wrf_data_wgs84.assign(
        VP=(wrf_data_wgs84['Q2'] * wrf_data_wgs84['PSFC']) / (0.622 + wrf_data_wgs84['Q2']))
    wrf_data_wgs84.VP.attrs['units'] = 'Pa'
    wrf_data_wgs84.VP.attrs['description'] = 'VAPOR PRESSURE'

    # unit conversion

    # air temperature K to C
    wrf_data_wgs84['T2'] = wrf_data_wgs84['T2'] - 273.15
    wrf_data_wgs84.T2.attrs['units'] = 'C'

    # atmospheric pressure Pa to kPa
    wrf_data_wgs84['PSFC'] = wrf_data_wgs84['PSFC'] / 1000
    wrf_data_wgs84.PSFC.attrs['units'] = 'kPa'

    # vapor pressure Pa to kPa
    wrf_data_wgs84['VP'] = wrf_data_wgs84['VP'] / 1000
    wrf_data_wgs84.VP.attrs['units'] = 'kPa'
    wrf_data_wgs84_subset = wrf_data_wgs84.get(['PRECIP', 'T2', 'PSFC', 'SWDOWN', 'GLW', 'VP', 'WSPEED'])

    # rename dimensions
    wrf_data_out = wrf_data_wgs84_subset.rename({'x': 'lon', 'y': 'lat'})

    # write out data
    file_out = out_dir + os.path.splitext(os.path.basename(wrf_file))[0] + '_' + file_label + '.nc'
    wrf_data_out.to_netcdf(path=file_out)

    # subset
    if subset_flag:
      wrf_data_dom = wrf_data_out.sel(lon=slice(min_lon, max_lon), lat=slice(min_lat, max_lat))
      file_out = out_dir + subset_dir + os.path.splitext(os.path.basename(wrf_file))[0] + '_' + file_label + '.nc'
      wrf_data_dom.to_netcdf(path=file_out)
      wrf_data_dom.close()

    # close datasets
    wrf_data_wgs84.close()
    wrf_data_wgs84_subset.close()
    wrf_data_out.close()

    runtime = round(time.time() - start_time, 2)
    print("Processing completed in {0} minutes for file {1} {2}".format(runtime/60, i, os.path.basename(wrf_file)))


if __name__ == "__main__":
  method(int(sys.argv[1]))

