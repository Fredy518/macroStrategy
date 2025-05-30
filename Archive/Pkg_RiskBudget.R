# RiskBudget_v2
library(xts)
library(plotrix)
library(tseries)
library(nloptr) #Risk Pariy Optimizer
library(mFilter) #HP Filter
library(tidyverse)
library(lubridate)
library(plyr)
library(cccp)
library(PerformanceAnalytics)




# MacroEcoCycle -----------------------------------------------------------

combineCMI <- function(cmib, cmie, beg, update){
  getAfter <- function(data, beg) data[index(data)>=beg]
  cmib <- getAfter(cmib, beg)
  cmie <- getAfter(cmie, beg)
  idx <- which(index(cmib)>update)
  if (length(idx)>0&sum(cmib[idx]==0)>0){
    tail_cmib <- cmib[c(idx[1]-1, idx)]
    tail_cmib[tail_cmib==0&index(tail_cmib)>update] <- NA
    tail_cmib <- xts(
      as.data.frame(tail_cmib) %>% fill(V1,.direction = 'down'),
      order.by = index(tail_cmib)
    )
    cmib <- rbind.xts(cmib[1:(idx[1]-2)], tail_cmib)
  }
  cmie[cmie==0] <- cmib[cmie==0]
  return(cmie)
}

getBeg <- function(name) {info[which(info$abbr==name),]$beg}
getUpdate <- function(name) {info[which(info$abbr==name),]$update}

# function: 数量->同比
getYOY <- function(x){
  if (!is.xts(x)) return('xts object is legal!')
  yoy <- c()
  for (m in 1:12){
    x_m <- x[which(month(x)==m)]
    yoy_m <- (x_m / lag.xts(x_m, 1, na.pad = F) - 1) * 100
    if (length(yoy)==0) yoy <- yoy_m
    else yoy <- rbind.xts(yoy, yoy_m)
  }
  return(yoy)
}


combineFIN <- function(fin, finc, fino, beg){
  getAfter <- function(data, beg) data[index(data)>=beg]
  fin <- getAfter(fin, beg) # 同比
  finc <- getAfter(finc, beg) # 累计
  fino <- getAfter(fino, beg) # 存量
  finc <- finc/10000 # finc 亿元->万亿

  fino[month(fino)!=12] <- NA
  fino_filled <- xts(as.data.frame(fino) %>% fill(V1, .direction = 'down'), index(fino))
  fino[is.na(fino)] <- finc[is.na(fino)] + fino_filled[is.na(fino)] # 存量 + 累计: 填充为实际存量
  fino_yoy <- getYOY(fino)
  if(sum(fin==0,na.rm=T)>0){
    fin[fin==0] <- fino_yoy[index(fin[fin==0])]
  }
  return(fin)
}


#
zero2na <- function(tso){
  cols <- names(tso)
  for (c in cols){
    # beg <- getBeg(c)
    # update <- getUpdate(c)
    # idx <- which((index(tso[,c])<(beg+365) | index(tso[,c])>=update) & tso[,c]==0)
    idx <- which(tso[,c]==0)
    if (length(idx)>0)  {tso[, c][idx] <- NA}
  }
  return(tso)
}

downFill <- function(tso, zeroAdj=T){
  if (zeroAdj) tso <- zero2na(tso)
  res <- xts(as.data.frame(tso) %>% fill(names(tso),.direction = 'down'), index(tso))
  return(res)
}

hpFilter <- function(tso, lambda){
  cols <- names(tso)
  hp_tso <- c()
  for (c in cols){
    ts_hp <- tso[,c][!is.na(tso[,c])]
    hptrend<-xts(hpfilter(ts_hp, freq=lambda, type="lambda", drift=F)$trend,
                 order.by = index(ts_hp))
    if (length(hp_tso)==0) hp_tso <- hptrend
    else hp_tso <- cbind.xts(hp_tso, hptrend)
  }
  names(hp_tso) <- cols
  return(hp_tso)
}

# calcDt: 扩散指数比较间隔(calcDt=3, T4-T1)
# stdTV:  标准差判断阈值
# smpNum: 标准差计算样本数
getDirection <- function(tso, calcDt, stdTV, smpNum=12){
  cols <- names(tso)
  factor_d <- xts()
  for (c in cols){
    ts_c <- tso[,c][!is.na(tso[,c])]
    dif_ts <- diff(ts_c, lag = calcDt)/calcDt
    rsd_ts <- roll_sd(dif_ts, width = smpNum, min_obs = 3)
    direction <- ifelse(dif_ts >= rsd_ts * stdTV, 1, ifelse(dif_ts<=rsd_ts * (-stdTV), -1, NA))
    direction <- downFill(direction, F)
    direction[is.na(direction)] <- (ifelse(dif_ts > 0, 1, -1))[is.na(direction)]
    if(length(factor_d)==0) factor_d <- direction
    else factor_d <- cbind.xts(factor_d, direction)
  }
  names(factor_d) <- cols
  return(factor_d)
}


# function 统计持续时长 which abs(diff)!=0
getDuration <- function(tso){
  cols <- names(tso)
  summary <- list()
  for (c in cols){
    ts_c <- tso[,c][!is.na(tso[,c])]
    dura <- diff(c(0,which(diff(ts_c)!=0)))
    len <- length(dura)
    summary[[c]] <- c(
      num = len + 1,
      avgDuration = if(len>0) round(mean(dura)) else length(ts_c),
      maxDuration = if(len>0) max(dura) else length(ts_c),
      minDuration = if(len>0) min(dura) else length(ts_c)
    )
  }
  return(as.data.frame(summary))
}


fillDrNaByidx2 <- function(tso, idx_map){
  idx_1.tso <- tso[,as.character(idx_map$idx_1)]
  idx_2.tso <- tso[,as.character(idx_map$idx_2)]
  result <- c()
  for(i in 1:length(idx_map$idx_1)){
    c_1 <- as.character(idx_map$idx_1)[i]
    c_2 <- as.character(idx_map$idx_2)[i]
    tc_1 <- tso[,c_1]
    tc_2 <- tso[,c_2]
    tc_1[is.na(tc_1)] <- tc_2[is.na(tc_1)]
    if (length(result)==0) result <- tc_1
    else result <- cbind.xts(result, tc_1)
  }
  return(result)
}

udCycleProb <- function(tso, idx_map){
  growth_cols <- idx_map %>% filter(cycType==1) %>% select(idx_1) %>% unlist %>% as.character
  inflation_cols <- idx_map %>% filter(cycType==2) %>% select(idx_1) %>% unlist %>% as.character
  liquid_cols <- idx_map %>% filter(cycType==3) %>% select(idx_1) %>% unlist %>% as.character
  cycleProb <- function(tso){
    xy <- dim(tso)
    prob <- xts(rowSums(tso==1)/xy[2], index(tso))
    return(prob)
  }
  prob <- cbind.xts(
    cycleProb(tso[,growth_cols]),
    cycleProb(tso[,inflation_cols]),
    cycleProb(tso[,liquid_cols])
  )
  names(prob) <- c('growth','inflation','liquid')
  return(prob)
}

hpCycleMap <- function(hp_tso, cyc_map){
  hp_tso.c <- drop_na(as.data.frame(hp_tso))
  hp_tso.c[hp_tso.c==-1] <- 0
  res <- xts(apply(hp_tso.c, 1, function(x) paste(x, collapse='')), as.Date(rownames(hp_tso.c)))
  final_res <- xts(unlist(lapply(as.character(unlist(res)),
                                 function(x) cyc_map$cyc_name[which(cyc_map$cyc_code==x)])),
                   as.Date(rownames(hp_tso.c)))
  names(final_res) <- 'cycle'
  return(final_res)
}

hist_ud_cycle <- function(tso, lambda, backtestBeg='2012-01'){
  m_idx <- as.character(index(tso[paste0(backtestBeg,'/')]))
  ud_final <- c()
  for(d in m_idx){
    tso_sub <- tso[paste0('/', d)]
    hp_res <- hpFilter(tso_sub, lambda)
    dr_res <- getDirection(hp_res, calcDt = 1, stdTV = 0.2)
    dr_res.ud <- drop_na(as.data.frame(fillDrNaByidx2(dr_res, idx_map)))
    dr_res.ud <- xts(dr_res.ud, ymd(rownames(dr_res.ud)))
    ud_prob <- udCycleProb(dr_res.ud, idx_map)
    ud_res <- udCycleMap(ud_prob, cyc_map, width=1)

    if(length(ud_final)==0) ud_final <- ud_res
    else ud_final <- rbind.xts(ud_final, ud_res[d])
  }
  return(ud_final)
}

# width滚动平均计算窗口
udCycleMap <- function(ud_prob, cyc_map, width=1){
  prob_lst <- as.data.frame(ud_prob) %>%
    mutate(
      '001'=(1-growth)*(1-inflation)*liquid,
      '101'=growth*(1-inflation)*liquid,
      '111'=growth*inflation*liquid,
      '110'=growth*inflation*(1-liquid),
      '000'=(1-growth)*(1-inflation)*(1-liquid),
      '010'=(1-growth)*inflation*(1-liquid),
      '011'=(1-growth)*inflation*liquid,
      '100'=growth*(1-inflation)*(1-liquid)
    ) %>% select(!c(growth, inflation, liquid)) %>% as.matrix %>%
    roll_mean(width=width)
  probts <- xts(prob_lst, index(ud_prob))
  new_names <- as.character(sapply(names(probts), function(x) cyc_map$cyc_name[which(cyc_map$cyc_code==x)]))
  names(probts) <- new_names
  return(probts)
}

# x12Adjust <- function(tso, x12path='./WinX12/x12a/x12a.exe'){
#   cols <- names(tso)
#   new_tso <- c()
#   for (c in cols){
#     ts_c <- tso[,c][!is.na(tso[,c])]
#     beg <- index(ts_c)[1]
#     len <- length(ts)
#     ts_n <- ts(ts_c, start = c(year(beg), month(beg)), frequency = 12)
#     ts_adj <- x12work(ts_n, x12path=x12path, keep_x12out=F,showWarnings=F)
#     ts_n <- xts(ts_adj$d11, index(ts_c))
#     if (length(new_tso)==0) new_tso <- ts_n
#     else new_tso <- cbind.xts(new_tso, ts_n)
#   }
#   names(new_tso) <- cols
#   return(new_tso)
# }


# getUDCyc <- function(ud_cycle, cyc_map){
#   cycList <- c()
#   probList <- c()
#   genPriorHelper <- function(num, len){
#     before <- num:len
#     after <- 1:num
#     helper <- c(before, after)[1:len]
#     return(helper)
#   }
#   for(i in 1:nrow(ud_cycle)){
#     cyc <- names(which(ud_cycle[i,]==max(ud_cycle[i,])))
#     prob <- ud_cycle[i, cyc]
#     ord <- cyc_map$order[which(cyc_map$cyc_name==cyc)]
#     helper <- genPriorHelper(min(ord), length(cyc_map$order))
#     if (length(cycList)>0&sum(cyc%in%cycList))
#   }
# }

# deflatorYOY <- function(yoy, bprice){
#   bp_yoy <- getYOY(bprice)/100 + 1
#   return(yoy/bp_yoy)
# }



# Utility Function --------------------------------------------------------
preFriday <- function(d){
  if((d-wday(d)+6)<=d) {
    lf <- (d-wday(d)+6)
  } else {
    lf <- (d-wday(d)-1)
  }
  return(lf)
}

# return last day in every week
getPosChgDts <- function(dts, beg, end, freq='W'){
  dts <- sort(as.Date(dts))
  dts.df <- data.frame(
    actualDay = dts,
    weekFriday = ceiling_date(dts, 'week', week_start = 7,change_on_boundary = F) - 2
  )
  chgdts_df <- ddply(dts.df, .variables='weekFriday',
                     .fun=function(x) c(firstDay=x$actualDay[1], lastDay=x$actualDay[dim(x)[1]])) %>%
    filter(firstDay != lastDay, lastDay >= beg, lastDay <= end) %>%
    mutate(month = format(weekFriday, '%Y-%m'))
  if(freq=='W'){
    chgdts <- chgdts_df %>% `[[`('weekFriday')
  } else{
    chgdts <- chgdts_df %>% group_by(month) %>%
      dplyr::summarise(monthLastFri = last(weekFriday)) %>% `[[`('monthLastFri')
  }
  return(chgdts)
}


# rm(list=ls()) #clean up global enviroment
# Exponent Weighted Moving Average Correlation #####
# Inputs: only matrix

EW.Corr<-function(x, ww, alpha, reverse=F){
  if(is.data.frame(x)) x0 <- x%>% drop_na() %>% data.matrix()
  if(is.vector(x)) x0=matrix(x)
  if(is.xts(x)) x0 <- coredata(x %>% data.frame %>% drop_na()) %>% data.matrix()
  lth=dim(x0)
  cnt<-floor(lth[1]/ww)
  seq <- if (reverse) cnt:1 else 1:cnt
  results <- matrix(data = 0, nrow = lth[2], ncol = lth[2])
  for(i in seq){
    if (i==seq[1]){
      results <- cor(x0[((i-1)*ww+1):(i*ww),],method='pearson')
    } else {
      results <- alpha * results + (1-alpha) * cor(x0[((i-1)*ww+1):(i*ww),],method='pearson')
    }
  }
  return(results)
}

# Exponent Weighted Moving Average Volatility
# x: ret vector
# ww: watching window(ww = 5, means calculate unit is weekly)
# alpha: decay factor
# variance(t) <- alpha * variance(t-1) + (1-alpha) * unit_var(t-1)
EW.Sig <- function(x, ww, alpha, reverse=F){
  # x0 <- x[!is.na(x)]
  x[is.na(x)] <- 0
  x0 <- x
  lth <- length(x0)
  cnt <- floor(lth/ww)
  results <- 0
  seq <- if (reverse) cnt:1 else 1:cnt
  for(i in seq){
    if(i==seq[1]) {
      results <- var(x0[((i-1)*ww+1):(i*ww)])
    } else {
      results <- results*alpha+(1-alpha)*var(x0[((i-1)*ww+1):(i*ww)])
    }
  }
  return(sqrt(results))
}

# wth: moving window of PE and Volatility
# ww: watching window of PE
# multi: define the multiple of volatility
EW.Volatility <- function(idx.cut, ww, multi_names, multi, alpha){
  stdev <- idx.cut %>% sapply(FUN = function(x) EW.Sig(x, ww, alpha, reverse = F)) * sqrt(250)
  stdev[multi_names] <- stdev[multi_names] * multi
  return(stdev)
}

Volatility <- function(idx.cut){
  stdev2 <- idx.cut %>% sapply(FUN = function(x) sqrt(var(x))) * sqrt(250)
  return(stdev2)
}

Corr<-function(x){
  if(is.data.frame(x)) x0 <- x%>% drop_na() %>% data.matrix()
  if(is.vector(x)) x0=matrix(x)
  if(is.xts(x)) x0 <- coredata(x %>% data.frame %>% drop_na()) %>% data.matrix()
  results <- cor(x0,method='pearson')
  return(results)
}


##### Cor->Cov#####
# Inputs: Cor matrix and sigma vector
Cor2Cov<-function(Sig,Cor){
  # if(class(Cor)=="data.frame") x0=data.matrix(x)
  # if(class(Cor)=="vector") x0=matrix(x)
  lth=dim(Cor)
  lth0=length(Sig)
  if(lth[1]!=lth[2]) print('Correlation is asymmetric!')
  if(lth[1]!=lth0) print('Correlation is not as long as Sigma!')
  results <- as.matrix(Sig) %*% t(as.matrix(Sig)) * Cor
  return(results)
}

##### Risk Budget Model #####
# cov is the covariance matrix
# bud is the budget vector
# target is the target volatility of portfolio
RiskParity<-function(cov, bud, target, assetMat=NA, upbound=NA){
  Na = dim(cov)[1]
  budget=unlist(bud)/sum(unlist(bud))
  Nb = length(budget)
  if(Na!=Nb)
    library(nloptr)
  fn<-function(w){
    vol = t(as.matrix(w))%*%cov%*%as.matrix(w)
    rc<-c(rep(0,length(w)))
    for(i in 1:length(w)){
      A1 = cov%*%w
      a = as.numeric(A1[i])
      rc[i] = w[i]*a/vol
    }
    m = abs(vol-target*target) #final volatility < target
    for(i in 1:length(rc)){
      for(j in i:length(rc)){
        m = m + abs(budget[j]*rc[i]-budget[i]*rc[j])
      }
    }
    return(m)
  }
  Eq<-function(w){
    if (any(is.na(upbound))){
      res <- abs(1-sum(w))
    } else {
      res <- c(as.vector(assetMat %*% w) - upbound, abs(1-sum(w)))
    }
    return(res)
  }
  x0 = c(rep(1/Na,Na))
  ans<-nloptr(x0 = x0, eval_f = fn, eval_grad_f = NULL,
              lb = rep(0,Na), ub = rep(1,Na),
              eval_g_ineq = Eq,
              opts = list("algorithm" = "NLOPT_LN_COBYLA",
                          "xtol_rel" = 1.0e-8,
                          "maxit"=10e8))
  return(ans)
}

# BACKTEST FUNCTIONS -------------------------------------------------------

smoothRPWT <- function(WT, Info, chgThreshold){
  assetNames <- Info$SecAsset; DTName <- '日期'
  otherNames <- setdiff(names(WT), c(assetNames, DTName))
  smoothweight <- function(wt){
    wt <- wt[order(wt[[DTName]]),]
    assetWT <- wt[,assetNames]
    smoothedwt <- matrix(0, nrow(assetWT), ncol(assetWT),
                         dimnames=list(rownames(assetWT),
                                       colnames(assetWT)))
    for(i in seq(nrow(assetWT))){
      wt_i <- unlist(assetWT[i,])
      if (i==1){
        smoothedwt[i,] <- wt_i
      } else {
        smwt_i <- smoothedwt[i-1,]
        chg <- sum(abs(smwt_i - wt_i))
        if(chg<=chgThreshold){
          smoothedwt[i,] <- smwt_i
        } else {
          smoothedwt[i,] <- wt_i
        }
      }
    }
    smoothedwt <- data.frame(smoothedwt)
    smoothedwt <- cbind(wt[DTName], smoothedwt)
    return(smoothedwt)
  }
  smoothedWT <- ddply(WT, .variables = otherNames, .fun = smoothweight)
  return(smoothedWT)
}

calcBacktestNav <- function(idx, wt){
  wt <- wt[order(wt$日期),]
  dts <- strftime(wt$日期, '%Y-%m-%d')
  assetName <- colnames(idx)
  idx.xts <- xts(idx, as.Date(rownames(idx)))
  wt.xts <- xts(wt[,assetName], as.Date(dts))
  y <- c()
  d <- c()
  for (dtid in seq(dts)){
    beg <- dts[dtid]
    end <- ifelse(is.na(dts[dtid+1]),'',dts[dtid+1])
    wt.cut <- wt.xts[beg]
    idx.cut <- idx.xts[paste(beg, end, sep='/')]
    idx.cut2 <- idx.cut[index(idx.cut)>index(wt.cut)]

    d <- append(d,index(idx.cut2))
    y.cut <- c(coredata(idx.cut2) %*% t(coredata(wt.cut)))
    y <- append(y, y.cut)
  }
  nav <- cumprod(1+y)/cumprod(1+y)[1]
  names(nav) <- d
  return(nav)
}

# 年化双向换手: 周频
# 大类资产平均仓位
evalPosition <- function(wt){
  Info <- list(
    BigAsset = c(rep('股票',11),rep('商品',2),'黄金',rep('债券',2)),
    SecAsset = c('沪深300','中证500','基地','金融','科技','消费','医疗',
                 '制造','周期','标普','恒生','动量','南华','黄金','短债','全债')
  )
  avgchg <- drop_na(wt[Info$SecAsset] -lag(wt[Info$SecAsset])) %>%
    abs() %>% rowSums() %>% mean() %>% round(digits=2)
  sckpos <- wt[Info$SecAsset[which(Info$BigAsset=='股票')]] %>% rowSums() %>% mean() %>% round(digits=2)
  bndpos <- wt[Info$SecAsset[which(Info$BigAsset=='债券')]] %>% rowSums() %>% mean() %>% round(digits=2)
  gldpos <- wt[Info$SecAsset[which(Info$BigAsset=='黄金')]] %>% rowSums() %>% mean() %>% round(digits=2)
  fthpos <- wt[Info$SecAsset[which(Info$BigAsset=='商品')]] %>% rowSums() %>% mean() %>% round(digits=2)
  pos.sm <- c(双向换手=avgchg*50,股票仓位=sckpos,债券仓位=bndpos,黄金仓位=gldpos,商品仓位=fthpos)
  return(pos.sm)
}

# 滚动一年(250tradeDt)收益/波动率/回撤 25/50/75/avg

evalApperance <- function(nav){
  ww <- 250
  probs <- c(0.1,0.5,0.9)
  nav.xts <- xts(t(nav), as.Date(colnames(nav)))
  y.xts <- nav.xts/lag.xts(nav.xts) - 1

  rollval <- rollapply(y.xts, width=ww, FUN=function(x) sd(x)*sqrt(ww))
  val.sm <- c(quantile(rollval, probs, na.rm=T), avg=mean(rollval, na.rm=T))
  names(val.sm) <- paste('滚动1年波动率', names(val.sm), sep='_')

  rollret <- rollapply(coredata(nav.xts), width=ww, FUN=function(x) (x[ww]/x[1]-1))
  ret.sm <- c(quantile(rollret, probs, na.rm=T), avg=mean(rollret, na.rm=T))
  names(ret.sm) <- paste('滚动1年收益率', names(ret.sm), sep='_')

  rollmdd <- rollapply(y.xts, width=ww, FUN=function(x) maxDrawdown(x)) * -1
  mdd.sm <- c(quantile(rollmdd, probs, na.rm=T), avg=mean(rollmdd, na.rm=T))
  names(mdd.sm) <- paste('滚动1年最大回撤', names(mdd.sm), sep='_')

  cumret <- coredata(nav.xts)[length(nav.xts)]/coredata(nav.xts)[1] - 1
  annret <- (cumret + 1)^(ww/length(nav.xts)) -1
  annval <- sd(y.xts,na.rm = T)*sqrt(ww)
  annshp <- annret/annval
  cummdd <- maxDrawdown(y.xts) * -1
  calmar <- annret/cummdd * -1

  cum.sm <- c(cumret, annret, annval, cummdd, annshp, calmar)
  names(cum.sm) <- c('累计收益率','年化收益率','年化波动率','最大回撤','夏普比率','Calmar比率')

  appearance <- c(cum.sm, ret.sm, val.sm, mdd.sm) %>% round(digits=4)
  return(appearance)
}

