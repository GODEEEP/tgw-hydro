library(sf)
library(tidyverse)

huc2_num <- 9

dams <- st_read("../mosart/mosartwmpy_conus_EHA_v1.0/mosartwmpy_conus_EHA_v1.0.shp")
ll <- st_coordinates(dams)
dams$lat <- ll[, "Y"]
dams$lon <- ll[, "X"]

# assign the HUC2 based on shapefile
huc2 <- st_read("../data/HUC2/HUC2.shp")
huc2_pl <- st_transform(huc2, 2163)
dsf <- st_transform(st_as_sf(
  data.frame(lon = dams$lon, lat = dams$lat),
  coords = c("lon", "lat"), crs = 4326
), 2163)
int <- st_intersects(dsf, huc2_pl)
ind <- sapply(int, function(x) {
  ifelse(length(x) > 0, x, NA)
})
dams$HUC2 <- huc2$huc2[ind] |> as.integer()

# Strg_Fl: missing storage data
# Hed_Flg: missing head data
# Trnsb_F: transbasin diversion
# WtrSr_F: water source not appropriate to simulate (unknown, municipal water supply, irrigation canal, spring, etc.)
# EIA_ID_D: duplicated EIA ID (EIA ID used for multiple facilities)
# PS_Flag: pumped storage
# OCONUS_: outside of CONUS
# EIA_G_F: missing generation data
excluded_dams <- read_csv("../data/excluded_dams_cat.csv") |>
  filter(Trnsb_F == 1 | WtrSr_F == 1 | EIA_ID_D == 1 | PS_Flag == 1)

# exclude most dams that were left out of 9505
# but include those that were excluded due to data,
# we can work with smaller data records
dams_for_mosart <- dams |>
  filter(!(EIA_PID %in% excluded_dams$EIA_PID))

dams_for_mosart |>
  st_write("../mosart/mosartwmpy_conus_EHA_v1.0/mosartwmpy_conus_EHA_v1.0_with_HUC2.shp", append = F)

dams_for_mosart |>
  st_drop_geometry() |>
  write_csv("../mosart/mosartwmpy_conus_EHA_v1.0/mosartwmpy_conus_EHA_v1.0_with_HUC2.csv")

dam_locs <- dams_for_mosart |>
  filter(HUC2 == huc2_num) |>
  select(geometry) |>
  st_coordinates()
paste0("    - ", round(dam_locs[, "Y"], 4), ",", round(dam_locs[, "X"], 4)) |> cat(sep = "\n")
