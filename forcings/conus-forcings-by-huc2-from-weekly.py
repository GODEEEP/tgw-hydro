import sys, os, glob, time
import numpy as np
import pandas as pd
import xarray as xr

from dask.distributed import Client

'''
Create VIC forcing files specific for one grid point directly using the weekly TGW forcing datasets (processed), and organize the files by HUC2

'''

# input path for the weekly TGW forcing datasets (processed)
#input_files = '/rcfs/projects/godeeep/VIC/forcings/1_16_deg/CONUS_TGW_WRF_Historical/tgw_wrf_historic_hourly_{}*'
input_files = '/vast/projects/godeeep/conus_tgw_1_16_deg_historical/tgw_wrf_historic_hourly_{}*'

xr.set_options(keep_attrs = True)
def subset_file(year, output_dir, nthread):
    print(f'Processing Year {year}')

    start_time = time.time()
    list_files = glob.glob(input_files.format(year))
    list_files.sort()

    forcing = xr.open_mfdataset(list_files, concat_dim = 'time', combine = 'nested', decode_cf = False, parallel = True)
    forcing['spatial_ref'] = forcing['spatial_ref'].isel(time = 0) # 'spatial_ref' should have no dimension
    forcing.load() # comment out for lazy-loading to save memory (not recommended as it leaves additional load process for each grid point)
    forcing.chunk(chunks = {'time': -1, 'lat': 1, 'lon': 1}) # chunking with respect to time

    input_csv = '../data/grid_ids_conus.csv' #'./grid_ids_ca.csv'
    grid_ids = pd.read_csv(input_csv)

    grid_lonlats = np.stack([grid_ids['lon'], grid_ids['lat']], axis = 1)

    ### if the .csv file contains a grid point outside of the TGW forcing domain (finite values)
    forcing_lons, forcing_lats = np.meshgrid(forcing['lon'], forcing['lat']) # grid points on the TGW forcing domain
    forcing_lonlats = np.stack([forcing_lons.flatten(), forcing_lats.flatten()], axis = 1)
    forcing_lonlats = forcing_lonlats[np.isfinite(forcing['T2'].isel(time = 0).values).flatten()]
    set_grid = set(map(tuple, grid_lonlats))
    set_forcing = set(map(tuple, forcing_lonlats))
    grid_lonlats = np.array(list(set_grid.intersection(set_forcing))) # find the intersection grids

    list_grid = []
    list_outputs, list_paths = [], []
    for lon, lat in grid_lonlats:
        grid_info = grid_ids[(grid_ids['lon'] == lon) & (grid_ids['lat'] == lat)].iloc[0]
        huc2_code = int(grid_info['huc2'])
        point_id = int(grid_info['id'])
        list_grid.append(grid_info)

        # make a subdirectory for each grid point
        point_dir = f'{output_dir}/{huc2_code:02}/{point_id:07}_{lon:0.5f}_{lat:0.5f}'
        os.makedirs(point_dir, exist_ok=True)
        forcing_fn = f'{point_dir}/forcings_16thdeg_{point_id:07}_{lon:0.5f}_{lat:0.5f}_{year}.nc'
    
        # store a list of datasets and paths to save as netcdf
        list_outputs.append(forcing.sel(lon = slice(lon, lon), lat = slice(lat, lat)))
        list_paths.append(forcing_fn)
    
    ### output a list of grid points in the same .csv formet - needed if the .csv file contains a grid point outside of the TGW forcing domain (finite values)
    pd_check = pd.DataFrame(list_grid)
    pd_check['huc2'] = pd_check['huc2'].astype(int).astype(str).str.zfill(2)
    pd_check['id'] = pd_check['id'].astype(int)
    pd_check.sort_values('id').to_csv(input_csv.replace('.csv', '_check.csv'), index = False)
    
    print(f'Loading and pre-processing the dataset took {round((time.time() - start_time)/60, 2)} minutes')

    n = 0
    while n < len(list_outputs):
        check_time = time.time()
        # save netcdf files using the avilable number of dask threads
        xr.save_mfdataset(list_outputs[n:n+nthread], list_paths[n:n+nthread])
        n += nthread
        print(f'{min(n, len(list_outputs))} / {len(list_outputs)} has been completed: {round(time.time() - check_time, 2)} seconds')

    runtime = round((time.time() - start_time)/60, 2)
    print(f'It took {runtime} minutes in total')
    
    return

if __name__ == "__main__":
    ### find the number of assigned cores for the dask threads
    if 'SLURM_CPUS_PER_TASK' in os.environ.keys(): nthread = int(os.environ['SLURM_CPUS_PER_TASK'])
    else:
        import threading
        nthread = int(threading.active_count())

    nworker = 1 # the dask threads will be split into the dask workers to share memory
    if len(sys.argv) > 2: nworker = int(sys.argv[2])
    client = Client(processes = True, n_workers = nworker, threads_per_worker = nthread // nworker)
    print('Dask distributed resources: ' + str(client))
    print(f'{nworker} worker(s) will work with {nthread // nworker} threads each')
    
    output_dir = '/rcfs/projects/godeeep/VIC/inputs_1_16_deg_by_huc2/'
    #output_dir = '/vast/projects/godeeep/inputs_1_16_deg_by_huc2/'
    #output_dir = '/vast/projects/godeeep/test_YS'
    subset_file(sys.argv[1], output_dir, nthread)
