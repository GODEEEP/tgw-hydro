# Add HUC2 to dam data for filtering
# Cameron Bracken, cameron.bracken@pnnl.gov
# March 2024

library(tidyverse)
library(sf)

options("readr.show_progress" = FALSE, "readr.num_columns" = 0, "readr.show_col_types" = FALSE)

dams <- read_csv("GO_WEST_MOSART_tbl_v6.csv")

huc2 <- st_read("../data/HUC2/HUC2.shp")
huc2_pl <- st_transform(huc2, 2163)
dsf <- st_transform(st_as_sf(dams |> select(lon, lat), coords = c("lon", "lat"), crs = 4326), 2163)
int <- st_intersects(dsf, huc2_pl)
ind <- sapply(int, function(x) {
  ifelse(length(x) > 0, x, NA)
})
dams$HUC2 <- huc2$huc2[ind] |> as.numeric()
dams |> write_csv("GO_WEST_MOSART_tbl_v6_with_HUC2.csv")
