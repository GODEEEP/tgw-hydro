### Y.Son: generate VIC run folders (after calibration) by HUC2

import os, shutil, stat

model = 'TGW-WRF'

path_forcings = '/scratch/sony061/foresight/forcings/{HUC}/'

dict_config = {
    'STARTYEAR': 1992,
    'STARTMONTH': 1,
    'STARTDAY': 1,
    'ENDYEAR': 1992,
    'ENDMONTH': 12,
    'ENDDAY': 31,
    'DOMAIN': 'namerica_domain_HUC{HUC}.nc',
    'FORCING1': 'forcings/tgw_wrf_hist_{HUC}_00625vic_',
    'INIT_STATE': None,
    'STATENAME': None,
    'STATEYEAR': None,
    'STATEMONTH': None,
    'STATEDAY': None,
    'PARAMETERS': 'namerica_params_HUC{HUC}.nc',
    'OUTFILE': 'vic_runoff_HUC{HUC}_calib',
}

dict_slurm = {
    'cpus-per-task': 4,
#    'nodelist': 'dc238',
    'job-name': 'VIC-FINAL-{HUC}',
}

path_run = f'/scratch/sony061/foresight/calibration/{model}/finalrun'
path_params = os.path.join(f'/scratch/sony061/foresight/calibration/{model}', 'namerica_params_HUC{HUC}_calib.nc')
path_state = ''
fn_config = 'config.txt'
fn_slurm = 'run_vic.slurm'
fn_bash = 'batch_slurm.sh'

path_domain = '/scratch/sony061/foresight/domain/subset/namerica_domain_HUC{HUC}.nc'
path_out = 'vic_runoff_HUC{HUC}'

exec_vic = '/scratch/sony061/foresight/calibration/vic_image.exe'
tpl_config = '/scratch/sony061/foresight/calibration/tpl_config.txt'
tpl_slurm = '/scratch/sony061/foresight/calibration/tpl_run_vic.slurm'

for huc in range(1, 19):
    huc_str = f'{huc:02d}'
    path_huc = os.path.join(path_run, huc_str)
    os.makedirs(path_huc, exist_ok = True)
    shutil.copyfile(src = exec_vic, dst = os.path.join(path_huc, os.path.basename(exec_vic)))
    if os.path.islink(os.path.join(path_huc, dict_config['DOMAIN'].format(HUC = huc_str))): os.unlink(path = os.path.join(path_huc, dict_config['DOMAIN'].format(HUC = huc_str)))
    os.symlink(src = path_domain.format(HUC = huc_str), dst = os.path.join(path_huc, dict_config['DOMAIN'].format(HUC = huc_str)))
    if os.path.islink(os.path.join(path_huc, dict_config['PARAMETERS'].format(HUC = huc_str))): os.unlink(path = os.path.join(path_huc, dict_config['PARAMETERS'].format(HUC = huc_str)))
    os.symlink(src = path_params.format(HUC = huc_str), dst = os.path.join(path_huc, dict_config['PARAMETERS'].format(HUC = huc_str)))
    if dict_config['INIT_STATE'] is not None:
        if os.path.islink(os.path.join(path_huc, dict_config['INIT_STATE'].format(HUC = huc_str))): os.unlink(path = os.path.join(path_huc, dict_config['INIT_STATE'].format(HUC = huc_str)))
        os.symlink(src = path_state.format(HUC = huc_str), dst = os.path.join(path_huc, dict_config['INIT_STATE'].format(HUC = huc_str)))
    if os.path.islink(os.path.join(path_huc, os.path.dirname(dict_config['FORCING1']))): os.unlink(path = os.path.join(path_huc, os.path.dirname(dict_config['FORCING1'])))
    os.symlink(src = path_forcings.format(HUC = huc_str), dst = os.path.join(path_huc, os.path.dirname(dict_config['FORCING1'])))

    # vic configuration
    with open(tpl_config, mode = 'r') as f:
        lines = f.readlines()
    
    lines_ = lines.copy()
    for i, l in enumerate(lines):
        if len(l.split()) > 0:
            if l.split()[0] in dict_config.keys():
                if dict_config[l.split()[0]] is None: ll = '#' + l
                else:
                    idx_s = l.index(l.split()[1])
                    ll = l[:idx_s]
                    ll += str(dict_config[l.split()[0]]).format(HUC = huc_str)
                    if len(l.split()) > 2:
                        ll += ' ' * (l.index(l.split()[2]) - len(ll))
                        ll += l[l.index(l.split()[2]):]
                if not ll.endswith('\n'): ll += '\n'
                lines_[i] = ll

    with open(os.path.join(path_run, huc_str, fn_config), mode = 'w') as f:
        f.writelines(lines_)

    # slurm script
    with open(tpl_slurm, mode = 'r') as f:
        lines = f.readlines()
    
    lines_ = lines.copy()
    for i, l in enumerate(lines):
        if l.startswith('#SBATCH'):
            key = l.split('--')[1].split('=')[0]
            if key in dict_slurm.keys():
                lines_[i] = l.split('=')[0] + '=' + str(dict_slurm[key]).format(HUC = huc_str) + '\n'
        elif l.startswith('cd '):
            lines_[i] = 'cd ' + os.path.join(path_run, huc_str) + '\n'
        elif l.startswith('mpirun '):
            lines_[i] = f'mpirun -np {dict_slurm["cpus-per-task"]} ./{os.path.basename(exec_vic)} -g {fn_config} >& {os.path.splitext(fn_slurm)[0]}.log\n'

    with open(os.path.join(path_run, huc_str, fn_slurm), mode = 'w') as f:
        f.writelines(lines_)

    os.chmod(os.path.join(path_huc, os.path.basename(exec_vic)), os.stat(os.path.join(path_huc, os.path.basename(exec_vic))).st_mode | stat.S_IEXEC)
#    os.chmod(os.path.join(path_huc, fn_config), os.stat(os.path.join(path_huc, fn_config)).st_mode | stat.S_IEXEC)
#    os.chmod(os.path.join(path_huc, fn_slurm), os.stat(os.path.join(path_huc, fn_slurm)).st_mode | stat.S_IEXEC)

# slurm batch
with open(os.path.join(path_run, fn_bash), mode = 'w') as f:
    f.write('#!/bin/bash\n')
    for huc in range(1, 19):
        huc_str = f'{huc:02d}'
        f.write(f'sbatch {os.path.join(huc_str, fn_slurm)}\n')

#os.chmod(os.path.join(path_run, fn_bash), os.stat(os.path.join(path_run, fn_bash)).st_mode | stat.S_IEXEC)