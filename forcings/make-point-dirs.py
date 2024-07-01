import pandas as pd
from tqdm import tqdm
import os


def subset_file(output_dir):

  grid_ids = pd.read_csv("../data/grid_ids_conus.csv")

  for i, cell in tqdm(grid_ids.iterrows(), total=grid_ids.shape[0]):

    huc2 = int(cell.huc2)
    lon = cell.lon
    lat = cell.lat

    point_dir = f'{output_dir}/{huc2:02}/{i+1:07}_{lon:0.5f}_{lat:0.5f}'
    os.makedirs(point_dir, exist_ok=True)
    # if not os.path.exists(point_dir):
    #   os.mkdir(point_dir)


if __name__ == "__main__":
  # output_dir = '/rcfs/projects/godeeep/VIC/forcings/1_16_deg/CONUS_TGW_WRF_Historical_Grid_Year_Files/'
  output_dir = '/vast/projects/godeeep/CONUS_TGW_WRF_Historical_Grid/'
  subset_file(output_dir)

