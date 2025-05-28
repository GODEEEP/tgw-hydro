### Y.Son: subset VIC input domain parameters by HUC2

import sys, os, glob
import numpy as np
import pandas as pd
import xarray as xr

xr.set_options(keep_attrs = True)

path_csv = '/scratch/sony061/foresight/domain/grid_ids_conus.csv'
path_nc = '/scratch/sony061/foresight/domain/namerica_domain.nc'
path_out = '/scratch/sony061/foresight/domain/subset/namerica_domain_HUC{HUC2:02d}.nc'
#path_nc = '/scratch/sony061/foresight/domain/namerica_params.nc'
#path_out = '/scratch/sony061/foresight/domain/subset/namerica_params_HUC{HUC2:02d}.nc'

flag_mask = True # if True, mask variables outside of HUC boundary, WARNINIG: Time-Consuming
vars_mask = {'mask': 0} # if empty, iterate all variables in path_nc

def subset(year = None):
    print(f'YEAR: {year}')
    df = pd.read_csv(path_csv)
    list_huc2 = df['huc2'].unique()

    ds = xr.open_dataset(path_nc, decode_cf = 'all')
    # VIC: ../shared_all/src/calc_root_fraction.c:60: errno: None: Input root fractions do not sum to 1.0: 0.990000, veg class: 5
    if 'root_fract' in ds.data_vars: ds['root_fract'] = ds['root_fract'] / ds['root_fract'].sum(dim = 'root_zone')
    for huc2 in list_huc2:
        os.makedirs(os.path.dirname(path_out.format(HUC2 = huc2, year = year)), exist_ok = True)

        # xarray 'where' forces dtype changes (float64)
        #lon_min, lon_max = df.loc[df['huc2'] == huc2, 'lon'].min(), df.loc[df['huc2'] == huc2, 'lon'].max()
        #lat_min, lat_max = df.loc[df['huc2'] == huc2, 'lat'].min(), df.loc[df['huc2'] == huc2, 'lat'].max()
        #ds_subset = ds.where((ds['lon'] >= lon_min) & (ds['lon'] <= lon_max) & (ds['lat'] >= lat_min) & (ds['lat'] <= lat_max), drop = True)

        lons, lats = np.sort(df.loc[df['huc2'] == huc2, 'lon'].unique()), np.sort(df.loc[df['huc2'] == huc2, 'lat'].unique())
        ds_subset = ds.sel(lon = lons, lat = lats)

        if flag_mask:
            da_mask = None
            if not bool(vars_mask): vars = {v: np.nan for v in ds_subset.data_vars}
            else: vars = vars_mask
            for v, na in vars.items():
                if 'lon' in ds_subset[v].dims and 'lat' in ds_subset[v].dims:
                    if da_mask is None:
                        da_mask = pd.merge(ds_subset[v].to_dataframe(), df.loc[df['huc2'] == huc2], on = ['lon', 'lat'], how = 'outer')
                        da_mask = np.isfinite(da_mask.set_index(['lat', 'lon'])['huc2'].rename({'huc2': 'mask'})).astype(int)
                        da_mask = da_mask.to_xarray()
                        da_mask = da_mask.where(da_mask, np.nan)

                    encoding = ds_subset[v].encoding.copy()
                    if 'dtype' not in encoding.keys():
                        ds_subset[v] = ds_subset[v] * da_mask
                        ds_subset[v] = ds_subset[v].fillna(na)
                    elif encoding['dtype'] != 'int32':
                        ds_subset[v] = ds_subset[v] * da_mask
                        ds_subset[v] = ds_subset[v].fillna(na)
                    else:
                        encoding['_FillValue'] = -2147483648
                        ds_subset[v] = ds_subset[v].where(ds_subset[v] != encoding['_FillValue']) * da_mask
                        if np.isnan(na): ds_subset[v] = ds_subset[v].fillna(encoding['_FillValue']).astype(int)
                        else: ds_subset[v] = ds_subset[v].fillna(na).astype(int)
                    ds_subset[v].encoding.update(encoding)

        ds_subset.to_netcdf(path_out.format(HUC2 = huc2, year = year))
        print(path_out.format(HUC2 = huc2, year = year))

    return

if __name__ == '__main__':
    #subset(year = sys.argv[1])
    #subset(year = 2045)
    subset()