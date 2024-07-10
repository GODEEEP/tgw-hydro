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

for (i in 1:length(huc2s)) {
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

  b1_monthly <- "../data/B1_monthly/" |>
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

  b1_weekly <- "../data/B1_weekly/" |>
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
    # inner_join(b1_weekly, by = join_by(datetime, eia_id)) |>
    group_by(eia_id) |>
    group_split() %>%
    # .[[10]] -> plant
    map(function(plant) {
      for (lagi in 1:53) {
        plant[[paste0("outflow_tm", lagi)]] <- lag(plant$outflow, lagi)
        plant[[paste0("inflow_tm", lagi)]] <- lag(plant$inflow, lagi)
        plant[[paste0("storage_tm", lagi)]] <- lag(plant$storage, lagi)
        # plant[[paste0("power_tm", lagi)]] <- lag(plant$power_mwh, lagi)
      }
      plant |> na.omit()
    }) |>
    bind_rows() %>%
    left_join(
      . |>
        group_by(eia_id) |>
        summarise(n = n()),
      by = join_by(eia_id)
    ) |>
    # exclude plants with one year of data or less (one year of data is lost due to lagging)
    filter(n > 12 * 52)

  # save the complete data
  complete_data_weekly |>
    write_csv(sprintf("output/%s/complete_data_weekly.csv", huc2_name))

  # save the training data for weekly
  b1_weekly |>
    inner_join(complete_data_weekly, by = join_by(datetime, eia_id)) |>
    select(
      datetime, eia_id,
      starts_with(c(
        "outflow", "storage", "inflow", "power", "n_hours"
      ))
    ) |>
    write_csv(sprintf("output/%s/training_data_weekly.csv", huc2_name))

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
    # inner_join(b1_monthly, by = join_by(datetime, eia_id)) |>
    group_by(eia_id) |>
    group_split() %>% # .[[1]] -> plant
    map(function(plant) {
      for (lagi in 1:12) {
        plant[[paste0("outflow_tm", lagi)]] <- lag(plant$outflow, lagi)
        plant[[paste0("inflow_tm", lagi)]] <- lag(plant$inflow, lagi)
        plant[[paste0("storage_tm", lagi)]] <- lag(plant$storage, lagi)
        # plant[[paste0("power_tm", lagi)]] <- lag(plant$power_mwh, lagi)
      }
      plant |> na.omit()
    }) |>
    bind_rows() %>%
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
    write_csv(sprintf("output/%s/complete_data_monthly.csv", huc2_name))

  # save the training data for monthly
  b1_monthly |>
    inner_join(complete_data_monthly, by = join_by(datetime, eia_id)) |>
    select(
      datetime, eia_id,
      starts_with(c(
        "outflow", "storage", "inflow", "power", "n_hours"
      ))
    ) |>
    write_csv(sprintf("output/%s/training_data_monthly.csv", huc2_name))

  # cross validation for monthly, drop one year at a time and predict the others
  power_monthly <- complete_data_monthly |>
    inner_join(b1_monthly, by = join_by(datetime, eia_id)) |>
    group_by(eia_id) |>
    group_split() %>%
    # .[[18]] -> plant_data
    map(function(plant_data) {
      unique_years <- plant_data |>
        pull(datetime) |>
        year() |>
        unique()
      unique_years |>
        map(function(drop_year) {
          #
          # print(drop_year)
          training_data <- plant_data |>
            filter(year(datetime) != drop_year) |>
            select(-c(datetime, eia_id, plant))
          test_data <- plant_data |>
            filter(year(datetime) == drop_year) |>
            select(-c(datetime, eia_id, plant))
          if (nrow(training_data) == 0 | nrow(test_data) == 0) {
            return(NULL)
          }
          # fit <- training_data %>%
          #   ranger(power_mwh ~ ., data = .)
          # test_data$power_mwh_pred <- predict(fit, test_data)$predictions

          fitlm1 <- training_data %>%
            lm(log1p(power_mwh) ~ outflow, data = .)
          test_data$power_mwh_pred_lm1 <- predict(fitlm1, test_data)

          fitlm2 <- training_data %>%
            lm(log1p(power_mwh) ~ ., data = .)
          test_data$power_mwh_pred_lm2 <- predict(fitlm2, test_data)

          test_data
        }) |>
        bind_rows() -> predictions
      # plant_data$power_mwh_pred <- predictions$power_mwh_pred
      plant_data$power_mwh_pred_lm1 <- predictions$power_mwh_pred_lm1
      plant_data$power_mwh_pred_lm2 <- predictions$power_mwh_pred_lm2
      plant_data
    }, .progress = TRUE) |>
    bind_rows()

  power_monthly |> write_csv(sprintf("output/%s/cross_validation_data_monthly.csv", huc2_name))


  # cross validation, drop one year at a time and predict the others
  power_weekly <- complete_data_weekly |>
    inner_join(b1_weekly, by = join_by(datetime, eia_id)) |>
    group_by(eia_id) |>
    group_split() %>%
    # .[[18]] -> plant_data
    map(function(plant_data) {
      unique_years <- plant_data |>
        pull(datetime) |>
        year() |>
        unique()
      unique_years |>
        map(function(drop_year) {
          #
          # print(drop_year)
          training_data <- plant_data |>
            filter(year(datetime) != drop_year) |>
            select(-c(datetime, eia_id, plant))
          test_data <- plant_data |>
            filter(year(datetime) == drop_year) |>
            select(-c(datetime, eia_id, plant))
          if (nrow(training_data) == 0 | nrow(test_data) == 0) {
            return(NULL)
          }
          # fit <- training_data %>%
          #   ranger(power_mwh ~ ., data = .)
          # test_data$power_mwh_pred <- predict(fit, test_data)$predictions

          fitlm1 <- training_data %>%
            lm(log1p(power_mwh) ~ outflow, data = .)
          test_data$power_mwh_pred_lm1 <- predict(fitlm1, test_data)

          fitlm2 <- training_data %>%
            lm(log1p(power_mwh) ~ ., data = .)
          test_data$power_mwh_pred_lm2 <- predict(fitlm2, test_data)


          test_data
        }) |>
        bind_rows() -> predictions
      # plant_data$power_mwh_pred <- predictions$power_mwh_pred
      plant_data$power_mwh_pred_lm1 <- predictions$power_mwh_pred_lm1
      plant_data$power_mwh_pred_lm2 <- predictions$power_mwh_pred_lm2
      plant_data
    }, .progress = TRUE) |>
    bind_rows()

  power_weekly |> write_csv(sprintf("output/%s/cross_validation_data_weekly.csv", huc2_name))
}
