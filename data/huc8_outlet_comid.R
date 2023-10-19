library(tidyverse)
library(sf)
library(nhdplusTools)
library(viridis)
import::from(janitor, clean_names)

wbd_path <- "WBD_National_GDB/WBD_National_GDB.gdb/"
# nwis <- st_read(wbd_path, "NWISDrainageArea")
# only grab huc8 basins in
huc8 <- st_read(wbd_path, "WBDHU8") |> filter(substr(huc8, 1, 2) %in% sprintf("%02d", 1:18))
states <- st_read("cb_2018_us_state_5m/cb_2018_us_state_5m.shp")

shape_dir <- "HUC8_outlet_terminal_reaches"
cache_dir <- "cache"
plot_dir <- "outlet_reach_plots"

map(c(shape_dir, cache_dir, plot_dir), function(x) dir.create(x, showWarnings = F))


find_nhd_info_comid <- function(comid, flowline_only = FALSE) {
  subset_file <- tempfile(fileext = ".gpkg")
  subset <- subset_nhdplus(
    comids = as.integer(comid),
    output_file = subset_file,
    nhdplus_data = "download",
    # "NHDPlusNationalData/NHDPlusV21_National_Seamless_Flattened_Lower48.gdb",
    flowline_only = flowline_only,
    return_data = TRUE,
    overwrite = TRUE,
    status = FALSE
  )

  return(list(
    flowline = subset$NHDFlowline_Network,
    catchment = subset$CatchmentSP,
    waterbody = subset$NHDWaterbody
  ))
}

# huc8_code <- "17090003"
map(huc8$huc8, function(huc8_code) {
  #
  # message(huc8_code)

  cache_fn <- sprintf("%s/outlet_reach_%s.rds", cache_dir, huc8_code)

  # read fronm the cache file if it exists
  if (file.exists(cache_fn)) {
    return(read_rds(cache_fn))
  }

  # get the huc8 boundary
  suppressMessages({
    huc8_basin <- get_huc(id = huc8_code, type = "huc08")
  })
  if (!is_tibble(huc8_basin)) {
    return(NULL)
  }

  # get all the reaches inside the huc8 (theoretically)
  flowlines <- tryCatch(
    suppressMessages({
      get_nhdplus(huc8_basin)
    }),
    error = function(x) {
      return(NULL)
    }
  )
  if (!is_tibble(flowlines)) {
    return(NULL)
    # if (is.null(flowlines) || is.na(flowlines) || length(flowlines) == 0) {
  }

  # fins the outlet reach that has the highest basin area
  # this is a heuristic and does not work wall on basins that
  # have multiple outlets
  outlet_reach <- flowlines |>
    # reach needs to be in the huc
    filter(substr(reachcode, 1, 8) == huc8_code) |>
    # reach needs to be as far downstream as possible
    filter(streamorde == max(streamorde)) |>
    # filter(terminalfl == 1) |>
    # reach should have the largest upstream area of any reach
    filter(totdasqkm == max(totdasqkm)) |>
    mutate(
      huc8 = huc8_code,
      reach_type = "outlet"
    )

  if (nrow(outlet_reach) == 0) {
    # some newer hucs have reach codes from other hucs
    outlet_reach <- flowlines |>
      filter(streamorde == max(streamorde)) |>
      filter(totdasqkm == max(totdasqkm)) |>
      mutate(huc8 = huc8_code)
  }

  # find the terminal reaches in the basin, we'll add them up later
  # to find the total runoff
  terminal_reaches <- flowlines |>
    # reach needs to be in the huc
    filter(substr(reachcode, 1, 8) == huc8_code) |>
    filter(terminalfl == 1) |>
    mutate(
      huc8 = huc8_code,
      reach_type = "terminal"
    )

  if (nrow(terminal_reaches) == 0) {
    # some newer hucs have reach codes from other hucs
    terminal_reaches <- flowlines |>
      filter(terminalfl == 1) |>
      mutate(
        huc8 = huc8_code,
        reach_type = "terminal"
      )
  }
  runoff_reaches <- bind_rows(outlet_reach, terminal_reaches)

  # cache the outlet reach
  runoff_reaches |> write_rds(file = cache_fn)

  # most downstream reach comid
  cid <- flowlines |>
    filter(streamorde == max(streamorde)) |>
    pull(comid)

  # get the features asociated with the most downstream reaches for plotting
  wbarea <- tryCatch(
    suppressMessages({
      find_nhd_info_comid(cid)
    }),
    error = function(x) {
      return(NULL)
    }
  )

  # bouding box for plotting
  basin_bbox <- huc8_basin |> st_bbox()

  # sometimes the api will return NA
  lakes <- if (is.list(wbarea)) {
    geom_sf(data = wbarea$waterbody, fill = "steelblue")
  } else {
    geom_blank()
  }

  p <- ggplot() +
    geom_sf(data = huc8_basin, fill = gray(.8)) +
    geom_sf(data = states, fill = NA) +
    lakes +
    geom_sf(aes(color = factor(streamorde)), data = flowlines) +
    geom_sf(color = "red", data = outlet_reach, linewidth = 1.5) +
    geom_sf(color = "orange", linetype = "dashed", data = terminal_reaches) +
    scale_color_viridis_d("order", option = "G", direction = -1) +
    theme_bw() +
    coord_sf(xlim = basin_bbox[c(1, 3)], ylim = basin_bbox[c(2, 4)]) +
    labs(title = huc8_code)
  p
  sprintf("%s/%s.pdf", plot_dir, huc8_code) |>
    ggsave(p, width = 10, height = 10)

  return(runoff_reaches)
}, .progress = TRUE) %>%
  do.call("rbind", .) ->
outlet_reaches

outlet_reaches |>
  st_write(sprintf("%s/HUC8_outlet_terminal_reaches.shp", shape_dir), append = FALSE)


basin_area_represented <- outlet_reaches |>
  st_drop_geometry() |>
  group_by(huc8) |>
  # in some basins the outlet is a terminal reach so it would get double counted
  distinct(reachcode, .keep_all = T) |>
  mutate(totdasqkm = ifelse(totdasqkm > 2000000, 0, totdasqkm)) |>
  select(huc8, totdasqkm) |>
  left_join(
    huc8 |>
      select(huc8, areasqkm),
    by = join_by(huc8)
  ) |>
  summarise(area_represented = sum(totdasqkm) / max(areasqkm), .groups = "drop")

outlet_area_represented <- outlet_reaches |>
  filter(reach_type == "outlet") |>
  st_drop_geometry() |>
  group_by(huc8) |>
  # in some basins the outlet is a terminal reach so it would get double counted
  distinct(reachcode, .keep_all = T) |>
  mutate(totdasqkm = ifelse(totdasqkm > 2000000, 0, totdasqkm)) |>
  select(huc8, totdasqkm) |>
  left_join(
    huc8 |>
      select(huc8, areasqkm),
    by = join_by(huc8)
  ) |>
  summarise(area_represented = sum(totdasqkm) / max(areasqkm), .groups = "drop")

# only 870 basins are reasonable with this method
basin_area_represented |> filter(abs(1 - area_represented) < 0.10)

huc8_with_outlets <- outlet_reaches |>
  pull(huc8) |>
  unique()
missing_huc <- huc8 |>
  filter(!(huc8 %in% missing_huc8)) |>
  pull(huc8)

ggplot(huc8) +
  geom_sf() +
  geom_sf(data = huc8 |> filter(!(huc8 %in% missing_huc8)), fill = "red")

outlet_reaches
