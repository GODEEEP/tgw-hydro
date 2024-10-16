library(tidyverse)
library(ggthemes)
options(
  readr.show_progress = FALSE,
  readr.show_col_types = FALSE,
  pillar.width = 1e6,
  dplyr.summarise.inform = FALSE
)

huc2_names_plot <- paste(1:18, "-", c(
  "Northeast", "Mid Atlantic", "South Atlantic", "Great Lakes",
  "Ohio", "Tennessee", "Upper Mississippi", "Lower Mississippi",
  "Souris", "Missouri", "Arkansas", "Texas", "Rio Grande", "Upper Colorado",
  "Lower Colorado", "Great Basin", "Columbia", "California"
))
huc2_names <- factor(huc2_names_plot, levels = huc2_names_plot)

gen9505 <- read_csv("data/gen_9505_GODEEEP.csv") |>
  mutate(
    datetime = ymd(sprintf("%s-%s-01", year, month)),
    power_mw = modeled_generation_MWh / days_in_month(datetime) / 24,
    dataset = "9505"
  ) |>
  rename(power_mwh = modeled_generation_MWh) |>
  mutate(model = ifelse(str_detect(model, "VIC"), "VIC", model)) |>
  filter(forcing == "Livneh") |>
  select(-forcing)
huc2_9505 <- read_csv("data/huc2_tbl.csv") |>
  rename(eia_id = eia_plant_id, huc2_9505 = huc2)

godeeep <- read_csv("godeeep_hydro/historical_monthly.csv") |>
  # duplicate hover dam
  filter(eia_id != 154) |>
  filter(eia_id != 8902) |>
  inner_join(huc2_9505, by = "eia_id") |>
  group_by(datetime, huc2) |>
  summarise(power_mwh = sum(power_predicted_mwh)) |>
  mutate(
    power_mw = power_mwh / days_in_month(datetime) / 24,
    hp = "B1hydro",
    model = "VIC",
    year = year(datetime),
    month = month(datetime),
    dataset = "godeeep"
  )

compare <- bind_rows(gen9505, godeeep)
compare2 <- compare |>
  select(-power_mwh) |>
  pivot_wider(names_from = c(hp, model, dataset), values_from = power_mw) |>
  pivot_longer(-c(huc2, year, month, datetime)) |>
  mutate(huc2_name = huc2_names[huc2])


compare |>
  filter(year == 2001) |>
  ggplot() +
  geom_line(aes(datetime, power_mw, color = hp, linetype = model)) +
  facet_wrap(~huc2, scales = "free_y") +
  theme_minimal() +
  scale_x_date(date_labels = "%b") +
  theme(panel.grid.minor = element_blank())

compare2 |>
  ggplot() +
  geom_boxplot(aes(factor(month), value, fill = name)) +
  facet_wrap(~huc2, scales = "free_y") +
  theme_minimal()

# average generation
p_ave_gen <- compare2 |>
  group_by(huc2_name, month, name) |>
  summarise(value = mean(value, na.rm = T)) |>
  ggplot() +
  geom_line(aes(month, value, color = name), linewidth = 1) +
  facet_wrap(~huc2_name, scales = "free_y", nrow = 3) +
  theme_minimal() +
  theme(
    legend.position = "top",
    panel.grid.minor = element_blank()
  ) +
  scale_x_continuous(breaks = c(2, 4, 6, 8, 10, 12)) +
  labs(x = "Month", y = "Average Generation [1982-2013]") +
  scale_color_manual("", values = colorblind_pal()(8)[c(2,3,4,7,6)])
p_ave_gen
ggsave("plots/ave_gen_compare_9505.pdf", width = 10, height = 4)

# difference
compare |>
  select(-power_mwh) |>
  pivot_wider(names_from = c(hp, model, dataset), values_from = power_mw) |>
  na.omit() |>
  mutate(
    diff_godeeep_WMP_PRMS_9505 = B1hydro_VIC_godeeep - WMP_PRMS_9505,
    diff_godeeep_WMP_VIC_9505 = B1hydro_VIC_godeeep - WMP_VIC_9505,
    diff_godeeep_WRES_PRMS_9505 = B1hydro_VIC_godeeep - WRES_PRMS_9505,
    diff_godeeep_WRES_VIC_9505 = B1hydro_VIC_godeeep - WRES_VIC_9505
  ) |>
  select(-c(WMP_PRMS_9505, WMP_VIC_9505, WRES_PRMS_9505, WRES_VIC_9505, B1hydro_VIC_godeeep)) |>
  pivot_longer(-c(huc2, year, month, datetime)) |>
  ggplot() +
  geom_boxplot(aes(factor(month), value, fill = name), outlier.shape = NA) +
  facet_wrap(~huc2, scales = "free_y") +
  theme_minimal() +
  theme(
    legend.position = "top",
    panel.grid.minor = element_blank()
  ) +
  # scale_x_continuous(breaks = c(2, 4, 6, 8, 10, 12)) +
  labs(x = "Month", y = "Average Generation [1982-2013]")
