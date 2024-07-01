import os
import pandas as pd
from tqdm import tqdm
import shutil

data_dir = '/vast/projects/godeeep/VIC/inputs_1_16_deg_by_huc2/'
grid_ids = pd.read_csv('../data/grid_ids_conus.csv')

good_point_dirs = {}
for h in range(1, 18+1):
  huc2 = f'{h:02}'
  good_point_dirs[huc2] = []

for i, row in grid_ids.iterrows():
  h = int(row.huc2)
  huc2 = f'{h:02}'
  id = int(row.id)
  lon = row.lon
  lat = row.lat
  good_point_dirs[huc2].append(f'{id:07}_{lon:0.5f}_{lat:0.5f}')

for h in range(1, 18+1):
  huc2 = f'{h:02}'
  print(huc2)
  point_dirs = os.listdir(f'{data_dir}/{huc2}')
  for point_dir in point_dirs:
    # for point_dir in tqdm(point_dirs):
    if point_dir in good_point_dirs[huc2]:
      num_files = len(os.listdir(f'{data_dir}/{huc2}/{point_dir}'))
      # 87 is 1 param, 1 domain, 44 forcing (1979-2022), 41 runoff (1979-2019)
      if num_files != 87:
        print(f'{point_dir} has {num_files} files')
    else:
      bad_point_dir = f'{data_dir}/{huc2}/{point_dir}'
      print(f'Deleting {bad_point_dir}')
      shutil.rmtree(bad_point_dir)
