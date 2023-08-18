# tgw-hydro

Scripts for producing hydropower generation data using the [TGW meteorology](https://tgw-data.msdlive.org/).

## Setup 

1. Download [VIC](https://github.com/UW-Hydro/VIC)
2. Download the [HUC8 shapefile] and unpack into the `data/` directory
3. Download the [VICGlobal parameters](https://zenodo.org/record/5038653/files/parameters_continents.zip?download=1) and [model domain](https://zenodo.org/record/5038653/files/domains.zip?download=1), unpack the files `namerica_params.nc` and `namerica_domain.nc` into the `params/` directory
4. Follow the instructions in `params/README.md` to create separate model parameter and domain files for each  HUC8 basin
5. Follow the instructions in `forcings/README.md` to create forcing input data