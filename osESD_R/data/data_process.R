# # File: prepare_data.R located in data-raw/
# rm(list=ls())
# library(usethis)
# library(tidyverse)  # if you need to do data manipulation
#
# setwd(dirname(rstudioapi::getSourceEditorContext()$path))
# getwd()
#
# seasonal_ber_21 <- read.csv(paste0("seasonal_ber_21",".csv"))
# use_data(list = seasonal_ber_21, overwrite = TRUE)
