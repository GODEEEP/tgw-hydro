### Y.Son: merge calibrated parameters from grid folders by HUC2

import sys, os, glob
import numpy as np
import xarray as xr

#huc = int(sys.argv[1])
huc = 6

path_ref = f'/scratch/sony061/foresight/domain/subset/namerica_params_HUC{huc:02d}.nc' # initial parameter file for reference
path_vic = f'/scratch/sony061/foresight/calibration/TGW-WRF/{huc:02d}' # calibration folder
vic_filename = 'params_updated.nc' # calibrated output filename

path_out = f'/scratch/sony061/foresight/calibration/TGW-WRF/namerica_params_HUC{huc:02d}_calib.nc' # merged parameter file

files_vic = glob.glob(os.path.join(path_vic, '**', vic_filename))
files_vic.sort()

arr = []
# iterate for grid folders
for f in files_vic:
    print(f'Processing: "{f}"')
    ds_vic = xr.open_dataset(f, decode_coords = 'all')
#    ds_vic = ds_vic[['infilt', 'Dsmax', 'Ds', 'Ws', 'depth', 'expt']]
    arr.append(ds_vic)

ds = xr.combine_by_coords(arr)
ds = ds.reindex_like(xr.open_dataset(path_ref, decode_coords = 'all'))
for v in ds.data_vars:
    if v == 'layer':
        ds[v] = xr.DataArray(ds['nlayer'] + 1, dims = ['nlayer'], coords = {'nlayer': ds['nlayer']})
        ds[v].encoding.update(ds_vic[v].encoding) # copy encoding

    #<string>:1: SerializationWarning: saving variable mask with floating point data as an integer dtype without any _FillValue to use for NaNs
    #<string>:1: SerializationWarning: saving variable run_cell with floating point data as an integer dtype without any _FillValue to use for NaNs
    #<string>:1: SerializationWarning: saving variable gridcell with floating point data as an integer dtype without any _FillValue to use for NaNs
    #<string>:1: SerializationWarning: saving variable fs_active with floating point data as an integer dtype without any _FillValue to use for NaNs
    #<string>:1: SerializationWarning: saving variable Nveg with floating point data as an integer dtype without any _FillValue to use for NaNs
    #<string>:1: SerializationWarning: saving variable overstory with floating point data as an integer dtype without any _FillValue to use for NaNs
    if 'dtype' in ds[v].encoding.keys():
        if ds[v].encoding['dtype'] == 'int32':
            ds[v].encoding['_FillValue'] = -2147483648 # fill value for an integer dtype
ds.to_netcdf(path_out)