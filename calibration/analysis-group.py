import os, glob, importlib
import numpy as np
import pandas as pd
import xarray as xr
import matplotlib.pyplot as plt
import cartopy.io.img_tiles
import cartopy.io.shapereader
import shapefile
import shapely

# set a date range of interest
#timespan = [pd.Timestamp('1983-01-01'), pd.Timestamp('1985-01-01')]
timespan = [pd.Timestamp('1981-01-01'), pd.Timestamp('1988-01-01')]

# set files to read
path_output = 'outputs_nse'
key = '08LD000' # '08LD000', '08FB002', '08MA001', '05CA000'
vic_output = 'vic_runoff.1979-01-01.nc'
valid_output = 'runoff_concat_16thdeg_*.nc'
force_input = 'forcings_6h_16thdeg_*.nc'
param_input = 'params_updated.nc'
costf_input = 'OSTGcopOut.txt'
path_shp, path_dbf = None, None

# set contourf scale properties
clim = [
    [0.001, 0.8], # infilt
    [1, 30], # Dsmax: [1, 30], ['-20%', '20%']
    [0, 1], # Ds
    [0.5, 1], # Ws
    [0.1, 2], # depth2
    [0.1, 2], # depth3
    [8, 30], # expt2: [8, 30], ['-20%', '20%']
    [8, 30], # expt3: [8, 30], ['-20%', '20%']
]

# load Canadian hydrometric station data
plot_obs = False
if plot_obs:
    hms = importlib.import_module('retrieve-ca-hms')
    station_id = '08LD003' # '08LD003', '08FB006', '08MA002', '05CA009'
    station = hms.HMS(identifier = station_id)
    df_hydro_daily_mean = station.retreive_daily_mean(begin_date = timespan[0], end_date = timespan[1])
    if df_hydro_daily_mean.empty:
        station_measure = 'Not Measured'
        station_scale = np.nan
        station_plot = pd.DataFrame([np.nan, np.nan], index = timespan)
    elif np.isfinite(df_hydro_daily_mean['LEVEL'].mean()):
        station_measure = 'Water Level'
        station_scale = 100
        station_plot = df_hydro_daily_mean['LEVEL']
    elif np.isfinite(df_hydro_daily_mean['DISCHARGE'].mean()):
        station_measure = 'Discharge'
        station_scale = 5
        station_plot = df_hydro_daily_mean['DISCHARGE']

# calculate NSE metric
def NSE(da_cal, da_obs):
    return 1 - ((da_cal - da_obs) ** 2).sum(dim = 'time') / ((da_obs - da_obs.mean(dim = 'time')) ** 2).sum(dim = 'time')

# calculate KGE metric, modified = False for original KGE and modified = True for modified KGE
def KGE(da_cal, da_obs, modified = True):
    r = xr.corr(da_cal, da_obs, dim = 'time')
    alpha = da_cal.std(dim = 'time') / da_obs.std(dim = 'time')
    beta = da_cal.mean(dim = 'time') / da_obs.mean(dim = 'time')
    if modified: var = alpha / beta
    else: var = alpha    
    return 1 - np.sqrt((r - 1) ** 2 + (beta - 1) ** 2 + (var - 1) ** 2)

# read shapefile
def read_shapefile(path_shp, path_dbf):
    shp, dbf = open(path_shp, 'rb'), open(path_dbf, 'rb')
    shpdbf = shapefile.Reader(shp = shp, dbf = dbf)
    shp_field = [x[0] for x in shpdbf.fields][1:]
    shp_records = [y[:] for y in shpdbf.records()]
    shp_points = [p.points for p in shpdbf.shapes()]
    df = pd.DataFrame(data = shp_records, columns = shp_field)
    df = df.assign(COORDS = shp_points)
    shp.close(); dbf.close()
    return df

# plot two countorf map side by side (e.g., before and after calibrations)
def plot_map_compare(list_da, shape = None, station_ll = None, baseMap = cartopy.io.img_tiles.OSM(), extent = None, vmin = -1, vmax = 1, cmap = 'PuOr', alpha = 0.7, suptitle = '', title = [], clabel = '', savefig = None):
    nplot = len(list_da)
    fig, axes = plt.subplots(ncols = nplot, figsize = (12, 8), subplot_kw = {'projection': baseMap.crs})
    fig.suptitle(suptitle)
    for i, ax in enumerate(axes.flat):
        ax.add_image(baseMap, 10)
        #ax.add_feature(shape)
        ax.add_geometries([shape], crs = cartopy.crs.PlateCarree(), edgecolor = 'r', linewidth = 1, facecolor = 'none')
        if extent is None: ax.set_extent([list_da[i]['lon'].min() - 0.1, list_da[i]['lon'].max() + 0.1, list_da[i]['lat'].min() - 0.1, list_da[i]['lat'].max() + 0.1])
        else: ax.set_extent(extent)
        fgl = ax.gridlines(crs = cartopy.crs.PlateCarree(), linestyle = '--', alpha = 0.25, draw_labels = True)
        fgl.top_labels, fgl.right_labels = False, False,
        fgl.xlabel_style, fgl.ylabel_style = {'color': 'gray', 'size': 8}, {'color': 'gray', 'size': 8}
        fda = list_da[i].plot(ax = ax, transform = cartopy.crs.PlateCarree(), vmin = vmin, vmax = vmax, cmap = cmap, alpha = alpha, add_colorbar = False)
        if station_ll is not None: ax.scatter([station_ll[0]], [station_ll[1]], c = 'red', marker = 'X', transform = cartopy.crs.PlateCarree())
        ax.set_title(title[i])
    fig.subplots_adjust(bottom = 0.1)
    cax = fig.add_axes([0.2, 0.06, 0.6, 0.03])
    fig.colorbar(fda, label = clabel, cax = cax, orientation = 'horizontal')
    fig.tight_layout(rect = [0, 0.1, 1, 1])
    if savefig is not None: plt.savefig(savefig, bbox_inches = 'tight')
    #plt.show()
    plt.close('all')
    return

# create temporary netcdf files that concatenate the input and output files to save time for the same runs
ncout_calib = os.path.join(path_output, '_{}_Daily_Output-Calib_{}-{}.nc'.format(key, timespan[0].strftime('%Y%m%d'), timespan[1].strftime('%Y%m%d')))
if not os.path.isfile(ncout_calib):
    files_calib = glob.glob(os.path.join(path_output, key, '**', 'mod0_calib', vic_output)); files_calib.sort()
    output_calib = xr.open_mfdataset(files_calib, chunks = {'time': -1}, decode_coords = 'all', parallel = True)
    output_calib = output_calib.where(output_calib['time'] >= timespan[0], drop = True).where(output_calib['time'] < timespan[1], drop = True).load()
    output_calib.to_netcdf(ncout_calib)
else: output_calib = xr.load_dataset(ncout_calib, decode_coords = 'all')
ncout_nocalib = os.path.join(path_output, '_{}_Daily_Output-NoCalib_{}-{}.nc'.format(key, timespan[0].strftime('%Y%m%d'), timespan[1].strftime('%Y%m%d')))
if not os.path.isfile(ncout_nocalib):
    files_nocalib = glob.glob(os.path.join(path_output, key, '**', 'nocalib', vic_output)); files_nocalib.sort()
    output_nocalib = xr.open_mfdataset(files_nocalib, chunks = {'time': -1}, decode_coords = 'all', parallel = True)
    output_nocalib = output_nocalib.where(output_nocalib['time'] >= timespan[0], drop = True).where(output_nocalib['time'] < timespan[1], drop = True).load()
    output_nocalib.to_netcdf(ncout_nocalib)
else: output_nocalib = xr.load_dataset(ncout_nocalib, decode_coords = 'all')
ncout_valid = os.path.join(path_output, '_{}_Daily_Runoff-Valid_{}-{}.nc'.format(key, timespan[0].strftime('%Y%m%d'), timespan[1].strftime('%Y%m%d')))
if not os.path.isfile(ncout_valid):
    files_valid = glob.glob(os.path.join(path_output, key, '**', 'input_symln', valid_output)); files_valid.sort()
    runoff_valid = xr.open_mfdataset(files_valid, decode_coords = 'all', parallel = True)
    runoff_valid = runoff_valid['ro'].where(runoff_valid['time'] >= timespan[0], drop = True).where(runoff_valid['time'] < timespan[1], drop = True).load()
    runoff_valid.to_netcdf(ncout_valid)
else: runoff_valid = xr.load_dataarray(ncout_valid, decode_coords = 'all')
ncout_forcing = os.path.join(path_output, '_{}_Daily_Forcing-TGW_{}-{}.nc'.format(key, timespan[0].strftime('%Y%m%d'), timespan[1].strftime('%Y%m%d')))
if not os.path.isfile(ncout_forcing):
    files_forcing = glob.glob(os.path.join(path_output, key, '**', 'input_symln', force_input)); files_forcing.sort()
    forcing_tgw = xr.open_mfdataset(files_forcing, decode_coords = 'all', parallel = True).drop_duplicates(dim = 'time')
    forcing_tgw = forcing_tgw['PRECIP'].where(forcing_tgw['time'] >= timespan[0], drop = True).where(forcing_tgw['time'] < timespan[1], drop = True).load()
    forcing_tgw.to_netcdf(ncout_forcing)
else: forcing_tgw = xr.load_dataarray(ncout_forcing, decode_coords = 'all')
ncout_param_calib, ncout_param_nocalib = os.path.join(path_output, '_{}_Param-Calib.nc'.format(key)), os.path.join(path_output, '_{}_Param-NoCalib.nc'.format(key))
if not os.path.isfile(ncout_param_calib) or not os.path.isfile(ncout_param_nocalib):
    files_param = glob.glob(os.path.join(path_output, key, '**', 'mod0_calib', param_input)); files_param.sort()
    param_calib = xr.open_mfdataset(files_param, decode_coords = 'all', parallel = True)
    param_calib.to_netcdf(ncout_param_calib)
    files_param = glob.glob(os.path.join(path_output, key, '**', 'nocalib', param_input)); files_param.sort()
    param_nocalib = xr.open_mfdataset(files_param, decode_coords = 'all', parallel = True)
    param_nocalib.to_netcdf(ncout_param_nocalib)
else:
    param_calib = xr.open_dataset(ncout_param_calib, decode_coords = 'all')
    param_nocalib = xr.open_dataset(ncout_param_nocalib, decode_coords = 'all')
files_costf = glob.glob(os.path.join(path_output, key, '**', 'mod0_calib', costf_input)); files_costf.sort()
list_costf = []
for f in files_costf:
    df = pd.read_csv(f, header = 0, delimiter = '\t')['True Cost ']
    df.name = f.split(key)[1][1:8]
    list_costf.append(df)
df_costf = pd.concat(list_costf, axis = 1)

# resample daily/weekly(7-day)/monthly
runoff_calib_1d = (output_calib['OUT_RUNOFF'] + output_calib['OUT_BASEFLOW']).resample(time = '1D').sum(skipna = False)
runoff_calib_7d = (output_calib['OUT_RUNOFF'] + output_calib['OUT_BASEFLOW']).resample(time = '7D').sum(skipna = False)
runoff_calib_ms = (output_calib['OUT_RUNOFF'] + output_calib['OUT_BASEFLOW']).resample(time = 'MS').sum(skipna = False)
runoff_nocalib_1d = (output_nocalib['OUT_RUNOFF'] + output_nocalib['OUT_BASEFLOW']).resample(time = '1D').sum(skipna = False)
runoff_nocalib_7d = (output_nocalib['OUT_RUNOFF'] + output_nocalib['OUT_BASEFLOW']).resample(time = '7D').sum(skipna = False)
runoff_nocalib_ms = (output_nocalib['OUT_RUNOFF'] + output_nocalib['OUT_BASEFLOW']).resample(time = 'MS').sum(skipna = False)
evap_calib_1d = output_calib['OUT_EVAP'].resample(time = '1D').sum(skipna = False)
evap_calib_7d = output_calib['OUT_EVAP'].resample(time = '7D').sum(skipna = False)
evap_calib_ms = output_calib['OUT_EVAP'].resample(time = 'MS').sum(skipna = False)
evap_nocalib_1d = output_nocalib['OUT_EVAP'].resample(time = '1D').sum(skipna = False)
evap_nocalib_7d = output_nocalib['OUT_EVAP'].resample(time = '7D').sum(skipna = False)
evap_nocalib_ms = output_nocalib['OUT_EVAP'].resample(time = 'MS').sum(skipna = False)
snow_calib_1d = output_calib['OUT_SWE'].resample(time = '1D').sum(skipna = False) 
snow_calib_7d = output_calib['OUT_SWE'].resample(time = '7D').sum(skipna = False)
snow_calib_ms = output_calib['OUT_SWE'].resample(time = 'MS').sum(skipna = False)
snow_nocalib_1d = output_nocalib['OUT_SWE'].resample(time = '1D').sum(skipna = False)
snow_nocalib_7d = output_nocalib['OUT_SWE'].resample(time = '7D').sum(skipna = False)
snow_nocalib_ms = output_nocalib['OUT_SWE'].resample(time = 'MS').sum(skipna = False)
runoff_valid_1d = runoff_valid.resample(time = '1D').sum(skipna = False)
runoff_valid_7d = runoff_valid.resample(time = '7D').sum(skipna = False)
runoff_valid_ms = runoff_valid.resample(time = 'MS').sum(skipna = False)
forcing_tgw_1d = forcing_tgw.resample(time = '1D').sum(skipna = False)
forcing_tgw_7d = forcing_tgw.resample(time = '7D').sum(skipna = False)
forcing_tgw_ms = forcing_tgw.resample(time = 'MS').sum(skipna = False)
if plot_obs:
    station_1d = station_plot.resample('1D').sum() * station_scale
    station_7d = station_plot.resample('7D').sum() * station_scale
    station_ms = station_plot.resample('MS').sum() * station_scale

# sum over watersheds
runoff_calib_1d_llsum = runoff_calib_1d.sum(dim = ['lon', 'lat'])
runoff_calib_7d_llsum = runoff_calib_7d.sum(dim = ['lon', 'lat'])
runoff_calib_ms_llsum = runoff_calib_ms.sum(dim = ['lon', 'lat'])
runoff_nocalib_1d_llsum = runoff_nocalib_1d.sum(dim = ['lon', 'lat'])
runoff_nocalib_7d_llsum = runoff_nocalib_7d.sum(dim = ['lon', 'lat'])
runoff_nocalib_ms_llsum = runoff_nocalib_ms.sum(dim = ['lon', 'lat'])
evap_calib_1d_llsum = evap_calib_1d.sum(dim = ['lon', 'lat']) / 10
evap_calib_7d_llsum = evap_calib_7d.sum(dim = ['lon', 'lat']) / 10
evap_calib_ms_llsum = evap_calib_ms.sum(dim = ['lon', 'lat']) / 10
evap_nocalib_1d_llsum = evap_nocalib_1d.sum(dim = ['lon', 'lat']) / 10
evap_nocalib_7d_llsum = evap_nocalib_7d.sum(dim = ['lon', 'lat']) / 10
evap_nocalib_ms_llsum = evap_nocalib_ms.sum(dim = ['lon', 'lat']) / 10
snow_calib_1d_llsum = snow_calib_1d.sum(dim = ['lon', 'lat']) / 100
snow_calib_7d_llsum = snow_calib_7d.sum(dim = ['lon', 'lat']) / 100
snow_calib_ms_llsum = snow_calib_ms.sum(dim = ['lon', 'lat']) / 100
snow_nocalib_1d_llsum = snow_nocalib_1d.sum(dim = ['lon', 'lat']) / 100
snow_nocalib_7d_llsum = snow_nocalib_7d.sum(dim = ['lon', 'lat']) / 100
snow_nocalib_ms_llsum = snow_nocalib_ms.sum(dim = ['lon', 'lat']) / 100
runoff_valid_1d_llsum = runoff_valid_1d.sum(dim = ['lon', 'lat'])
runoff_valid_7d_llsum = runoff_valid_7d.sum(dim = ['lon', 'lat'])
runoff_valid_ms_llsum = runoff_valid_ms.sum(dim = ['lon', 'lat'])
forcing_tgw_1d_llsum = forcing_tgw_1d.sum(dim = ['lon', 'lat'])
forcing_tgw_7d_llsum = forcing_tgw_7d.sum(dim = ['lon', 'lat'])
forcing_tgw_ms_llsum = forcing_tgw_ms.sum(dim = ['lon', 'lat'])

# plot water balance comparisons - daily/weekly(7-day)/monthly
fig, ax = plt.subplots(nrows = 3, ncols = 1, figsize = (16, 8))
# plot daily comparisons
ax[0].plot(runoff_valid_1d['time'], runoff_valid_1d_llsum, label = 'ReachHydro')
ax[0].plot(runoff_nocalib_1d['time'], runoff_nocalib_1d_llsum, label = 'VICGlobal w/o Calibration')
ax[0].plot(runoff_calib_1d['time'], runoff_calib_1d_llsum, label = 'VICGlobal w/ Calibration')
if plot_obs: ax[0].plot(station_1d, '--', label = '{} at Station {} (x{})'.format(station_measure, station_id, station_scale))
ax[0].plot(evap_nocalib_ms['time'], evap_nocalib_ms_llsum, ':', label = 'Evaporation w/o Calibration (/10)')
ax[0].plot(evap_calib_ms['time'], evap_calib_ms_llsum, ':', label = 'Evaporation w/ Calibration (/10)')
ax[0].plot(snow_nocalib_1d['time'], snow_nocalib_1d_llsum, '-.', label = 'Snow Water Equiv. w/o Calibration (/100)')
ax[0].plot(snow_calib_1d['time'], snow_calib_1d_llsum, '-.', label = 'Snow Water Equiv. w/ Calibration (/100)')
ax0_twin = ax[0].twinx()
ax0_twin.bar(forcing_tgw_1d['time'], forcing_tgw_1d_llsum, color = 'r', width = pd.Timedelta('16h'), alpha = 0.25)
ax0_twin.invert_yaxis()
ax[0].set_title('Daily Runoff & Precipitation Total for Workout {}'.format(key) + '\n' + 'NSE: {:.3f} \u2192 {:.3f}'.format(NSE(runoff_nocalib_1d_llsum, runoff_valid_1d_llsum), NSE(runoff_calib_1d_llsum, runoff_valid_1d_llsum)) + ', KGE: {:.3f} \u2192 {:.3f}'.format(KGE(runoff_nocalib_1d_llsum, runoff_valid_1d_llsum), KGE(runoff_calib_1d_llsum, runoff_valid_1d_llsum)))
# plot weekly(7-day) comparisons
ax[1].plot(runoff_valid_7d['time'], runoff_valid_7d_llsum, label = 'ReachHydro')
ax[1].plot(runoff_nocalib_7d['time'], runoff_nocalib_7d_llsum, label = 'VICGlobal w/o Calibration')
ax[1].plot(runoff_calib_7d['time'], runoff_calib_7d_llsum, label = 'VICGlobal w/ Calibration')
if plot_obs: ax[1].plot(station_7d, '--', label = '{} at Station {} (x{})'.format(station_measure, station_id, station_scale))
ax[1].plot(evap_nocalib_ms['time'], evap_nocalib_ms_llsum, ':', label = 'Evaporation w/o Calibration (/10)')
ax[1].plot(evap_calib_ms['time'], evap_calib_ms_llsum, ':', label = 'Evaporation w/ Calibration (/10)')
ax[1].plot(snow_nocalib_7d['time'], snow_nocalib_7d_llsum, '-.', label = 'Snow Water Equiv. w/o Calibration (/100)')
ax[1].plot(snow_calib_7d['time'], snow_calib_7d_llsum, '-.', label = 'Snow Water Equiv. w/ Calibration (/100)')
ax1_twin = ax[1].twinx()
ax1_twin.bar(forcing_tgw_7d['time'], forcing_tgw_7d_llsum, color = 'r', width = pd.Timedelta('4d'), alpha = 0.25)
ax1_twin.invert_yaxis()
ax[1].set_title('7-day Runoff & Precipitation Total for Workout {}'.format(key) + '\n' + 'NSE: {:.3f} \u2192 {:.3f}'.format(NSE(runoff_nocalib_7d_llsum, runoff_valid_7d_llsum), NSE(runoff_calib_7d_llsum, runoff_valid_7d_llsum)) + ', KGE: {:.3f} \u2192 {:.3f}'.format(KGE(runoff_nocalib_7d_llsum, runoff_valid_7d_llsum), KGE(runoff_calib_7d_llsum, runoff_valid_7d_llsum)))
# plot monthly comparisons
ax[2].plot(runoff_valid_ms['time'], runoff_valid_ms_llsum, label = 'ReachHydro')
ax[2].plot(runoff_nocalib_ms['time'], runoff_nocalib_ms_llsum, label = 'VICGlobal w/o Calibration')
ax[2].plot(runoff_calib_ms['time'], runoff_calib_ms_llsum, label = 'VICGlobal w/ Calibration')
if plot_obs: ax[2].plot(station_ms, '--', label = '{} at Station {} (x{})'.format(station_measure, station_id, station_scale))
ax[2].plot(evap_nocalib_ms['time'], evap_nocalib_ms_llsum, ':', label = 'Evaporation w/o Calibration (/10)')
ax[2].plot(evap_calib_ms['time'], evap_calib_ms_llsum, ':', label = 'Evaporation w/ Calibration (/10)')
ax[2].plot(snow_nocalib_ms['time'], snow_nocalib_ms_llsum, '-.', label = 'Snow Water Equiv. w/o Calibration (/100)')
ax[2].plot(snow_calib_ms['time'], snow_calib_ms_llsum, '-.', label = 'Snow Water Equiv. w/ Calibration (/100)')
ax2_twin = ax[2].twinx()
ax2_twin.bar(forcing_tgw_ms['time'], forcing_tgw_ms_llsum, color = 'r', width = pd.Timedelta('20d'), alpha = 0.25)
ax2_twin.invert_yaxis()
ax[2].set_title('Monthly Runoff & Precipitation Total for Workout {}'.format(key) + '\n' + 'NSE: {:.3f} \u2192 {:.3f}'.format(NSE(runoff_nocalib_ms_llsum, runoff_valid_ms_llsum), NSE(runoff_calib_ms_llsum, runoff_valid_ms_llsum)) + ', KGE: {:.3f} \u2192 {:.3f}'.format(KGE(runoff_nocalib_ms_llsum, runoff_valid_ms_llsum), KGE(runoff_calib_ms_llsum, runoff_valid_ms_llsum)))
for a in ax.flat: a.grid()

fig.subplots_adjust(bottom = 0.07)
handles, labels = ax[0].get_legend_handles_labels()
fig.legend(handles, labels, ncol = 4, loc = 'lower center', bbox_to_anchor = (0, 0.01, 1, 0.02))
fig.tight_layout(rect = [0, 0.07, 1, 1])

plt.savefig(os.path.join(path_output, '{}-RunoffTotal.png'.format(key)))
#plt.show()
plt.close('all')

# calculate NSE and KGE metrics
NSE_calib_1d = NSE(runoff_calib_1d, runoff_valid_1d); KGE_calib_1d = KGE(runoff_calib_1d, runoff_valid_1d, modified = True)
NSE_calib_7d = NSE(runoff_calib_7d, runoff_valid_7d); KGE_calib_7d = KGE(runoff_calib_7d, runoff_valid_7d, modified = True)
NSE_calib_ms = NSE(runoff_calib_ms, runoff_valid_ms); KGE_calib_ms = KGE(runoff_calib_ms, runoff_valid_ms, modified = True)
NSE_nocalib_1d = NSE(runoff_nocalib_1d, runoff_valid_1d); KGE_nocalib_1d = KGE(runoff_nocalib_1d, runoff_valid_1d, modified = True)
NSE_nocalib_7d = NSE(runoff_nocalib_7d, runoff_valid_7d); KGE_nocalib_7d = KGE(runoff_nocalib_7d, runoff_valid_7d, modified = True)
NSE_nocalib_ms = NSE(runoff_nocalib_ms, runoff_valid_ms); KGE_nocalib_ms = KGE(runoff_nocalib_ms, runoff_valid_ms, modified = True)

if path_shp is not None and path_dbf is not None:
    df = read_shapefile(path_shp, path_dbf)
    shape = shapely.geometry.Polygon(df.loc[df['DATASETNAM'] == key, 'COORDS'].iloc[0])

if plot_obs: station_ll = [station.lon, station.lat]
else: station_ll = None

# plot spatial distributions of NSE and KGE - daily/weekly(7-day)/monthly
plot_map_compare(list_da = [NSE_nocalib_1d, NSE_calib_1d], shape = shape, station_ll = station_ll, baseMap = cartopy.io.img_tiles.OSM(), vmin = -1, vmax = 1, cmap = 'PuOr', alpha = 0.7, suptitle = 'Daily Runoff NSE for Workout {}'.format(key),
                title = ['w/o Calibration: {:.3f}/{:.3f}/{:.3f} (Q25/Q50/Q75)'.format(NSE_nocalib_1d.quantile(0.25), NSE_nocalib_1d.quantile(0.5), NSE_nocalib_1d.quantile(0.75)), 'w/ Calibration: {:.3f}/{:.3f}/{:.3f} (Q25/Q50/Q75)'.format(NSE_calib_1d.quantile(0.25), NSE_calib_1d.quantile(0.5), NSE_calib_1d.quantile(0.75))],
                clabel = 'Nash-Sutcliffe Efficiency', savefig = os.path.join(path_output, '{}-NSE-Daily.png'.format(key)))
plot_map_compare(list_da = [NSE_nocalib_7d, NSE_calib_7d], shape = shape, station_ll = station_ll, baseMap = cartopy.io.img_tiles.OSM(), vmin = -1, vmax = 1, cmap = 'PuOr', alpha = 0.7, suptitle = '7-Day Runoff NSE for Workout {}'.format(key),
                title = ['w/o Calibration: {:.3f}/{:.3f}/{:.3f} (Q25/Q50/Q75)'.format(NSE_nocalib_7d.quantile(0.25), NSE_nocalib_7d.quantile(0.5), NSE_nocalib_7d.quantile(0.75)), 'w/ Calibration: {:.3f}/{:.3f}/{:.3f} (Q25/Q50/Q75)'.format(NSE_calib_7d.quantile(0.25), NSE_calib_7d.quantile(0.5), NSE_calib_7d.quantile(0.75))],
                clabel = 'Nash-Sutcliffe Efficiency', savefig = os.path.join(path_output, '{}-NSE-7Day.png'.format(key)))
plot_map_compare(list_da = [NSE_nocalib_ms, NSE_calib_ms], shape = shape, station_ll = station_ll, baseMap = cartopy.io.img_tiles.OSM(), vmin = -1, vmax = 1, cmap = 'PuOr', alpha = 0.7, suptitle = 'Monthly Runoff NSE for Workout {}'.format(key),
                title = ['w/o Calibration: {:.3f}/{:.3f}/{:.3f} (Q25/Q50/Q75)'.format(NSE_nocalib_ms.quantile(0.25), NSE_nocalib_ms.quantile(0.5), NSE_nocalib_ms.quantile(0.75)), 'w/ Calibration: {:.3f}/{:.3f}/{:.3f} (Q25/Q50/Q75)'.format(NSE_calib_ms.quantile(0.25), NSE_calib_ms.quantile(0.5), NSE_calib_ms.quantile(0.75))],
                clabel = 'Nash-Sutcliffe Efficiency', savefig = os.path.join(path_output, '{}-NSE-Monthly.png'.format(key)))
plot_map_compare(list_da = [KGE_nocalib_1d, KGE_calib_1d], shape = shape, station_ll = station_ll, baseMap = cartopy.io.img_tiles.OSM(), vmin = -1, vmax = 1, cmap = 'PuOr', alpha = 0.7, suptitle = "Daily Runoff KGE' for Workout {}".format(key),
                title = ['w/o Calibration: {:.3f}/{:.3f}/{:.3f} (Q25/Q50/Q75)'.format(KGE_nocalib_1d.quantile(0.25), KGE_nocalib_1d.quantile(0.5), KGE_nocalib_1d.quantile(0.75)), 'w/ Calibration: {:.3f}/{:.3f}/{:.3f} (Q25/Q50/Q75)'.format(KGE_calib_1d.quantile(0.25), KGE_calib_1d.quantile(0.5), KGE_calib_1d.quantile(0.75))],
                clabel = 'Kling-Gupta Efficiency', savefig = os.path.join(path_output, '{}-KGE-Daily.png'.format(key)))
plot_map_compare(list_da = [KGE_nocalib_7d, KGE_calib_7d], shape = shape, station_ll = station_ll, baseMap = cartopy.io.img_tiles.OSM(), vmin = -1, vmax = 1, cmap = 'PuOr', alpha = 0.7, suptitle = "7-Day Runoff KGE' for Workout {}".format(key),
                title = ['w/o Calibration: {:.3f}/{:.3f}/{:.3f} (Q25/Q50/Q75)'.format(KGE_nocalib_7d.quantile(0.25), KGE_nocalib_7d.quantile(0.5), KGE_nocalib_7d.quantile(0.75)), 'w/ Calibration: {:.3f}/{:.3f}/{:.3f} (Q25/Q50/Q75)'.format(KGE_calib_7d.quantile(0.25), KGE_calib_7d.quantile(0.5), KGE_calib_7d.quantile(0.75))],
                clabel = 'Kling-Gupta Efficiency', savefig = os.path.join(path_output, '{}-KGE-7Day.png'.format(key)))
plot_map_compare(list_da = [KGE_nocalib_ms, KGE_calib_ms], shape = shape, station_ll = station_ll, baseMap = cartopy.io.img_tiles.OSM(), vmin = -1, vmax = 1, cmap = 'PuOr', alpha = 0.7, suptitle = "Monthly Runoff KGE' for Workout {}".format(key),
                title = ['w/o Calibration: {:.3f}/{:.3f}/{:.3f} (Q25/Q50/Q75)'.format(KGE_nocalib_ms.quantile(0.25), KGE_nocalib_ms.quantile(0.5), KGE_nocalib_ms.quantile(0.75)), 'w/ Calibration: {:.3f}/{:.3f}/{:.3f} (Q25/Q50/Q75)'.format(KGE_calib_ms.quantile(0.25), KGE_calib_ms.quantile(0.5), KGE_calib_ms.quantile(0.75))],
                clabel = 'Kling-Gupta Efficiency', savefig = os.path.join(path_output, '{}-KGE-Monthly.png'.format(key)))

# plot spatial distributions of water balance - runoff/baseflow/evaporation/snow water/precipitation
da_plot1, da_plot2 = output_nocalib['OUT_RUNOFF'].resample(time = 'MS').sum(skipna = False).mean(dim = 'time'), output_calib['OUT_RUNOFF'].resample(time = 'MS').sum(skipna = False).mean(dim = 'time')
plot_map_compare(list_da = [da_plot1, da_plot2], shape = shape, station_ll = station_ll, baseMap = cartopy.io.img_tiles.OSM(), vmin = np.minimum(da_plot1.min(), da_plot2.min()), vmax = np.maximum(da_plot1.max(), da_plot2.max()), cmap = 'Blues', alpha = 0.7, suptitle = 'Average Monthly Surface Runoff Total for Workout {}'.format(key), title = ['w/o Calibration', 'w/ Calibration'],
                clabel = 'Average Monthly Surface Runoff Total [mm]', savefig = os.path.join(path_output, '{}-OUT-RUNOFF-AverageMonthlyTotal.png'.format(key)))
da_plot1, da_plot2 = output_nocalib['OUT_BASEFLOW'].resample(time = 'MS').sum(skipna = False).mean(dim = 'time'), output_calib['OUT_BASEFLOW'].resample(time = 'MS').sum(skipna = False).mean(dim = 'time')
plot_map_compare(list_da = [da_plot1, da_plot2], shape = shape, station_ll = station_ll, baseMap = cartopy.io.img_tiles.OSM(), vmin = np.minimum(da_plot1.min(), da_plot2.min()), vmax = np.maximum(da_plot1.max(), da_plot2.max()), cmap = 'Blues', alpha = 0.7, suptitle = 'Average Monthly Baseflow Total for Workout {}'.format(key), title = ['w/o Calibration', 'w/ Calibration'],
                clabel = 'Average Monthly Baseflow Total [mm]', savefig = os.path.join(path_output, '{}-OUT-BASEFLOW-AverageMonthlyTotal.png'.format(key)))
plot_map_compare(list_da = [evap_nocalib_ms.mean(dim = 'time'), evap_calib_ms.mean(dim = 'time')], shape = shape, station_ll = station_ll, baseMap = cartopy.io.img_tiles.OSM(), vmin = np.minimum(evap_nocalib_ms.mean(dim = 'time').min(), evap_calib_ms.mean(dim = 'time').min()), vmax = np.maximum(evap_nocalib_ms.mean(dim = 'time').max(), evap_calib_ms.mean(dim = 'time').max()), cmap = 'Blues', alpha = 0.7, suptitle = 'Average Net Evaporation Total for Workout {}'.format(key), title = ['w/o Calibration', 'w/ Calibration'],
                clabel = 'Average Monthly Net Evaporation Total [mm]', savefig = os.path.join(path_output, '{}-OUT-EVAP-AverageMonthlyTotal.png'.format(key)))
plot_map_compare(list_da = [snow_nocalib_ms.mean(dim = 'time'), snow_calib_ms.mean(dim = 'time')], shape = shape, station_ll = station_ll, baseMap = cartopy.io.img_tiles.OSM(), vmin = np.minimum(snow_nocalib_ms.mean(dim = 'time').min(), snow_calib_ms.mean(dim = 'time').min()), vmax = np.maximum(snow_nocalib_ms.mean(dim = 'time').max(), snow_calib_ms.mean(dim = 'time').max()), cmap = 'Blues', alpha = 0.7, suptitle = 'Average Monthly Snow Water Equiv. Total for Workout {}'.format(key), title = ['w/o Calibration', 'w/ Calibration'],
                clabel = 'Average Monthly Snow Water Equiv. Total [mm]', savefig = os.path.join(path_output, '{}-OUT-SWE-AverageMonthlyTotal.png'.format(key)))
plot_map_compare(list_da = [forcing_tgw_ms.mean(dim = 'time'), forcing_tgw_ms.mean(dim = 'time') * np.nan], shape = shape, station_ll = station_ll, baseMap = cartopy.io.img_tiles.GoogleTiles(style = 'satellite'), vmin = forcing_tgw_ms.mean(dim = 'time').min(), vmax = forcing_tgw_ms.mean(dim = 'time').max(), cmap = 'Blues', alpha = 0.7, suptitle = 'Average Monthly Precipitation Total for Workout {}'.format(key), title = ['Precipitation', 'Satellite Map'],
                clabel = 'Average Monthly Precipitation Total [mm]', savefig = os.path.join(path_output, '{}-IN-PRECIP-AverageMonthlyTotal.png'.format(key)))

# plot spatial distributions of input parameters - infilt/Dsmax/Ds/Ws/depth1/depth2/expt1/expt2
plot_map_compare(list_da = [param_nocalib['infilt'], param_calib['infilt']], shape = shape, station_ll = station_ll, baseMap = cartopy.io.img_tiles.OSM(), vmin = clim[0][0], vmax = clim[0][1], cmap = 'plasma_r', alpha = 0.7, suptitle = 'infilt: Variable Infiltration Curve Parameter', title = ['w/o Calibration', 'w/ Calibration'],
                clabel = 'Variable infiltration curve parameter (binfilt)', savefig = os.path.join(path_output, '{}-Param-1infilt.png'.format(key)))
plot_map_compare(list_da = [param_nocalib['Dsmax'], param_calib['Dsmax']], shape = shape, station_ll = station_ll, baseMap = cartopy.io.img_tiles.OSM(), vmin = clim[1][0], vmax = clim[1][1], cmap = 'plasma_r', alpha = 0.7, suptitle = 'Dsmax: Maximum Velocity of Baseflow', title = ['w/o Calibration', 'w/ Calibration'],
                clabel = 'Maximum velocity of baseflow [mm/day]', savefig = os.path.join(path_output, '{}-Param-2Dsmax.png'.format(key)))
plot_map_compare(list_da = [param_nocalib['Ds'], param_calib['Ds']], shape = shape, station_ll = station_ll, baseMap = cartopy.io.img_tiles.OSM(), vmin = clim[2][0], vmax = clim[2][1], cmap = 'plasma_r', alpha = 0.7, suptitle = 'Ds: Fraction of Dsmax where Non-linear Baseflow Begins', title = ['w/o Calibration', 'w/ Calibration'],
                clabel = 'Fraction of Dsmax where non-linear baseflow begins', savefig = os.path.join(path_output, '{}-Param-3Ds.png'.format(key)))
plot_map_compare(list_da = [param_nocalib['Ws'], param_calib['Ws']], shape = shape, station_ll = station_ll, baseMap = cartopy.io.img_tiles.OSM(), vmin = clim[3][0], vmax = clim[3][1], cmap = 'plasma_r', alpha = 0.7, suptitle = 'Ws: Fraction of Maximum Soil Moisture where Non-linear Baseflow Occurs', title = ['w/o Calibration', 'w/ Calibration'],
                clabel = 'Fraction of maximum soil moisture where non-linear baseflow occurs', savefig = os.path.join(path_output, '{}-Param-4Ws.png'.format(key)))
plot_map_compare(list_da = [param_nocalib['depth'].sel(nlayer = 1), param_calib['depth'].sel(nlayer = 1)], shape = shape, station_ll = station_ll, baseMap = cartopy.io.img_tiles.OSM(), vmin = clim[4][0], vmax = clim[4][1], cmap = 'plasma_r', alpha = 0.7, suptitle = 'depth2: Thickness of 2nd Soil Moisture Layer', title = ['w/o Calibration', 'w/ Calibration'],
                clabel = 'Thickness of 2nd soil moisture layer [m]', savefig = os.path.join(path_output, '{}-Param-5depth2.png'.format(key)))
plot_map_compare(list_da = [param_nocalib['depth'].sel(nlayer = 2), param_calib['depth'].sel(nlayer = 2)], shape = shape, station_ll = station_ll, baseMap = cartopy.io.img_tiles.OSM(), vmin = clim[5][0], vmax = clim[5][1], cmap = 'plasma_r', alpha = 0.7, suptitle = 'depth3: Thickness of 3rd Soil Moisture Layer', title = ['w/o Calibration', 'w/ Calibration'],
                clabel = 'Thickness of 3rd soil moisture layer [m]', savefig = os.path.join(path_output, '{}-Param-6depth3.png'.format(key)))
plot_map_compare(list_da = [param_nocalib['expt'].sel(nlayer = 1), param_calib['expt'].sel(nlayer = 1)], shape = shape, station_ll = station_ll, baseMap = cartopy.io.img_tiles.OSM(), vmin = clim[6][0], vmax = clim[6][1], cmap = 'plasma_r', alpha = 0.7, suptitle = "expt2: Exponent n (=3+2/lambda) in Campbell's Eqn for Hydraulic Conductivity", title = ['w/o Calibration', 'w/ Calibration'],
                clabel = "Exponent n (=3+2/lambda) in Campbell's eqn for hydraulic conductivity", savefig = os.path.join(path_output, '{}-Param-7expt2.png'.format(key)))
plot_map_compare(list_da = [param_nocalib['expt'].sel(nlayer = 2), param_calib['expt'].sel(nlayer = 2)], shape = shape, station_ll = station_ll, baseMap = cartopy.io.img_tiles.OSM(), vmin = clim[7][0], vmax = clim[7][1], cmap = 'plasma_r', alpha = 0.7, suptitle = "expt3: Exponent n (=3+2/lambda) in Campbell's Eqn for Hydraulic Conductivity", title = ['w/o Calibration', 'w/ Calibration'],
                clabel = "Exponent n (=3+2/lambda) in Campbell's eqn for hydraulic conductivity", savefig = os.path.join(path_output, '{}-Param-8expt3.png'.format(key)))

# plot cost functions
fig, ax = plt.subplots(figsize = (10, 6))
for c, df in df_costf.items(): ax.plot(df.index, df, 'gray', alpha = 0.3)
ax.plot(df.index, df_costf.mean(axis = 1), 'b')
ax.set_title('Cost Functions')
ax.set_xlabel('# of Attempts'); ax.set_ylabel('True Cost')
ax.set_xlim([0, 100]); ax.set_ylim([-1, 3]); ax.grid()
#ax.set_xlim([0, 100]); ax.set_ylim([0, 1]); ax.grid()
fig.tight_layout()
plt.savefig(os.path.join(path_output, '{}-CostFunction.png'.format(key)))
#plt.show()
plt.close('all')