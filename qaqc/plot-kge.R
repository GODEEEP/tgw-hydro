library(ncdf4)
library(tidyverse)
library(sf)

options(
  readr.show_progress = FALSE,
  readr.show_col_types = FALSE,
  pillar.width = 1e6
)

huc2_nums <- 1:18

dam_shape <- st_read("../mosart/mosartwmpy_conus_EHA_v1.0/mosartwmpy_conus_EHA_v1.0_with_HUC2.shp")
huc2_shape <- st_read("/Volumes/data/shapefiles/HUC2/HUC2.shp")
grid_conus <- read_csv("../data/grid_ids_conus.csv")

full_grid_list <- full_grid_missing_list <- list()
for (huc2_num in huc2_nums) {
  message(huc2_num)
  # huc2_num <- 16

  dams <- dam_shape |> filter(HUC2 == huc2_num)
  ll <- st_coordinates(dams)
  dams$lat <- ll[, "Y"]
  dams$lon <- ll[, "X"]
  # dams |>
  #   filter(substr(HUC, 1, 2) == huc2_num) |>
  #   select(geometry) |>
  #   st_coordinates() |>
  #   as_tibble()

  grid <- grid_conus |> filter(huc2 == "%02d" |> sprintf(huc2_num))
  nc <- nc_open("gof_huc%02d.nc" |> sprintf(huc2_num))
  kge_calib <- ncvar_get(nc, "kge_calib")
  kge_valid <- ncvar_get(nc, "kge_valid")
  lon <- ncvar_get(nc, "lon")
  lat <- ncvar_get(nc, "lat")

  rownames(kge_calib) <- lon
  colnames(kge_calib) <- lat

  rownames(kge_valid) <- lon
  colnames(kge_valid) <- lat

  long_grid <- function(x) {
    x |>
      as.data.frame.table(responseName = "value") |>
      as_tibble() |>
      rename(lon = Var1, lat = Var2) |>
      mutate(
        lon = as.numeric(as.character(lon)),
        lat = as.numeric(as.character(lat))
      ) |>
      na.omit()
  }

  kge_valid_long <- long_grid(kge_valid)
  kge_calib_long <- long_grid(kge_calib)

  grid_with_missing <- grid |>
    left_join(kge_valid_long, by = join_by(lon, lat)) |>
    rename(kge_valid = value) |>
    mutate(kge_valid = ifelse(kge_valid < 0, 0, kge_valid)) |>
    left_join(kge_calib_long, by = join_by(lon, lat)) |>
    rename(kge_calib = value) |>
    mutate(kge_calib = ifelse(kge_calib < 0, 0, kge_calib))
  full_grid_list[[huc2_num]] <- grid_with_missing

  grid_missing <- grid |>
    filter(id %in% scan("pick_broken_%02d.txt" |> sprintf(huc2_num), what = "c", quiet = T))
  # grid_missing |> filter(lon > -121)
  full_grid_missing_list[[huc2_num]] <- grid_missing

  # ggplot(kge_valid_long |> mutate(value = ifelse(value < 0, 0, value))) +
  #   geom_raster(aes(lon, lat, fill = value)) +
  #   scale_y_continuous(breaks = seq(40, 54, by = 2)) +
  #   theme_bw() +
  #   theme(panel.grid.minor = element_blank())

  ylim <- kge_valid_long$lat |> range()
  xlim <- kge_valid_long$lon |> range()

  kge_plot <- function(grid, missing_grid, dam_sf, huc2_boundary) {
    grid |>
      na.omit() |>
      pivot_longer(-c(huc2, id, lon, lat), names_to = "kge") |>
      ggplot() +
      geom_tile(aes(lon, lat),
        width = 1 / 16, height = 1 / 16,
        fill = "orange",
        data = missing_grid
      ) +
      geom_raster(aes(lon, lat, fill = value)) +
      facet_wrap(~kge) +
      # scale_y_continuous(limits=ylim) +
      # scale_x_continuous(limits=xlim) +
      theme_bw() +
      theme(panel.grid = element_blank()) +
      # geom_point(aes(lon, lat), color = "orange", data = grid_missing) +
      scale_fill_viridis_c("KGE", option = "G", limits = c(0, 1)) +
      geom_sf(data = dam_sf, color = "black", pch = 21, fill = "white", size = 0.6) #+
    # geom_sf(data = huc2_boundary, fill = NA, size = 1, color='grey')
  }
  p_kge <- kge_plot(
    grid_with_missing, grid_missing, dams # ,
    # huc2_shape |> filter(huc2 == "%02d" |> sprintf(huc2_num))
  )
  p_kge
  ggsave("plots/kge_huc%02d.png" |> sprintf(as.numeric(huc2_num)), p_kge, width = 10, height = 6, dpi = 300)
}
full_grid <- bind_rows(full_grid_list)
full_grid_missing <- bind_rows(full_grid_missing_list)
p_kge_conus <- full_grid |>
  rename(
    `Validation Period [2001-2019]` = kge_valid,
    `Calibration Period [1980-2000]` = kge_calib
  ) |>
  na.omit() |>
  pivot_longer(-c(huc2, id, lon, lat), names_to = "kge") |>
  ggplot() +
  geom_raster(aes(lon, lat, fill = value)) +
  facet_wrap(~kge, ncol = 1) +
  theme_void() +
  theme(panel.grid = element_blank()) +
  scale_fill_viridis_c("KGE", option = "G", limits = c(0, 1)) +
  geom_sf(
    data = dam_shape |> filter(HUC2 %in% huc2_nums),
    color = "white", pch = 21, fill = "white", alpha = 0,
    size = 0.6
  ) +
  # geom_sf(data = huc2_shape, fill = NA, size = 1, color = "grey") +
  theme(
    legend.position = "inside",
    legend.position.inside = c(.9, .55)
  )
p_kge_conus
ggsave("plots/kge_conus.pdf", p_kge_conus, width = 6, height = 8, dpi = 300)
#
# ggplot(kge_calib_long |> mutate(value = ifelse(value < 0, NA, value))) +
#   geom_raster(aes(lon, lat, fill = value)) +
#   scale_fill_continuous(limits = c(0, 1)) +
#   scale_y_continuous(breaks = 40:55)

p_kge_conus_calib_only <- full_grid |>
  na.omit() |>
  pivot_longer(-c(huc2, id, lon, lat), names_to = "kge") |>
  filter(kge == "kge_calib") |>
  ggplot() +
  geom_raster(aes(lon, lat, fill = value)) +
  theme_void() +
  theme(panel.grid = element_blank(), legend.position = "inside", legend.position.inside = c(.9, .25)) +
  scale_fill_viridis_c("KGE", option = "G", limits = c(0, 1)) +
  geom_sf(data = dam_shape |> filter(HUC2 %in% huc2_nums), alpha = 0)
p_kge_conus_calib_only
ggsave("plots/kge_conus_calib.png", p_kge_conus_calib_only, width = 8, height = 6, dpi = 300)

power_monthly <- read_csv("../mosart/godeeep-hydro/historical/godeeep-hydro-monthly.csv")
p_power_constraints <- power_monthly |>
  filter(datetime == as.Date("2018-07-01")) |>
  pivot_longer(c(p_avg, p_max, p_min), names_to = "constraint") |>
  mutate(
    constraint = case_when(
      constraint == "p_avg" ~ "Ave Power Target",
      constraint == "p_min" ~ "Min Power",
      constraint == "p_max" ~ "Max Power"
    ),
    constraint = factor(constraint, levels = c("Max Power", "Ave Power Target", "Min Power"))
  ) |>
  ggplot() +
  geom_sf(data = huc2_shape, fill = grey(.95)) +
  geom_point(aes(lon, lat, size = value, color = value), alpha = .6) +
  theme_void() +
  facet_wrap(~constraint, ncol = 1) +
  scale_size_continuous("Power [MW]", range = c(1, 12), breaks = seq(0, 5000, by = 1000)) +
  scale_color_viridis_c("Power [MW]", option = "G", breaks = seq(0, 5000, by = 1000)) +
  guides(color = guide_legend(), size = guide_legend()) +
  theme(legend.position = "inside", legend.position.inside = c(.88, .35)) #+
# labs(title='Hydropower Constraints July 2018')
p_power_constraints
ggsave("plots/power_constraints.png", p_power_constraints, width = 5, height = 10, dpi = 300)
