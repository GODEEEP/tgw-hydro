import pandas as pd
import xarray as xr
import os
import sys
import shutil
import glob
import subprocess
from time import time
from datetime import timedelta
import numpy as np
from run_vic import read_params, modify_params

# upper and lower limits of calibration parameters
plim_ctr = [
    [0.001, 0.8],  # infilt
    [1, 30],  # Dsmax: [1, 30], ['-20%', '20%']
    [0, 1],  # Ds
    [0.5, 1],  # Ws
    [0.1, 2],  # depth2
    [0.1, 2],  # depth3
    [8, 30],  # expt2: [8, 30], ['-20%', '20%']
    [8, 30],  # expt3: [8, 30], ['-20%', '20%']
]

vic_input_dir = '/rcfs/projects/godeeep/VIC/inputs_1_16_deg_by_huc2'

# the period to use for calibration, first 2 years are spin up time
calib_start_year = 1979
calib_end_year = 2000
calib_snow_band = 'FALSE'

# after the calibration, we do a full run of the entire period
full_run_start_year = 1979
full_run_end_year = 2019
full_run_snow_band = 'TRUE'


def run_calibration(path_csv, path_output, point_id):

  start = time()

  # write in progress output to a temporary location for speed
  cwd = os.getcwd()
  print(cwd)
  final_path_output = path_output
  path_output = '/dev/shm'

  grid_ids = pd.read_csv(path_csv)
  row = grid_ids[grid_ids.id == point_id]
  lon = row.lon.values[0]
  lat = row.lat.values[0]
  huc2_code = row.huc2.values[0]

  # create an output folder and symlink to the input folder
  id_ll = f'{point_id:07}_{lon:0.5f}_{lat:0.5f}'
  point_subdir = f'{huc2_code:02}/{id_ll}'
  input_path = f'{vic_input_dir}/{point_subdir}'

  subpath_output = f'{path_output}/{id_ll}'
  os.makedirs(subpath_output, exist_ok=True)
  if not os.path.islink(f'{subpath_output}/input_symln'):
    # copy the forcing data to memory for speed
    os.system(f"cp -r {input_path} {subpath_output}/input_symln")
    # os.symlink(input_path, f'{subpath_output}/input_symln')

  # aggregate forcing files into 6 hours and save in the same input folder, "forcings_6h_16thdeg_*.nc"
  # concatenate runoff files into one single file not to repeat during calibrations
  # (potentially to increase efficiency), "runoff_concat_16thdeg_*.nc"
  def update_forcing_runoff(input_path):
    files_forcing = glob.glob(f'{input_path}/forcings_16thdeg_{id_ll}_*.nc')
    files_forcing.sort()
    for f in files_forcing:
      if not os.path.isfile(f.replace('forcings_16thdeg', 'forcings_6h_16thdeg')):
        print('Creating 6h forcing:', f.replace('forcings_16thdeg', 'forcings_6h_16thdeg'))
        ds = xr.load_dataset(f, decode_coords='all')
        ds_6h = ds[['T2', 'PSFC', 'SWDOWN', 'GLW', 'VP', 'WSPEED']].resample(time='6H').mean()
        ds_6h['PRECIP'] = ds['PRECIP'].resample(time='6H').sum()
        ds_6h.to_netcdf(f.replace('forcings_16thdeg', 'forcings_6h_16thdeg'))
        ds.close()
        ds_6h.close()

    files_runoff = glob.glob(f'{input_path}/runoff_16thdeg_{id_ll}_*.nc')
    files_runoff.sort()
    filename_runoff = f'/runoff_concat_16thdeg_{id_ll}_' + \
                      f'{files_runoff[0].split("_")[-1][:4]}-{files_runoff[-1].split("_")[-1][:4]}.nc'
    if not os.path.isfile(f'{input_path}/{filename_runoff}'):
      ds = xr.open_mfdataset(files_runoff, concat_dim='time', combine='nested', decode_coords='all')
      ds = ds.load()
      ds.to_netcdf(f'{input_path}/{filename_runoff}')
      ds.close()

  # check if the calibration is done already, if so, end here
  calib_progress_file = f'{subpath_output}/OstStatus0.txt'
  if os.path.exists(calib_progress_file):
    with open(calib_progress_file, 'r') as reader:
      # read the third line
      pct_complete = reader.read().split('\n')[2].split(':')[1]
      if float(pct_complete) == 100:
        return None

  update_forcing_runoff(f'{subpath_output}/input_symln')

  print('Preparing calibration')
  # copy model and calibration files
  shutil.copy('vic.in.tpl', subpath_output)
  # shutil.copy('vic.in', subpath_output) # "vic.in" will have the initial values from VICGlobal
  shutil.copy('vic_image.exe', subpath_output)  # vic_image
  shutil.copy('run_vic.py', subpath_output)
  # shutil.copy('config.txt', subpath_output)
  shutil.copy(f'{subpath_output}/input_symln/params_{id_ll}.nc', f'{subpath_output}/params_updated.nc')
  shutil.copy(f'{subpath_output}/input_symln/params_{id_ll}.nc', f'{subpath_output}/params.nc')
  # shutil.copy('ostIn.txt', subpath_output) # "ostIn.txt" will have the initial values from VICGlobal
  shutil.copy('Ostrich', subpath_output)

  # extract the initial values from VICGlobal
  p = []
  with xr.load_dataset(f'{subpath_output}/params.nc') as ds:
    for s in ['infilt', 'Dsmax', 'Ds', 'Ws', 'depth2', 'depth3', 'expt2', 'expt3']:
      if s.startswith('depth'):
        p.append(float(ds['depth'].isel(lon=0, lat=0, nlayer=int(s[-1]) - 1)))
      elif s.startswith('expt'):
        p.append(float(ds['expt'].isel(lon=0, lat=0, nlayer=int(s[-1]) - 1)))
      else:
        p.append(float(ds[s].isel(lon=0, lat=0)))

  # if plim_ctr has percent(%) strings to constrain the upper and lower limits of calibration parameters
  plim = plim_ctr.copy()
  for i, arr in enumerate(plim):
    if isinstance(arr[0], str) and arr[0].endswith('%'):
      plim[i][0] = p[i] * (1 + int(arr[0][:-1]) / 100)
    if isinstance(arr[1], str) and arr[1].endswith('%'):
      plim[i][1] = p[i] * (1 + int(arr[1][:-1]) / 100)

  # "vic.in" will have the initial values from VICGlobal
  vic_in = f'''\
{p[0]:0.4f} # Variable infitration parameter
{p[1]:0.4f} # Max velocity of base flow
{p[2]:0.4f} # Fraction of where nonlinear base flow occurs
{p[3]:0.4f} # Fraction of maximum soil moisture where non-linear baseflow occurs
{p[4]:0.4f} # Thickness of soil moisture layer 2
{p[5]:0.4f} # Thickness of soil moisture layer 3
{p[6]:0.4f} # Brooks-Corey baseflow parameter layer 2
{p[7]:0.4f} # Brooks-Corey baseflow parameter layer 3
  '''

  # "ostIn.txt" will have the initial values from VICGlobal
  ostIn_txt = f'''\
ProgramType DDS
ObjectiveFunction  GCOP
ModelExecutable  ./run_vic.py

BeginFilePairs
vic.in.tpl ; vic.in
EndFilePairs

BeginExtraFiles
params.nc
config.txt
vic_image.exe
#input_dir.txt
EndExtraFiles

BeginParams
# name       init.      lower       upper       transformations
<infilt>  {p[0]:0.4f}   {plim[0][0]:0.3f}   {plim[0][1]:0.3f}   none   none   none
<Dsmax>   {p[1]:0.4f}   {plim[1][0]:0.3f}   {plim[1][1]:0.3f}   none   none   none
<D_s>     {p[2]:0.4f}   {plim[2][0]:0.3f}   {plim[2][1]:0.3f}   none   none   none
<Ws>      {p[3]:0.4f}   {plim[3][0]:0.3f}   {plim[3][1]:0.3f}   none   none   none
<depth2>  {p[4]:0.4f}   {plim[4][0]:0.3f}   {plim[4][1]:0.3f}   none   none   none
<depth3>  {p[5]:0.4f}   {plim[5][0]:0.3f}   {plim[5][1]:0.3f}   none   none   none
<expt2>   {p[6]:0.4f}   {plim[6][0]:0.3f}   {plim[6][1]:0.3f}   none   none   none
<expt3>   {p[7]:0.4f}   {plim[7][0]:0.3f}   {plim[7][1]:0.3f}   none   none   none
EndParams

BeginResponseVars
# name  filename  ; keyword   skip_lines  col token
   NSE  vic.out   ; NSE                0    2   ' ' 
EndResponseVars

BeginConstraints
EndConstraints

BeginGCOP
CostFunction NSE
PenaltyFunction APM
EndGCOP

BeginInitParams  
{p[0]:0.4f} {p[1]:0.4f} {p[2]:0.4f} {p[3]:0.4f} {p[4]:0.4f} {p[5]:0.4f} {p[6]:0.4f} {p[7]:0.4f}
EndInitParams

BeginDDS
PerturbationValue      0.5
MaxIterations          100
UseInitialParamValues
EndDDS
  '''

  # use symlink path
  vic_config = '''\
# ######################################################################
# Simulation Parameters
# ######################################################################
MODEL_STEPS_PER_DAY   4  # number of model time steps in 24 hour period
SNOW_STEPS_PER_DAY    4  # number of snow model time steps in 24 hour period
RUNOFF_STEPS_PER_DAY  4  # number of runoff time steps in 24 hour period

STARTYEAR             {start_year} # year model simulation starts
STARTMONTH            1    # month model simulation starts
STARTDAY              1    # day model simulation starts
ENDYEAR               {end_year}
ENDMONTH              12
ENDDAY                31
CALENDAR              PROLEPTIC_GREGORIAN

FULL_ENERGY           FALSE # calculate full energy balance
FROZEN_SOIL           FALSE # calculate frozen soils

# ######################################################################
# DOMAIN INFO
# ######################################################################
DOMAIN input_symln/domain_{id_ll}.nc
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
FORCING1      input_symln/forcings_6h_16thdeg_{id_ll}_
FORCE_TYPE    AIR_TEMP     T2      # Average air temperature, C
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
SNOW_BAND           {snow_band}
BASEFLOW            ARNO
JULY_TAVG_SUPPLIED  FALSE
LAI_SRC             FROM_VEGPARAM
ALB_SRC             FROM_VEGPARAM
FCAN_SRC            FROM_VEGPARAM
ORGANIC_FRACT       FALSE
NODES               3  # number of soil thermal nodes

# ######################################################################
# Output Files and Parameters
# ######################################################################
RESULT_DIR  ./
OUTFILE     vic_runoff
AGGFREQ     NDAYS   1  # Write output every 1 day
OUT_FORMAT  NETCDF4
OUTVAR      OUT_RUNOFF
OUTVAR      OUT_BASEFLOW
{out_evap}OUTVAR      OUT_EVAP
{out_swe}OUTVAR      OUT_SWE
'''

  # this is a hack to pass the input data directory to the model
  # wrapper script avoids some duplicate code
  # f = open(f'{subpath_output}/input_dir.txt', 'w')
  # f.write(input_path)
  # f.close()

  os.chdir(subpath_output)
  print(subpath_output)

  # write the files specific to each cell
  with open('vic.in', 'w') as f:
    f.write(vic_in)
  with open('ostIn.txt', 'w') as f:
    f.write(ostIn_txt)
  with open('config.txt', 'w') as f:
    f.write(vic_config.format(start_year=calib_start_year, end_year=calib_end_year, id_ll=id_ll, snow_band=calib_snow_band, out_evap='#', out_swe='#'))
  with open('config_final.txt', 'w') as f:
    f.write(vic_config.format(start_year=full_run_start_year, end_year=full_run_end_year, id_ll=id_ll, snow_band=full_run_snow_band, out_evap='', out_swe=''))

  # print('Running uncalibrated')
  # run the uncalibrated case
  if os.path.isdir('nocalib'):
    shutil.rmtree('nocalib')
  os.makedirs('nocalib', exist_ok=True)

  # run VIC with the production configuration before calibration
  subprocess.run(['./vic_image.exe', '-g', 'config_final.txt'], env={'OMP_NUM_THREADS': '1', **os.environ})  # vic_image

  # return None

  # copy output files
  # some grid cells are in the ocean and the runs may fail
  vic_runoff = 'vic_runoff.{}-01-01.nc'.format(full_run_start_year)
  if os.path.exists(vic_runoff):
    shutil.move(vic_runoff, f'nocalib/{vic_runoff}')
    shutil.copy('params.nc', './nocalib/params_updated.nc')
  else:
    # remove binaries to save space
    os.system(f'rm vic_image.exe Ostrich')
    # the run failed, so just bail out
    sys.exit()
    pass

  print('Running calibration')
  # # run the calibration, takes a few hours
  subprocess.run(['time', './Ostrich', '>', '/dev/null'])

  # Do a full period run with the final parameters
  # make sure the param file is updated
  params = read_params()
  modify_params(params)

  # run VIC with the production configuration after calibration
  subprocess.run(['./vic_image.exe', '-g', 'config_final.txt'], env={'OMP_NUM_THREADS': '1', **os.environ})  # vic_image

  # remove binaries to save space
  os.system(f'rm vic_image.exe Ostrich run_vic.py')

  os.chdir(cwd)

  # create the final output dir
  # copy the whole output directory to the hard disk
  final_subpath_output = f'{final_path_output}/{id_ll}'
  os.makedirs(final_subpath_output, exist_ok=True)
  print(f"copying from {subpath_output} to {final_path_output}")
  # os.system(f"cp -r {subpath_output} {final_path_output}")
  # copy the output directory to its final location, but exclude the forcing data
  os.system(f'rsync -av --progress {subpath_output} {final_path_output} --exclude input_symln')
  print(f'ln -sf {input_path} {final_path_output}/{id_ll}/input_symln')
  os.system(f'ln -sf {input_path} {final_path_output}/{id_ll}/input_symln')
  # os.symlink(input_path, f'{final_path_output}/input_symln')

  # remove the temporary directory
  os.system(f'rm -rf {subpath_output}')

  print("Calibration took:", str(timedelta(seconds=np.round(time() - start))))


if __name__ == '__main__':
  # print(sys.argv)
  if len(sys.argv[3].split(',')) == 1:
    path_csv, path_output, idx = sys.argv[1], sys.argv[2], int(sys.argv[3])
    print(f'Running calibration for point {idx}')
    run_calibration(path_csv, path_output, idx)
    print(f'Done with calibration for point {idx}')
  else:
    path_csv, path_output = sys.argv[1], sys.argv[2]
    for idx in sys.argv[3].split(','):
      print(f'Running calibration for point {idx}')
      run_calibration(path_csv, path_output, idx)
      print(f'Done with calibration for point {idx}')
