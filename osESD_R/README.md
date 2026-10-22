
# Automated Online Sequential ESD (R)

This package includes R codes for online sequential ESD(osESD), a variation of GESD tests.  
It is a statistical testing method for anomaly detection in univariate time series datasets.  
We provide osESD and an automated grid search method auto-osESD.  
Auto-osESD can be used to find the best parameters for a specific dataset,  
using parameters either provided explicitly or basic parameters if not provided.  
Original paper can be found in [LINK].  

## Installation
### 1. Install devtools for R.
Clone or download zip. file of our repository into local device.

'''
install.packages('devtools)
'''

### 2. Install package from writer's github and load.
Download package from writer's github.
This should also download all dependent libraries used within the codes.

```
install_github("iguv221/osESD")
library(osESD)
```


### 3. Datasets.

<!-- [Dataset Link](https://drive.google.com/drive/folders/1ng4eqciexoEOJp_T5D4nwXVN7OVQfBp7?usp=sharing) -->

Yahoo! benchmark datasets are not included in this drive due to Yahoo! license policies.
These can be found and downloaded in 
[Yahoo dataset](https://webscope.sandbox.yahoo.com/catalog.php?datatype=s&did=70&guccounter=1&guce_referrer=aHR0cHM6Ly93d3cuZ29vZ2xlLmNvbS8&guce_referrer_sig=AQAAAAtaVR04P1M9zgds3PzfnAtAVhsUOz4pZiQ5UEtlYB3z1JjyVl2oO-GopA8MTYZoEUJ4AhNDXHLP5SoGcCqai8FnucvuOsaZLXiTF9Xo4-4mXTqcRoUVT-SrkziayaB0j0MDrrVmMyZD0LlaPgFoPJkyePrvECHAfNxfaH_6YjyC) .

A few of the datasets have been loaded into the package, and can be used once package is loaded.
```
data(A2Benchmark_synthetic_44)
data(A2Benchmark_synthetic_19)
data(A3Benchmark_TS79)
data(A3Benchmark_TS86)
data(ARIMA3_lin_4)
data(ARIMA5_quad_2)
data(seasonal_ber_6)
data(seasonal_ber_16)
data(seasonal_ber_21)
```

Again, Yahoo! datasets are under license policies, and must be obliged to.


## Versions
R = 4.4.0
Rstudio = RStudio 2024.04.1+748



## Example Usage

After cloning this repository and installing all dependencies, one can run our osESD method with the below code in R,  
with data_name being directory to dataset and result_directory being directory to where indices of anomalies be exported.

```
ex_osESD_anoms<-run_osESD(data=ex_data,size=size)
```

To run auto-osESD, the below code should be run.  

```
auto_osESD_anoms<-run_auto_osESD(data=ex_data,labeled=labeled,parameters=ex_opt,weights=ex_weights,min_max_switch = min_max_switch)
```

To change parameters and provide new ones, the below code should be modified and run.  

```
ex_opt_list <- list(
  make_option(c("--WindowSizes"), type="double", default=c(50,200)),
  make_option(c("--AndOr"), type="double", default=c(1,0)),
  make_option(c("--MaxRs"), type="double", default=c(3,20)),
  make_option(c("--Dwins"), type="double", default=c(2,30)),
  make_option(c("--Rwins"), type="double", default=c(4,30)),
  make_option(c("--Alphas"), type="double", default=c(0.001,0.05)))

ex_opt <- parse_args(OptionParser(option_list = ex_opt_list))

labeled<-TRUE
min_max_switch<-TRUE
auto_osESD_anoms<-run_auto_osESD(data=ex_data,labeled=labeled,parameters=ex_opt,weights=ex_weights,min_max_switch = min_max_switch)
```

Finally, if the dataset is unlabeled, then one should set '--labeled' to False.  
```
labeled<-FALSE
ex_auto_osESD_anoms_3<-run_auto_osESD(data=ex_data,labeled=labeled)
```
