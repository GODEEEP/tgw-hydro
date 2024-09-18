import yaml
import datetime
import os
os.chdir('./mosart/configs/')
huc2s = list(range(1, 18 + 1))
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

scenarios = ["rcp45cooler", "rcp45hotter", "rcp85cooler", "rcp85hotter"]

for i in range(len(huc2s)):
    #
    huc2 = huc2s[i]
    huc2_name = huc2_names[i]

    with open(f"historical/{huc2_name}.yaml", "r") as file:
        config = yaml.safe_load(file)

    config["simulation"]["start_date"] = datetime.date(2020, 1, 1)
    config["simulation"]["end_date"] = datetime.date(2099, 12, 31)
    config["simulation"]["output_path"] = "/vast/projects/godeeep/VIC/future_projections/mosart/runs"
    config["water_management"]["demand"]["path"] = "./input/demand/RCP8.5_GCAM_water_demand_2020_2099.nc"

    for scenario in scenarios:
        config["simulation"]["name"] = f"{huc2_name}_{scenario}"
        config["runoff"]["path"] = (
#            f"./input/runoff/{scenario}/{huc2:02}/mosart_{scenario}_huc{huc2:02}"
            f"/vast/projects/godeeep/VIC/future_projections/mosart/{scenario}/{huc2:02}/mosart_{scenario}_huc{huc2:02}"
            + "_8th_runoff_{Y}_{M}.nc"
        )
        with open(f'{scenario}/{huc2_name}_{scenario}.yaml', 'w') as file:
            yaml.dump(config, file, sort_keys=False)
        #write_yaml(config, sprintf("%s/%s_%s.yaml", scenario, huc2_name, scenario))
