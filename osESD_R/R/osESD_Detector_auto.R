
library(optparse)

osESD_Detector_auto <- function(database, data_label, weights, par_len, parameters, min_max_switch) {

  if(sum(weights)<=0){
    stop("Weight value must be above 0.")
  }

  weights<-weights/sum(weights)
  if (length(parameters)==1){
    print("No parameters found for input, will use basic default parameter set")
    opt_list <- list(
      make_option(c("--WindowSizes"), type="double", default=c(50,100,150,200)),
      make_option(c("--AndOr"), type="double", default=c(1,0)),
      make_option(c("--MaxRs"), type="double", default=c(3,5,7,10)),
      make_option(c("--Dwins"), type="double", default=c(2,5,10,30)),
      make_option(c("--Rwins"), type="double", default=c(4,5,10,30)),
      make_option(c("--Alphas"), type="double", default=c(0.001,0.005,0.01,0.05)))
    opt_parser <- OptionParser(option_list = opt_list)
    opt <- parse_args(opt_parser)
  }

  else if (min_max_switch){
    print("Parameters expanded according to Min and Max input values")
    A1<-c(parameters$WindowSize[1])
    A2<-c(1,0)
    A3<-c(parameters$MaxRs[1])
    A4<-c(parameters$Dwins[1])
    A5<-c(parameters$Rwins[1])
    A6<-c(parameters$Alphas[1])

    Interval <- 4
    for (i in 1:Interval){
      A1<-c(A1,as.integer((parameters$WindowSize[1]*(Interval-i)+parameters$WindowSize[2]*(i))/Interval))
    }
    for (i in 1:Interval){
      A3<-c(A3,as.integer((parameters$MaxRs[1]*(Interval-i)+parameters$MaxRs[2]*(i))/Interval))
    }
    for (i in 1:Interval){
      A4<-c(A4,as.integer((parameters$Dwins[1]*(Interval-i)+parameters$Dwins[2]*(i))/Interval))
    }
    for (i in 1:Interval){
      A5<-c(A5,as.integer((parameters$Rwins[1]*(Interval-i)+parameters$Rwins[2]*(i))/Interval))
    }
    for (i in 1:Interval){
      A6<-c(A6,(parameters$Alphas[1]*(Interval-i)+parameters$Alphas[2]*(i))/Interval)
    }
    opt_list <- list(
      make_option(c("--WindowSizes"), type="double", default=A1),
      make_option(c("--AndOr"), type="double", default=A2),
      make_option(c("--MaxRs"), type="double", default=A3),
      make_option(c("--Dwins"), type="double", default=A4),
      make_option(c("--Rwins"), type="double", default=A5),
      make_option(c("--Alphas"), type="double", default=A6))
    opt_parser <- OptionParser(option_list = opt_list)
    opt <- parse_args(opt_parser)
  }
  else {
    print("Will use input parameters")
  }

  par_len <- as.integer(length(database$value)*par_len)
  database<-timestamp_creator(database)

  if (data_label==TRUE){
    anoms<-database$anomaly
    data<-database$value
    time<-database$timestamps
    par_anoms <- as.factor(anoms[1:par_len])
  }
  else{
    data_front<- database$value[1:par_len]
    cont_data <- contaminate(ts = data_front, alpha = 0.01, anom_percent = 0.02,func="quad")
    par_anoms<-cont_data$anomaly
    par_data<-cont_data$value
    par_time<-database$timestamps[1:par_len]
    data<-database$value
    time<-database$timestamps
  }

  Max_Score1<--.Machine$integer.max
  Max_Score2<--.Machine$integer.max
  Max_Score3<--.Machine$integer.max
  Max_Score4<--.Machine$integer.max
  Max_Score5<--.Machine$integer.max

  Max_Pars1<-c()
  Max_Pars2<-c()
  Max_Pars3<-c()
  Max_Pars4<-c()
  Max_Pars5<-c()

  Total_length<-length(opt$AndOr)*length(opt$WindowSize)*length(opt$MaxRs)*length(opt$Dwins)*length(opt$Rwins)*length(opt$Alphas)

  param_idx<-0
  for (andor in opt$AndOr){
    for (win_size in opt$WindowSize){
      for (maxr in opt$MaxRs){
        for (dwin in opt$Dwins){
          for (rwin in opt$Rwins){
            for (alpha in opt$Alphas){

              if (param_idx != 0 & param_idx %% (floor((Total_length/4))) == 0) {
                percent <- param_idx/Total_length * 100
                print(paste0(percent, " % done."))
              }

              param_idx<-param_idx+1
              win_size <- min(win_size,as.integer(par_len*0.1))

              new_pars <- c(andor,win_size,maxr,dwin,rwin,alpha)
              t1<-Sys.time()
              if (data_label==TRUE){
                anomal_preds<-grid_search_osESD(data=data,time=time,full_size=par_len,init_size=win_size,params=new_pars)
              }
              else{
                anomal_preds<-grid_search_osESD(data=par_data,time=par_time,full_size=par_len,init_size=win_size,params=new_pars)
              }
              t2<-Sys.time()

              scores<-GetPRF(par_anoms,anomal_preds)
              run_time<-t2-t1
              scores<-c(scores,-run_time)
              Score<-0
              for(i in 1:4){
                Score<-Score+scores[i]*weights[i]
              }


              if (Score>Max_Score1){
                s<-Max_Score1
                p<-Max_Pars1
                Max_Score1<-Score
                Max_Pars1<-new_pars
                Score<-s
                new_pars<-p
              }
              if (Score>Max_Score2){
                s<-Max_Score2
                p<-Max_Pars2
                Max_Score2<-Score
                Max_Pars2<-new_pars
                Score<-s
                new_pars<-p
              }
              if (Score>Max_Score3){
                s<-Max_Score3
                p<-Max_Pars3
                Max_Score3<-Score
                Max_Pars3<-new_pars
                Score<-s
                new_pars<-p
              }
              if (Score>Max_Score4){
                s<-Max_Score4
                p<-Max_Pars4
                Max_Score4<-Score
                Max_Pars4<-new_pars
                Score<-s
                new_pars<-p
              }
              if (Score>Max_Score5){
                s<-Max_Score5
                p<-Max_Pars5
                Max_Score5<-Score
                Max_Pars5<-new_pars
                Score<-s
                new_pars<-p
              }
            }
          }
        }
      }
    }
  }

  ADD<-4

  param_df<-data.frame()
  param_df<-rbind(param_df,Max_Pars1)
  for (i in 1:(ADD-1)){
    new_pars<-((Max_Pars1*(ADD-i)+Max_Pars2*i)/ADD)
    param_df<-rbind(param_df,new_pars)
  }
  param_df<-rbind(param_df,Max_Pars2)
  for (i in 1:(ADD-1)){
    new_pars<-((Max_Pars2*(ADD-i)+Max_Pars5*i)/ADD)
    param_df<-rbind(param_df,new_pars)
  }
  param_df<-rbind(param_df,Max_Pars5)
  for (i in 1:(ADD-1)){
    new_pars<-((Max_Pars1*(ADD-i)+Max_Pars5*i)/ADD)
    param_df<-rbind(param_df,new_pars)
  }

  Final_Score<--1
  for (i in 1:(ADD*3)){
    param<-c(math_round(param_df[i,1]))
    for (j in 2:5){
      param<-c(param,as.integer(param_df[i,j]))
    }
    param<-c(param,param_df[i,6])


    t1<-Sys.time()

    if (data_label==TRUE){
      anomal_preds<-grid_search_osESD(data=data,time=time,full_size=par_len,init_size=param[2],params=param)
    }
    else{
      anomal_preds<-grid_search_osESD(data=par_data,time=par_time,full_size=par_len,init_size=param[2],params=param)
    }


    t2<-Sys.time()

    scores<-GetPRF(par_anoms,anomal_preds)
    run_time<-t2-t1
    scores<-c(scores,-run_time)
    Score<-0
    for(i in 1:4){
      Score<-Score+scores[i]*weights[i]
    }

    if (Score>Final_Score){
      Final_Param<-param
      Final_Score<-Score
    }
  }

  ### FULL FINAL LEARNING
  final_anomal_preds <- grid_search_osESD(data=data,time=time,full_size=length(data),init_size=Final_Param[2],params=Final_Param)
  final_anomaly_index <- which(final_anomal_preds == 1)
  final_anomaly_index <- final_anomaly_index[final_anomaly_index > Final_Param[2]]
  return (list('preds'=final_anomaly_index,'params'=Final_Param))
}




grid_search_osESD<-function(data,time,full_size,init_size,params){
  rwin<-params[5]
  train_data <- data[1:init_size]
  online_data <- data[(init_size+1):full_size]
  train_time <- time[1:init_size]
  online_time <- time[(init_size+1):full_size]
  c_ins <- osESD_TCHA$new(data=train_data, time=train_time, wins=params[4])
  r_ins <- osESD_TRES$new(data=train_data, time=train_time, wins=rwin)
  SESD_TCHA <- osESD_vector$new(data=c_ins$tcha, alpha=params[6], maxr=params[3])
  SESD_TRES <- osESD_vector$new(data=r_ins$tres, alpha=params[6], maxr=params[3])
  anomal_index <- c()
  for(i in 1:length(online_data)) {
    canom <- SESD_TCHA$test(c_ins$update(online_data[i], online_time[i]))
    ranom <- SESD_TRES$test(r_ins$update(online_data[i], online_time[i]))
    if (params[1]){function_<-(canom && ranom)
    }else {function_<-(canom||ranom)}
    if (function_){
      anomal_index <- c(anomal_index, (i+init_size))
      data_ <- r_ins$data[-rwin]
      time_ <- r_ins$time[-rwin]
      x_bar <- ((rwin * r_ins$x_bar) - r_ins$time[rwin])/(rwin-1)
      y_bar <- ((rwin * r_ins$y_bar) - r_ins$data[rwin])/(rwin-1)
      beta_ <- sum((time_-x_bar)*(data_-y_bar))/sum((time_-x_bar)^2)
      alpha_ <- y_bar - beta_ * x_bar
      rep <- alpha_ + beta_ * time_[rwin-1]
      c_ins$replace(rep)
      r_ins$replace(rep)
    }
  }
  pred_outlier <- rep(0, full_size)
  if (length(anomal_index)!=0){
    for (anom_index in anomal_index) {
      pred_outlier[anom_index] <- 1
    }
  }
  pred_outlier <- as.factor(pred_outlier)
  return (pred_outlier)
}

math_round<-function(x){
  t <- x%/%1
  if (x-t<0.5){
    return (t)
  }
  else {return(t+1)}
}

GetPRF <- function(trues,preds) {
  precision <- posPredValue(preds, trues, positive="1")
  recall <- sensitivity(preds, trues, positive="1")
  excepts<-c(0,NaN)
  if ((precision %in% excepts)||(recall %in% excepts)){
    return (c(-.Machine$integer.max*0.1,-.Machine$integer.max*0.1,-.Machine$integer.max*0.1))
  }
  F1 <- (2 * precision * recall) / (precision + recall)
  return (c(precision,recall,F1))
}



