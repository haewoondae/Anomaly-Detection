

timestamp_creator <- function(data) {
  if (length(data$timestamps)==0){
    time=1:length(data$value)
  }
  else{
    return (list('timestamps'=data$timestamps, 'value'=data$value, 'anomaly'=data$anomaly))
  }
  return (list('timestamps'=time, 'value'=data$value, 'anomaly'=data$anomaly))
}

#' Title
#'
#' @param Reals, indices of real anomalies
#' @param Preds, indices of predicted anomalies
#' @param t1, starting time
#' @param t2, ending time
#'
#' @return precision, recall, f1score, and run time of run method
#' @export
PRFTcalculator <- function(Reals, Preds, t1, t2) {
  TP <- 0
  TN <- 0
  FP <- 0
  FN <- 0
  for (i in 1:length(Reals)) {
    real <- Reals[i]
    pred <- Preds[i]
    if (real == 0 & pred == 0) { TN <- TN + 1 }
    else if (real == 0 & pred == 1) { FP <- FP + 1 }
    else if (real == 1 & pred == 0) { FN <- FN + 1 }
    else { TP <- TP + 1 }
  }
  run_time <- as.numeric(difftime(t2, t1, units="secs"))

  if (TP + FN == 0) {return(list('precision'=0,'recall'=0,'F1Score'=0,'Run_Time'=run_time))}
  else if (TP + FN == 0) { P <- TP / (TP + FP); return(list('precision'=P,'recall'=0,'F1Score'=0,'Run_Time'=run_time)) }
  else if (TP + FP == 0) { R <- TP / (TP + FN); return(list('precision'=0,'recall'=R,'F1Score'=0,'Run_Time'=run_time)) }

  R <- TP / (TP + FN)
  P <- TP / (TP + FP)
  if (R + P == 0) { return(list('precision'=0,'recall'=0,'F1Score'=0,'Run_Time'=run_time)) }
  F1 <- 2 * R * P / (R + P)

  return(list('precision'=P,'recall'=R,'F1Score'=F1,'Run_Time'=run_time))
}
