import sys, subprocess, os, shutil, time
import numpy as np
import pandas as pd
import xarray as xr
from datetime import timedelta

start_year, end_year = 2018, 2099
vic_input_dir = '/vast/projects/godeeep/VIC/inputs_1_16_deg_by_huc2/'
vic_calib_dir = '/vast/projects/godeeep/VIC/calibration/'
warmups = [2018, 2019]

vic_config_final = '''\
# ######################################################################
# Simulation Parameters
# ######################################################################
MODEL_STEPS_PER_DAY   4  # number of model time steps in 24 hour period
SNOW_STEPS_PER_DAY    4  # number of snow model time steps in 24 hour period
RUNOFF_STEPS_PER_DAY  4  # number of runoff time steps in 24 hour period

STARTYEAR             {start_year} # year model simulation starts
STARTMONTH            1    # month model simulation starts
STARTDAY              1    # day model simulation starts
ENDYEAR               {end_year}
ENDMONTH              12
ENDDAY                31
CALENDAR              PROLEPTIC_GREGORIAN

FULL_ENERGY           FALSE # calculate full energy balance
FROZEN_SOIL           FALSE # calculate frozen soils

# ######################################################################
# DOMAIN INFO
# ######################################################################
DOMAIN input_symln/domain_{id_ll}.nc
DOMAIN_TYPE    LAT     lat
DOMAIN_TYPE    LON     lon
DOMAIN_TYPE    MASK    mask
DOMAIN_TYPE    AREA    area
DOMAIN_TYPE    FRAC    frac
DOMAIN_TYPE    YDIM    lat
DOMAIN_TYPE    XDIM    lon

# ######################################################################
# Forcing Files and Parameters
# netcdf forcing files will be of the form: <FORCING1>YYYY.nc
# ######################################################################
FORCING1      input_symln/{scenario}/forcings_6h_16thdeg_{id_ll}_
FORCE_TYPE    AIR_TEMP     T2      # Average air temperature, C
FORCE_TYPE    PREC         PRECIP  # Total precipitation (rain and snow), kg/m2/s
FORCE_TYPE    PRESSURE     PSFC    # Atmospheric pressure, Pa
FORCE_TYPE    SWDOWN       SWDOWN  # Incoming shortwave, W/m2
FORCE_TYPE    LWDOWN       GLW     # Incoming longwave radiation, W/m2
FORCE_TYPE    VP           VP      # Vapor pressure, kPa
FORCE_TYPE    WIND         WSPEED  # Wind speed, m/s

# ######################################################################
# Land Surface Files and Parameters
# ######################################################################
PARAMETERS          params_updated.nc
SNOW_BAND           FALSE
BASEFLOW            ARNO
JULY_TAVG_SUPPLIED  FALSE
LAI_SRC             FROM_VEGPARAM
ALB_SRC             FROM_VEGPARAM
FCAN_SRC            FROM_VEGPARAM
ORGANIC_FRACT       FALSE
NODES               3  # number of soil thermal nodes

# ######################################################################
# Output Files and Parameters
# ######################################################################
RESULT_DIR  ./
OUTFILE     vic_runoff
AGGFREQ     NDAYS   1  # Write output every 1 day
OUT_FORMAT  NETCDF4
OUTVAR      OUT_RUNOFF
OUTVAR      OUT_BASEFLOW
OUTVAR      OUT_EVAP
OUTVAR      OUT_SWE
'''

def run_VIC(path_csv, scenario, path_output, point_id):
    start = time.time()

    grid_ids = pd.read_csv(path_csv)
    row = grid_ids[grid_ids.id == point_id]
    lon = row.lon.values[0]
    lat = row.lat.values[0]
    huc2_code = row.huc2.values[0]

    ### create an output folder and symlink to the input folder
    id_ll = f'{point_id:07}_{lon:0.5f}_{lat:0.5f}'

    path_output_id = os.path.join(path_output, id_ll)
    path_input_id = os.path.join(vic_input_dir, f'{huc2_code:02}', id_ll)
    path_calib_id = os.path.join(vic_calib_dir, f'{huc2_code:02}', id_ll)
    
    os.makedirs(path_output_id, exist_ok=True)

    # check if simulation is already done
    if os.path.isfile(os.path.join(path_output_id, f'vic_runoff.{start_year}-01-01.nc')):
        print(f'{id_ll}: Already Completed!')
        return

    # forcing files
    path_symln = os.path.join(path_output_id, 'input_symln')
    if os.path.islink(path_symln): os.unlink(path_symln)
    os.symlink(path_input_id, path_symln)

    # forcing files for warm-ups
    for y in warmups:
        path_dst = os.path.join(path_input_id, scenario, f'forcings_6h_16thdeg_{id_ll}_{y}.nc')
        if os.path.islink(path_dst): os.unlink(path_dst)
        elif os.path.isfile(path_dst): shutil.move(path_dst, path_dst.replace('.nc', '.nc.overlap'))
        path_src = os.path.join(path_input_id, f'forcings_6h_16thdeg_{id_ll}_{y}.nc')
        if not os.path.isfile(path_src):
            ds = xr.load_dataset(os.path.join(path_input_id, f'forcings_16thdeg_{id_ll}_{y}.nc'), decode_coords='all')
            ds_6h = ds[['T2', 'PSFC', 'SWDOWN', 'GLW', 'VP', 'WSPEED']].resample(time='6H').mean()
            ds_6h['PRECIP'] = ds['PRECIP'].resample(time='6H').sum(skipna=False)
            for var in list(ds_6h.data_vars.keys()):
                ds_6h[var].encoding.pop('original_shape', None)
                if len(ds_6h[var].shape) > 0: ds_6h[var].encoding['chunksizes'] = ds_6h[var].shape
                ds_6h.encoding = {'unlimited_dims': ['time']}
            ds_6h.to_netcdf(path_src)
            ds.close()
            ds_6h.close()
        os.symlink(path_src, path_dst)

    # vic configuration file
    path_config = os.path.join(path_output_id, 'config.txt')
    with open(path_config, 'w') as f:
        f.write(vic_config_final.format(start_year=start_year, end_year=end_year, id_ll=id_ll, scenario=scenario))
    
    # vic_image
    shutil.copy('vic_image.exe', path_output_id)

    # calibrated domain file
    path_src = os.path.join(path_calib_id, 'params_updated.nc')
    if os.path.isfile(path_src):
        path_dst = os.path.join(path_output_id, f'params_updated.nc')
        if os.path.islink(path_dst): os.unlink(path_dst)
        os.symlink(path_src, path_dst)
    else:
        print(f'{id_ll}: No Calibrated Domain Input!')
        return

    ### run VIC
    os.chdir(path_output_id)
    subprocess.run(['./vic_image.exe', '-g', 'config.txt'], env={'OMP_NUM_THREADS': '1', **os.environ})  # vic_image

    print('VIC run took:', str(timedelta(seconds=np.round(time.time() - start))))

    return

if __name__ == '__main__':
    # print(sys.argv)
    if len(sys.argv[4].split(',')) == 1:
        path_csv, scenario, path_output, idx = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4])
        print(f'Running VIC for point {idx}')
        run_VIC(path_csv, scenario, path_output, idx)
        print(f'Done with VIC for point {idx}')
    else:
        path_csv, scenario, path_output = sys.argv[1], sys.argv[2], sys.argv[3]
        for idx in sys.argv[4].split(','):
            print(f'Running VIC for point {idx}')
            run_VIC(path_csv, scenario, path_output, idx)
            print(f'Done with VIC for point {idx}')
'''
    os.chdir('futureruns')
    path_csv = '../data/grid_ids_conus.csv'
    scenario = 'rcp45cooler'
    path_output = f'/vast/projects/godeeep/VIC/future_projections/conus_tgw_1_16_deg_{scenario}/17'
    point_id = 208242 #0208228

    run_VIC(path_csv = path_csv, scenario = scenario, path_output = path_output, point_id = point_id)
'''