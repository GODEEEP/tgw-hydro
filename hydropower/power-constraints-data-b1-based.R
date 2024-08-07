library(tidyverse)

options(
  readr.show_progress = FALSE,
  readr.show_col_types = FALSE,
  pillar.width = 1e6
)

huc2s <- 1:18
huc2_names <- c(
  "northeast", "midatlantic", "southatlantic", "greatlakes",
  "ohio", "tennessee", "uppermississippi", "lowermississippi",
  "souris", "missouri", "arkansas", "texas", "riogrande", "uppercolorado",
  "lowercolorado", "greatbasin", "columbia", "california"
)

eha_fn <- "data/ORNL_EHAHydroPlant_FY2023_rev.xlsx"

modes <- readxl::read_xlsx(eha_fn, sheet = "Operational") %>%
  select(
    eia_id = EIA_PtID, nameplate = CH_MW, mode = Mode, plant = PtName,
    state = State, lat = Lat, lon = Lon,
    nameplate_capacity = CH_MW, nerc_region = NERC, ba = BACode
  ) %>%
  filter(!is.na(eia_id)) %>%
  mutate(mode = if_else(grepl("Run-of-river", mode), "RoR", "Storage")) %>%
  filter(!duplicated(eia_id)) %>%
  unique()

monthly_params_general <- read_csv("data/PNW_28_max_min_ador_parameters.csv", show = F) %>%
  rename_all(tolower) |>
  left_join(modes, by = join_by(eia_id)) %>%
  group_by(mode) %>%
  summarise(
    max_param = mean(max_param),
    min_param = mean(min_param),
    ador_param = mean(ador_param)
  )

monthly_params_pnw <- read_csv("data/PNW_28_max_min_ador_parameters.csv", show = F) %>%
  select(-dam) |>
  rename_all(tolower)


weekly_params_general <- read_csv("data/PNW_28_max_min_ador_parameters_WEEKLY_BASED.csv", show = F) %>%
  rename_all(tolower) |>
  left_join(modes, by = join_by(eia_id)) %>%
  group_by(mode) %>%
  summarise(
    max_param = mean(max_param),
    min_param = mean(min_param),
    ador_param = mean(ador_param)
  )

weekly_params_pnw <- read_csv("data/PNW_28_max_min_ador_parameters_WEEKLY_BASED.csv", show = F) %>%
  select(-dam) |>
  rename_all(tolower)


constraints_monthly_list <- constraints_weekly_list <- list()
for (i in 1:length(huc2s)) {
  #
  huc2 <- huc2s[i]
  huc2_name <- huc2_names[i]
  message(huc2, " ", huc2_name)

  training_monthly <- "output/%s/training_data_monthly.csv" |>
    sprintf(huc2_name) |>
    read_csv()
  training_weekly <- "output/%s/training_data_weekly.csv" |>
    sprintf(huc2_name) |>
    read_csv()

  complete_monthly <- "output/%s/complete_data_monthly.csv" |>
    sprintf(huc2_name) |>
    read_csv()
  complete_weekly <- "output/%s/complete_data_weekly.csv" |>
    sprintf(huc2_name) |>
    read_csv()

  # models_monthly <- training_monthly |>
  #   group_by(eia_id) |> # .[[1]] -> plant
  #   group_split() |>
  #   map(function(plant) {
  #     plant |>
  #       select(-c(datetime, eia_id)) %>%
  #       lm(power_mwh ~ ., data = .)
  #   }, .progress = T)
  eia_ids_monthly <- training_monthly |>
    pull(eia_id) |>
    unique()
  # names(models_monthly) <- eia_ids_monthly
  # # models_monthly |> saveRDS("output/columbia/model_power_monthly.rds")
  #
  # models_weekly <- training_weekly |>
  #   group_by(eia_id) |> # .[[1]] -> plant
  #   group_split() |>
  #   map(function(plant) {
  #     plant |>
  #       select(-c(datetime, eia_id)) %>%
  #       lm(power_mwh ~ ., data = .)
  #   }, .progress = T)
  eia_ids_weekly <- training_weekly |>
    pull(eia_id) |>
    unique()
  # names(models_weekly) <- eia_ids_weekly
  # # models_weekly |> saveRDS("output/columbia/model_power_weekly.rds")


  power_monthly <- eia_ids_monthly |>
    map(function(eia_idi) {
      #
      # print(eia_idi)
      complete_data <- complete_monthly |> filter(eia_id == eia_idi)
      training_data <- training_monthly |> filter(eia_id == eia_idi)
      model <- training_data |>
        select(-c(datetime, eia_id)) %>%
        lm(power_mwh ~ ., data = .)

      # if (eia_idi == 6388) browser()
      complete_data |>
        select(datetime, outflow, inflow, n_hours) |>
        mutate(
          power_predicted_mwh = predict(model, complete_data),
          eia_id = eia_idi
        )
    }, .progress = T) |>
    bind_rows()

  power_weekly <- eia_ids_weekly |>
    map(function(eia_idi) {
      #
      # print(eia_idi)
      complete_data <- complete_weekly |> filter(eia_id == eia_idi)
      training_data <- training_weekly |> filter(eia_id == eia_idi)
      model <- training_data |>
        select(-c(datetime, eia_id)) %>%
        lm(power_mwh ~ ., data = .)

      complete_data |>
        select(datetime, outflow, inflow, n_hours) |>
        mutate(
          power_predicted_mwh = predict(model, complete_data),
          eia_id = eia_idi
        )
    }, .progress = T) |>
    bind_rows()



  constraints_monthly_list[[huc2_name]] <- power_monthly |>
    left_join(modes, by = join_by(eia_id)) |>
    left_join(monthly_params_general, by = join_by(mode)) |>
    left_join(monthly_params_pnw, by = join_by(eia_id)) |>
    # use the pnw params for these projects,
    # but use the average params for everywhere else
    mutate(
      max_param = ifelse(is.na(max_param.y), max_param.x, max_param.y),
      min_param = ifelse(is.na(min_param.y), min_param.x, min_param.y),
      ador_param = ifelse(is.na(ador_param.y), ador_param.x, ador_param.y),
    ) |>
    select(-ends_with(c(".y", ".x"))) |>
    mutate(
      p_avg = power_predicted_mwh,
      p_avg = if_else(p_avg < 0, 0, p_avg) / n_hours,
      p_avg = if_else(p_avg > nameplate, nameplate, p_avg)
    ) |>
    mutate(
      p_max = p_avg + max_param * (nameplate - p_avg),
      p_min = min_param * p_avg,
      ador = ador_param * (p_max - p_min)
    )


  constraints_weekly_list[[huc2_name]] <- power_weekly |>
    left_join(modes, by = join_by(eia_id)) |>
    left_join(weekly_params_general, by = join_by(mode)) |>
    left_join(weekly_params_pnw, by = join_by(eia_id)) |>
    # use the pnw params for these projects,
    # but use the average params for everywhere else
    mutate(
      max_param = ifelse(is.na(max_param.y), max_param.x, max_param.y),
      min_param = ifelse(is.na(min_param.y), min_param.x, min_param.y),
      ador_param = ifelse(is.na(ador_param.y), ador_param.x, ador_param.y),
    ) |>
    select(-ends_with(c(".y", ".x"))) |>
    mutate(
      p_avg = power_predicted_mwh,
      p_avg = if_else(p_avg < 0, 0, p_avg) / n_hours,
      p_avg = if_else(p_avg > nameplate, nameplate, p_avg)
    ) |>
    mutate(
      p_max = p_avg + max_param * (nameplate - p_avg),
      p_min = min_param * p_avg,
      ador = ador_param * (p_max - p_min)
    )

  # constraints_monthly
}

constraints_monthly <- bind_rows(constraints_monthly_list)
constraints_weekly <- bind_rows(constraints_weekly_list)

constraints_monthly |>
  mutate(across(where(is.numeric), round, 5)) |>
  write_csv("godeeep-hydro/historical/godeeep-hydro-monthly.csv", )
constraints_weekly |>
  mutate(across(where(is.numeric), round, 5)) |>
  write_csv("godeeep-hydro/historical/godeeep-hydro-weekly.csv")
