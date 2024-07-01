import pandas as pd
import numpy as np
import os
import sys

huc2 = int(sys.argv[1])
data_path = '/vast/projects/godeeep/VIC/inputs_1_16_deg_by_huc2'

broken_fn = f'pick_broken_{huc2}.txt'
grid = pd.read_csv('../data/grid_ids_conus.csv')
cell_ids = np.fromfile(broken_fn)

with open(broken_fn) as f:
  ids = f.readline()
ids = [int(float(id.rstrip())) for id in ids.split(' ')]


for cell_id in ids:
  print(cell_id)

  row = grid[(grid.huc2 == huc2) & (grid.id == cell_id)]
  lon = float(row.lon)
  lat = float(row.lat)
  path = f'{data_path}/{huc2}/{cell_id:07}_{lon:0.5f}_{lat:0.5f}'

  runoff_files = [file for file in os.listdir(path) if file[0:6] == 'runoff']
  [os.unlink(f'{path}/{runoff_file}') for runoff_file in runoff_files]

  forcing_files = [file for file in os.listdir(path) if file[0:7] == 'forcing']
  [os.unlink(f'{path}/{forcing_file}') for forcing_file in forcing_files]
