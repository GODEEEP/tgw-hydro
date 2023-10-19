library(tidyverse)
library(sf)
library(nhdplusTools)
import::from(janitor, clean_names)

wbd_path <- "WBD_National_GDB/WBD_National_GDB.gdb/"
# nwis <- st_read(wbd_path, "NWISDrainageArea")
# only grab huc8 basins in
huc8 <- st_read(wbd_path, "WBDHU8") |> filter(substr(huc8, 1, 2) %in% sprintf("%02d", 1:18))
# huc8 |> filter(substr(huc8,1,2) %in% sprintf('%02d',1:18)) |> st_geometry() |> plot()
huc12 <- st_read(wbd_path, "WBDHU12")
# gages <- read_sf("data/GageLoc/GageLoc.shp") |> st_zm()
# huc8 <- read_sf("HUC8_CONUS/HUC8_US.shp")
huc12pp <- rjson::fromJSON(file = "huc12pp.json")
huc12_names <- sapply(huc12pp$features, function(x) x$properties$name)

find_huc8_downstream <- function(huc8_code, mode = "DM") {
  huc12 |>
    filter(substr(huc12, 1, 8) == huc8_code) |>
    pull(huc12) |>
    sort() -> huc12_codes

  # use the first huc12 in the list, it really doesnt matter which one is used
  # since we'll traverse downstream until the outlet
  flowline <- navigate_nldi(list(featureSource = "huc12pp", featureID = huc12_codes[1]),
    mode = mode, distance_km = 250
  )
  comid <- flowline[[paste0(mode, "_flowlines")]]$nhdplus_comid |> unique()
  return(find_nhd_info_comid(comid, flowline_only = TRUE))
}

find_huc8_outlet_comid <- function(huc8_code) {
  huc12 |>
    filter(substr(huc12, 1, 8) == huc8_code) |>
    pull(huc12) -> huc12_codes
  huc12_outlet_code <- huc12_codes |>
    substr(9, 12) |>
    as.numeric() |>
    max() %>%
    sprintf("%04d", .) %>%
    paste0(huc8_code, .)

  flowline <- navigate_nldi(
    list(featureSource = "huc12pp", featureID = huc12_outlet_code),
    mode = "DM", distance_km = 1
  )
  return(flowline)
}

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

# huc8_code <- "15030201"

outlet <- outlet_reach <- list()
for (huc8_code in huc8$huc8) {

  #
  message(huc8_code)

  # trace the river downstream
  flowline <- tryCatch(find_huc8_outlet_comid(huc8_code),
    error = function(cond) {
      return(NULL)
    }
  )

  if (!is.null(flowline)) {
    # find the intersection between the downstream river and the huc8 boundary
    # which will be the huc8 outlet
    # intersection <- huc8 |>
    #   filter(huc8 == huc8_code) |>
    #   st_cast("MULTILINESTRING", group_or_split = FALSE) %>%
    #   st_intersects(downstream$flowline, .) |>
    #   lengths() |>
    #   as.logical() |>
    #   which()

    # outlet[[huc8_code]] <- huc8 |>
    #   filter(huc8 == huc8_code) |>
    #   st_cast("MULTILINESTRING", group_or_split = FALSE) %>%
    #   st_intersection(downstream$flowline, .)

    # outlet_reach[[huc8_code]] <- downstream$flowline[intersection, ]

    # find the basin outlet
    outlet[[huc8_code]] <- flowline$origin
    outlet[[huc8_code]]$huc8 <- huc8_code
    outlet_reach[[huc8_code]] <- flowline$DM_flowlines
    outlet_reach[[huc8_code]]$huc8 <- huc8_code
  }

  # ggplot() +
  #   theme_bw() +
  #   geom_sf(data = huc8 |> filter(huc8 == huc8_code)) +
  #   geom_sf(data = downstream$flowline, color = "steelblue") +
  #   # geom_sf_label(aes(label=comid),data=downstream$flowline)+
  #   geom_sf(data = huc8 |> filter(huc8 == huc8_code), fill = NA) +
  #   geom_sf_label(aes(label = huc8), data = huc8 |> filter(huc8 == huc8_code),
  #                 fill = NA, border = NA) +
  #   geom_sf(data = outlet, color = "red") +
  #   geom_sf(data = downstream$flowline[intersection, ], color = "red")
}

# fix some of the attributes so we can bind all the points/reaches together
# outlets <- map(outlet, function(x) {
#   tags_to_fix <- c(
#     "maxelevraw", "minelevraw", "maxelevsmo", "minelevsmo", "slope",
#     "slopelenkm", "lakefract", "surfarea", "rareahload", "hwnodesqkm"
#   )
#   for (tag in tags_to_fix) x[[tag]] <- as.numeric(x[[tag]])
#   x
# }) |> bind_rows()
#
# outlet_reaches <- map(outlet_reach, function(x) {
#   tags_to_fix <- c(
#     "maxelevraw", "minelevraw", "maxelevsmo", "minelevsmo", "slope",
#     "slopelenkm", "lakefract", "surfarea", "rareahload", "hwnodesqkm"
#   )
#   for (tag in tags_to_fix) x[[tag]] <- as.numeric(x[[tag]])
#   x
# }) |> bind_rows()

outlets <- bind_rows(outlet)
outlet_reaches <- bind_rows(outlet_reach)

dir.create("HUC8_outlets", showWarnings = F)
dir.create("HUC8_outlet_reaches", showWarnings = F)
outlets |> st_write("HUC8_outlets/HUC8_outlets.shp")
outlet_reaches |> st_write("HUC8_outlet_reaches/HUC8_outlet_reaches.shp")

missing_huc8 <- huc8 |>
  filter(!(huc8 %in% names(outlet_reaches))) |>
  pull(huc8)

# ggplot(huc8) +
#   geom_sf() +
#   geom_sf(fill = "red", data = huc8 |> filter(!(huc8 %in% names(outlet)))) +
#   theme_bw()





# ggplot() +
#  theme_bw() +
#  #geom_sf(data=huc8)+
#   geom_sf(data = upstream$catchment) +
#  geom_sf(data = upstream$flowline, color = "steelblue")
# #geom_sf_label(aes(label=huc8),data=huc8, label.size=.3)
# #coord_sf(xlim=c(-110,-107),ylim=c(33.5,37))
#
# natural_flow <- read_csv("~/Downloads/13.1.1/21404075.csv", show = F) |>
#   clean_names() |>
#   # convert from cfs to mm/month
#   mutate(nat_runoff = estimated_q * 86400 * days_in_month(month) / (3.28084^3 * area * 1000)) |>
#   select(comid, area, year, month, ends_with("_q"), nat_runoff)
#
# ww_runoff <- runoff |>
#   filter(huc_cd == "15030201") |>
#   pivot_longer(-huc_cd, values_to = "ww_runoff") |>
#   mutate(
#     year = substr(name, 1, 4) |> as.numeric(),
#     month = substr(name, 5, 6) |> as.numeric()
#   ) |>
#   select(-name)
#
# compare_wide <- ww_runoff |>
#   inner_join(natural_flow, by = c("year", "month")) |>
#   mutate(date = ISOdate(year, month, 1)) # ,
# # ww_runoff=ww_runoff*100)
#
# compare_long <- compare_wide |>
#   pivot_longer(-c(huc_cd, year, month, date, comid, area))
#
# compare_long |>
#   filter(name %in% c("ww_runoff", "nat_runoff")) |>
#   ggplot(aes(factor(month), value, fill = name)) +
#   geom_line(aes(date, value, color = name))
#
# compare_long |>
#   filter(name %in% c("ww_runoff", "nat_runoff")) |>
#   ggplot(aes(factor(month), value, fill = name)) +
#   geom_boxplot() +
#   scale_y_log10()


# p <- ggplot() +
#   geom_sf(data = upstream$flowline, color = "lightblue") +
#   geom_sf(data = upstream$catchment, fill = NA) +
#   # geom_sf(data = downstream$catchment, color = "black", fill=NA) +
#   geom_sf(data = huc12 |> filter(substr(huc12, 1, 8) == huc8_code), color = "orange", fill = NA) +
#   geom_sf(data = flowline$origin, color = "red") +
#   # geom_sf(data = flowline_ut$origin, color = "red") +
#   geom_sf(data = flowline$DM_flowlines, color = "steelblue") +
#   geom_sf_text(aes(label = huc12), data = huc12 |> filter(substr(huc12, 1, 8) == huc8_code))
# ggplotly(p)
