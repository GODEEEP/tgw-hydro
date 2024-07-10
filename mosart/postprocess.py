import xarray as xr
import pandas as pd
import numpy as np
from tqdm import tqdm
from scipy.spatial import KDTree

# huc2s = [10, 15, 16, 17, 18]
# huc2_names = ['missouri', 'uppercolorado',
#               'greatbasin', 'columbia', 'california']

# huc2s = [10, 17, 18]
# huc2_names = ['missouri', 'columbia', 'california']

# huc2s = [12, 13, 14]
# huc2_names = ["texas", "riogrande", "uppercolorado"]

huc2s = list(range(1, 18+1))
huc2_names = [
    "northeast", "midatlantic", "southatlantic", "greatlakes",
    "ohio", "tennessee", "uppermississippi", "lowermississippi",
    "souris", "missouri", "arkansas", "texas", "riogrande", "uppercolorado",
    "lowercolorado", "greatbasin", "columbia", "california"
]


def nearest_grid_index_from_points(var, plants):

  lon = var.lon
  lat = var.lat
  grid_points = np.array(np.meshgrid(lon, lat)).reshape(2, lon.shape[0]*lat.shape[0]).T
  tree = KDTree(grid_points)
  dists, rows = tree.query(plants[['lon', 'lat']])
  lons = grid_points[rows][:, 0]
  lats = grid_points[rows][:, 1]

  return (lons, lats)


def extract_points_from_grid(ds, plants):

  lons, lats = nearest_grid_index_from_points(ds, plants)
  # gen_points = gen['capacity_factor'][:, indexi, indexj]

  point_list = []
  for lon, lat in tqdm(zip(lons, lats), total=len(lons)):
    point_list.append(ds.sel(lon=slice(lon, lon), lat=slice(lat, lat)).squeeze())

  point_array = np.vstack(point_list).transpose()
  point_df = pd.DataFrame(point_array, index=pd.to_datetime(ds['time']), columns=plants.EIA_PID.astype('int32'))

  return point_df


if __name__ == '__main__':

  for huc2, huc2_name in zip(huc2s, huc2_names):

    print(huc2, huc2_name)

    mosart_output = xr.open_mfdataset(f'output/{huc2_name}/{huc2_name}*.nc')
    dams = pd.read_csv('mosartwmpy_conus_EHA_v1.0/mosartwmpy_conus_EHA_v1.0.csv')
    dams = dams[(dams.HUC2 == huc2) & ~pd.isna(dams.EIA_PID)].drop_duplicates(subset=['EIA_PID'])
    outflow = mosart_output.channel_outflow.load()
    inflow = mosart_output.channel_inflow.load()
    storage = mosart_output.STORAGE_LIQ.load()

    outflow_points = extract_points_from_grid(outflow, dams)
    outflow_points.to_csv(f'output/{huc2_name}/dam_outflow.csv', index_label='datetime')

    inflow_points = extract_points_from_grid(inflow, dams)
    inflow_points.to_csv(f'output/{huc2_name}/dam_inflow.csv', index_label='datetime')

    storage_points = extract_points_from_grid(storage, dams)
    storage_points.to_csv(f'output/{huc2_name}/dam_storage.csv', index_label='datetime')
