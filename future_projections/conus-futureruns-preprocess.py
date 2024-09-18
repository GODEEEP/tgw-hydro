import os, glob, shutil
import pandas as pd

vic_input_dir = '/vast/projects/godeeep/VIC/inputs_1_16_deg_by_huc2/'
vic_calib_dir = '/vast/projects/godeeep/VIC/calibration/'

def check_missing_files(path_csv):
    grid_ids = pd.read_csv(path_csv)

    f0 = open('calib_no_input.txt', 'w')
    f1 = open('calib_no_dirs.txt', 'w')
    f2 = open('calib_no_params.txt', 'w')
    f3 = open('calib_no_runs.txt', 'w')
    for _, cell in grid_ids.iterrows():
        i = int(cell.id)
        huc2_code = int(cell.huc2)
        lat = cell.lat
        lon = cell.lon

        path_dir_symln = os.path.join(vic_input_dir, f'{huc2_code:02}', f'{i:07}_{lon}_{lat}')
        if not os.path.isdir(path_dir_symln):
            #print(f'{path_dir_symln}: No Input Directory!')
            f0.write(path_dir_symln + '\n')

        path_dir = os.path.join(vic_calib_dir, f'{huc2_code:02}', f'{i:07}_{lon}_{lat}')
        if not os.path.isdir(path_dir):
            #print(f'{path_dir}: No Calibration Directory!')
            f1.write(path_dir + '\n')
        else:
            path_file = os.path.join(path_dir, 'params_updated.nc')
            if not os.path.isfile(path_file):
                #print(f'{path_file}: No Calibration Input!')
                f2.write(path_file + '\n')

            path_file = os.path.join(path_dir, 'vic_runoff.1979-01-01.nc')
            if not os.path.isfile(path_file):
                #print(f'{path_file}: No Vic Run!')
                f3.write(path_file + '\n')
    f0.close()
    f1.close()
    f2.close()
    f3.close()

    return

def pre_process(path_csv, key, path_run):
    grid_ids = pd.read_csv(path_csv)
    
    for _, cell in grid_ids.iterrows():
        i = int(cell.id)
        huc2_code = int(cell.huc2)
        lat = cell.lat
        lon = cell.lon
        
        # set id paths
        id_ll = f'{i:07}_{lon:0.5f}_{lat:0.5f}'

        path_run_id = os.path.join(path_run, f'{huc2_code:02}', id_ll)
        path_input_id = os.path.join(vic_input_dir, f'{huc2_code:02}', id_ll)

        # move forcing files into input directory
        path_from = os.path.join(path_run_id, f'forcings_6h_16thdeg_{id_ll}_*.nc')
        print(f'FROM: {path_from}')
        files = glob.glob(path_from)
        files.sort()

        path_to = os.path.join(path_input_id, key)
        print(f'TO: {path_to}')
        os.makedirs(path_to, exist_ok = True)
        for f in files:
            shutil.move(f, path_to)

    return

if __name__ == '__main__':
    path_csv = './data/grid_ids_conus.csv'
#    check_missing_files(path_csv = path_csv)

    #key = 'rcp45cooler'
    #key = 'rcp45hotter'
    #key = 'rcp85cooler'
    key = 'rcp85hotter'
    path_run = f'/vast/projects/godeeep/VIC/future_projections/conus_tgw_1_16_deg_{key}/'
    pre_process(path_csv = path_csv, key = key, path_run = path_run)