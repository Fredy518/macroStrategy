# MacroEconomicCycle_v1
# version: 20200802_wuh

library(xts)
library(openxlsx)
library(nloptr) #Risk Pariy Optimizer
library(mFilter) #HP Filter
library(lubridate)
library(tidyverse)
# library(x12)
library(roll)


rm(list = ls())
source("Pkg_RiskBudget.R",encoding = 'UTF-8', echo=FALSE)
# 1. 计算价格基期指数 -------------------------------------------------------------

# # yoy: 同比数据
# # qoq: 环比数据
# makeBasePrice <- function(yoy, qoq, baseYear, prefer_qoq = T){
#   if (!(is.xts(yoy)&is.xts(qoq))) return('xts object is legal!')
#   baseYear <- as.character(baseYear)
#   baseYearData <- cumprod(qoq[baseYear]/100 + 1)/(as.numeric(qoq[baseYear][1]/100)+1)
#   finalData <- c()
#   for (m in 1:12){
#     yoy_before <- lag.xts(yoy[which(month(qoq)==m&year(yoy)<=as.numeric(baseYear))]/100 + 1,-1,na.pad = F)
#     before_num <- length(yoy_before)
#     baseData <- as.numeric(baseYearData[which(month(baseYearData)==m)])
#     if (before_num > 0){
#       yoy_cum_before <- cumprod(yoy_before)
#       multi <- as.numeric(yoy_cum_before[before_num] * yoy_before[before_num])
#       yoy_before <- yoy_cum_before / multi * baseData # 归一化
#     }
#     if (prefer_qoq){
#       finalData <- c(yoy_before, finalData)
#     } else {
#       yoy_after <- yoy[which(month(yoy)==m&year(yoy)>as.numeric(baseYear))]/100 + 1
#       yoy_cum_after <- cumprod(yoy_after)
#       yoy_after <- baseData * yoy_cum_after
#       finalData <- c(yoy_before, finalData, yoy_after)
#     }
#   }
#   if (prefer_qoq){
#     qoq_after <- qoq[which(year(qoq)>=as.numeric(baseYear))]
#     qoq_cum_after <- cumprod(qoq_after/100+1)/(as.numeric(qoq_after[1]/100)+1)
#     finalData <- c(finalData, qoq_cum_after)
#   } else {
#     finalData <- c(finalData, baseYearData)
#   }
#   avgYear <- mean(baseYearData)
#   finalData/avgYear
# }
#
# base_price <- read.xlsx('Eg_MacroEcoCycle.XLSX', sheet = '价格指数', startRow = 2, detectDates = T)
# cpi_yoy <- xts(base_price$`CPI:当月同比`, base_price$指标名称)
# cpi_qoq <- xts(base_price$`CPI:环比`, base_price$指标名称)
# ppi_yoy <- xts(base_price$`PPI:全部工业品:当月同比`, base_price$指标名称)
# ppi_qoq <- xts(base_price$`PPI:全部工业品:环比`, base_price$指标名称)
# rpi_yoy <- xts(base_price$`RPI:当月同比`, base_price$指标名称)
# rpi_qoq <- xts(base_price$`RPI:环比`, base_price$指标名称)
# cpi_b <- makeBasePrice(cpi_yoy, cpi_qoq, 2002)
# ppi_b <- makeBasePrice(ppi_yoy, ppi_qoq, 2002)
# rpi_b <- makeBasePrice(rpi_yoy, rpi_qoq, 2010)


# 2. 处理宏观数据 ---------------------------------------------------------------

macro_data <- read.xlsx('Eg_MacroEcoCycle.xlsx', sheet = 'EDB', startRow = 2, detectDates = T)
info <- read.xlsx('Eg_MacroEcoCycle.xlsx', sheet = 'INFO', startRow = 2, detectDates = T)
macro_data <- melt(macro_data[3:dim(macro_data)[1],], id.vars = '指标名称')
colnames(macro_data) <- c('date','variable','value')
macro_input <- macro_data %>%
  merge(info, by.x = 'variable', by.y = 'macroEcoIdx') %>%
  mutate(
    date = ymd(date),
    value = as.numeric(value),
    beg = ymd(beg),
    update = ymd(update)
  ) %>% filter(inModel)

# combine_input中的cmi & fin 需要进一步合成
combine_input <- macro_input %>% filter(combine) %>% dcast(date ~ abbr, value.var = 'value')

# (1) CMI


cmib <- xts(combine_input$CMIB, combine_input$date)
cmie <- xts(combine_input$CMIE, combine_input$date)
cmi <- combineCMI(cmib, cmie, getBeg('CMIE'), getUpdate('CMIE'))
names(cmi) <- 'CMIE'



# (2) FIN

fin <- xts(combine_input$FIN, combine_input$date)
finc <- xts(combine_input$FINC, combine_input$date)
fino <- xts(combine_input$FINO, combine_input$date)
fin_yoy <- combineFIN(fin, finc, fino, getBeg('FIN')) # 同比数据
names(fino) <- 'FINO'
names(fin_yoy) <- 'FIN'

noneed_combine <-  macro_input %>% filter(!combine) %>% dcast(date ~ abbr, value.var = 'value')

# (3) deflator

# m1_dft <- deflatorYOY(xts(noneed_combine$M1, noneed_combine$date), cpi_b)
# m2_dft <- deflatorYOY(xts(noneed_combine$M2, noneed_combine$date), cpi_b)
# names(m1_dft) <- 'M1'
# names(m2_dft) <- 'M2'
# asset_dft <- deflatorYOY(xts(noneed_combine$ASSET, noneed_combine$date), cpi_b)
# names(asset_dft) <- 'ASSET'
# fin_dft <- deflatorYOY(fin_yoy, cpi_b)
# names(fin_dft) <- 'FIN'
# ind_dft <- deflatorYOY(xts(noneed_combine$IND, noneed_combine$date), ppi_b)
# names(ind_dft) <- 'IND'
# cons_dft <- deflatorYOY(xts(noneed_combine$CONS, noneed_combine$date), rpi_b)
# names(cons_dft) <- 'CONS'

# g_cols <- unlist(info %>% filter(inModel&(!deflator)&(!combine)&(cycType==1)) %>% select(abbr))
g_cols <- unlist(info %>% filter(inModel&(!combine)&(cycType==1)) %>% select(abbr))
growth <- xts(noneed_combine[g_cols], noneed_combine$date)
# growth <- cbind.xts(growth, ind_dft, cmi, cons_dft, fino)
growth <- cbind.xts(growth, cmi, fino)

# i_cols <- unlist(info %>% filter(inModel&(!deflator)&(!combine)&(cycType==2)) %>% select(abbr))
i_cols <- unlist(info %>% filter(inModel&(!combine)&(cycType==2)) %>% select(abbr))
inflation <- xts(noneed_combine[i_cols], noneed_combine$date)
l_cols <- unlist(info %>% filter(inModel&(!combine)&(cycType==3)) %>% select(abbr))
liquid <- xts(noneed_combine[l_cols], noneed_combine$date)
# liquid <- cbind.xts(m1_dft, m2_dft, asset_dft, fin_dft)
liquid <- cbind.xts(liquid, fin_yoy)


raw_factor <- downFill(cbind.xts(growth, liquid, inflation))

# 由于raw_factor得到的处理后经济数据在wind数据更新及时的情况下，不会出现变动。
# 合成类经济数据如CMI和FIN，虽然各子项数据如社融存量、社融累计值的更新时间并不一致，但影响不大。
# 这里简单处理，认为合成类经济数据均为同一天更新。

# 硬编码: 经济数据更新时间
# factor_update_day <- data.frame(
#   factor = c('GDP','ECI','PMI','PMIN','CONS','PRICE','IND','CMIE','FINO','M1','M2','ASSET','FIN','CPI','PPI','RPI','PPIRM'),
#   update_day = c(20, 1, 1, 1, 20, 20, 20, 1, 10, 10, 10, 20, 10, 10, 10, 12, 10)
# )

idx_map <- data.frame(
  idx_1 = c('CMIE','PMI','IND','PMIN','CPI','PPI','RPI','PPIRM','M1','M2','FIN','ASSET'),
  idx_2 = c('ECI','IND','IND','CONS','CPI','PPI','RPI','PPIRM','M1','M2','FIN','FINO'),
  update_day = c(1, 1, 20, 1, 10, 10, 12, 10, 10, 10, 10, 20), stringsAsFactors = F
)%>% merge(info, by.x = 'idx_1', by.y = 'abbr') %>%
  select(idx_1,idx_2,cycType,update_day) %>% arrange(cycType)

beg <- as.Date('2012-01-16')
end <- preFriday(Sys.Date())

dts <- getPosChgDts(seq.Date(from = beg, to = end, by = 1), beg, end)

getDynamicUDCycle <- function(raw_factor, dts, idx_map, hp_lambda=20){
  dynamic_prob <- xts()
  for(dt_i in seq(length(dts))){
    dt <- dts[dt_i]
    sub_factor <- raw_factor[paste0('/',dt)]
    day_num <- day(dt)
    zero_idx <- with(subset(idx_map, update_day>day_num), unique(idx_1, idx_2))
    sub_factor[nrow(sub_factor), zero_idx] <- 0
    sub_factor <- downFill(sub_factor)

    sub_hpfactor <- hpFilter(sub_factor, hp_lambda)
    sub_drfactor <- getDirection(sub_hpfactor[paste0(dt-700,'/',dt)], calcDt = 1, stdTV = 0.2) %>%
      fillDrNaByidx2(idx_map) %>% as.data.frame() %>% drop_na()
    sub_drfactor.xts <- xts(sub_drfactor, ymd(rownames(sub_drfactor)))
    sub_prob <- udCycleProb(tail(sub_drfactor.xts, 1), idx_map)
    index(sub_prob) <- dt
    if(day_num<10) sub_prob[dt, c('inflation','liquid')] <- NA
    if(length(dynamic_prob)==0) dynamic_prob <- sub_prob
    else dynamic_prob <- rbind.xts(dynamic_prob, sub_prob)
  }
  dynamic_prob <- downFill(dynamic_prob, zeroAdj = F)
  return(dynamic_prob)
}

cyc_map <- data.frame(
  cyc_code = c('001',     '101',     '111',     '110',     '000',     '010',     '011',     '100'),
  cyc_name = c('衰退后期','复苏前期','繁荣前期','繁荣后期','衰退前期','滞涨前期','滞涨后期','复苏后期'),
  order = c(1,2,4,5,8,6,7,3), stringsAsFactors = FALSE
)

dynamic_prob <- getDynamicUDCycle(raw_factor, dts, idx_map)
dynamic_cycle <- udCycleMap(dynamic_prob, cyc_map, width=1)

# 3.判断宏观周期 ----------------------------------------------------------------

# (1) HP filter

# hp_lambda越大, 扩散指数的方向越稳定
# 月度数据推荐lambda=14400, 但是无法捕捉到疫情后的经济复苏
hp_lambda <- 20
hp_factor <- hpFilter(raw_factor, hp_lambda)


# (2) 扩散指数


# 经过多次实验观察dr_summary发现
# (a) 确定指标方向的函数参数不敏感;
# (b) x12调整对结果影响接近于0;
# (c) hp滤波对结果影响特别大
dr_factor <- getDirection(hp_factor, calcDt = 1, stdTV = 0.2)
dr_summary <- getDuration(dr_factor)

# (3) 宏观周期

dr_factor.ud <- drop_na(as.data.frame(fillDrNaByidx2(dr_factor, idx_map)))
dr_factor.ud <- xts(dr_factor.ud, ymd(rownames(dr_factor.ud)))

ud_prob <- udCycleProb(dr_factor.ud, idx_map)

ud_cycle <- udCycleMap(ud_prob, cyc_map, width=1)

hp_model_idx <- c('GDP','PRICE','M1')
dr_factor.hp <- dr_factor[,hp_model_idx]

hp_cycle <- hpCycleMap(dr_factor.hp, cyc_map)

ud_cycle <- hist_ud_cycle(raw_factor, hp_lambda)

# 4.输出计算结果 ----------------------------------------------------------------

openxlsx::write.xlsx(
  list(
    RawFactor = raw_factor %>% as.data.frame,
    HP = hp_factor %>% as.data.frame,
    DR = dr_factor %>% as.data.frame,
    rawProb = ud_prob %>% as.data.frame,
    PbBacktest = dynamic_prob %>% as.data.frame,
    UDBacktest = dynamic_cycle %>% as.data.frame,
    UDCyc = ud_cycle %>% as.data.frame,
    HPCyc = hp_cycle %>% as.data.frame
  ), format(Sys.time(), "Result_MacroEcoCycle_%Y%m%d.xlsx"), rowNames = TRUE
)

