from shapely.geometry import shape, Point
import xarray as xr
import numpy as np
import fiona
from pyogrio import read_dataframe
import geopandas as gpd
from tqdm import tqdm

domain = xr.open_dataset('./namerica_domain.nc')
params = xr.open_dataset('./namerica_params.nc')
huc8_shp = read_dataframe("../data/HUC8_CONUS/HUC8_US.shp")

for i, huc8 in tqdm(huc8_shp.iterrows(), total=len(huc8_shp.geometry)):

  # huc8 = huc8_shp[huc8_shp.HUC8 == '10020001']
  huc8_code = huc8.HUC8
  geometry = huc8.geometry
  bounds = geometry.bounds

  subdomain = domain.sel(lat=slice(bounds[1], bounds[3]), lon=slice(bounds[0], bounds[2]))
  subdomain_params = params.sel(lat=slice(bounds[1], bounds[3]), lon=slice(bounds[0], bounds[2]))
  mask = subdomain.mask
  root_fract = subdomain_params.root_fract

  # set the mask based on the basin boundary
  for i in range(len(mask.lon)):
    for j in range(len(mask.lat)):
      mask[j, i] = int(geometry.contains(Point(mask.lon[i], mask.lat[j])))
      for k in range(len(root_fract.veg_class)):
        # root fraction was throwing errors so renormalize
        root_fract[k, :, j, i] = root_fract[k, :, j, i]/sum(root_fract[k, :, j, i])

  subdomain['mask'] = mask
  subdomain_params['mask'] = mask
  subdomain_params['run_cell'] = mask
  subdomain_params['root_fract'] = root_fract
  # ax = gpd.GeoSeries(geometry).plot()
  # subdomain.mask.plot(ax=ax)
  # gpd.GeoSeries(geometry).plot(ax=ax)

  subdomain.to_netcdf(f'domains_huc8/domain_{huc8_code}.nc')
  subdomain_params.to_netcdf(f'params_huc8/params_{huc8_code}.nc')
