library(xts)
library(plotrix)
library(tseries)
library(nloptr) #Risk Pariy Optimizer
library(mFilter) #HP Filter
library(plyr)
library(tidyverse)
library(lubridate)
library(PerformanceAnalytics)
library(parallel)
library(cccp)

source("Calc_MacroEcoCycle_v3.R",encoding = 'UTF-8', echo=FALSE)
source("Calc_AssetPrice_v2.R",encoding = 'UTF-8', echo=FALSE)

rm(list=ls())
source("Pkg_RiskBudget.R",encoding = 'UTF-8', echo=FALSE)

options(dplyr.summarise.inform = FALSE, warn = -1) # ignore warnings

T0 <- Sys.time()

# 1. Data Prepare
UDCyc <- openxlsx::read.xlsx(strftime(Sys.Date(), 'Result_MacroEcoCycle_%Y%m%d.xlsx'),
                             sheet='UDCyc',rowNames=T,detectDates=T)

UDBacktest <- openxlsx::read.xlsx(strftime(Sys.Date(), 'Result_MacroEcoCycle_%Y%m%d.xlsx'),
                                  sheet = 'UDBacktest', rowNames=T, detectDates=T)

HPCyc <- openxlsx::read.xlsx(strftime(Sys.Date(), 'Result_MacroEcoCycle_%Y%m%d.xlsx'),
                             sheet='HPCyc',rowNames=T,detectDates=T)

Idx <- openxlsx::read.xlsx(strftime(Sys.Date(), 'Result_AssetPrice_%Y%m%d.xlsx'),
                           sheet='Idx', rowNames=T, detectDates=T)

PE <- openxlsx::read.xlsx(strftime(Sys.Date(), 'Result_AssetPrice_%Y%m%d.xlsx'),
                          sheet='PE', rowNames=T, detectDates=T)

Asset <- openxlsx::read.xlsx('Result_BestAsset.xlsx',sheet='Asset',rowNames=T,detectDates=T)

RPRet <- openxlsx::read.xlsx(strftime(Sys.Date(), 'Result_AssetPrice_%Y%m%d.xlsx'),
                             sheet='RPRet', rowNames=T, detectDates=T)

# hist_wt <- openxlsx::read.xlsx('0_Disp_Result_RPWT.xlsx', sheet = 'DyntotRPWT_sm', detectDates=T)


# AssetLimit <- 13
# Asset[,(AssetLimit+1):ncol(Asset)] <- 0
Budget <- data.frame(
  BudgetTarget  = c(2,    5,   8),         # define stdev target of portfolio
  LowRiskTarget = c(0.75, 0.5, 0.25), # define low-risk risk budget of portfolio 低风险预算
  HighRiskWtUB  = c(0.2,  0.5, 0.8)   # 高风险资产权重上限
)

Info <- data.frame(
  BigAsset = c(rep('股票',11), rep('商品',3), rep('债券',2)),
  SecAsset = c('沪深300','中证500','基地','金融','科技','消费','医疗','制造','周期',
               '标普','恒生','动量','南华','黄金','短债','全债'),
  RiskType = c(rep('H',14), rep('L',2)),
  stringsAsFactors = F
)

para <- c(wth=750, ww=20, multi=1.5, alpha=0.8, alpha_long = 0.95)

# # 获得静态结果
# RPWT.stkbond_static <- calcRPWT(dts[length(dts)], Idx, PE, Asset, Info, Budget, UDCyc, para, mode='StkBond')
# RPWT.all_static <- calcRPWT(dts[length(dts)], Idx, PE, Asset, Info, Budget, UDCyc, para, mode='All')
roundWT <- function(wt, digits=2){
  wt <- wt/sum(wt)
  base_num <- 0.1^round(digits)
  wt_round <- round(wt, digits)
  err_num <- (1 - sum(wt_round))/base_num
  if (err_num>0){
    wtpos <- order(wt_round - wt)[1:err_num]
    wt_round[wtpos] <- wt_round[wtpos] + base_num
  } else if(err_num<0){
    wtpos <- order(wt_round - wt)[(length(wt)+err_num+1):length(wt)]
    wt_round[wtpos] <- wt_round[wtpos] - base_num
  }
  return(round(wt_round,digits))
}

# 使用dynamic_cycle结果作为周期划分依据 当周的行情数据划归每周概率最大的周期
calcRPWT2 <- function(the_day, Idx, PE, Asset,Info, Budget, UDBacktest, para, mode){
  if (mode=='StkBond'){
    assetNames <- Info$SecAsset[which(Info$BigAsset %in% c('股票','债券'))]
  } else {
    assetNames <- Info$SecAsset
  }

  wth <- para[['wth']]; ww <- para[['ww']]; volmulti <- para[['multi']]; alpha <- para[['alpha']]

  highRisk <- Info$SecAsset[which(Info$RiskType=='H')] %>% intersect(assetNames)
  lowRisk  <- Info$SecAsset[which(Info$RiskType=='L')] %>% intersect(assetNames)

  UDBacktest.flt <- UDBacktest %>% mutate(Dt = ymd(rownames(UDBacktest))) %>%
    pivot_longer(colnames(UDBacktest), names_to = 'cycle') %>%
    group_by(Dt) %>%
    filter(value > 0) %>% ungroup()

  idx.wday <- Idx %>%
    mutate(Dt = ymd(rownames(Idx)) ,
           fri = ceiling_date(Dt, 'week', week_start = 7,change_on_boundary = F) - 2) %>%
    filter(Dt < the_day)

  pe.wday <- PE %>%
    mutate(Dt = ymd(rownames(PE)),
           fri = ceiling_date(Dt, 'week', week_start = 7,change_on_boundary = F) - 2) %>%
    filter(Dt < the_day)

  cyc_name <- colnames(UDBacktest)

  getWT <- function(budget){
    std_target  <- budget$BudgetTarget
    low_bud <- budget$LowRiskTarget
    high_ub <- budget$HighRiskWtUB
    bud <- rep(0,length(good_asset))
    bud[lowID] <- low_bud/length(lowID)
    bud[highID] <- (1-low_bud)/length(highID)
    # 不同宏观周期
    weight <- rep(0, length(Info$SecAsset))
    names(weight) <- Info$SecAsset
    # RiskParity求解
    high_arg <- rep(0, length(good_asset))
    high_arg[highID] <- 1
    wt <- RiskParity(covtemp, bud, std_target, high_arg, high_ub)$solution
    # 取整, 并确保sum(wt)=1
    wt <- roundWT(wt, 2)
    weight[good_asset] <- wt
    return(weight)
  }

  rpwt <- vector(mode='list', length=ncol(UDBacktest))
  for(i in seq(cyc_name)){
    cyc <- cyc_name[i]
    cyc.wday <- (UDBacktest.flt %>% dplyr::filter(cycle==cyc))$Dt + 7
    idx.cut <- idx.wday %>% filter(fri %in% cyc.wday)  %>% tail(wth)
    idx.cut <- xts(idx.cut%>% select(-c(fri, Dt)), ymd(idx.cut$Dt)) * 100
    pe.cut <- pe.wday %>% filter(fri %in% cyc.wday) %>% tail(wth)
    pe.cut <- xts(pe.cut%>% select(-c(fri, Dt)) , ymd(pe.cut$Dt))
    pe.obs <- pe.cut %>% tail(ww) %>% colMeans(na.rm = T)
    pe.qtl <- pe.cut %>% tail(wth) %>%
      sapply(FUN = function(x) quantile(x,0.9,na.rm = T) %>% as.numeric)
    multi_names <- names(pe.obs[pe.obs > pe.qtl])

    good_asset <- assetNames[which(Asset[cyc, assetNames] > 0)]

    highID <- which(good_asset %in% highRisk)
    lowID  <- which(good_asset %in% lowRisk)

    stdev <- EW.Volatility(idx.cut, ww, multi_names, volmulti, alpha)[good_asset]
    corr <- EW.Corr(idx.cut[,good_asset], ww, alpha)
    covtemp <- Cor2Cov(stdev, corr)

    cyc.weight <- ddply(Budget, .variables = 'BudgetTarget', .fun = getWT)
    rpwt[[i]] <- cbind(list(cycDate=rep(the_day, nrow(cyc.weight)),cycName=rep(cyc, nrow(cyc.weight))),cyc.weight)
  }

  rpwt <- bind_rows(rpwt)
  name_map <- c(cycDate='日期',cycName='宏观',BudgetTarget='风险')
  colnames(rpwt) <- ifelse(colnames(rpwt) %in% Info$SecAsset, colnames(rpwt), name_map[colnames(rpwt)])
  return(rpwt)
}

# cycle prob WT -> final WT
getRPWTSummary <- function(RPWT.hist, UDBacktest, assetName){
  hist0 <- RPWT.hist
  cyc0 <- UDBacktest

  # hist0$宏观月度 <- strftime(as.Date(hist0$日期 - dmonths(1) - ddays(15)), '%Y%m')
  cyc0$日期 <- as.Date(rownames(cyc0))
  cyc0 <- merge(unique(hist0['日期']), cyc0, by='日期', all.x=TRUE) %>%
    fill(names(UDBacktest), .direction='down')
  cyc.long <- cyc0 %>% gather(key='宏观',value='概率',-日期)
  merge_data <- merge(hist0, cyc.long, by=c('日期','宏观'))

  wt.adj <- merge_data[,assetName] * merge_data$概率
  wt.adj$日期 <- merge_data$日期
  wt.adj$风险 <- merge_data$风险

  finalwt <- wt.adj %>% gather(key='资产',value='权重',-c(日期, 风险)) %>%
    ddply(.(日期,风险,资产), dplyr::summarise, 权重=sum(权重)) %>%
    spread(资产, 权重) %>% select(c('日期','风险',assetName))
  return(finalwt)
}

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

# 原生风险预算
calcRawRPWT <- function(the_day, Idx, RPRet, Info, Budget, para){
  ww <- para[['ww']]; wth <- para[['wth']]
  volmulti <- para[['multi']]
  alpha    <- para[['alpha_long']]
  AssetComb <- list(
    comb1 = c('股票', '债券'),
    comb2 = c('股票', '债券', '商品')
  )

  # 数据准备
  idx.cut <- xts(Idx*100, rownames(Idx)%>%as.Date) %>%
    `[`(strftime(the_day-1, "/%Y-%m-%d")) %>%
    as.data.frame %>% tail(wth)
  cols <- idx.cut %>% sapply(function(x) sum(is.na(x))/length(x)<0.1)
  idx.cut <- idx.cut[,cols]%>%drop_na

  idx.rep <- xts(RPRet*100, as.Date(rownames(RPRet))) %>%
    `[`(strftime(the_day-1, "/%Y-%m-%d")) %>%
    as.data.frame %>% tail(wth)

  pe.cut  <- xts(PE, rownames(PE)%>%as.Date) %>%
    `[`(strftime(the_day-1, "/%Y-%m-%d")) %>%
    as.data.frame %>% tail(wth)
  cols <- pe.cut %>% sapply(function(x) sum(is.na(x))/length(x)<0.1)
  pe.cut <- pe.cut[,cols]%>%drop_na
  pe.obs <- pe.cut %>% tail(ww) %>% colMeans(na.rm = T)
  pe.qtl <- pe.cut %>% tail(wth) %>%
    sapply(FUN = function(x) quantile(x,0.9,na.rm = T) %>% as.numeric)
  multi_names <- names(pe.obs[pe.obs > pe.qtl])
  # 双层平价
  getWT2 <- function(budget){
    std_target  <- budget$BudgetTarget
    low_bud <- budget$LowRiskTarget
    high_ub <- budget$HighRiskWtUB

    assetName <- colnames(covtemp.rep)
    bud.rep <- rep(0, length(assetName))
    bud.rep[which(assetName=='bond')] <- low_bud
    bud.rep[which(assetName!='bond')] <- (1-low_bud)/(sum(assetName!='bond'))
    assetMat <- matrix(0, nrow=2, ncol=length(assetName)) # 分成高风险-低风险两个维度
    assetMat[1, which(assetName!='bond')] <- 1
    assetMat[2, which(assetName=='bond')] <- 1
    ub <- c(high_ub, 1)
    # 确定bud.rep & assetMat & upbound

    bigwt <- RiskParity(covtemp.rep, bud.rep, std_target, assetMat, ub)$solution
    totasset <- intersect(names(idx.cut), asset_cols)
    namemap <- c(stock='股票',bond='债券',future='商品')
    bigasset <- namemap[colnames(covtemp.rep)]
    names(bigwt) <- bigasset

    stdev <- EW.Volatility(idx.cut[,totasset], ww, multi_names, volmulti, alpha)
    corr <- EW.Corr(idx.cut[,totasset], ww, alpha)
    covtemp <- Cor2Cov(stdev, corr)

    secWT <- c()
    for(a in bigasset){
      secAsset <- intersect(Info$SecAsset[which(Info$BigAsset==a)],totasset)
      m <- length(secAsset)
      x0 <- matrix(1/m, nrow=m, ncol=1)
      mrc <- matrix(1/m, nrow=m, ncol=1)
      Cov <- cov(idx.cut, use = "na.or.complete")

      rp_result <- rp(x0, Cov[secAsset, secAsset], mrc, ctrl(trace=FALSE))
      wt <- c(getx(rp_result)) * bigwt[a]
      names(wt) <- secAsset
      secWT <- c(secWT, wt)
    }
    secWT <- roundWT(secWT,2)
    return(secWT)
  }

  raw_rpwt <- vector('list', length(AssetComb))

  count = 1
  # 股债 & 股债商
  for(comb in AssetComb){
    asset_cols <- Info$SecAsset[which(Info$BigAsset %in% comb)]
    repst_cols <- if(length(comb)==2) c('stock','bond') else c('stock','bond','future')

    # bud.rep <- rep(1,length(repst_cols))

    stdev.rep <- EW.Volatility(idx.rep, ww, multi_names, volmulti, alpha)[repst_cols]
    corr.rep <- EW.Corr(idx.rep[repst_cols], ww, alpha)
    covtemp.rep <- Cor2Cov(stdev.rep, corr.rep)
    raw.weight <- ddply(Budget, .variables = 'BudgetTarget', .fun=getWT2)

    raw_rpwt[[count]] <- cbind(list(`日期`=rep(the_day, nrow(raw.weight)),
                                    `组合`=rep(paste(comb, collapse='+'), nrow(raw.weight))),
                               raw.weight)
    count <- count + 1
  }
  raw_rpwt <- bind_rows(raw_rpwt)
  raw_rpwt[is.na(raw_rpwt)] <- 0
  names(raw_rpwt) <- ifelse(names(raw_rpwt)=='BudgetTarget','风险',names(raw_rpwt))
  return(raw_rpwt)
}



beg <- as.Date('2014-01-01')
end <- preFriday(Sys.Date())

dts <- getPosChgDts(as.Date(rownames(Idx)), beg, end)

# Calculate the number of cores
no_cores <- detectCores() - 1

# Initiate cluster
cl <- makeCluster(no_cores)

clusterExport(cl, c('calcRawRPWT','calcRPWT2','Asset','UDCyc','UDBacktest','ymd','ceiling_date',
                    'Idx', 'PE', 'Info', 'Budget', 'para','%>%','index','ddply','RPRet','mutate','pivot_longer',
                    'EW.Volatility','EW.Corr','Cor2Cov','ldply','bind_rows','Corr','Volatility','group_by',
                    'RiskParity','xts','drop_na','select','EW.Sig','is.xts','rp','ctrl','getx','ungroup',
                    'nloptr','roundWT','coredata','merge','filter','arrange'))

RPWT.stkbond_static <- calcRPWT2(dts[length(dts)], Idx, PE, Asset, Info, Budget, UDBacktest, para, mode='StkBond')
RPWT.all_static <- calcRPWT2(dts[length(dts)], Idx, PE, Asset, Info, Budget, UDBacktest, para, mode='All')
RPWT.static <- bind_rows(bind_cols(组合= 'MARB_股债',getRPWTSummary(RPWT.stkbond_static, UDBacktest, names(Asset))),
                         bind_cols(组合= 'MARB_全委',getRPWTSummary(RPWT.all_static, UDBacktest, names(Asset))))

RPWT.stkbond_hist <- parLapply(cl, dts, function(x) calcRPWT2(
  x,Idx,PE,Asset,Info,Budget,UDBacktest,para,mode='StkBond'
)) %>% bind_rows()
sumRPWT.stkbond <- getRPWTSummary(RPWT.stkbond_hist, UDBacktest, names(Asset))
sumRPWT.stkbond <- cbind(list(`组合`=rep('MARB_股债', nrow(sumRPWT.stkbond))), sumRPWT.stkbond)

RPWT.all_hist <- parLapply(cl, dts, function(x) calcRPWT2(x,Idx,PE,Asset,Info,Budget,UDBacktest,para,mode='All')) %>% bind_rows()
sumRPWT.all <- getRPWTSummary(RPWT.all_hist, UDBacktest, names(Asset))
sumRPWT.all <- cbind(list(`组合`=rep('MARB_全委', nrow(sumRPWT.all))), sumRPWT.all)

rawRPWT <- parLapply(cl, dts, function(x) calcRawRPWT(x,Idx,RPRet,Info,Budget,para)) %>% bind_rows() # parllel lapply
rawRPWT[is.na(rawRPWT)] <- 0
stopCluster(cl)

# 获得静态结果
# RPWT.stkbond_static <- calcRPWT(dts[length(dts)], Idx, PE, Asset, Info, Budget, UDCyc, para, mode='StkBond')
# RPWT.all_static <- calcRPWT(dts[length(dts)], Idx, PE, Asset, Info, Budget, UDCyc, para, mode='All')

# (2) Combine & Smooth & Evaluate
# (2.1) 不平滑
# 合并所有资产权重时间序列
totRPWT <- bind_rows(sumRPWT.stkbond, sumRPWT.all, rawRPWT)
# 生成净值序列
Nav.h <- ddply(totRPWT, .(组合, 风险),.fun = function(x) calcBacktestNav(idx=Idx, wt=x))
Nav.v <- cbind(colnames(Nav.h[3:dim(Nav.h)[2]]), data.frame(t(Nav.h[,3:dim(Nav.h)[2]])))
colnames(Nav.v) <- c('日期',paste(Nav.h$组合, Nav.h$风险, sep='|目标风险:'))
# 评价效果
positionEval <- ddply(totRPWT, .(组合, 风险), .fun=evalPosition)
appearanceEval <- ddply(Nav.h,.(组合, 风险), .fun=function(x) evalApperance(x[3:ncol(x)]))

summaryEval <- merge(positionEval, appearanceEval, by=c('组合','风险'))

# (2.2) 平滑资产权重时间序列
# 模型用0.35平滑
marb_wt <- smoothRPWT(bind_rows(sumRPWT.stkbond, sumRPWT.all), Info, 0.35)
chgdate <- ymd(20210101)
rp_wt1 <- smoothRPWT(filter(rawRPWT, 日期<=chgdate), Info, 0.05)
rp_wt2 <- smoothRPWT(bind_rows(filter(rp_wt1, 日期==chgdate),filter(rawRPWT, 日期>chgdate)), Info, 0.25)
rp_wt <- bind_rows(rp_wt1%>%filter(日期<=chgdate), rp_wt2%>%filter(日期>chgdate))

totRPWT.sm <- bind_rows(marb_wt, rp_wt)

totRPWT <- totRPWT[names(totRPWT.sm)]

# 生成净值序列
Nav.h_sm <- ddply(totRPWT.sm, .(组合, 风险),.fun = function(x) calcBacktestNav(idx=Idx, wt=x))
Nav.v_sm <- cbind(colnames(Nav.h_sm[3:dim(Nav.h_sm)[2]]), data.frame(t(Nav.h_sm[,3:dim(Nav.h_sm)[2]])))
colnames(Nav.v_sm) <- c('日期',paste(Nav.h_sm$组合, Nav.h_sm$风险, sep='|目标风险:'))
# 评价效果
positionEval.sm <- ddply(totRPWT.sm, .(组合, 风险), .fun=evalPosition)
appearanceEval.sm <- ddply(Nav.h_sm,.(组合, 风险), .fun=function(x) evalApperance(x[3:ncol(x)]))

summaryEval.sm <- merge(positionEval.sm, appearanceEval.sm, by=c('组合','风险'))


openxlsx::write.xlsx(list(StaticStkBond=RPWT.stkbond_static,
                          StaticAll=RPWT.all_static,
                          Static = RPWT.static,
                          DynCycStkBond=RPWT.stkbond_hist,
                          DynCycAll=RPWT.all_hist,
                          DyntotRPWT=totRPWT,
                          DyntotRPWT_sm=totRPWT.sm),
                     format(Sys.time(), "Result_RPWT_%Y%m%d.xlsx"), asTable = T)
openxlsx::write.xlsx(list(Nav=Nav.v, Nav_sm=Nav.v_sm,
                          Result=summaryEval,
                          Result_sm=summaryEval.sm),
                     format(Sys.time(), 'Result_MARBNav_%Y%m%d.xlsx'), asTable=T)

T1 <- Sys.time()
print(T1 - T0)

