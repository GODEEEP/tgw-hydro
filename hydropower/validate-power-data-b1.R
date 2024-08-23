library(tidyverse)

import::from(janitor, clean_names)
import::from(hydroGOF, KGE)

options(
  readr.show_progress = FALSE,
  readr.show_col_types = FALSE,
  pillar.width = 1e6
)

output_dir <- "mosart-output"

# huc2s <- c(10, 15, 16, 17, 18)
# huc2_names <- c("missouri", "lowercolorado", "greatbasin", "columbia", "california")

huc2s <- 1:18
huc2_names <- c(
  "northeast", "midatlantic", "southatlantic", "greatlakes",
  "ohio", "tennessee", "uppermississippi", "lowermississippi",
  "souris", "missouri", "arkansas", "texas", "riogrande", "uppercolorado",
  "lowercolorado", "greatbasin", "columbia", "california"
)

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
  #
  huc2 <- huc2s[i]
  huc2_name <- huc2_names[i]
  message(huc2, " ", huc2_name)

  complete_data_monthly <- "%s/%s_historical/complete_data_monthly.csv" |>
    sprintf(output_dir, huc2_name) |>
    read_csv() |>
    na.omit()
  complete_data_weekly <- "%s/%s_historical/complete_data_weekly.csv" |>
    sprintf(output_dir, huc2_name) |>
    read_csv() |>
    na.omit()

  cross_validation <- function(complete_data) {
    complete_data |>
      group_by(eia_id) |>
      group_split() %>%
      # .[[1]] -> plant_data
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
              select(-c(datetime, eia_id, plant, n, n_hours))
            test_data <- plant_data |>
              filter(year(datetime) == drop_year) |>
              select(-c(datetime, eia_id, plant, n, n_hours))
            if (nrow(training_data) == 0 | nrow(test_data) == 0) {
              return(NULL)
            }
            # fit <- training_data %>%
            #   ranger(power_mwh ~ ., data = .)
            # test_data$power_mwh_pred <- predict(fit, test_data)$predictions

            # this is the original version of the hydrofixr model, for comparison
            fitlm1 <- training_data |>
              mutate(outflow = outflow_sqrt^2) %>%
              lm(power_mwh ~ outflow, data = .)
            test_data$power_mwh_pred_lm1 <- predict(
              fitlm1,
              test_data |> mutate(outflow = outflow_sqrt^2)
            )

            # updated regression model using lagged variables no transformation
            fitlm2 <- training_data %>%
              lm(power_mwh ~ ., data = .)
            test_data$power_mwh_pred_lm2 <- predict(fitlm2, test_data)

            # # updated regression model using lagged variables with transformation
            # fitlm3 <- training_data %>%
            #   lm(log1p(power_mwh) ~ ., data = .)
            # test_data$power_mwh_pred_lm3 <- expm1(predict(fitlm3, test_data))

            test_data
          }) |>
          bind_rows() -> predictions
        # plant_data$power_mwh_pred <- predictions$power_mwh_pred
        plant_data$power_mwh_pred_lm1 <- predictions$power_mwh_pred_lm1
        plant_data$power_mwh_pred_lm2 <- predictions$power_mwh_pred_lm2
        # plant_data$power_mwh_pred_lm3 <- predictions$power_mwh_pred_lm3
        plant_data
      }, .progress = TRUE) |>
      bind_rows()
  }
  power_monthly <- cross_validation(complete_data_monthly)
  power_monthly |> write_csv(sprintf("%s/%s_historical/cross_validation_data_monthly.csv", output_dir, huc2_name))

  power_weekly <- cross_validation(complete_data_weekly)
  power_weekly |> write_csv(sprintf("%s/%s_historical/cross_validation_data_weekly.csv", output_dir, huc2_name))
}
