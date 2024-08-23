library(tidyverse)

import::from(janitor, clean_names)
import::from(hydroGOF, KGE)

options(
  readr.show_progress = FALSE,
  readr.show_col_types = FALSE,
  pillar.width = 1e6
)

output_dir <- "mosart-output"

huc2s <- c(1:9, 11:18) # 1:18
huc2_names <- c(
  "northeast", "midatlantic", "southatlantic", "greatlakes",
  "ohio", "tennessee", "uppermississippi", "lowermississippi",
  "souris",
  # "missouri",
  "arkansas", "texas", "riogrande", "uppercolorado",
  "lowercolorado", "greatbasin", "columbia", "california"
)

# huc2s <- c(10)
# huc2_names <- c(
# "missouri"
# )

scenarios <- c("historical", "rcp45cooler", "rcp45hotter", "rcp85cooler", "rcp85hotter")

read_dam_data <- function(fn, name) {
  fn |>
    read_csv() |>
    pivot_longer(-datetime, values_to = name, names_to = "eia_id") |>
    mutate(eia_id = as.numeric(eia_id))
}

b1_monthly <- "data/B1_monthly/" |>
  list.files("*", full.names = T) |>
  map(read_csv) |>
  bind_rows() |>
  mutate(datetime = fast_strptime(sprintf("%s-%s-01", year, month), "%Y-%b-%d") |> as.Date()) |>
  rename_all(tolower) |>
  mutate(power_mwh = target_mwh) |>
  select(datetime, eia_id, plant, power_mwh) |>
  # all the values for this plant are zero
  group_by(plant) |>
  # don't include plants with all zero gen
  filter(!length(unique(power_mwh)) == 1) |>
  ungroup()

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

for (i in 1:length(huc2s)) {
  for (scenario in scenarios) {
    #
    huc2 <- huc2s[i]
    huc2_name <- huc2_names[i]
    message(huc2, " ", huc2_name, " ", scenario)

    outflow <- "%s/%s_%s/dam_outflow.csv" |>
      sprintf(output_dir, huc2_name, scenario) |>
      read_dam_data("outflow")
    inflow <- "%s/%s_%s/dam_inflow.csv" |>
      sprintf(output_dir, huc2_name, scenario) |>
      read_dam_data("inflow")
    storage <- "%s/%s_%s/dam_storage.csv" |>
      sprintf(output_dir, huc2_name, scenario) |>
      read_dam_data("storage")

    # set up weekly time sequence
    sequence_weekly <- tibble(
      date_time = seq(as.POSIXct("1981-01-01 00:00:00"),
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
      bind_rows()

    # build the complete dataset for weekly, include 12 lagged variables
    complete_data_weekly <- outflow |>
      inner_join(inflow, by = join_by(datetime, eia_id)) |>
      inner_join(storage, by = join_by(datetime, eia_id)) |>
      mutate(
        outflow = ifelse(outflow < 0, 0, outflow),
        storage = ifelse(storage < 0, 0, storage),
        inflow = ifelse(inflow < 0, 0, inflow)
      ) |>
      left_join(sequence_weekly, by = join_by(datetime)) |>
      na.omit() |>
      group_by(eia_id, week_start) |>
      summarise(
        # power is nonlinear with outflow
        outflow_sqrt = sqrt(mean(outflow)),
        inflow = mean(inflow),
        storage_sqrt = sqrt(mean(storage)),
        n_hours = n_hours[1],
        .groups = "drop"
      ) |>
      rename(datetime = week_start) |>
      left_join(b1_weekly, by = join_by(datetime, eia_id)) |>
      group_by(eia_id) |>
      group_split() |>
      # .[[10]] -> plant
      map(function(plant) {
        for (lagi in 1:53) {
          plant[[paste0("outflow_sqrt_tm", lagi)]] <- lag(plant$outflow_sqrt, lagi) |> round(2)
          plant[[paste0("inflow_tm", lagi)]] <- lag(plant$inflow, lagi) |> round(2)
          plant[[paste0("storage_sqrt_tm", lagi)]] <- lag(plant$storage_sqrt, lagi) |> round(2)
          plant[[paste0("power_tm", lagi)]] <- lag(plant$power_mwh, lagi) |> round(2)
        }
        plant |>
          fill(plant, .direction = "updown") |>
          filter(year(datetime) > 1981)
      }) |>
      bind_rows() |>
      # filter out plants that have no B1 data
      filter(!is.na(plant)) %>%
      left_join(
        . |>
          group_by(eia_id) |>
          summarise(n = n()),
        by = join_by(eia_id)
      ) |>
      # exclude plants with one year of data or less (one year of data is lost due to lagging)
      filter(n > 52)

    # save the complete data
    complete_data_weekly |>
      write_csv(sprintf("%s/%s_%s/complete_data_weekly.csv", output_dir, huc2_name, scenario))

    # build the complete dataset for monthly, include 12 lagged variables
    complete_data_monthly <- outflow |>
      inner_join(inflow, by = join_by(datetime, eia_id)) |>
      inner_join(storage, by = join_by(datetime, eia_id)) |>
      mutate(
        outflow = ifelse(outflow < 0, 0, outflow),
        storage = ifelse(storage < 0, 0, storage),
        inflow = ifelse(inflow < 0, 0, inflow),
        year = year(datetime),
        month = month(datetime)
      ) |>
      group_by(eia_id, year, month) |>
      summarise(
        datetime = datetime[1],
        # power is nonlinear with outflow
        outflow_sqrt = sqrt(mean(outflow)),
        inflow = mean(inflow),
        storage_sqrt = sqrt(mean(storage)),
        .groups = "drop"
      ) |>
      mutate(n_hours = days_in_month(datetime) * 24) |>
      left_join(b1_monthly, by = join_by(datetime, eia_id)) |>
      group_by(eia_id) |>
      group_split() %>% # .[[1]] -> plant
      map(function(plant) {
        for (lagi in 1:12) {
          plant[[paste0("outflow_sqrt_tm", lagi)]] <- lag(plant$outflow_sqrt, lagi) |> round(2)
          plant[[paste0("inflow_tm", lagi)]] <- lag(plant$inflow, lagi) |> round(2)
          plant[[paste0("storage_sqrt_tm", lagi)]] <- lag(plant$storage_sqrt, lagi) |> round(2)
          plant[[paste0("power_tm", lagi)]] <- lag(plant$power_mwh, lagi) |> round(2)
        }
        plant |>
          # this adds the plant name to all rows so that locations without plant 
          # names can be filtered out later
          fill(plant, .direction = "updown") |>
          filter(year(datetime) > 1981)
      }) |>
      bind_rows() |>
      filter(!is.na(plant)) %>%
      left_join(
        . |>
          group_by(eia_id) |>
          summarise(n = n()),
        by = join_by(eia_id)
      ) |>
      # exclude plants with one year of data or less (one year of data is lost due to lagging)
      filter(n > 12)

    # save the complete data
    complete_data_monthly |>
      write_csv(sprintf("%s/%s_%s/complete_data_monthly.csv", output_dir, huc2_name, scenario))
  }
}
