
library(R6)

osESD_Detector <- function(data, time=1:length(data), dwins, rwins, train_size, alpha, maxr, condition) {
  train_data <- data[1:train_size]
  online_data <- data[(train_size+1):length(data)]
  train_time <- time[1:train_size]
  online_time <- time[(train_size+1):length(data)]
  c_ins <- osESD_TCHA$new(data=train_data, time=train_time, wins=dwins)
  r_ins <- osESD_TRES$new(data=train_data, time=train_time, wins=rwins)
  SESD_TCHA <- osESD_vector$new(data=c_ins$tcha, alpha=alpha, maxr=maxr)
  SESD_TRES <- osESD_vector$new(data=r_ins$tres, alpha=alpha, maxr=maxr)
  anomal_index <- c()
  for(i in 1:length(online_data)) {
    canom <- SESD_TCHA$test(c_ins$update(online_data[i], online_time[i]))
    ranom <- SESD_TRES$test(r_ins$update(online_data[i], online_time[i]))
    if (condition) {function_<-(canom && ranom)
    }else {function_<-(canom||ranom)}
    if (function_){
      anomal_index <- c(anomal_index, (i+train_size))
      data_ <- r_ins$data[-rwins]
      time_ <- r_ins$time[-rwins]
      x_bar <- ((rwins * r_ins$x_bar) - r_ins$time[rwins])/(rwins-1)
      y_bar <- ((rwins * r_ins$y_bar) - r_ins$data[rwins])/(rwins-1)
      beta_ <- sum((time_-x_bar)*(data_-y_bar))/sum((time_-x_bar)^2)
      alpha_ <- y_bar - beta_ * x_bar
      rep <- alpha_ + beta_ * time_[rwins-1]
      c_ins$replace(rep)
      r_ins$replace(rep)
    }
  }
  return(anomal_index)
}


#transform data to residual with update
osESD_TRES <- R6Class("osESD_TRES",
                      public = list(
                        data = NULL,
                        time = NULL,
                        tres = NULL,
                        x_bar = 0,
                        y_bar = 0,
                        wins = 0,

                        initialize = function(data, time=1:length(data), wins) {
                          self$wins <- wins
                          self$data <- data[1:wins]
                          self$time <- time[1:wins]
                          self$x_bar <- mean(self$time)
                          self$y_bar <- mean(self$data)
                          beta <- sum((self$time-self$x_bar)*(self$data-self$y_bar))/sum((self$time-self$x_bar)^2)
                          alpha <- self$y_bar - beta * self$x_bar
                          self$tres <- self$data[wins] - (alpha + beta * self$time[wins])

                          for(i in (wins+1):length(data)) {
                            self$data <- c(self$data[-1], data[i])
                            self$time <- c(self$time[-1], time[i])
                            self$x_bar <- self$x_bar - (time[i-wins] - time[i])/wins
                            self$y_bar <- self$y_bar - (data[i-wins] - data[i])/wins
                            beta <- sum((self$time-self$x_bar)*(self$data-self$y_bar))/sum((self$time-self$x_bar)^2)
                            alpha <- self$y_bar - beta * self$x_bar
                            self$tres[i-wins+1] <- data[i] - (alpha + beta * time[i])
                          }
                        },

                        update = function(ond, ont=(self$time[self$wins]+1)) {
                          first_data <- self$data[1]
                          first_time <- self$time[1]
                          self$data <- c(self$data[-1], ond)
                          self$time <- c(self$time[-1], ont)
                          self$x_bar = self$x_bar - (first_time - ont)/self$wins
                          self$y_bar = self$y_bar - (first_data - ond)/self$wins
                          beta <- sum((self$time-self$x_bar)*(self$data-self$y_bar))/sum((self$time-self$x_bar)^2)
                          alpha <- self$y_bar - beta * self$x_bar
                          tres_ <- ond - (alpha + beta * ont)
                          self$tres <- c(self$tres[-1], tres_)
                          return(tres_)
                        },

                        replace = function(rep) {
                          prev <- self$data[self$wins]
                          self$data[self$wins] <- rep
                          self$y_bar = self$y_bar - (prev - rep)/self$wins
                        }
                      )
)

#transform data to change rate with update
osESD_TCHA <- R6Class("osESD_TCHA",
                      public = list(
                        data = NULL,
                        time = NULL,
                        tcha = NULL,
                        wins = 0,
                        initialize = function(data, time=1:length(data), wins) {
                          size <- length(data)
                          self$wins <- wins
                          self$tcha <- (data[(wins):size]-data[1:(size-wins+1)])/(time[wins:size]-time[1:(size-wins+1)])
                          self$data <- data[(length(data)-wins+1):length(data)]
                          self$time <- time[(length(time)-wins+1):length(time)]
                        },

                        update = function(ond, ont=self$time[self$wins]+1) {
                          self$data <- c(self$data[-1], ond)
                          self$time <- c(self$time[-1], ont)
                          tcha_ <- (self$data[self$wins]-self$data[1])/(self$time[self$wins]-self$time[1])
                          self$tcha <- c(self$tcha[-1], tcha_)
                          return(tcha_)
                        },

                        replace = function(rep) {
                          self$data[self$wins] <- rep
                        }
                      )
)


osESD_vector <- R6Class("osESD_vector",
                        public = list(
                          mean = 0,
                          sqsum = 0,
                          alpha = 0,
                          maxr = 0,
                          data = NULL,
                          size = 0,

                          initialize = function(data = NA, alpha = 0.01, maxr = 10) {
                            self$data <- data
                            self$size <- length(data)
                            self$mean <- mean(data)
                            self$sqsum <- sum(data^2)
                            self$alpha <- alpha
                            self$maxr <- maxr
                          },

                          test = function(on) {
                            out <- self$data[1]
                            self$data <- c(self$data[-1], on)
                            self$mean <- self$mean - (out - on) / self$size
                            self$sqsum <- self$sqsum - out^2 + on^2
                            mean_ <- self$mean
                            sqsum_ <- self$sqsum
                            size_ <- self$size
                            data_ <- self$data
                            sd_ <- sqrt((sqsum_ - size_ * mean_^2 + 1e-8)/(size_-1))
                            ares <- abs((data_-mean_)/sd_)
                            esd_index <- which.max(ares)
                            esd <- ares[esd_index]
                            tryCatch({
                              if(esd > self$getLambda(self$alpha, size_)) {
                                if(esd_index == size_) {
                                  return(TRUE)
                                }
                              } else {
                                return(FALSE)
                              }
                            }, error = function(e) {
                              return (FALSE)
                            })
                            for(i in 2:self$maxr) {
                              size_ <- size_ - 1
                              # print(size_)
                              mean_ <- ((size_+1)*mean_ - data_[esd_index])/size_
                              sqsum_ <- sqsum_ - data_[esd_index]^2
                              sd_ <- sqrt((sqsum_ - size_ * mean_^2 + 1e-8)/(size_-1))
                              data_ <- data_[-esd_index]
                              ares <- abs((data_-mean_)/sd_)
                              esd_index <- which.max(ares)
                              esd <- ares[esd_index]
                              tryCatch({
                                if(esd > self$getLambda(self$alpha, size_)) {
                                  if(esd_index == size_) {
                                    return(TRUE)
                                  }
                                } else {
                                  return(FALSE)
                                }
                              }, error = function(e) {
                                return (FALSE)
                              })
                            }
                            return(FALSE)
                          },

                          getLambda = function(alpha, size) {
                            if (size<=2){
                              return (0)
                            }
                            p = 1 - alpha/(2*(size))
                            t_ = qt(p,(size-2))
                            return(t_ * (size-1) / sqrt((size + t_^2) * size))
                          }
                        )
)


timestamp_creator <- function(data) {
  if (length(data$timestamps)==0){
    time=1:length(data$value)
  }
  else{
    return (list('timestamps'=data$timestamps, 'value'=data$value, 'anomaly'=data$anomaly))
  }
  return (list('timestamps'=time, 'value'=data$value, 'anomaly'=data$anomaly))
}


