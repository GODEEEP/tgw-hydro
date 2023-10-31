import os

data_dir = '/rcfs/projects/godeeep/inputs_1_16_deg_by_huc2/'

for h in range(1, 18+1):
  huc2 = f'{h:02}'
  point_dirs = os.listdir(f'{data_dir}/{huc2}')
  for point_dir in point_dirs:
    num_files = len(os.listdir(f'{data_dir}/{huc2}/{point_dir}'))
    # 87 is 1 param, 1 domain, 44 forcing (1979-2022), 41 runoff (1979-2019)
    if num_files != 87:
      print(f'{point_dir} has {num_files} files')
