#! /usr/bin/env python

import os
from xarray import open_dataset, open_mfdataset
from pandas import read_csv
from numpy import mean, sum, log1p
import sys
from glob import glob
# from hydroeval import evaluator, nse, kge
import hydroeval as he


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
  expt1       10.0     8.000     30.0
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


def nse_obj(obs, pred):
  val = (1-(sum((obs-pred)**2)/sum((obs-mean(obs))**2)))
  # try:
  #   val = (1-(sum((obs-pred)**2)/sum((obs-mean(obs))**2)))
  # except KeyboardInterrupt:
  #   sys.exit()
  # except:
  #   val = 999
  return -val


def kge_obj(obs, pred):
  kge, r, alpha, beta = he.evaluator(he.kge, pred, obs)
  return -kge[0]


def compute_obj(input_dir):

  # read VIC output data
  output = open_dataset('vic_runoff.1980-01-01.nc')
  runoff_vic = output['OUT_RUNOFF'].resample(time='M').sum(['time', 'lat', 'lon'])
  baseflow_vic = output['OUT_BASEFLOW'].resample(time='M').sum(['time', 'lat', 'lon'])

  runoff_files = glob(f'{input_dir}/runoff*')
  runoff_files.sort()
  # ro_path = '/Users/brac840/projects/godeeep/tgw-hydro/calibration/input_files/'
  # ro_fn = [f'runoff_16thdeg_0090815_-114.53125_49.65625_{y}.nc' for y in range(1980, 2009+1)]
  # runoff data is 1979:2019
  runoff_obs = open_mfdataset(runoff_files[1:31])

  # obs = runoff_obs.ro[:, 0, 0].to_numpy()
  obs = runoff_obs.ro.resample(time='M').sum(['time', 'lat', 'lon']).to_numpy()
  pred = baseflow_vic.to_numpy().flatten() + runoff_vic.to_numpy().flatten()

  output.close()
  runoff_obs.close()

  # runoff_obs.ro[:, 0, 0].plot()
  runoff_obs.ro.resample(time='M').sum(['time', 'lat', 'lon']).plot()
  # baseflow_vic.plot()
  # runoff_vic.plot()
  (runoff_vic+baseflow_vic).plot()

  # negative because we are minimizing
  # skip the first 2 years for spinup
  # the length is a hack because for some
  # vic runs one day less on PIC
  # return -nse(obs[730:10227], pred[730:10227])-nse(log1p(obs[730:10227]), log1p(pred[730:10227]))
  return kge_obj(obs[24:], pred[24:])


def write_output(obj):
  f = open('vic.out', 'w')
  # ostrich bugs out if there is only one value on a line
  f.write('NSE '+str(obj)+' '+str(obj)+'\n')
  f.close()


if __name__ == '__main__':

  f = open(f'input_dir.txt', 'r')
  input_dir = f.read().strip()
  f.close()

  updated_params = read_params()
  modify_params(updated_params)
  run_vic()
  obj = compute_obj(input_dir)
  write_output(obj)
