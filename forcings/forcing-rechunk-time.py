import glob
import xarray as xr

dir_parent = './'
files = glob.glob(dir_parent + '/**/*.nc', recursive = True) # recursively search within the parent directory
suffix = '_rechunk'

for f in files:
    ds = xr.open_dataset(f)
    for v in ds.data_vars:
        if 'time' in ds[v].dims:
            ds[v].encoding['chunksizes'] = (len(ds['time']), 1, 1)

    ds.to_netcdf(f.replace('.nc', f'{suffix}.nc'))
    ds.close()