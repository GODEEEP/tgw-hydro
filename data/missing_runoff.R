library(tidyverse)
library(sf)
library(nhdplusTools)

wbd_path <- "data/WBD_National_GDB/WBD_National_GDB.gdb/"
nwis <- st_read(wbd_path, "NWISDrainageArea")
# huc8 <- st_read(wbd_path, "WBDHU8")
huc12 <- st_read(wbd_path, "WBDHU12")
gages <- read_sf("data/GageLoc/GageLoc.shp") |> st_zm()
huc8 <- read_sf("data/HUC8_CONUS/HUC8_US.shp")
runoff <- read_delim("data/huc8_runoff_mv01d/mv01d_row_data.txt", delim = "\t")

huc8_missing_runoff <- huc8 |> filter(!(HUC8 %in% runoff$huc_cd))

find_upstream_info_nwis <- function(nwis_id) {
  flowline <- navigate_nldi(list(featureSource = "nwissite", featureID = sprintf("USGS-%s", nwis_id)),
    mode = "upstreamTributaries", distance_km = 1000
  )
  comid <- flowline$UT$nhdplus_comid
  if (is.null(comid)) {
    return(NULL)
  }
  return(find_nhd_info_comid(comid))
}

find_nhd_info_huc12 <- function(huc12_code, mode = "UT") {
  # UT - Upstream Tribs
  # UM - Upstream Main
  # DM - Downstream Main
  # DD - Downstream ?
  flowline <- navigate_nldi(list(featureSource = "huc12pp", featureID = huc12_code),
    mode = mode, distance_km = 100
  )
  comid <- flowline[[paste0(mode, "_flowlines")]]$nhdplus_comid
  if (is.null(comid)) {
    return(NULL)
  }
  return(find_nhd_info_comid(comid))
}

find_huc8_downstream <- function(huc8_code, mode = "DM") {
  huc12 |>
    filter(substr(huc12, 1, 8) == huc8_code) |>
    pull(huc12) -> huc12_codes

  # use the first huc12 in the list, it really doesnt matter which one is used
  # since we'll traverse downstream until the outlet
  flowline <- navigate_nldi(list(featureSource = "huc12pp", featureID = huc12_codes[1]),
    mode = mode, distance_km = 250
  )
  comid <- flowline[[paste0(mode, "_flowlines")]]$nhdplus_comid |> unique()
  return(find_nhd_info_comid(comid, flowline_only = FALSE))
}

find_nhd_info_comid <- function(comid, flowline_only = FALSE) {
  subset_file <- tempfile(fileext = ".gpkg")
  subset <- subset_nhdplus(
    comids = as.integer(comid),
    output_file = subset_file,
    nhdplus_data = "download",
    flowline_only = flowline_only,
    return_data = TRUE, overwrite = TRUE, status = FALSE
  )

  return(list(
    flowline = subset$NHDFlowline_Network,
    catchment = subset$CatchmentSP,
    waterbody = subset$NHDWaterbody
  ))
}


for (h in 1:nrow(huc8_missing_runoff)) {
  # bbox <- (huc8[h, ] |> st_bbox()) + c(-5, -5, 5, 5) / 100
  gages_in_basin <- gages[st_intersects(huc8_missing_runoff[h, ], gages |> st_transform(4326), par = 0.2)[[1]], ]
  # gages_in_basin <- gages[substr(gages$REACHCODE, 1, 8) == huc8_missing_runoff[h, ]$HUC8, ]
  huc8_code <- huc8_missing_runoff[h, ]$HUC8
  message(huc8_code)

  for (g in 1:nrow(gages_in_basin)) {
    gage <- gages_in_basin[g, ]
    usgs_id <- gage$SOURCE_FEA
    comid <- gage$FLComID
    message("\t", usgs_id)

    upstream <- find_upstream_info(usgs_id)
    if (is.null(upstream)) next
    p <- ggplot(huc8_missing_runoff[h, ]) +
      geom_sf() +
      theme_bw() +
      geom_sf(data = upstream$catchment) +
      geom_sf(data = upstream$flowline, color = "steelblue") +
      geom_sf(data = gage) +
      geom_sf_label(aes(label = SOURCE_FEA), data = gage, size = 3, alpha = 0, nudge_y = .02)
    ggsave("plots/%s-%s.pdf" |> sprintf(huc8_code, usgs_id), p, width = 10, height = 10)
  }
}

ggplot(huc8 |> filter(substr(HUC8, 1, 4) == "1310", !(HUC8 %in% runoff$huc_cd))) +
  geom_sf() +
  geom_sf_label(aes(label = HUC8), label.size = .1, alpha = 0) +
  geom_sf(data = gages) +
  coord_sf(xlim = c(-108, -104), ylim = c(26, 30)) +
  geom_sf_label(aes(label = SOURCE_FEA), data = gages)
