library(tidyverse)
library(ranger)

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

kge_weekly_conus_list <- kge_monthly_conus_list <- list()

for (i in 1:length(huc2s)) {
  #
  huc2 <- huc2s[i]
  huc2_name <- huc2_names[i]
  message(huc2, " ", huc2_name)

  #########################################################
  # Monthly
  #########################################################
  power_monthly <- "%s/%s_historical/cross_validation_data_monthly.csv" |>
    sprintf(output_dir, huc2_name) |>
    read_csv()

  # compute drop-one year CV KGE
  kge_monthly <- power_monthly |>
    filter(eia_id != 359) |>
    group_by(plant) |>
    summarise(
      # kge_rf = KGE(power_mwh_pred, power_mwh),
      `hydrofixr original` = KGE(power_mwh_pred_lm1, power_mwh),
      `hydrofixr updated` = KGE(power_mwh_pred_lm2, power_mwh)
      # `hydrofixr updated power transform` = KGE(power_mwh_pred_lm3, power_mwh)
    ) |>
    pivot_longer(-plant, values_to = "kge")

  kge_monthly |> write_csv(sprintf("%s/%s_historical/cross_validation_stats_monthly.csv", output_dir, huc2_name))
  # print(problems(kge_monthly))

  kge_monthly_conus_list[[huc2]] <- kge_monthly |> mutate(
    huc2 = huc2,
    huc2_name = huc2_name,
    huc2_name_plot = huc2_names_plot[huc2_name]
  )

  # compute ave for plot label
  ave_kge <- kge_monthly |>
    group_by(name) |>
    summarise(kge = mean(kge, na.rm = T)) |>
    mutate(
      text = paste0("Ave KGE: ", round(kge, 3)),
      x = min(kge_monthly$kge), y = Inf
    )

  p_kge_monthly <- ggplot(kge_monthly) +
    geom_histogram(aes(kge), bins = 30, color = "black") +
    facet_wrap(~name) +
    geom_text(aes(kge, y, label = text), vjust = 1.5, data = ave_kge, hjust = 1.1) +
    geom_vline(aes(xintercept = kge), data = ave_kge) +
    theme_bw() +
    theme(panel.grid.minor = element_blank()) +
    labs(x = "KGE", y = "Number of plants", title = sprintf("HUC %02d - %s", huc2, huc2_names_plot[huc2_name]))
  p_kge_monthly
  ggsave("plots/power_kge_monthly_huc%02d.png" |> sprintf(huc2), p_kge_monthly, width = 8, height = 4)
  # scale_x_continuous(limits = c(0, 1))

  #########################################################
  # Weekly
  #########################################################
  power_weekly <- "%s/%s/cross_validation_data_weekly.csv" |>
    sprintf(output_dir, huc2_name) |>
    read_csv()

  # compute drop-one year CV KGE
  kge_weekly <- power_weekly |>
    filter(eia_id != 359) |>
    group_by(plant) |>
    summarise(
      # kge_rf = KGE(power_mwh_pred, power_mwh),
      `hydrofixr original` = KGE(power_mwh_pred_lm1, power_mwh),
      `hydrofixr updated` = KGE(power_mwh_pred_lm2, power_mwh)
      # `hydrofixr updated power transform` = KGE(power_mwh_pred_lm3, power_mwh),
      `GLM` = KGE(power_mwh_pred_glm, power_mwh)
    ) |>
    pivot_longer(-plant, values_to = "kge")

  kge_weekly_conus_list[[huc2]] <- kge_weekly |> mutate(
    huc2 = huc2,
    huc2_name = huc2_name,
    huc2_name_plot = huc2_names_plot[huc2_name]
  )

  kge_weekly |> write_csv(sprintf("%s/%s/cross_validation_stats_weekly.csv", output_dir, huc2_name))
  # print(problems(kge_weekly))

  # compute ave for plot label
  ave_kge <- kge_weekly |>
    group_by(name) |>
    summarise(kge = mean(kge, na.rm = T)) |>
    mutate(
      text = paste0("Ave KGE: ", round(kge, 3)),
      x = min(kge_weekly$kge), y = Inf
    )

  p_kge_weekly <- ggplot(kge_weekly) +
    geom_histogram(aes(kge), bins = 30, color = "black") +
    facet_wrap(~name) +
    geom_text(aes(kge, y, label = text), vjust = 1.5, data = ave_kge, hjust = 1.2) +
    geom_vline(aes(xintercept = kge), data = ave_kge) +
    theme_bw() +
    theme(panel.grid.minor = element_blank()) +
    labs(x = "KGE", y = "Number of plants", title = sprintf("HUC %02d - %s", huc2, huc2_names_plot[huc2_name]))
  p_kge_weekly
  ggsave("plots/power_kge_weekly_huc%02d.png" |> sprintf(huc2), p_kge_weekly, width = 8, height = 4)
}

# combine all the huc2 basins
kge_conus <- bind_rows(
  bind_rows(kge_monthly_conus_list) |> mutate(dataset = "monthly"),
  bind_rows(kge_weekly_conus_list) |> mutate(dataset = "weekly")
)

#
ave_kge_conus <- kge_conus |>
  group_by(name, dataset) |>
  summarise(
    min_kge = min(kge),
    kge = mean(kge, na.rm = T),
    .groups = "drop"
  ) |>
  mutate(
    text = paste0("Ave. KGE: ", round(kge, 3)),
    x = min_kge, y = Inf
  )

p_kge_conus <- ggplot(kge_conus |> filter(kge > -1.5)) +
  geom_histogram(aes(kge), bins = 30, color = "black") +
  facet_wrap(~name) +
  geom_text(aes(kge, y, label = text), vjust = 1.5, data = ave_kge_conus, hjust = 1.2) +
  geom_vline(aes(xintercept = kge), data = ave_kge_conus) +
  facet_grid(dataset ~ name) +
  theme_bw() +
  theme(panel.grid.minor = element_blank()) +
  labs(x = "KGE", y = "Number of plants", title = "CONUS")
p_kge_conus
ggsave("plots/power_kge_conus.png", p_kge_conus, width = 8, height = 6)

p_kge_conus2 <- ggplot(kge_conus |> filter(kge > -1.5, name == "hydrofixr updated")) +
  geom_histogram(aes(kge), bins = 30, color = "black") +
  facet_wrap(~dataset) +
  geom_text(aes(kge, y, label = text),
    vjust = 1.5,
    data = ave_kge_conus |> filter(kge > -1.5, name == "hydrofixr updated"),
    hjust = 1.2
  ) +
  # geom_vline(aes(xintercept = kge), data = ave_kge_conus |> filter(kge > -1.5, name == "hydrofixr updated")) +
  # facet_grid(dataset ~ name) +
  theme_bw() +
  theme(panel.grid.minor = element_blank()) +
  labs(x = "KGE", y = "Number of plants")
p_kge_conus2
ggsave("plots/power_kge_conus_new_only.pdf", p_kge_conus2, width = 6, height = 3)
