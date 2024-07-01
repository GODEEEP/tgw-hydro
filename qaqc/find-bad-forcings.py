import os
import glob

input_path = '/vast/projects/godeeep/VIC/inputs_1_16_deg_by_huc2'
huc2_dirs = os.listdir(input_path)
huc2_dirs.sort()

bad_forcing_files = []
for huc2_dir in huc2_dirs:
  if huc2_dir == '00':
    continue
  print(huc2_dir)
  point_dirs = os.listdir(f'{input_path}/{huc2_dir}')
  point_dirs.sort()
  for point_dir in point_dirs:
    # print(point_dir)
    forcing_files = glob.glob(f'{input_path}/{huc2_dir}/{point_dir}/forcings_16*')
    for forcing_file in forcing_files:
      if os.path.getsize(forcing_file) < 3813000:
        bad_forcing_files.append(forcing_file)
        print(forcing_file)

for fn in bad_forcing_files:
  os.unlink(fn)
