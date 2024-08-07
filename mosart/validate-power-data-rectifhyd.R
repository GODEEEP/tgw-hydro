library(tidyverse)
library(ranger)

import::from(janitor, clean_names)
import::from(hydroGOF, KGE)

options(
  readr.show_progress = FALSE,
  readr.show_col_types = FALSE,
  pillar.width = 1e6
)

huc2 <- 6
huc2_name <- "tennessee"
read_dam_data <- function(fn, name) {
  fn |>
    read_csv() |>
    pivot_longer(-datetime, values_to = name, names_to = "eia_id") |>
    mutate(eia_id = as.numeric(eia_id))
}

outflow <- "output/%s/dam_outflow.csv" |>
  sprintf(huc2_name) |>
  read_dam_data("outflow")
inflow <- "output/%s/dam_inflow.csv" |>
  sprintf(huc2_name) |>
  read_dam_data("inflow")
storage <- "output/%s/dam_storage.csv" |>
  sprintf(huc2_name) |>
  read_dam_data("storage")

rectifhyd <- "../data/RectifHyd_v1.3.csv" |>
  read_csv() |>
  mutate(datetime = fast_strptime(sprintf("%s-%s-01", year, month), "%Y-%b-%d") |> as.Date()) |>
  rename_all(tolower) |>
  mutate(power_mwh = ifelse(recommended_data == "RectifHyd", rectifhyd_mwh, eia_mwh)) |>
  select(datetime, eia_id, plant, power_mwh)

# build the complete dataset, include 12 lagged variables
complete_data <- outflow |>
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
    storage = mean(storage), .groups = "drop"
  ) |>
  inner_join(rectifhyd, by = join_by(datetime, eia_id)) |>
  group_by(eia_id) |>
  group_split() %>% # .[[1]] -> plant
  map(function(plant) {
    plant |>
      arrange(datetime) |>
      mutate(
        outflow_tm1 = lag(outflow, 1),
        outflow_tm2 = lag(outflow, 2),
        outflow_tm3 = lag(outflow, 3),
        outflow_tm4 = lag(outflow, 4),
        outflow_tm5 = lag(outflow, 5),
        outflow_tm6 = lag(outflow, 6),
        outflow_tm7 = lag(outflow, 7),
        outflow_tm8 = lag(outflow, 8),
        outflow_tm9 = lag(outflow, 9),
        outflow_tm10 = lag(outflow, 10),
        outflow_tm11 = lag(outflow, 11),
        outflow_tm12 = lag(outflow, 12),
        # inflow_tm1 = lag(inflow, 1),
        # inflow_tm2 = lag(inflow, 2),
        # inflow_tm3 = lag(inflow, 3),
        # inflow_tm4 = lag(inflow, 4),
        # inflow_tm5 = lag(inflow, 5),
        # inflow_tm6 = lag(inflow, 6),
        # inflow_tm7 = lag(inflow, 7),
        # inflow_tm8 = lag(inflow, 8),
        # inflow_tm9 = lag(inflow, 9),
        # inflow_tm10 = lag(inflow, 10),
        # inflow_tm11 = lag(inflow, 11),
        # inflow_tm12 = lag(inflow, 12),
        # storage_tm1 = lag(storage, 1),
        # storage_tm2 = lag(storage, 2),
        # storage_tm3 = lag(storage, 3),
        # storage_tm4 = lag(storage, 4),
        # storage_tm5 = lag(storage, 5),
        # storage_tm6 = lag(storage, 6),
        # storage_tm7 = lag(storage, 7),
        # storage_tm8 = lag(storage, 8),
        # storage_tm9 = lag(storage, 9),
        # storage_tm10 = lag(storage, 10),
        # storage_tm11 = lag(storage, 11),
        # storage_tm12 = lag(storage, 12),
        power_tm1 = lag(power_mwh, 1),
        power_tm2 = lag(power_mwh, 2),
        power_tm3 = lag(power_mwh, 3),
        power_tm4 = lag(power_mwh, 4),
        power_tm5 = lag(power_mwh, 5),
        power_tm6 = lag(power_mwh, 6),
        power_tm7 = lag(power_mwh, 7),
        power_tm8 = lag(power_mwh, 8),
        power_tm9 = lag(power_mwh, 9),
        power_tm10 = lag(power_mwh, 10),
        power_tm11 = lag(power_mwh, 11),
        power_tm12 = lag(power_mwh, 12)
      ) |>
      na.omit()
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

# cross validation, drop one year at a time and predict the others
power <- complete_data |>
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
        fit <- training_data %>%
          ranger(power_mwh ~ ., data = .)
        test_data$power_mwh_pred <- predict(fit, test_data)$predictions
        test_data
      }) |>
      bind_rows() -> predictions
    plant_data$power_mwh_pred <- predictions$power_mwh_pred
    plant_data
  }, .progress = TRUE) |>
  bind_rows()

kge <- power |>
  group_by(plant) |>
  summarise(kge = KGE(power_mwh_pred, power_mwh))

kge |>
  pull(kge) |>
  mean()

ggplot(kge) +
  geom_histogram(aes(kge), bins = 30, color = "black") +
  theme_bw()
