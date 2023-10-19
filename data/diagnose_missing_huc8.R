library(tidyverse)
library(sf)
library(nhdplusTools)

wbd_path <- "WBD_National_GDB/WBD_National_GDB.gdb/"
nwis <- st_read(wbd_path, "NWISDrainageArea")
huc8 <- st_read(wbd_path, "WBDHU8")
huc12 <- st_read(wbd_path, "WBDHU12")
gages <- read_sf("GageLoc/GageLoc.shp") |> st_zm()
# huc8 <- read_sf("HUC8_CONUS/HUC8_US.shp")
runoff <- read_delim("huc8_runoff_mv01d/mv01d_row_data.txt", delim = "\t")
huc12pp <- rjson::fromJSON(file = "huc12pp.json")
huc12_names <- sapply(huc12pp$features, function(x) x$properties$name)

find_huc12_downstream <- function(huc12_code, mode = "DM") {

  # use the first huc12 in the list, it really doesnt matter which one is used
  # since we'll traverse downstream until the outlet
  flowline <- navigate_nldi(list(featureSource = "huc12pp", featureID = huc12_code),
    mode = mode, distance_km = 250
  )
  comid <- flowline[[paste0(mode, "_flowlines")]]$nhdplus_comid |> unique()
  return(find_nhd_info_comid(comid, flowline_only = TRUE))
}

find_huc8_downstream <- function(huc8_code, mode = "DM") {
  # huc12 |>
  #   filter(substr(huc12, 1, 8) == huc8_code) |>
  #   pull(huc12) |>
  #   sort() -> huc12_codes
  huc12_names[substr(huc12_names, 1, 8) == huc8_code] |> sort() -> huc12_codes
  # use the first huc12 in the list, it really doesnt matter which one is used
  # since we'll traverse downstream until the outlet
  for (huc12_code in huc12_codes) {
    message(huc12_code)
    flowline <- tryCatch(navigate_nldi(list(featureSource = "huc12pp", featureID = huc12_code),
      mode = mode, distance_km = 250
    ),
    error = function(cond) {
      return(NULL)
    }
    )
    if (!is.null(flowline)) {
      comid <- flowline[[paste0(mode, "_flowlines")]]$nhdplus_comid |> unique()
      return(find_nhd_info_comid(comid, flowline_only = TRUE))
    } else {
      next
    }
  }
  return(NULL)
}

find_all_huc8_downstream <- function(huc8_code, mode = "DM") {
  huc12 |>
    filter(substr(huc12, 1, 8) == huc8_code) |>
    pull(huc12) |>
    sort() -> huc12_codes
  # huc12_names[substr(huc12_names, 1, 8) == huc8_code] |> sort() -> huc12_codes
  # use the first huc12 in the list, it really doesnt matter which one is used
  # since we'll traverse downstream until the outlet
  flowlines <- list()
  for (huc12_code in huc12_codes) {
    message(huc12_code)
    flowline <- tryCatch(navigate_nldi(list(featureSource = "huc12pp", featureID = huc12_code),
      mode = mode, distance_km = 250
    ),
    error = function(cond) {
      return(NULL)
    }
    )
    downstream <- flowline[[paste0(mode, "_flowlines")]]
    if (!is.null(downstream)) {
      comid <- downstream$nhdplus_comid |> unique()
      flowlines[[huc12_code]] <- find_nhd_info_comid(comid, flowline_only = TRUE)$flowline
    } else {
      next
    }
  }
  return(flowlines)
}

missing_huc8s <-
  c(
    "01010004", "01010005", "01010009", "01010010", "01010011",
    "01050004", "01060003", "01090002", "01090004", "01090006", "01100007",
    "02030104", "02030202", "02030203", "02040204", "02040301", "02040303",
    "02040304", "02060001", "02060004", "02080101", "02080102", "02080108",
    "02080110", "02080111", "03020105", "03020301", "03020302", "03030005",
    "03040208", "03050207", "03050209", "03050210", "03060204", "03080201",
    "03080202", "03080203", "03090203", "03090206", "03100102", "03100201",
    "03100203", "03100207", "03110205", "03120001", "03130014", "03170009",
    "03180004", "04020201", "04030113", "04030114", "04040001", "04090004",
    "04090006", "04090007", "04100013", "04140301", "04140302", "04160001",
    "04160002", "04160003", "04160004", "04170001", "04170002", "04170003",
    "04170004", "04170005", "04170006", "04180000", "04190000", "04200001",
    "04200002", "04200003", "04200004", "04200005", "04200006", "04200007",
    "04200008", "04200009", "04210001", "04210002", "04210003", "04210004",
    "04220001", "04220002", "04220003", "04220004", "04230001", "04230002",
    "04230003", "04230004", "04230005", "04230006", "04240001", "04240002",
    "04250001", "04250002", "04250003", "04250004", "04250005", "04260000",
    "04270101", "04270102", "04270103", "04270104", "04270105", "04270106",
    "04270107", "04270201", "04270202", "04270203", "04270204", "04270205",
    "04280001", "04280002", "04290001", "04290002", "04290003", "04290004",
    "04290005", "04290006", "04290007", "04290008", "04300101", "04300102",
    "04300103", "04300104", "04300105", "04300106", "04300107", "04300108",
    "04300109", "04300201", "04300202", "04310001", "04320000", "04330000",
    "05140101", "06010108", "07030002", "08010300", "08020302", "08020401",
    "08030207", "08030209", "08080206", "08090100", "08090203", "09010006",
    "09010007", "09010008", "09010009", "09020314", "09020316", "09020317",
    "09020318", "09020319", "09030003", "09030010", "09030011", "09040002",
    "09040003", "09040004", "10050001", "10050002", "10050003", "10050007",
    "10050008", "10050011", "10050013", "10060003", "10060004", "10060007",
    "10070007", "10080001", "10080016", "10090208", "10130104", "10130106",
    "10150005", "10160003", "10170104", "10170202", "10180003", "10180010",
    "10180011", "10190009", "10190014", "10190016", "12040204", "12040205",
    "12050004", "12050006", "12080005", "12090402", "12100401", "12100402",
    "12100403", "12100404", "12100405", "12110202", "12110203", "12110205",
    "12110207", "12110208", "13030102", "13030201", "13040201", "13040205",
    "13040212", "13050004", "13060004", "13080001", "13080003", "13090001",
    "13090002", "13100000", "13110000", "13120000", "14040101", "14040108",
    "14040109", "14060010", "15030107", "15030108", "15080101", "15080102",
    "15080103", "15080200", "15080302", "15080303", "16020303", "16050203",
    "17010101", "17010104", "17010106", "17010107", "17010108", "17010109",
    "17010110", "17020002", "17020007", "17020017", "17020018", "17020019",
    "17020020", "17020021", "17040104", "17050108", "17080006", "17100106",
    "17100201", "17100203", "17100204", "17100205", "17100207", "17100303",
    "17110001", "17110002", "17110003", "17110018", "17110021", "17120005",
    "17120006", "18030012", "18050005", "18060006", "18060014", "18070107",
    "18070201", "18070305", "18090207"
  )

for (huc8_code in missing_huc8s) {
  message(huc8_code)
  # huc8_code <- "13080001"
  huc12 |>
    filter(substr(huc12, 1, 8) == huc8_code) |>
    pull(huc12) -> huc12_codes

  huc12_names[substr(huc12_names, 1, 8) == huc8_code] |> sort() -> huc12_codes
  if (length(huc12_codes) == 0) next
  most_upstream_huc12 <- # "18010101404"
    huc12_codes |>
    substr(9, 12) |>
    as.numeric() |>
    min() %>%
    sprintf("%04d", .) %>%
    paste0(huc8_code, .)
  most_downstream_huc12 <- # "18010101404"
    huc12_codes |>
    substr(9, 12) |>
    as.numeric() |>
    max() %>%
    sprintf("%04d", .) %>%
    paste0(huc8_code, .)

  flowlines <- upstream <- list()
  for (h12 in huc12_codes) {
    flowlines[[h12]] <- navigate_nldi(
      list(featureSource = "huc12pp", featureID = h12),
      mode = "UT", distance_km = 200
    )
    flowlines[[h12]]$UT_flowlines[["huc12"]] <- h12
  }
  upstream <- navigate_nldi(
    list(featureSource = "huc12pp", featureID = most_downstream_huc12),
    mode = "UM", distance_km = 100
  )
  tribs <- lapply(flowlines, function(x) x$UT_flowlines) |> bind_rows()
  huc12_outlets <- lapply(flowlines, function(x) x$origin) |> bind_rows()
  downstream <- find_all_huc8_downstream(huc8_code) %>% do.call("rbind", .)
  if (is.null(downstream)) {
    next
  } else {
    downstream <- downstream |> distinct(comid, .keep_all = TRUE)
  }

  p <- ggplot() +
    geom_sf(data = huc8 |> filter(huc8 == huc8_code), fill = "grey95") +
    # geom_sf(data = downstream$catchment, fill = NA) +
    geom_sf(aes(geometry = geometry, color = huc12), data = tribs |> na.omit() |> as_tibble()) +
    # geom_sf(data = downstream$waterbody, fill = "steelblue") +
    geom_sf(data = upstream$waterbody, fill = "steelblue") +
    geom_sf(aes(linetype = factor(terminalfl)), data = downstream) +
    # scale_size_discrete("") +
    geom_sf(data = huc12 |> filter(huc12 %in% huc12_codes), fill = NA) +
    geom_sf(data = huc12_outlets) +
    # geom_sf_text(aes(label = identifier), data = huc12_outlets, size = 3) +
    geom_sf(data = upstream$UM_flowlines, color = "lightgreen") +
    theme_bw() +
    labs(x = "", y = "", title = huc8_code)
  p
  # geom_sf_text(aes(label = reachcode), data = downstream$flowline)
  ggsave(sprintf("missing_basin_plots/%s.pdf", huc8_code), width = 10, height = 10)
}

for (huc8_code in missing_huc8s) {
  #
  message(huc8_code)

  huc12_codes <-
    huc12 |>
    filter(substr(huc12, 1, 8) == huc8_code) |>
    pull(huc12)

  terminal_reaches <- list()
  for (huc12_code in huc12_codes) {
    downstream <- tryCatch(find_huc12_downstream(huc12_code),
      error = function(cond) {
        return(NULL)
      }
    )
    if (!is.null(downstream)) {
      terminal_reaches[[huc12_code]] <- downstream$flowline |> filter(terminalfl == 1)
    }
  }
}

missing_huc8 <- huc8 |>
  filter(!(huc8 %in% names(outlet_reach))) |>
  pull(huc8)
