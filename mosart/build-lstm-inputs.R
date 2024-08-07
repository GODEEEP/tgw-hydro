library(tidyverse)
library(ranger)

import::from(janitor, clean_names)
import::from(hydroGOF, KGE)

options(
  readr.show_progress = FALSE,
  readr.show_col_types = FALSE,
  pillar.width = 1e6
)

# huc2s <- c(10, 15, 16, 17, 18)
# huc2_names <- c("missouri", "lowercolorado", "greatbasin", "columbia", "california")

huc2s <- 1:18
huc2_names <- c(
  "northeast", "midatlantic", "southatlantic", "greatlakes",
  "ohio", "tennessee", "uppermississippi", "lowermississippi",
  "souris", "missouri", "arkansas", "texas", "riogrande", "uppercolorado",
  "lowercolorado", "greatbasin", "columbia", "california"
)

huc2_names_plot <- c(
  "Northeast", "Mid Atlantic", "South Atlantic", "Great Lakes",
  "Ohio", "Tennessee", "Upper Mississippi", "Lower Mississippi",
  "Souris", "Missouri", "Arkansas", "Texas", "Rio Grande", "Upper Colorado",
  "Lower Colorado", "Great Basin", "Columbia", "California"
) |> `names<-`(huc2_names)

# huc2s <- 10:18
# huc2_names <- c(
#   "missouri", "arkansas", "texas", "riogrande", "uppercolorado",
#   "lowercolorado", "greatbasin", "columbia", "california"
# )
#
# huc2s <- 9
# huc2_names <- "souris"

read_dam_data <- function(fn, name) {
  fn |>
    read_csv() |>
    pivot_longer(-datetime, values_to = name, names_to = "eia_id") |>
    mutate(eia_id = as.numeric(eia_id))
}


eha <- "data/ORNL_EHAHydroPlant_FY2023_rev.xlsx" |>
  readxl::read_xlsx(sheet = "Operational") %>%
  select(
    eia_id = EIA_PtID, nameplate = CH_MW, mode = Mode, plant = PtName,
    state = State, lat = Lat, lon = Lon,
    nameplate_capacity = CH_MW, nerc_region = NERC, ba = BACode
  ) %>%
  filter(!is.na(eia_id)) %>%
  mutate(mode = if_else(grepl("Run-of-river", mode), "RoR", "Storage")) %>%
  filter(!duplicated(eia_id)) %>%
  unique() |>
  select(eia_id, nameplate_capacity, lat, lon)

b1_monthly <- "data/B1_monthly/" |>
  list.files("*", full.names = T) |>
  map(read_csv) |>
  bind_rows() |>
  mutate(datetime = fast_strptime(sprintf("%s-%s-01", year, month), "%Y-%b-%d") |> as.Date()) |>
  rename_all(tolower) |>
  mutate(power_mwh = target_mwh) |>
  select(datetime, eia_id, plant, power_mwh, p_avg, p_min, p_max) |>
  # all the values for this plant are zero
  group_by(plant) |>
  # don't include plants with all zero gen
  filter(!length(unique(power_mwh)) == 1) |>
  ungroup()

message("Monthly")
all_plants_monthly <-
  1:length(huc2s) |>
  map(function(i) {
    #
    huc2 <- huc2s[i]
    huc2_name <- huc2_names[i]
    message(huc2, " ", huc2_name)

    outflow <- "output/%s/dam_outflow.csv" |>
      sprintf(huc2_name) |>
      read_dam_data("outflow")
    inflow <- "output/%s/dam_inflow.csv" |>
      sprintf(huc2_name) |>
      read_dam_data("inflow")
    storage <- "output/%s/dam_storage.csv" |>
      sprintf(huc2_name) |>
      read_dam_data("storage")

    # build the complete dataset for monthly, include 12 lagged variables
    complete_data_monthly <- outflow |>
      inner_join(inflow, by = join_by(datetime, eia_id)) |>
      inner_join(storage, by = join_by(datetime, eia_id)) |>
      mutate(
        year = year(datetime),
        month = month(datetime)
      ) |>
      group_by(eia_id, year, month) |>
      summarise(
        datetime = datetime[1],
        outflow = mean(outflow),
        inflow = mean(inflow),
        storage = mean(storage),
        .groups = "drop"
      ) |>
      mutate(n_hours = days_in_month(datetime) * 24) |>
      inner_join(b1_monthly, by = join_by(datetime, eia_id)) %>%
      left_join(
        . |>
          group_by(eia_id) |>
          summarise(n = n()),
        by = join_by(eia_id)
      ) |>
      # exclude plants with one year of data or less (one year of data is lost due to lagging)
      filter(n > 12)
  }) |>
  bind_rows()

all_plants_monthly |>
  mutate(year = year(datetime), month = month(datetime)) |>
  group_by(eia_id, year, month) |>
  inner_join(eha, by = join_by(eia_id)) |>
  write_csv("data/mosart_training_data_monthly.csv")

all_plants_complete_monthly <-
  1:length(huc2s) |>
  map(function(i) {
    #
    huc2 <- huc2s[i]
    huc2_name <- huc2_names[i]
    message(huc2, " ", huc2_name)

    training_monthly <- "output/%s/training_data_monthly.csv" |>
      sprintf(huc2_name) |>
      read_csv() |>
      inner_join(b1_monthly, by = join_by(datetime, eia_id))
  }) |>
  bind_rows()

all_plants_complete_monthly |>
  mutate(
    year = year(datetime),
    month = month(datetime)
  ) |>
  group_by(eia_id, year, month) |>
  inner_join(eha, by = join_by(eia_id)) |>
  write_csv("data/mosart_traning_data_monthly_with_lags.csv")

##############################################################
# Weekly
##############################################################

b1_weekly <- "data/B1_weekly/" |>
  list.files("*", full.names = T) |>
  map(read_csv) |>
  bind_rows() |>
  mutate(datetime = week_start) |>
  rename_all(tolower) |>
  mutate(power_mwh = target_mwh) |>
  select(datetime, eia_id, plant, power_mwh) |>
  # all the values for this plant are zero
  group_by(plant) |>
  # don't include plants with all zero gen
  filter(!length(unique(power_mwh)) == 1) |>
  ungroup()

message("Weekly")
all_plants_weekly <-
  1:length(huc2s) |>
  map(function(i) {
    #
    huc2 <- huc2s[i]
    huc2_name <- huc2_names[i]
    message(huc2, " ", huc2_name)

    outflow <- "output/%s/dam_outflow.csv" |>
      sprintf(huc2_name) |>
      read_dam_data("outflow")
    inflow <- "output/%s/dam_inflow.csv" |>
      sprintf(huc2_name) |>
      read_dam_data("inflow")
    storage <- "output/%s/dam_storage.csv" |>
      sprintf(huc2_name) |>
      read_dam_data("storage")

    # set up weekly time sequence
    tibble(
      date_time = seq(as.POSIXct("2001-01-01 00:00:00"),
        as.POSIXct(sprintf(
          "%s-12-31 23:00:00",
          outflow$datetime |> year() |> max()
        )),
        by = "hour"
      )
    ) |>
      mutate(year = year(date_time)) %>%
      split(.$year) |>
      # .[[1]] -> x
      map(
        function(x) {
          # stop()
          x[["date_time"]][1] %>% year() -> yr

          rep(1:53, each = 7) -> weekdef

          x %>%
            # mutate(week_commencing = floor_date(date(date_time), "week", 8)) %>%
            # mutate(week_commencing =
            # if_else(year(week_commencing) < yr, ymd(paste0(yr, "-01-01")), week_commencing)) %>%
            mutate(date = date(date_time)) %>%
            select(-date_time) %>%
            unique() %>%
            mutate(jweek = weekdef[1:n()]) %>%
            group_by(jweek) %>%
            mutate(
              n_hours = 24 * n(),
              week_start = min(date)
            ) |>
            rename(datetime = date)
        }
      ) |>
      bind_rows() ->
    sequence_weekly

    # build the complete dataset for weekly, include 12 lagged variables
    complete_data_weekly <- outflow |>
      inner_join(inflow, by = join_by(datetime, eia_id)) |>
      inner_join(storage, by = join_by(datetime, eia_id)) |>
      left_join(sequence_weekly, by = join_by(datetime)) |>
      na.omit() |>
      group_by(eia_id, week_start) |>
      summarise(
        outflow = mean(outflow),
        inflow = mean(inflow),
        storage = mean(storage),
        n_hours = n_hours[1],
        .groups = "drop"
      ) |>
      rename(datetime = week_start) |>
      inner_join(b1_weekly, by = join_by(datetime, eia_id)) |>
      group_by(eia_id) |>
      group_split() %>%
      bind_rows() %>%
      left_join(
        . |>
          group_by(eia_id) |>
          summarise(n = n()),
        by = join_by(eia_id)
      ) |>
      # exclude plants with one year of data or less (one year of data is lost due to lagging)
      filter(n > 12 * 52)
  }) |>
  bind_rows()

all_plants_weekly |>
  inner_join(eha, by = join_by(eia_id)) |>
  write_csv("data/mosart_training_data_weekly.csv")

all_plants_complete_weekly <-
  1:length(huc2s) |>
  map(function(i) {
    #
    huc2 <- huc2s[i]
    huc2_name <- huc2_names[i]
    message(huc2, " ", huc2_name)

    training_weekly <- "output/%s/training_data_weekly.csv" |>
      sprintf(huc2_name) |>
      read_csv() |>
      inner_join(b1_weekly, by = join_by(datetime, eia_id))
  }) |>
  bind_rows()

all_plants_complete_monthly |>
  mutate(
    year = year(datetime),
    month = month(datetime)
  ) |>
  group_by(eia_id, year, month) |>
  inner_join(eha, by = join_by(eia_id)) |>
  write_csv("data/mosart_traning_data_weekly_with_lags.csv")
