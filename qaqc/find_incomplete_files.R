library(tidyverse)

huc8_dirs <- list.files("tgw-huc8-forcings", full.names = T)
pb <- txtProgressBar(1, length(huc8_dirs), style = 3)
files_to_delete = character(0)
for (huc8_dir in huc8_dirs) {
  setTxtProgressBar(pb, which(huc8_dirs == huc8_dir))
  week_files <- list.files(huc8_dir, full.names = T)
  sizes <- sapply(week_files, function(x) file.info(x)$size)
  f <- sizes[sizes < quantile(sizes, 0.25) - 1.5*IQR(sizes)]
  files_to_delete = c(files_to_delete, f)
}
close(pb)

files_to_delete = names(files_to_delete)
years = substr(files_to_delete,46,49)
huc8s = substr(files_to_delete,19,26)

year_files_to_delete = sprintf('tgw-huc8-forcings-year/%s/tgw_forcing_d01_00625vic_%s_%s.nc',huc8s, huc8s, years)

unlink(year_files_to_delete)
unlink(files_to_delete)