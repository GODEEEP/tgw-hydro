#! /usr/bin/env python

import os
from xarray import open_dataset, open_mfdataset
from pandas import read_csv
from numpy import mean, sum
import sys
# from hydroeval import evaluator, nse


def run_vic():
  os.system('OMP_NUM_THREADS=1 ./vic_image -g config.txt')


def modify_params(params):
  """
  # name       init.      lower    upper
  infilt       0.1     0.001      0.8 
  Dsmax        5.0     1.000     30.0 
  D_s          0.5     0.000      1.0 
  Ws           0.7     0.500      1.0 
  depth1       0.5     0.001      0.1 
  depth2       0.5     0.100      1.0 
  depth3       1.0     0.100      2.0 
  expt1       10.0     8.000     30.0 \
  expt2       10.0     8.000     30.0 
  expt3       10.0     8.000     30.0 
  """

  vic_params = open_dataset('params.nc')

  vic_params['infilt'][:, :] = params['infilt']
  vic_params['Dsmax'][:, :] = params['Dsmax']
  vic_params['Ds'][:, :] = params['D_s']
  vic_params['Ws'][:, :] = params['Ws']
  vic_params['depth'][0, :, :] = params['depth1']
  vic_params['depth'][1, :, :] = params['depth2']
  vic_params['depth'][2, :, :] = params['depth3']
  # should we have separate parameters for each later?
  vic_params['expt'][0, :, :] = params['expt1']
  vic_params['expt'][1, :, :] = params['expt2']
  vic_params['expt'][2, :, :] = params['expt3']

  vic_params.to_netcdf('params_updated.nc')

  return


def read_params():
  """
  <infilt> # Variable infitration parameter
  <Dsmax>  # Max velocity of base flow
  <D_s>    # Fraction of where nonlinear base flow occurs
  <Ws>     # Fraction of maximum soil moisture where non-linear baseflow occurs
  <depth1> # Thickness of soil moisture layer 1
  <depth2> # Thickness of soil moisture layer 2
  <depth3> # Thickness of soil moisture layer 3
  <expt1>  # Brooks-Corey baseflow parameter layer 1
  <expt2>  # Brooks-Corey baseflow parameter layer 2
  <expt3>  # Brooks-Corey baseflow parameter layer 3
  """

  f = open('vic.in', 'r')
  lines = f.readlines()
  p = [float(line.split(' ')[0]) for line in lines]
  f.close()

  params = {}
  params['infilt'] = p[0]
  params['Dsmax'] = p[1]
  params['D_s'] = p[2]
  params['Ws'] = p[3]
  params['depth1'] = p[4]
  params['depth2'] = p[5]
  params['depth3'] = p[6]
  params['expt1'] = p[7]
  params['expt2'] = p[8]
  params['expt3'] = p[9]

  return params


def nse(obs, pred):
  val = (1-(sum((obs-pred)**2)/sum((obs-mean(obs))**2)))
  # try:
  #   val = (1-(sum((obs-pred)**2)/sum((obs-mean(obs))**2)))
  # except KeyboardInterrupt:
  #   sys.exit()
  # except:
  #   val = 999
  return val


def compute_obj():

  # read VIC output data
  output = open_dataset('fluxes.1980-01-01.nc')

  # aggregate to monthly
  runoff_vic = output['OUT_RUNOFF'].resample(time='D').sum(['time', 'lat', 'lon'])
  # ym_keys = [str(x)[0:4]+str(x)[5:7] for x in runoff_vic.time.to_numpy()]

  # runoff_obs = read_csv('mv01d_row_data.txt', index_col='huc_cd', dtype={'huc_cd': str})
  ro_path = '/Users/brac840/projects/godeeep/tgw-hydro/calibration/input_files/'
  ro_fn = [f'runoff_16thdeg_0090815_-114.53125_49.65625_{y}.nc' for y in range(1980, 2009+1)]
  runoff_obs = open_mfdataset([f'{ro_path}/{fn}' for fn in ro_fn])

  obs = runoff_obs.ro[:, 0, 0].to_numpy()
  pred = runoff_vic.to_numpy()

  output.close()
  runoff_obs.close()

  # f = open('vic.out', 'w')
  # f.write('OBS ')
  # [f.write(str(o)+' ') for o in obs]
  # f.write('\n')
  # f.write('PRED ')
  # [f.write(str(p)+' ') for p in pred]
  # f.write('\n')
  # f.close()

  # negative because we are minimizing
  # skip the first 2 years for spinup
  return -nse(obs[730:], pred[730:])


def write_output(obj):
  f = open('vic.out', 'w')
  f.write('NSE '+str(obj)+' '+str(obj)+'\n')
  f.close()


if __name__ == '__main__':
  updated_params = read_params()
  modify_params(updated_params)
  run_vic()
  obj = compute_obj()
  write_output(obj)
