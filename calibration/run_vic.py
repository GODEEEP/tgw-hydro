#! /usr/bin/env python

import os
from xarray import open_dataset, open_mfdataset
import pandas as pd
from numpy import mean, sum, corrcoef, std, sqrt, log1p
import sys
from glob import glob
# from hydroeval import evaluator, nse
import subprocess


def run_vic():
  # os.system('OMP_NUM_THREADS=1 ./vic_image -g config.txt')
  subprocess.run(['./vic_image.exe', '-g', 'config.txt'], env={'OMP_NUM_THREADS': '1', **os.environ})  # vic_image


def modify_params(params):
  """
  # name       init.      lower    upper
  infilt       0.1     0.001      0.8 
  Dsmax        5.0     1.000     30.0 
  D_s          0.5     0.000      1.0 
  Ws           0.7     0.500      1.0 
  depth2       0.5     0.100      1.0 
  depth3       1.0     0.100      2.0 
  expt2       10.0     8.000     30.0 
  expt3       10.0     8.000     30.0 
  """

  vic_params = open_dataset('params.nc')

  vic_params['infilt'][:, :] = params['infilt']
  vic_params['Dsmax'][:, :] = params['Dsmax']
  vic_params['Ds'][:, :] = params['D_s']
  vic_params['Ws'][:, :] = params['Ws']
  vic_params['depth'][1, :, :] = params['depth2']
  vic_params['depth'][2, :, :] = params['depth3']
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
  <depth2> # Thickness of soil moisture layer 2
  <depth3> # Thickness of soil moisture layer 3
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
  params['depth2'] = p[4]
  params['depth3'] = p[5]
  params['expt2'] = p[6]
  params['expt3'] = p[7]

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


def kge(obs, pred):
  r = corrcoef(pred, obs)[0, 1]
  alpha = std(pred) / std(obs)
  beta = mean(pred) / mean(obs)
  gramma = alpha / beta
  return 1 - sqrt((r - 1) ** 2 + (beta - 1) ** 2 + (gramma - 1) ** 2)


def compute_obj(input_dir, begin_date, end_date):

  # read VIC output data
  output = open_dataset('vic_runoff.1979-01-01.nc')
  runoff_vic = output['OUT_RUNOFF'].isel(lon=0, lat=0) + output['OUT_BASEFLOW'].isel(lon=0, lat=0)
  # .resample(time='D').sum(['time', 'lat', 'lon'])

  # read the concatenated runoff file at once (potentially to increase efficiency)
  runoff_files = glob(f'{input_dir}/runoff_concat_16thdeg_*.nc')
  runoff_obs = open_dataset(runoff_files[0]).isel(lon=0, lat=0)['ro']

  # only compare for the date range of interest
  runoff_vic = runoff_vic.where(
      runoff_vic['time'] >= begin_date, drop=True).where(
      runoff_vic['time'] < end_date, drop=True)
  runoff_obs = runoff_obs.where(
      runoff_obs['time'] >= begin_date, drop=True).where(
      runoff_obs['time'] < end_date, drop=True)

  # compare the monthly mean statistics
  runoff_vic = runoff_vic.resample(time='M').mean()
  runoff_obs = runoff_obs.resample(time='M').mean()

  # negative because we are minimizing
  # skip the first 2 years for spinup
  # return -nse(runoff_obs.to_numpy(), runoff_vic.to_numpy())
  return -kge(runoff_obs.to_numpy(), runoff_vic.to_numpy())
  # return 1-1/(2-nse(runoff_obs.to_numpy(), runoff_vic.to_numpy())) # normalization
  # return -nse(runoff_obs.to_numpy(), runoff_vic.to_numpy()) -nse(log1p(runoff_obs.to_numpy()), log1p(runoff_vic.to_numpy()))


def write_output(obj):
  f = open('vic.out', 'w')
  # ostrich bugs out if there is only one value on a line
  f.write('NSE '+str(obj)+' '+str(obj)+'\n')
  f.close()


if __name__ == '__main__':

  # f = open(f'input_dir.txt', 'r')
  # input_dir = f.read()
  # f.close()
  # os.chdir('outputs/05DC000/0245388_-116.65625_52.34375/mod0')

  updated_params = read_params()
  modify_params(updated_params)
  run_vic()
  obj = compute_obj('input_symln', pd.Timestamp('1981-01-01'), pd.Timestamp('1988-01-01'))
  write_output(obj)
