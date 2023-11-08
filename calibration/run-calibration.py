import pandas as pd
import xarray as xr
import os
import sys
import shutil


def run_calibration(point_id):

  grid_ids = pd.read_csv('../data/grid_ids_conus.csv')
  row = grid_ids[grid_ids.id == point_id]
  lon = row.lon.values[0]
  lat = row.lat.values[0]
  huc2_code = row.huc2.values[0]

  # set up scratch directory
  id_ll = f'{point_id:07}_{lon:0.5f}_{lat:0.5f}'
  point_subdir = f'{huc2_code:02}/{id_ll}'
  input_path = f'/rcfs/projects/godeeep/VIC/inputs_1_16_deg_by_huc2/{point_subdir}'
  scratch_path = f'/scratch/godeeep/{point_subdir}'
  os.makedirs(scratch_path, exist_ok=True)

  # copy model and calibration files
  shutil.copy('vic.in.tpl', scratch_path)
  shutil.copy('vic.in', scratch_path)
  shutil.copy('vic_image', scratch_path)
  shutil.copy('run_vic.py', scratch_path)
  # shutil.copy('config.txt', scratch_path)
  shutil.copy(f'{input_path}/params_{id_ll}.nc', f'{scratch_path}/params_updated.nc')
  shutil.copy(f'{input_path}/params_{id_ll}.nc', f'{scratch_path}/params.nc')
  shutil.copy('ostIn.txt', scratch_path)
  shutil.copy('ostrich', scratch_path)

  vic_config = f'''
  # ######################################################################
  # Simulation Parameters
  # ######################################################################
  MODEL_STEPS_PER_DAY   24  # number of model time steps in 24 hour period
  SNOW_STEPS_PER_DAY    24  # number of snow model time steps in 24 hour period
  RUNOFF_STEPS_PER_DAY  24  # number of runoff time steps in 24 hour period

  STARTYEAR             1980 # year model simulation starts
  STARTMONTH            1    # month model simulation starts
  STARTDAY              1    # day model simulation starts
  ENDYEAR               2009
  ENDMONTH              12
  ENDDAY                31
  CALENDAR              PROLEPTIC_GREGORIAN

  FULL_ENERGY           FALSE # calculate full energy balance
  FROZEN_SOIL           FALSE # calculate frozen soils

  # ######################################################################
  # DOMAIN INFO
  # ######################################################################
  DOMAIN {input_path}/domain_{id_ll}.nc
  DOMAIN_TYPE    LAT     lat
  DOMAIN_TYPE    LON     lon
  DOMAIN_TYPE    MASK    mask
  DOMAIN_TYPE    AREA    area
  DOMAIN_TYPE    FRAC    frac
  DOMAIN_TYPE    YDIM    lat
  DOMAIN_TYPE    XDIM    lon

  # ######################################################################
  # Forcing Files and Parameters
  # netcdf forcing files will be of the form: <FORCING1>YYYY.nc
  # ######################################################################
  FORCING1      {input_path}/forcings_16thdeg_{id_ll}_
  FORCE_TYPE    AIR_TEMP     T2      # Average air temperature, K
  FORCE_TYPE    PREC         PRECIP  # Total precipitation (rain and snow), kg/m2/s
  FORCE_TYPE    PRESSURE     PSFC    # Atmospheric pressure, Pa
  FORCE_TYPE    SWDOWN       SWDOWN  # Incoming shortwave, W/m2
  FORCE_TYPE    LWDOWN       GLW     # Incoming longwave radiation, W/m2
  FORCE_TYPE    VP           VP      # Vapor pressure, kPa
  FORCE_TYPE    WIND         WSPEED  # Wind speed, m/s

  # ######################################################################
  # Land Surface Files and Parameters
  # ######################################################################
  PARAMETERS          params_updated.nc
  SNOW_BAND           TRUE
  BASEFLOW            ARNO
  JULY_TAVG_SUPPLIED  FALSE
  VEGPARAM_LAI        TRUE    # TRUE = veg param file contains LAI information
  VEGPARAM_ALB        TRUE    # TRUE = veg param file contains albedo information
  VEGPARAM_FCAN       TRUE    # TRUE = veg param file contains veg_cover information
  LAI_SRC             FROM_VEGLIB    # FROM_VEGPARAM = read LAI from veg param file
  ALB_SRC             FROM_VEGLIB    # FROM_VEGLIB = read albedo from veg library file
  FCAN_SRC            FROM_VEGLIB    # FROM_VEGPARAM = read fcanopy from veg param file
  ORGANIC_FRACT       FALSE
  LAI_SRC             FROM_VEGPARAM
  NODES               3  # number of soil thermal nodes

  # ######################################################################
  # Output Files and Parameters
  # ######################################################################
  RESULT_DIR  .
  OUTFILE     vic_runoff
  AGGFREQ     NDAYS   1  # Write output every 1 day
  OUT_FORMAT  NETCDF4
  OUTVAR      OUT_RUNOFF
  
  '''

  # write the vic config file
  f = open(f'{scratch_path}/config.txt', 'w')
  f.write(vic_config)
  f.close()

  # this is a hack to pass the input data directory to the model
  # wrapper script avoids some duplicate code
  f = open(f'{scratch_path}/input_dir.txt', 'w')
  f.write(input_path)
  f.close()

  os.chdir(scratch_path)

  # run the calibration, takes a few hours
  os.system('./ostrich')

  # copy files for archiving
  os.system(f'cp Ost* {input_path}/')
  os.system(f'cp input_dir.txt {input_path}/')
  os.system(f'cp -r mod0 {input_path}/')


if __name__ == '__main__':
  point_id = int(sys.argv[1])
  run_calibration(point_id)
