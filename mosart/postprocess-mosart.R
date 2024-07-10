library(tidyverse)
import::from(raster, brick, extract, getZ)

options(
  readr.show_progress = FALSE,
  readr.show_col_types = FALSE,
  pillar.width = 1e6
)

huc2 <- 18
huc2_name <- "columbia"
dams <- read_csv("mosartwmpy_conus_EHA_v1.0/mosartwmpy_conus_EHA_v1.0.csv") |>
  filter(HUC2 == huc2)

nc_files <- "output/california" |> list.files("*.nc", full.names = T)

get_var_from_nc_file <- function(nc_file, var) {
  d <- brick(nc_file, varname = var)
  d |>
    extract(select(dams, lon, lat), df = T) |>
    as_tibble() |>
    pivot_longer(-ID, names_to = "date") |>
    mutate(
      date = as_date(substr(date, 2, nchar(date))),
      var = var
    )
}

nc_files |>
  map(function(nc_file) {
    get_var_from_nc_file(nc_file, "channel_outflow")
  }, .progress = T) |>
  bind_rows()
