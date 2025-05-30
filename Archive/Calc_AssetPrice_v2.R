# MacroAssetPrice_v2
# version: 20200810_wuh

# output: Asset Ret & BigAsset RP Index

library(plyr)
library(DBI)
library(RMySQL)
library(reshape2)
library(dplyr)
library(tidyr)
library(lubridate)
library(cccp)
library(openxlsx)
library(xts)
library(WindR)

source("Pkg_RiskBudget.R",encoding = 'UTF-8', echo=FALSE)
# Function 1: getCIPlateData
# when PE is NULL, assign it as 0 (PE_median < 0, windDB return NULL)
# weighted by free market value(free_mv = float_mv * free_share / float_share)
# beg: %Y%m%d
getCIPlateData<- function(con, beg){
  sql.st <- sprintf("
  SELECT
  	v.s_info_windcode code,
  	v.trade_dt date,
  	v.mv_float*v.tot_shr_free/v.tot_shr_float/1e8 mv_free,
    CASE
    WHEN v.pe_ttm is NULL then 0 ELSE pe_ttm END pe,
  	e.s_dq_close price
  FROM
  	aindexindustrieseodcitics e
  	INNER JOIN aindexvaluation v ON v.trade_dt = e.trade_dt
  	AND v.S_INFO_WINDCODE = e.S_INFO_WINDCODE
  WHERE
    e.s_info_windcode in ('%s')
    and e.trade_dt >= %s
  ",paste(citics_index, collapse = "','"),beg)

  citicsInd.df <- dbGetQuery(con, sql.st)
  plate <- citicsInd.df %>%
    merge(ind2plate, by = 'code') %>%
    mutate(date = ymd(date)) %>%
    arrange(date) %>%
    group_by(code) %>%
    dplyr::summarise(
      date = date,
      asset = as.character(asset),
      mv_free = mv_free,
      pe = pe,
      ret = c(1,price[2:length(price)] / price[1:(length(price)-1)])-1
    ) %>% ungroup() %>% dplyr::group_by(date, asset) %>%
    dplyr::summarise(
      ret = weighted.mean(ret, mv_free, na.rm = T),
      pe = weighted.mean(pe, mv_free, na.rm = T)
    )
  first_date <- min(plate$date)
  plate %>% dplyr::filter(date > first_date)
}

# Function2: getStockIdxData
getStockIdxData <- function(con, beg){
  sql.st <- sprintf("
  SELECT
  	v.s_info_windcode code,
  	v.trade_dt date,
    CASE
    WHEN v.pe_ttm is NULL then 0 ELSE pe_ttm END pe,
  	e.s_dq_close price
  FROM
  	aindexeodprices e
  	INNER JOIN aindexvaluation v ON v.trade_dt = e.trade_dt
  	AND v.S_INFO_WINDCODE = e.S_INFO_WINDCODE
  WHERE
    e.s_info_windcode in ('%s')
    and e.trade_dt >= %s
  ",paste(stock_plate$code, collapse = "','"),beg)
  stockIdx.df <- dbGetQuery(con, sql.st)
  stockIdx <- stockIdx.df %>%
    merge(stock_plate, by = 'code') %>%
    mutate(date = ymd(date)) %>%
    arrange(date) %>%
    group_by(asset) %>%
    dplyr::summarise(
      date = date,
      pe = pe,
      ret = c(1,price[2:length(price)] / price[1:(length(price)-1)])-1
    ) %>% ungroup()
  first_date <- min(stockIdx$date)
  stockIdx.f <- stockIdx %>% filter(date > first_date)
  return(stockIdx.f)
}

# Function3: getAStockData
getAStockData <- function(con, beg){
  StockIdx <- getStockIdxData(con, beg)
  CIPlate <- getCIPlateData(con, beg)
  AStock <- bind_rows(StockIdx, CIPlate)
  return(AStock)
}

# Function4: getOverseasData
getOverSeasData <- function(beg){
  overseas.close <- w.wsd(overseas_plate$code, 'close', ymd(beg),
                          as.Date(Sys.time())-1,"Fill=Previous")$Data
  overseas.ret <- overseas.close %>%
    melt(id.vars='DATETIME',variable.name='code', value.name='price') %>%
    merge(overseas_plate, by = 'code') %>%
    mutate(date = ymd(DATETIME)) %>%
    arrange(date) %>%
    group_by(asset) %>%
    dplyr::summarise(
      date = date,
      ret = c(1,price[2:length(price)] / price[1:(length(price)-1)])-1
    ) %>% ungroup()
  overseas.pe <- w.wsd(overseas_plate$code, 'pe_ttm',ymd(beg),
                       as.Date(Sys.time())-1,"Fill=Previous")$Data %>%
    melt(id.vars='DATETIME',variable.name='code',value.name='pe') %>%
    merge(overseas_plate, by = 'code') %>%
    mutate(date = ymd(DATETIME)) %>%
    arrange(date) %>%
    select(date, asset, pe)
  overseasIdx <- overseas.ret %>% merge(overseas.pe, by = c('date','asset'))
  return(overseasIdx)
}

# Function5: getBondData
getBondData <- function(con, beg){
  sql.st <- sprintf("
  SELECT
  	trade_dt date,
  	S_INFO_WINDCODE code,
  	s_dq_close price
  FROM
  	cbondindexeodcnbd
  WHERE
  	S_INFO_WINDCODE IN ('%s')
  	and trade_dt >= %s
  ",paste(cbond_plate$code, collapse = "','"),beg)
  bondIdx.df <- dbGetQuery(con, sql.st)
  bondIdx <- bondIdx.df %>%
    merge(cbond_plate, by = 'code') %>%
    mutate(date = ymd(date)) %>%
    arrange(date) %>%
    group_by(asset) %>%
    dplyr::summarise(
      date = date,
      ret = c(1,price[2:length(price)] / price[1:(length(price)-1)])-1
    ) %>% ungroup()
  return(bondIdx)
}


# Function6: getFuturesData
getFuturesData <- function(beg){
  futuresIdx.df <- w.wsd(futures_plate$code,"close",ymd(beg),
                         as.Date(Sys.time())-1,"Fill=Previous")$Data
  futuresIdx <- futuresIdx.df %>%
    melt(id.vars='DATETIME',variable.name='code', value.name='price') %>%
    merge(futures_plate, by = 'code') %>%
    mutate(date = ymd(DATETIME)) %>%
    arrange(date) %>%
    group_by(asset) %>%
    dplyr::summarise(
      date = date,
      ret = c(1,price[2:length(price)] / price[1:(length(price)-1)])-1
    ) %>% ungroup()
  return(futuresIdx)
}

ceiling2friday <- function(d){
  d <- as.Date(d)
  friday <- ceiling_date(d, 'week', week_start = 7,change_on_boundary = F) - 2
  return(friday)
}


getPosChgDts <- function(dts, beg, end, freq='W'){
  dts <- sort(as.Date(dts))
  dts.df <- data.frame(
    actualDay = dts,
    weekFriday = ceiling2friday(dts)
  )
  chgdts_df <- ddply(dts.df, .variables='weekFriday',
                     .fun=function(x) c(firstDay=x$actualDay[1], lastDay=x$actualDay[dim(x)[1]])) %>%
    filter(firstDay != lastDay, lastDay >= as.Date(beg), lastDay <= as.Date(end)) %>%
    mutate(month = format(weekFriday, '%Y-%m'))
  if(freq=='W'){
    chgdts <- chgdts_df %>% `[[`('weekFriday')
  } else{
    chgdts <- chgdts_df %>% group_by(month) %>%
      dplyr::summarise(monthLastFri = last(weekFriday)) %>% `[[`('monthLastFri')
  }
  return(chgdts)
}


getBigAssetRPWeight <- function(the_day, asset_idx, wth){
  idx.cut <- asset_idx  %>% `[`(strftime(the_day-1, "/%Y-%m-%d")) %>% as.data.frame %>% tail(wth)
  cols_bool <- idx.cut %>% sapply(function(x) sum(is.na(x))/length(x)<0.1)
  idx.cut <- idx.cut[,cols_bool] %>% drop_na

  m <- ncol(idx.cut)
  Cov <- matrix(cov(idx.cut*100, use = "na.or.complete"), m, m)
  x0 <- matrix(1/m, nrow=m, ncol=1)
  mrc <- matrix(1/m, nrow=m, ncol=1)

  rp_result <- cccp::rp(x0, Cov, mrc, ctrl(trace=FALSE))
  wt <- c(getx(rp_result))
  names(wt) <- names(cols_bool[cols_bool])
  return(wt)
}

getPdDailyRet <- function(beg_dt, end_dt, asset_idx, asset_wt){
  idx.cut <- (asset_idx)  %>% `[`(sprintf('%s/%s', strftime(beg_dt, '%Y-%m-%d'), strftime(end_dt, '%Y-%m-%d'))) %>% as.data.frame %>% `[`(names(asset_wt))
  pd_nav <- data.matrix(cumprod(idx.cut + 1)) %*% asset_wt
  pd_nav.xts <- xts(pd_nav, as.Date(rownames(pd_nav)))
  pd_nav.lag <- lag.xts(pd_nav.xts)
  pd_nav.lag[is.na(pd_nav.lag)] <- 1
  daily_ret <- pd_nav.xts / pd_nav.lag - 1
  return(daily_ret)
}

getRPIdxRet <- function(chgdts, asset_idx){
  RPIndWt  <- list()
  RPIndRet <- c()
  for(i_day in seq_along(chgdts)){
    the_day <- chgdts[i_day]
    asset_wt <- getBigAssetRPWeight(the_day, asset_idx, 750)
    end_day <- if(i_day==length(chgdts)) the_day + 30 else chgdts[i_day+1]-1
    daily_ret <- getPdDailyRet(the_day, end_day, asset_idx, asset_wt)
    if(length(RPIndRet)==0){
      RPIndRet <- daily_ret
    } else {
      RPIndRet <- rbind.xts(RPIndRet, daily_ret)
    }
    RPIndWt[[i_day]] <- asset_wt
  }
  RPIndWt.df <- bind_rows(RPIndWt)
  RPIndWt.df <- cbind(日期=chgdts,RPIndWt.df)
  return(list(RPRet = RPIndRet, RPWt = RPIndWt.df))
}



# 中信一级行业代码
citics_index <- c("CI005001.WI","CI005002.WI","CI005003.WI",
                  "CI005004.WI","CI005005.WI","CI005006.WI",
                  "CI005007.WI","CI005008.WI","CI005009.WI",
                  "CI005010.WI","CI005011.WI","CI005012.WI",
                  "CI005013.WI","CI005014.WI","CI005015.WI",
                  "CI005016.WI","CI005017.WI","CI005018.WI",
                  "CI005019.WI","CI005020.WI","CI005021.WI",
                  "CI005022.WI","CI005023.WI","CI005030.WI",
                  "CI005024.WI","CI005025.WI","CI005026.WI",
                  "CI005027.WI","CI005028.WI")
# 中信一级行业对应板块信息
asset_plate <- c('周期','周期','周期','基地','周期','周期',
                 '基地','基地','消费','制造','制造','制造',
                 '制造','消费','消费','消费','消费','医疗',
                 '消费','消费','金融','金融','基地','金融',
                 '基地','科技','科技','科技','科技')
ind2plate <- data.frame(code = citics_index, asset = asset_plate)

stock_plate <- data.frame(
  code = c('000300.SH','000905.SH'),
  asset = c('沪深300','中证500')
)

overseas_plate <- data.frame(
  code = c('HSI.HI','SPX.GI'),
  asset = c('恒生','标普')
)

cbond_plate <- data.frame(
  code = c('CBA01803.CS','CBA00103.CS'),
  asset = c('短债','全债')
)

futures_plate <- data.frame(
  code = c('AU9999.SGE','NH0100.NHF','HTCI0101.WI'),
  asset = c('黄金','南华','动量')
)

# Output Asset Price--------------------------------------------------------------

w.start(showmenu=FALSE)
options(dplyr.summarise.inform = FALSE, warn = -1) # ignore warnings

wind.con <- dbConnect(MySQL(), dbname="wind", username="readuser", password="user123",
                      host="windfof2014.mysql.rds.aliyuncs.com", port = 3306)

dbSendQuery(wind.con,'SET NAMES gbk')
astock <- getAStockData(wind.con, 20050101)
overseas <- getOverSeasData(20050101)
cbond <- getBondData(wind.con, 20050101)
futures <- getFuturesData(20050101)

PE <- bind_rows(astock, overseas) %>% dcast(date~asset, value.var = 'pe')
Idx <- bind_rows(astock, overseas, futures) %>%
  dcast(date~asset, value.var = 'ret') %>%
  merge(
    bind_rows(cbond) %>% dcast(date~asset, value.var = 'ret'),
    by = 'date', all.x = T
  )


# 用周五作为开始和结束日期
RP_beg <- as.Date('2009-1-23')
RP_end <- preFriday(Sys.Date())

stock_vector <- c('沪深300','中证500','基地','金融','科技','消费','医疗','制造','周期','标普','恒生')
bond_vector <- c('短债','全债')
future_vector <- c('动量','黄金','南华')


stock_asset <- xts(Idx[stock_vector], order.by = as.Date(Idx$date))
bond_asset <- xts(Idx[bond_vector], order.by = as.Date(Idx$date))
future_asset <- xts(Idx[future_vector], order.by = as.Date(Idx$date))

chgdts <- getPosChgDts(as.Date(Idx$date), RP_beg, RP_end, freq = 'M')
# chgdts <- if(chgdts[length(chgdts)]==index(stock_asset)[nrow(stock_asset)]) chgdts[1:(length(chgdts)-1)] else chgdts
chgdts <- if(chgdts[length(chgdts)]==index(stock_asset)[nrow(stock_asset)]) chgdts else chgdts[1:(length(chgdts)-1)]

stockRPIdx <- getRPIdxRet(chgdts, stock_asset)
bondRPIdx <- getRPIdxRet(chgdts, bond_asset)
futureRPIdx <- getRPIdxRet(chgdts, future_asset)

RPRet <- data.frame(index(stockRPIdx$RPRet),cbind.xts(stockRPIdx$RPRet, bondRPIdx$RPRet, futureRPIdx$RPRet))
names(RPRet) <- c('date','stock', 'bond', 'future')


openxlsx::write.xlsx(list(PE = PE,Idx = Idx, RPRet=RPRet,
                          stockRPWt = stockRPIdx$RPWt,
                          bondRPWt = bondRPIdx$RPWt,
                          futureRPWt = futureRPIdx$RPWt),
                     strftime(Sys.Date(), 'Result_AssetPrice_%Y%m%d.xlsx'))
