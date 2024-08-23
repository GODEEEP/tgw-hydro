library(tidyverse)

options(
  readr.show_progress = FALSE,
  readr.show_col_types = FALSE,
  pillar.width = 1e6
)

output_dir <- "mosart-output"

huc2s <- 1:18
huc2_names <- c(
  "northeast", "midatlantic", "southatlantic", "greatlakes",
  "ohio", "tennessee", "uppermississippi", "lowermississippi",
  "souris", "missouri", "arkansas", "texas", "riogrande", "uppercolorado",
  "lowercolorado", "greatbasin", "columbia", "california"
)

# "" is the historical scenario
scenarios <- c("historical", "rcp45cooler", "rcp45hotter", "rcp85cooler", "rcp85hotter")

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
  for (scenario in scenarios) {
    #
    huc2 <- huc2s[i]
    huc2_name <- huc2_names[i]
    message(huc2, " ", huc2_name, " ", scenario)

    complete_monthly <- "%s/%s_%s/complete_data_monthly.csv" |>
      sprintf(output_dir, huc2_name, scenario) |>
      read_csv()
    complete_weekly <- "%s/%s_%s/complete_data_weekly.csv" |>
      sprintf(output_dir, huc2_name, scenario) |>
      read_csv() |>
      mutate(year = year(datetime))

    if (scenario == "historical") {
      complete_monthly_historical <- complete_monthly
      complete_weekly_historical <- complete_weekly
    }

    predict_power <- function(eia_ids, complete_data, complete_data_historical) {
      eia_ids |>
        map(function(eia_idi) {
          #
          # print(eia_idi)
          training_data <- complete_data_historical |> filter(eia_id == eia_idi)
          model <- training_data |>
            filter(year > 2001) |>
            select(-c(datetime, eia_id, plant, n, n_hours)) %>%
            lm(power_mwh ~ ., data = .)
          model_nopower <- training_data |>
            select(-c(datetime, eia_id, plant, n, n_hours)) |>
            select(-starts_with("power_tm")) %>%
            lm(power_mwh ~ ., data = .)

          # if (eia_idi == 6388) browser()
          if (scenario == "historical") {
            # B1 data starts in 2002 so we have have to use a different model for the earlier period
            power_preb1 <- predict(model_nopower, training_data |> filter(year < 2002))
            power_b1 <- predict(model, training_data |> filter(year >= 2002 & year <= 2019))

            training_data |>
              select(datetime, outflow_sqrt, inflow, storage_sqrt, n_hours) |>
              mutate(
                year = year(datetime),
                power_predicted_mwh = c(power_preb1, power_b1),
                eia_id = eia_idi
              )
          } else {
            # function to predict power one timestep at a time
            # the first year is lost due to lagging
            future_data <- complete_data |>
              filter(eia_id == eia_idi) |>
              filter(year > 2020)
            np <- nrow(future_data)
            power_future <- numeric(np)

            # do the first iteration
            first_row <- future_data[1, ]
            power_future[1] <- predict(model, first_row)
            n_lag <- nrow(future_data |> filter(year == 2021, eia_id == eia_idi))

            # predict one timestep at a time
            for (r in 2:np) {
              # message(r)
              row <- future_data[r, ]
              if (r == 2) last_row <- first_row
              # shift the data back by one timestep
              for (i in (n_lag - 1):1) {
                row[[paste0("power_tm", i + 1)]] <- last_row[[paste0("power_tm", i)]]
              }
              row[["power_tm1"]] <- last_row[["power_mwh"]]
              power_future[r] <- predict(model, row)
              # sometimes the model produces negative generation, just zero it out
              if (power_future[r] < 0) power_future[r] <- 0
              row[["power_mwh"]] <- power_future[r]
              last_row <- row
              # if(any(is.na(row)))browser()
            }
          }
        }, .progress = T) |>
        bind_rows()
    }

    power_monthly <- predict_power(eia_ids_monthly, complete_monthly, complete_monthly_historical)
    power_weekly <- predict_power(eia_ids_weekly, complete_weekly, complete_weekly_historical)



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
  }
}

constraints_monthly <- bind_rows(constraints_monthly_list)
constraints_weekly <- bind_rows(constraints_weekly_list)

constraints_monthly |>
  mutate(across(where(is.numeric), round, 5)) |>
  write_csv("godeeep-hydro/historical/godeeep-hydro-monthly.csv", )
constraints_weekly |>
  mutate(across(where(is.numeric), round, 5)) |>
  write_csv("godeeep-hydro/historical/godeeep-hydro-weekly.csv")
