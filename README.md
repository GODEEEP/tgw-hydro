# tgw-hydro

Scripts for producing hydropower generation data using the [TGW meteorology](https://tgw-data.msdlive.org/).

## Setup 

1. Download [VIC](https://github.com/UW-Hydro/VIC)
2. Download the [VICGlobal parameters](https://zenodo.org/record/5038653/files/parameters_continents.zip?download=1) and [model domain](https://zenodo.org/record/5038653/files/domains.zip?download=1), unpack the files `namerica_params.nc` and `namerica_domain.nc` into the `params/` directory
3. Follow the instructions in `params/README.md` to create separate model parameter and domain files for each  HUC8 basin
4. Follow the instructions in `forcings/README.md` to create forcing input data
5. Follow the instructions in `calibration/README.md` to conduct calibrations, note this is very computationally expensive and will likely require a HPC setup
6. Follow the instructions in `mosart/README.md` to conduct the mosart simulations
7. Follow the instructions in `hydropower/README.md` to develop hydropower estimates 


## Funding

This research was supported by the Grid Operations, Decarbonization, Environmental and Energy Equity Platform (GODEEEP) Investment, under the Laboratory Directed Research and Development (LDRD) Program at Pacific Northwest National Laboratory (PNNL).

PNNL is a multi-program national laboratory operated for the U.S. Department of Energy (DOE) by Battelle Memorial Institute under Contract No. DE-AC05-76RL01830.

## Authors

Cameron Bracken, Youngjun Son, Dan Broman, Nathalie Voisin

## Corresponding author

Cameron Bracken, cameron.bracken@pnnl.gov