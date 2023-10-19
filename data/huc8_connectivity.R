library(tidyverse)
library(sf)

from <- st_read("/Volumes/data/fpp/fpp.shp") |>
  st_transform(4326)
to <- st_read("/Volumes/data/tpp/tpp.shp") |>
  st_transform(4326) |>
  mutate(outlet = ifelse(HU_12_DS == "OCEAN", "ocean", "internal"))

wbd_path <- "WBD_National_GDB/WBD_National_GDB.gdb"
huc6 <- st_read(wbd_path, "WBDHU6") |>
  filter(substr(huc6, 1, 2) %in% sprintf("%02d", 1:18))
huc8 <- st_read(wbd_path, "WBDHU8") |>
  filter(substr(huc8, 1, 2) %in% sprintf("%02d", 1:18))
huc12 <- st_read(wbd_path, "WBDHU12") |>
  filter(substr(huc12, 1, 2) %in% sprintf("%02d", 1:18))

# huc8_to = numeric(length(huc8$huc8))
huc8_to <- map(huc8$huc8, function(huc8_code) {
  # huc8_code = huc8$huc8
  matches <- huc12 |>
    filter(substr(huc12, 1, 8) == huc8_code) |>
    pull(tohuc) |>
    substr(1, 8) |>
    unique()
  huc <- matches[matches != huc8_code & matches != "CLOSED B"]
  if (length(huc) == 0) NA else huc
}, .progress = TRUE)

huc8_flow <- tibble(
  huc8 = huc8$huc8,
  to1 = huc8_to |> sapply("[", 1) |> tolower(),
  to2 = huc8_to |> sapply("[", 2) |> tolower()
) |>
  mutate(flow_to_type = case_when(
    to1 == "ocean" ~ "ocean",
    to1 == "canada" ~ "canada",
    to1 == "mexico" ~ "mexico",
    !is.na(as.numeric(to1)) | !is.na(as.numeric(to2)) ~ "huc",
    to1 == "closed b" ~ "closed",
    .default = NA_character_
  ))
huc8_connected <- huc8 |> left_join(huc8_flow, by = "huc8")

ggplot() +
  geom_sf(aes(fill = flow_to_type), data = huc8_connected)

huc6_to <- map(huc6$huc6, function(huc6_code) {
  # huc8_code = huc8$huc8
  matches <- huc12 |>
    filter(substr(huc12, 1, 6) == huc6_code) |>
    pull(tohuc) |>
    substr(1, 6) |>
    unique()
  huc <- matches[matches != huc8_code & matches != "CLOSED"]
  if (length(huc) == 0) NA else huc
}, .progress = TRUE)

huc6_flow <- tibble(
  huc6 = huc6$huc6,
  to1 = huc6_to |> sapply("[", 1) |> tolower(),
  to2 = huc6_to |> sapply("[", 2) |> tolower(),
  to3 = huc6_to |> sapply("[", 3) |> tolower()
) |>
  mutate(flow_to_type = case_when(
    !is.na(as.numeric(to1)) | !is.na(as.numeric(to2)) | !is.na(as.numeric(to3)) ~ "huc",
    to1 == "ocean" ~ "ocean",
    to1 == "canada" ~ "canada",
    to1 == "mexico" ~ "mexico",
    to1 == "closed" ~ "closed",
    .default = NA_character_
  ))
huc6_connected <- huc6 |> left_join(huc6_flow, by = "huc6")

ggplot() +
  geom_sf(aes(fill = flow_to_type), data = huc6_connected)

# for(i in 1:length(huc8_to)){
#   huc8_code = huc8$huc8
#   matches = huc12 |>
#     filter(substr(huc12, 1,8)==huc8_code) |>
#     pull(tohuc) |>
#     substr(1,8) |>
#     unique()
#   huc8_to[i] = matches[matches == huc8_code]
# }
