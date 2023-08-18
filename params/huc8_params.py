from shapely.geometry import shape, Point
import xarray as xr
import numpy as np
import fiona
from pyogrio import read_dataframe
import geopandas as gpd
from tqdm import tqdm

na = xr.open_dataset('./namerica_params.nc')
huc8_shp = read_dataframe("../data/HUC8_CONUS/HUC8_US.shp")

for i, huc8 in tqdm(huc8_shp.iterrows(), total=len(huc8_shp.geometry)):

  huc8_code = huc8.HUC8
  geometry = huc8.geometry
  bounds = geometry.bounds

  subregion = na.sel(lat=slice(bounds[1], bounds[3]), lon=slice(bounds[0], bounds[2]))
  mask = subregion.mask

  # set the mask based on the basin boundary
  for i in range(len(mask.lon)):
    for j in range(len(mask.lat)):
      mask[j, i] = int(geometry.contains(Point(mask.lon[i], mask.lat[j])))

  subregion['mask'] = mask
  # ax = gpd.GeoSeries(geometry).plot()
  # subregion.mask.plot(ax=ax)
  # gpd.GeoSeries(geometry).plot(ax=ax)

  subregion.to_netcdf(f'params_huc8/params_{huc8_code}.nc')
