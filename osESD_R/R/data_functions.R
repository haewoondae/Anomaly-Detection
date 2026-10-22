# rm(list=ls())


# set.seed(42)

RUN_DATA_1<-function(data_length,noise_value){
  alpha<-c(0.6,-0.5,0.4,-0.4,0.3)
  beta<-c(0.3,-0.2)
  noise_mean<-0
  noise_std<-noise_value
  seq_num<-data_length
  last_seq<-noise_std*rnorm(length(alpha))
  last_noise<-noise_mean+noise_std*rnorm(length(beta))
  seq_d0<-c()
  for (i in 1:seq_num){
    noise_term<-noise_mean+noise_std*rnorm(1)
    seq_d0[i]<-sum(alpha*last_seq)+sum(beta*last_noise)+noise_term
    last_seq<- c(seq_d0[i],last_seq[1:(length(alpha)-1)])
    last_noise<-c(noise_term,last_noise[1:(length(beta)-1)])
  }

  seq_d0<-as.matrix(seq_d0)

  seq_d1<-c(seq_d0[1])
  for (i in 2:seq_num){
    seq_d1<-c(seq_d1,seq_d1[length(seq_d1)]+seq_d0[i])
  }

  return (seq_d1)

}

## 2 은 one split.
RUN_DATA_2<-function(data_length,noise_value){
  alpha<-c(0.6,-0.5,0.4,-0.4,0.3)
  beta<-c(0.3,-0.2)
  Noise_terms<-runif(data_length,min=-noise_value,max=noise_value)
  last_seq<-runif(length(alpha),min=-noise_value,max=noise_value)
  last_noise<-runif(length(beta),min=-noise_value,max=noise_value)
  seq_d0_a<-c()
  half<-data_length/2
  for (i in 1:half){
    noise_term<-Noise_terms[i]
    seq_d0_a[i]<-sum(alpha*last_seq)+sum(beta*last_noise)+noise_term
    last_seq<- c(seq_d0_a[i],last_seq[1:(length(alpha)-1)])
    last_noise<-c(noise_term,last_noise[1:(length(beta)-1)])
  }

  alpha<-c(-0.4,-0.5,0.4,0.4,0.1)
  beta<-c(-0.3,0.2)

  seq_d0_b<-c()
  for (i in 1:(half+data_length%%2)){
    noise_term<-Noise_terms[i+half]
    seq_d0_b[i]<-sum(alpha*last_seq)+sum(beta*last_noise)+noise_term
    last_seq<- c(seq_d0_b[i],last_seq[1:(length(alpha)-1)])
    last_noise<-c(noise_term,last_noise[1:(length(beta)-1)])
  }
  seq_d0<-c(seq_d0_a,seq_d0_b)

  seq_d0<-as.matrix(seq_d0)

  seq_d1<-c(seq_d0[1])
  for (i in 2:data_length){
    seq_d1<-c(seq_d1,seq_d1[length(seq_d1)]+seq_d0[i])
  }
  return (seq_d1)
}
100%%7

## 3 은 two split.
RUN_DATA_3<-function(data_length,noise_value){
  alpha<-c(0.6,-0.5,0.4,-0.4,0.3)
  beta<-c(0.3,-0.2)
  seq_num<-data_length
  Noise_terms<-runif(seq_num,min=-noise_value,max=noise_value)
  last_seq<-runif(length(alpha),min=-noise_value,max=noise_value)
  last_noise<-runif(length(beta),min=-noise_value,max=noise_value)
  seq_d0_a<-c()
  third<-seq_num/3


  for (i in 1:third){
    noise_term<-Noise_terms[i]
    seq_d0_a[i]<-sum(alpha*last_seq)+sum(beta*last_noise)+noise_term
    last_seq<- c(seq_d0_a[i],last_seq[1:(length(alpha)-1)])
    last_noise<-c(noise_term,last_noise[1:(length(beta)-1)])
  }

  alpha<-c(-0.4,-0.5,0.4,0.4,0.1)
  beta<-c(-0.3,0.2)
  seq_d0_b<-c()
  for (i in 1:third){
    noise_term<-Noise_terms[i+third]
    seq_d0_b[i]<-sum(alpha*last_seq)+sum(beta*last_noise)+noise_term
    last_seq<- c(seq_d0_b[i],last_seq[1:(length(alpha)-1)])
    last_noise<-c(noise_term,last_noise[1:(length(beta)-1)])
  }

  alpha<-c(0.5,-0.3,0.5,-0.6,0.4)
  beta<-c(0.2,-0.3)
  seq_d0_c<-c()
  for (i in 1:(third+seq_num%%3)){
    noise_term<-Noise_terms[i+third*2]
    seq_d0_c[i]<-sum(alpha*last_seq)+sum(beta*last_noise)+noise_term
    last_seq<- c(seq_d0_c[i],last_seq[1:(length(alpha)-1)])
    last_noise<-c(noise_term,last_noise[1:(length(beta)-1)])
  }

  seq_d0<-c(seq_d0_a,seq_d0_b,seq_d0_c)
  seq_d0<-as.matrix(seq_d0)
  seq_d1<-c(seq_d0[1])
  for (i in 2:seq_num){
    seq_d1<-c(seq_d1,seq_d1[length(seq_d1)]+seq_d0[i])
  }
  return (seq_d1)
}

## 4 은 gradually change.
RUN_DATA_4<-function(data_length,noise_value){
  alpha1<-c(-0.4,0.5,0.4,0.4,0.1)
  alpha2<-c(0.6,-0.5,0.4,-0.4,0.3)
  beta<-c(0.3,-0.2)
  noise_mean<-0
  seq_num<-data_length
  noise_std<-noise_value
  last_seq<-noise_std*rnorm(length(alpha1))
  last_noise<-noise_mean+noise_std*rnorm(length(beta))
  seq_d0<-c()
  for (i in 1:data_length){
    noise_term<-noise_mean+noise_std*rnorm(1)
    alpha_t<-alpha1*(i/data_length) + alpha2*(1-(i/data_length))
    seq_d0[i]<-sum(alpha_t*last_seq)+sum(beta*last_noise)+noise_term
    last_seq<- c(seq_d0[i],last_seq[1:(length(alpha_t)-1)])
    last_noise<-c(noise_term,last_noise[1:(length(beta)-1)])
  }
  seq_d0<-as.matrix(seq_d0)
  seq_d1<-c(seq_d0[1])
  for (i in 2:seq_num){
    seq_d1<-c(seq_d1,seq_d1[length(seq_d1)]+seq_d0[i])
  }
  return (seq_d1)
}

## 5 은 correlated change.
RUN_DATA_5<-function(data_length,noise_value){
  alpha<-c(0.6,-0.5,0.4,-0.4,0.3)
  beta<-c(0.3,-0.2)
  noise_mean<-0
  noise_std<-noise_value
  seq_num<-data_length
  noise_corr_value<-0.3
  last_seq<-noise_std*rnorm(length(alpha))
  last_noise<-noise_mean+noise_std*rnorm(length(beta))
  seq_d0<-c()
  noise_term<-noise_mean
  for (i in 1:seq_num){
    noise_term<-noise_term*noise_corr_value+noise_std*rnorm(1)
    seq_d0[i]<-sum(alpha*last_seq)+sum(beta*last_noise)+noise_term
    last_seq<- c(seq_d0[i],last_seq[1:(length(alpha)-1)])
    last_noise<-c(noise_term,last_noise[1:(length(beta)-1)])
  }
  seq_d0<-as.matrix(seq_d0)
  seq_d1<-c(seq_d0[1])
  for (i in 2:seq_num){
    seq_d1<-c(seq_d1,seq_d1[length(seq_d1)]+seq_d0[i])
  }
  return (seq_d1)
}

## 6은 correlated change with one split.
RUN_DATA_6<-function(data_length,noise_value){
  alpha<-c(0.6,-0.5,0.4,-0.4,0.3)
  beta<-c(0.3,-0.2)
  noise_mean<-0
  noise_std<-noise_value
  seq_num<-data_length
  noise_corr_val<-0.3
  last_seq<-noise_std*rnorm(length(alpha))
  last_noise<-noise_mean+noise_std*rnorm(length(beta))
  noise_term<-noise_mean
  seq_d0_a<-c()

  for (i in 1:seq_num/2){
    noise_term<-noise_term*noise_corr_val+noise_std*rnorm(1)
    seq_d0_a[i]<-sum(alpha*last_seq)+sum(beta*last_noise)+noise_term
    last_seq<- c(seq_d0_a[i],last_seq[1:(length(alpha)-1)])
    last_noise<-c(noise_term,last_noise[1:(length(beta)-1)])
  }
  alpha<-c(-0.4,-0.5,0.4,0.4,0.1)
  beta<-c(-0.3,0.2)
  seq_d0_b<-c()

  for (i in 1:(seq_num/2+seq_num%%2)){
    noise_term<-noise_term*noise_corr_val+noise_std*rnorm(1)
    seq_d0_b[i]<-sum(alpha*last_seq)+sum(beta*last_noise)+noise_term
    last_seq<- c(seq_d0_b[i],last_seq[1:(length(alpha)-1)])
    last_noise<-c(noise_term,last_noise[1:(length(beta)-1)])
  }

  seq_d0<-c(seq_d0_a,seq_d0_b)
  seq_d0<-as.matrix(seq_d0)
  seq_d1<-c(seq_d0[1])
  for (i in 2:seq_num){
    seq_d1<-c(seq_d1,seq_d1[length(seq_d1)]+seq_d0[i])
  }
  return (seq_d1)
}

### Function for creating original dataset
State_space_data <- function(len=1000, wp=1000, sd_epsilon=30, sd_eta=10, sd_Xi=0.01,seasonality=TRUE) {

  update<-function(List,old_mean,old_sd,new_val){
    Len <- length(List)
    new_std <- sqrt(((Len-1)/(Len))*old_sd^2+(1/(Len+1))*(new_val-old_mean)^2)
    new_mean <- old_mean*(Len)/(Len+1) + new_val/(Len+1)
    List<-c(List,new_val)
    return (list('mean'=new_mean,'sd'=new_std,'List'=List))
  }

  mu <- 0
  ts <- 0
  beta <- 0
  season <- len*0.1

  non_seasonal<-c(0)
  non_seasonal_mean<-0
  non_seasonal_sd<-0

  sine_factor<-c()

  for(s in 1:(season)) {
    sine_factor<-c(sine_factor,sin(2*s*pi/season))
  }

  return_vals<-c(0)
  for(t in 1:(wp+len)) {
    Xi <- rnorm(1,0,sd_Xi)
    beta <- beta + Xi
    eta <- rnorm(1,0,sd_eta)
    mu <- mu + beta + eta
    seasonal <- sine_factor[t%%season+1]
    new_vals <- update(non_seasonal,non_seasonal_mean,non_seasonal_sd,ts)
    non_seasonal_mean<-new_vals$mean
    non_seasonal_sd<-new_vals$sd
    non_seasonal<-new_vals$List
    epsilon <- rnorm(1,0,sd_epsilon)
    ts <- mu + epsilon + non_seasonal_sd * seasonal
    return_vals<-c(return_vals,ts)
  }
  ts <- return_vals[(wp+1):(wp+len)]
  return(ts)
}


contaminate<-function(ts, alpha, anom_percent, func){

  update<-function(List,old_mean,old_sd,new_val){
    Len <- length(List)
    new_std <- sqrt(((Len-1)/(Len))*old_sd^2+(1/(Len+1))*(new_val-old_mean)^2)
    new_mean <- old_mean*(Len)/(Len+1) + new_val/(Len+1)
    List<-c(List,new_val)
    return (list('mean'=new_mean,'sd'=new_std,'List'=List))
  }


  bernoulli <- function() {
    return(sample(c(-1, 1), 10000, prob = c(0.5, 0.5),replace=TRUE))
  }

  uniform <- function(){
    return (runif(10000,-1,1))}

  linear <- function(){
    L<-10000
    x<-1:L
    probs <- seq(0, 1, length.out = L)
    probs <- probs/(sum(probs))
    samples<-sample(x/L, size = L, replace = TRUE, prob = probs)
    signs<-bernoulli()
    return (samples*signs)
  }

  quadratic <- function(){
    L<-10000
    x <- 1:L
    probs <- seq(0, 1, length.out = L)
    probs <- probs^2/sum(probs)
    samples<-sample(x/L, size = L, replace = TRUE, prob = probs)
    signs<-bernoulli()
    return (samples*signs)
  }

  L<-length(ts)

  X_t<-c(ts[1])
  X_t_mean<-ts[1]
  X_t_sd<-0

  anomal_index<-c()
  randoms <- runif(L,0,1)

  Ber<-c("Bernoulli","Ber","bernoulli","ber")
  Uni<-c("Uniform","Uni","uniform","uni")
  Lin<-c("Linear","Lin","linear","lin")
  Quad<-c("Quadratic","Quad","quadratic","quad")

  if (func %in% Ber){samples<-bernoulli()}
  else if (func %in% Uni){samples<-uniform()}
  else if (func %in% Lin){samples<-linear()}
  else if (func %in% Quad){samples<-quadratic()}
  else{stop("Anomaly generating function must be 'Bernoulli','Uniform','Linear', or 'Quadratic'.")}

  for (i in 2:L){
    new_vals<-update(X_t,X_t_mean,X_t_sd,ts[i])
    X_t_mean<-new_vals$mean
    X_t_sd<-new_vals$sd
    X_t<-new_vals$List
    if (randoms[i]<anom_percent){
      multiplier<-sample(samples,1,replace=TRUE)
      anomal_index<-c(anomal_index,i)
      ts[i]<-ts[i]+(multiplier*qnorm(1-alpha/2,0,X_t_sd))
    }
  }

  anomal_val <- rep(0, length(ts))
  for (anom_index in anomal_index) {
    anomal_val[anom_index] <- 1
  }
  anomal_val <- as.factor(anomal_val)
  return (list("value"=ts,"anomaly"=anomal_val))
}


#####################################################
#####################################################
#####################################################
#####################################################
#####################################################


# new_data<-function(len=1000, mag=5, trend=0.01, sd_epsilon=30, sd_eta=10,seasonality=TRUE){
#   len<-10000
#   season<-700
#   mag<-5
#   s_factor<-c()
#   for(s in 1:(len+season*2)) {
#     s_factor<-c(s_factor,mag*sin(2*s*pi/season))
#   }
#   s_factor<-s_factor[as.integer(runif(1, min = 0, max = season)):(len+season)]
#   A_noise_sequence<-rnorm(n=len,mean=0,sd=sd_epsilon)
#   B_noise_sequence<-rnorm(n=len,mean=0,sd=sd_eta)
#   ts<-c()
#   for(i in 1:len){
#     ts<-c(ts,s_factor[i]+i*trend+A_noise_sequence[i]+B_noise_sequence[i])
#   }
#   return (ts)
# }
# anom_percent=0.01
# testing<-new_data(len=10000,mag=10, trend= runif(1,min=-0.001,max=0.001), sd_epsilon=0.1, sd_eta=0.5)
# plot.ts(testing)
# cont_data <-contaminate(testing,alpha=0.05,anom_percent=anom_percent,func='lin')
# plot.ts(cont_data$value)



#####################################################
#####################################################
#####################################################
#####################################################
#####################################################

# setwd(dirname(rstudioapi::getSourceEditorContext()$path))
# getwd()
# datalen<-1000
# epsilon <- 3
# eta <- 0.1
# Xi <- 0.02
# anom_percent = 0.01
#
#
# data <- State_space_data(len = datalen, wp = datalen, sd_epsilon = epsilon, sd_eta = eta, sd_Xi = Xi, seasonality=TRUE)
# plot.ts(data)
# cont_data <-contaminate(data,alpha=0.05,anom_percent=anom_percent,func='quad')
# plot.ts(cont_data$value)
#
# for (i in 1:100){
#   print(i)
#   # data <- State_space_data(len = datalen, wp = datalen, sd_epsilon = epsilon, sd_eta = eta, sd_Xi = Xi, seasonality=TRUE)
#   data <- new_data(len=10000,mag=10, trend= runif(1,min=-0.001,max=0.001), sd_epsilon=0.1, sd_eta=0.5)
#   plot.ts(data)
#   if (i%%4==0){func<-'ber'}
#   else if (i%%4==1){func<-'uni'}
#   else if (i%%4==2){func<-'lin'}
#   else if (i%%4==3){func<-'quad'}
#   cont_data <-contaminate(data,alpha=0.05,anom_percent=anom_percent,func=func)
#   plot.ts(cont_data$value)
#   write.csv(cont_data,paste("../Datasets/Seasonal/dataset_",func,"_",(i-1)%/%4+1,".csv",sep=""))
# }


#####################################################
#####################################################
#####################################################
#####################################################
#####################################################

# setwd(dirname(rstudioapi::getSourceEditorContext()$path))
# getwd()
#
# datalen<-10000
# noise<-0.3
# anom_percent <- 0.02
# alpha<-0.05
# for (i in 1:16){
#   data<-RUN_DATA_1(data_length=datalen,noise_value=noise)
#   if (i%%4==0){func<-'ber'}
#   else if (i%%4==1){func<-'uni'}
#   else if (i%%4==2){func<-'lin'}
#   else if (i%%4==3){func<-'quad'}
#   cont_data <- contaminate(ts = data, alpha=alpha, anom_percent=anom_percent,func=func)
#   write.csv(cont_data,paste("../Datasets/synthetic/ARIMA1_",func,"_",(1+(i-1)%/%4),".csv",sep=""))
# }
# for (i in 1:16){
#   data<-RUN_DATA_2(data_length=datalen,noise_value=noise)
#   if (i%%4==0){func<-'ber'}
#   else if (i%%4==1){func<-'uni'}
#   else if (i%%4==2){func<-'lin'}
#   else if (i%%4==3){func<-'quad'}
#   cont_data <- contaminate(ts = data, alpha=alpha, anom_percent=anom_percent,func=func)
#   write.csv(cont_data,paste("../Datasets/synthetic/ARIMA2_",func,"_",(1+(i-1)%/%4),".csv",sep=""))
# }
# for (i in 1:16){
#   data<-RUN_DATA_3(data_length=datalen,noise_value=noise)
#   if (i%%4==0){func<-'ber'}
#   else if (i%%4==1){func<-'uni'}
#   else if (i%%4==2){func<-'lin'}
#   else if (i%%4==3){func<-'quad'}
#   cont_data <- contaminate(ts = data, alpha=alpha, anom_percent=anom_percent,func=func)
#   write.csv(cont_data,paste("../Datasets/synthetic/ARIMA3_",func,"_",(1+(i-1)%/%4),".csv",sep=""))
# }
# for (i in 1:16){
#   data<-RUN_DATA_4(data_length=datalen,noise_value=noise)
#   if (i%%4==0){func<-'ber'}
#   else if (i%%4==1){func<-'uni'}
#   else if (i%%4==2){func<-'lin'}
#   else if (i%%4==3){func<-'quad'}
#   cont_data <- contaminate(ts = data, alpha=alpha, anom_percent=anom_percent,func=func)
#   write.csv(cont_data,paste("../Datasets/synthetic/ARIMA4_",func,"_",(1+(i-1)%/%4),".csv",sep=""))
# }
# for (i in 1:16){
#   data<-RUN_DATA_5(data_length=datalen,noise_value=noise)
#   if (i%%4==0){func<-'ber'}
#   else if (i%%4==1){func<-'uni'}
#   else if (i%%4==2){func<-'lin'}
#   else if (i%%4==3){func<-'quad'}
#   cont_data <- contaminate(ts = data, alpha=alpha, anom_percent=anom_percent,func=func)
#   write.csv(cont_data,paste("../Datasets/synthetic/ARIMA5_",func,"_",(1+(i-1)%/%4),".csv",sep=""))
# }
#
# for (i in 1:16){
#   data<-RUN_DATA_6(data_length=datalen,noise_value=noise)
#   if (i%%4==0){func<-'ber'}
#   else if (i%%4==1){func<-'uni'}
#   else if (i%%4==2){func<-'lin'}
#   else if (i%%4==3){func<-'quad'}
#   cont_data <- contaminate(ts = data, alpha=alpha, anom_percent=anom_percent,func=func)
#   write.csv(cont_data,paste("../Datasets/synthetic/ARIMA6_",func,"_",(1+(i-1)%/%4),".csv",sep=""))
# }


#####################################################
#####################################################
#####################################################
#####################################################
#####################################################
