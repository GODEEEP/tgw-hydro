library(tidyverse)
options(
  readr.show_progress = FALSE,
  readr.show_col_types = FALSE,
  pillar.width = 1e6,
  dplyr.summarise.inform = FALSE
)

input_dir <- "godeeep-hydro/"
scenarios <- c("historical", "rcp45cooler", "rcp45hotter", "rcp85cooler", "rcp85hotter")

hydro_plants <- read_csv("godeeep-hydro/godeeep-hydro-plants.csv")

weekly <- scenarios |>
  map(function(scenario) {
    "%s/godeeep-hydro-%s-weekly.csv" |>
      sprintf(input_dir, scenario) |>
      read_csv() #|>
    # mutate(scenario = scenario)
  }) |>
  bind_rows() |>
  filter(!is.na(datetime))

monthly <- scenarios |>
  map(function(scenario) {
    "%s/godeeep-hydro-%s-monthly.csv" |>
      sprintf(input_dir, scenario) |>
      read_csv() #|>
    # mutate(scenario = scenario)
  }) |>
  bind_rows() |>
  filter(!is.na(datetime))

pnw_obs <- read_csv("data/pnw_daily_data_with_libby.csv") |>
  rename(eia_id = EIA_ID) |>
  mutate(datetime = ymd(sprintf("%s-%s-%s", year, month, day)))

sequence_weekly <- tibble(
  date_time = seq(as.POSIXct("1981-01-01 00:00:00"),
    as.POSIXct(sprintf(
      "%s-12-31 23:00:00",
      pnw_obs$datetime |> year() |> max()
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

annual <- monthly |>
  mutate(year = year(datetime)) |>
  group_by(eia_id, plant, year, scenario) |>
  summarise(power_mw = mean(p_avg))

annual2 <- weekly |>
  mutate(year = year(datetime)) |>
  group_by(eia_id, plant, year, scenario) |>
  summarise(power_mw = mean(p_avg))

annual_conus <- monthly |>
  group_by(datetime, scenario) |>
  summarise(power_mw = sum(p_avg)) |>
  mutate(year = year(datetime)) |>
  group_by(year, scenario) |>
  summarise(power_mw = mean(power_mw))

annual_conus |>
  filter(year > 2020) |>
  ggplot() +
  geom_density(aes(power_mw, fill = scenario), alpha = 0.5) +
  theme_bw()

pnw_weekly <- pnw_obs |>
  inner_join(sequence_weekly, by = join_by(year, datetime)) |>
  group_by(eia_id, dam, week_start) |>
  summarise(power_mw_obs = mean(value)) |>
  rename(datetime = week_start)

pnw_monthly <- pnw_obs |>
  filter(variable == "power_MW") |>
  group_by(eia_id, dam, year, month) |>
  summarise(power_mw_obs = mean(value)) |>
  mutate(datetime = ymd(sprintf("%s-%s-01", year, month)))

pnw_annual <- pnw_obs |>
  filter(variable == "power_MW") |>
  group_by(eia_id, dam, year) |>
  summarise(power_mw_obs = mean(value))

weekly |>
  inner_join(pnw_weekly, by = join_by(datetime, eia_id)) |>
  mutate(error = power_mw_obs - p_avg) |>
  filter(scenario == "historical") |>
  ggplot() +
  geom_boxplot(aes(plant, error)) +
  theme_bw() +
  theme(axis.text.x = element_text(angle = 90, vjust = .5))

monthly |>
  inner_join(pnw_monthly, by = join_by(datetime, eia_id)) |>
  mutate(error = power_mw_obs - p_avg) |>
  filter(scenario == "historical") |>
  ggplot() +
  geom_boxplot(aes(plant, error)) +
  theme_bw() +
  theme(axis.text.x = element_text(angle = 90, vjust = .5))

p_annual <- annual |>
  inner_join(pnw_annual, by = join_by(eia_id, year)) |>
  mutate(error = power_mw_obs - power_mw) |>
  filter(scenario == "historical") |>
  # group_by(plant) |>
  # mutate(sd = sd(error)) |>
  # arrange(sd, year) |>
  ggplot() +
  geom_boxplot(aes(plant, error)) +
  theme_bw() +
  labs(x = "", y = "Annual Generation Error [aMW]") +
  theme(axis.text.x = element_text(angle = 90, vjust = .5, hjust = 1))
p_annual
ggsave("plots/annual_verif.pdf", width = 8, height = 5)
