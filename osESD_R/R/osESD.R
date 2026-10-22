


#' Title
#'
#' @param dataset, dataset used for anomaly detection. x label 'value', y label 'anomaly'
#' @param size, size of offline initiating set
#' @param dwin, size of change rate trend vector
#' @param rwin, size of residual rate vector
#' @param maxr, maximum R in sequential ESD
#' @param alpha, alpha for lambda threshold
#' @param condition, TRUE for and, FALSE for or
#' @param visualize, TRUE for plot export, FALSE for only results
#'#' \dontrun{
#' data("A3Benchmark_TS4") # Load the dataset
#' ex_osESD_anoms <- osESD(data=A3Benchmark_TS4, size=100)
#' print(ex_osESD_anoms)
#' }
#' @return indices of anomalies
#' @export
osESD <- function(data,size=100,dwin=5,rwin=5,maxr=10,alpha=0.01,condition=TRUE,visualize=FALSE){
  data<-timestamp_creator(data)
  osESD_anoms <- osESD_Detector(data=data$value, time=data$timestamps, dwin=dwin, rwin=rwin,
                                train_size=size, alpha=alpha, maxr=maxr, condition=condition)
  return (osESD_anoms)
}


