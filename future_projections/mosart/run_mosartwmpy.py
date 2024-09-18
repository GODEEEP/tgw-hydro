import os, datetime
import mosartwmpy

os.chdir('/vast/projects/godeeep/VIC/forcing/tgw-hydro/mosart')
#scenario = 'rcp45cooler'
#scenario = 'rcp45hotter'
#scenario = 'rcp85cooler'
scenario = 'rcp85hotter'
huc2_idx = 17
huc2_names = [
    "northeast",
    "midatlantic",
    "southatlantic",
    "greatlakes",
    "ohio",
    "tennessee",
    "uppermississippi",
    "lowermississippi",
    "souris",
    "missouri",
    "arkansas",
    "texas",
    "riogrande",
    "uppercolorado",
    "lowercolorado",
    "greatbasin",
    "columbia",
    "california",
]
print(f'./configs/{scenario}/{huc2_names[huc2_idx - 1]}_{scenario}.yaml')

mosart = mosartwmpy.Model()
mosart.initialize(f'./configs/{scenario}/{huc2_names[huc2_idx - 1]}_{scenario}.yaml')
#mosart.config["simulation.end_date"] = datetime.date(1979, 1, 3)
mosart.update_until(mosart.get_end_time())