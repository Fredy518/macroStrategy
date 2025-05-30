import pandas as pd
import numpy as np
from statsmodels.tsa.filters import hpfilter as sm_hpfilter
from datetime import datetime, timedelta 

def get_beg(info_df: pd.DataFrame, name: str) -> pd.Timestamp:
    """Gets the beginning date for a given macro indicator abbreviation."""
    try:
        beg_date_str = info_df.loc[info_df['abbr'] == name, 'beg'].iloc[0]
        return pd.to_datetime(beg_date_str)
    except IndexError:
        raise ValueError(f"Indicator abbreviation '{name}' not found in info_df or 'beg' column missing.")
    except Exception as e:
        raise type(e)(f"Error processing 'beg' date for '{name}': {e}")

def get_update(info_df: pd.DataFrame, name: str) -> pd.Timestamp:
    """Gets the update date for a given macro indicator abbreviation."""
    try:
        update_date_str = info_df.loc[info_df['abbr'] == name, 'update'].iloc[0]
        return pd.to_datetime(update_date_str)
    except IndexError:
        raise ValueError(f"Indicator abbreviation '{name}' not found in info_df or 'update' column missing.")
    except Exception as e:
        raise type(e)(f"Error processing 'update' date for '{name}': {e}")

def get_yoy(series: pd.Series) -> pd.Series:
    """Calculates Year-over-Year percentage change for a monthly series."""
    if not isinstance(series.index, pd.DatetimeIndex):
        raise ValueError("Series index must be a DatetimeIndex.")
    series_sorted = series.sort_index()
    yoy = (series_sorted / series_sorted.shift(12) - 1) * 100
    return yoy

def combine_cmi(cmib_series: pd.Series, cmie_series: pd.Series, 
                  beg_date: pd.Timestamp, update_date: pd.Timestamp) -> pd.Series:
    """Combines CMI B and CMI E based on R script logic."""
    cmib = cmib_series[cmib_series.index >= beg_date].copy()
    cmie = cmie_series[cmie_series.index >= beg_date].copy()
    zero_after_update_mask = (cmib.index > update_date) & (cmib == 0)
    idx_zero_after_update = cmib.index[zero_after_update_mask]
    if not idx_zero_after_update.empty:
        try:
            cmib_after_update = cmib[cmib.index > update_date].copy()
            cmib_after_update[cmib_after_update == 0] = np.nan
            cmib_after_update_filled = cmib_after_update.fillna(method='ffill')
            cmib.update(cmib_after_update_filled)
        except IndexError: 
            pass 
    mask_cmie_zero = (cmie == 0)
    cmie.loc[mask_cmie_zero] = cmib.loc[mask_cmie_zero]
    return cmie

def combine_fin(fin_series: pd.Series, finc_series: pd.Series, fino_series: pd.Series,
                  beg_date: pd.Timestamp) -> pd.Series:
    """Combines FIN, FINC, FINO based on R script logic."""
    fin = fin_series[fin_series.index >= beg_date].copy()
    finc = finc_series[finc_series.index >= beg_date].copy()
    fino = fino_series[fino_series.index >= beg_date].copy()
    finc = finc / 10000
    fino.loc[fino.index.month != 12] = np.nan
    fino_filled = fino.fillna(method='ffill') 
    fino_na_mask = fino.isna()
    fino.loc[fino_na_mask] = finc.loc[fino_na_mask] + fino_filled.loc[fino_na_mask]
    fino_yoy = get_yoy(fino)
    fin_zero_mask = (fin == 0)
    common_index_for_fin_update = fin.loc[fin_zero_mask].index.intersection(fino_yoy.index)
    if not common_index_for_fin_update.empty:
        fin.loc[common_index_for_fin_update] = fino_yoy.loc[common_index_for_fin_update]
    return fin

def zero_to_na(df: pd.DataFrame) -> pd.DataFrame:
    """Replaces all zero values in a DataFrame with NaN."""
    return df.replace(0, np.nan)

def down_fill(df: pd.DataFrame, zero_adj: bool = True) -> pd.DataFrame:
    """Downwards fill NA values in a DataFrame.
    If zero_adj is True, converts zeros to NA before filling.
    """
    if df.empty:
        return df.copy()
    output_df = df.copy()
    if zero_adj:
        output_df = zero_to_na(output_df)
    return output_df.fillna(method='ffill')

def hp_filter_df(df: pd.DataFrame, lambda_val: float) -> pd.DataFrame:
    """Applies HP filter to each column of a DataFrame and returns the trend components."""
    if not isinstance(df.index, pd.DatetimeIndex):
        pass 
    trend_df = pd.DataFrame(index=df.index)
    for col_name in df.columns:
        series = df[col_name].dropna()
        if len(series) < 2:
            trend_df[col_name] = np.nan
            continue
        try:
            _cycle, trend = sm_hpfilter(series, lamb=lambda_val)
            trend_df[col_name] = trend.reindex(df.index) 
        except Exception as e:
            trend_df[col_name] = np.nan
            trend_df[col_name] = trend_df[col_name].astype(float)
    return trend_df

def get_direction(df: pd.DataFrame, calc_dt: int, std_tv: float, smp_num: int = 12) -> pd.DataFrame:
    """Calculates the direction of change for each column in a DataFrame."""
    direction_df = pd.DataFrame(index=df.index)
    for col_name in df.columns:
        series = df[col_name].dropna()
        if series.empty:
            direction_df[col_name] = np.nan
            continue
        dif_ts = series.diff(calc_dt) / calc_dt
        rsd_ts = dif_ts.rolling(window=smp_num, min_periods=3).std()
        conditions = [
            dif_ts >= rsd_ts * std_tv,
            dif_ts <= rsd_ts * (-std_tv)
        ]
        choices = [1, -1]
        direction_col = pd.Series(np.select(conditions, choices, default=np.nan), index=series.index)
        direction_col_filled = direction_col.fillna(method='ffill')
        remaining_na_mask = direction_col_filled.isna()
        direction_col_filled.loc[remaining_na_mask] = np.where(dif_ts[remaining_na_mask] > 0, 1, -1)
        direction_df[col_name] = direction_col_filled.reindex(df.index)
    return direction_df

def fill_dr_na_by_idx2(df: pd.DataFrame, idx_map_df: pd.DataFrame) -> pd.DataFrame:
    """Fills NA values in direction DataFrame based on idx_map (idx_1 gets from idx_2)."""
    df.columns = df.columns.astype(str)
    idx_map_df = idx_map_df.astype(str)
    result_df = pd.DataFrame(index=df.index)
    processed_cols = []
    for _idx, row in idx_map_df.iterrows():
        c1 = row['idx_1']
        c2 = row['idx_2']
        if c1 not in df.columns:
            continue 
        if c2 not in df.columns and c1 in df.columns and df[c1].hasnans:
             if c1 not in processed_cols:
                result_df[c1] = df[c1].copy()
                processed_cols.append(c1)
             continue
        if c1 not in processed_cols:
            tc1_series = df[c1].copy()
            if c2 in df.columns :
                tc1_series.fillna(df[c2], inplace=True)
            result_df[c1] = tc1_series
            processed_cols.append(c1)
    final_cols_ordered = idx_map_df['idx_1'].unique().tolist()
    existing_final_cols = [col for col in final_cols_ordered if col in result_df.columns]
    return result_df[existing_final_cols]

def ud_cycle_prob(df: pd.DataFrame, idx_map_df: pd.DataFrame) -> pd.DataFrame:
    """Calculates Up/Down cycle probabilities for growth, inflation, liquid."""
    if 'cycType' in idx_map_df.columns and pd.api.types.is_numeric_dtype(idx_map_df['cycType']):
        idx_map_df['cycType'] = idx_map_df['cycType'].astype(int)
    growth_cols = idx_map_df.loc[idx_map_df['cycType'] == 1, 'idx_1'].unique().tolist()
    inflation_cols = idx_map_df.loc[idx_map_df['cycType'] == 2, 'idx_1'].unique().tolist()
    liquid_cols = idx_map_df.loc[idx_map_df['cycType'] == 3, 'idx_1'].unique().tolist()
    growth_cols_exist = [col for col in growth_cols if col in df.columns]
    inflation_cols_exist = [col for col in inflation_cols if col in df.columns]
    liquid_cols_exist = [col for col in liquid_cols if col in df.columns]
    probs = pd.DataFrame(index=df.index)
    if growth_cols_exist:
        probs['growth'] = (df[growth_cols_exist] == 1).sum(axis=1) / len(growth_cols_exist)
    else:
        probs['growth'] = np.nan
    if inflation_cols_exist:
        probs['inflation'] = (df[inflation_cols_exist] == 1).sum(axis=1) / len(inflation_cols_exist)
    else:
        probs['inflation'] = np.nan
    if liquid_cols_exist:
        probs['liquid'] = (df[liquid_cols_exist] == 1).sum(axis=1) / len(liquid_cols_exist)
    else:
        probs['liquid'] = np.nan
    return probs

def ud_cycle_map(ud_prob_df: pd.DataFrame, cyc_map_df: pd.DataFrame, width: int = 1) -> pd.DataFrame:
    """Maps UD probabilities to 8 cycle type probabilities, with optional rolling mean."""
    g = ud_prob_df['growth']
    i = ud_prob_df['inflation']
    l = ud_prob_df['liquid']
    cycle_probs_df = pd.DataFrame(index=ud_prob_df.index)
    cycle_probs_df['001'] = (1 - g) * (1 - i) * l
    cycle_probs_df['101'] = g * (1 - i) * l
    cycle_probs_df['111'] = g * i * l
    cycle_probs_df['110'] = g * i * (1 - l)
    cycle_probs_df['000'] = (1 - g) * (1 - i) * (1 - l)
    cycle_probs_df['010'] = (1 - g) * i * (1 - l)
    cycle_probs_df['011'] = (1 - g) * i * l
    cycle_probs_df['100'] = g * (1 - i) * (1 - l)
    if width > 1:
        cycle_probs_df = cycle_probs_df.rolling(window=width, min_periods=1).mean()
    if 'cyc_code' in cyc_map_df.columns and 'cyc_name' in cyc_map_df.columns:
        cyc_code_to_name = pd.Series(cyc_map_df.cyc_name.values, index=cyc_map_df.cyc_code.astype(str)).to_dict()
        cycle_probs_df.rename(columns=cyc_code_to_name, inplace=True)
    else:
        pass
    return cycle_probs_df

def hp_cycle_map(hp_df: pd.DataFrame, cyc_map_df: pd.DataFrame) -> pd.Series:
    """Maps HP factor directions (subset of factors) to cycle names."""
    if hp_df.empty:
        return pd.Series(dtype=str, name='cycle')
    hp_df_01 = hp_df.replace(-1, 0)
    codes = hp_df_01.astype(str).apply(lambda row: "".join(row.dropna().values), axis=1)
    if 'cyc_code' in cyc_map_df.columns and 'cyc_name' in cyc_map_df.columns:
        cyc_code_to_name_map = pd.Series(cyc_map_df.cyc_name.values, 
                                         index=cyc_map_df.cyc_code.astype(str)).to_dict()
        mapped_cycles = codes.map(cyc_code_to_name_map)
    else:
        mapped_cycles = codes
    mapped_cycles.name = 'cycle'
    return mapped_cycles

def pre_friday(d_date) -> pd.Timestamp:
    """Calculates the previous Friday, or current day if it's a Friday.
    Matches the logic of preFriday in Pkg_RiskBudget.R given specific wday behavior interpretation.
    Input can be datetime.date, datetime.datetime, or pd.Timestamp.
    """
    d = pd.to_datetime(d_date)
    offset_days = (d.weekday() + 3) % 7
    return d - pd.Timedelta(days=offset_days)

def get_pos_chg_dts(dts_input: pd.Series, beg_date: pd.Timestamp, end_date: pd.Timestamp, 
                      freq: str = 'W') -> pd.Series:
    """Generates position change dates (Fridays) based on input dates and frequency.
    Matches R's getPosChgDts logic.
    dts_input: A Series of dates (e.g., from pd.date_range).
    """
    if not isinstance(dts_input, pd.Series):
        dts = pd.Series(dts_input)
    else:
        dts = dts_input.copy()
    dts = pd.to_datetime(dts).sort_values().reset_index(drop=True)
    week_fridays = (dts - pd.to_timedelta(dts.dt.weekday, unit='D')) + pd.Timedelta(days=4)
    dts_df = pd.DataFrame({
        'actualDay': dts,
        'weekFriday': week_fridays
    })
    chgdts_agg = dts_df.groupby('weekFriday')['actualDay'].agg(
        firstDay='first',
        lastDay='last'
    ).reset_index()
    chgdts_filtered = chgdts_agg[
        (chgdts_agg['firstDay'] != chgdts_agg['lastDay']) &
        (chgdts_agg['lastDay'] >= beg_date) &
        (chgdts_agg['lastDay'] <= end_date)
    ].copy()
    if chgdts_filtered.empty:
        return pd.Series(dtype='datetime64[ns]')
    if freq == 'W':
        result_dts = chgdts_filtered['weekFriday']
    else: 
        chgdts_filtered['month'] = chgdts_filtered['weekFriday'].dt.to_period('M')
        result_dts = chgdts_filtered.groupby('month')['weekFriday'].last().reset_index(drop=True)
    return result_dts.sort_values().reset_index(drop=True)

def hist_ud_cycle(raw_factor_df: pd.DataFrame, 
                  idx_map_df: pd.DataFrame, 
                  cyc_map_df: pd.DataFrame, 
                  lambda_val: float, 
                  backtest_beg_str: str = '2012-01') -> pd.DataFrame:
    """Calculates historical UD cycle probabilities based on iterating through dates."""
    loop_dates = raw_factor_df[raw_factor_df.index >= pd.to_datetime(backtest_beg_str)].index
    if loop_dates.empty:
        # Return empty DataFrame with columns based on cyc_map_df cycle names if possible
        if 'cyc_name' in cyc_map_df.columns:
            cols = cyc_map_df['cyc_name'].unique().tolist()
            return pd.DataFrame(columns=cols, dtype=float)
        return pd.DataFrame(dtype=float)

    ud_final_probs_list = []

    for current_date in loop_dates:
        tso_sub = raw_factor_df[raw_factor_df.index <= current_date]
        hp_res = hp_filter_df(tso_sub, lambda_val)
        dr_res = get_direction(hp_res, calc_dt=1, std_tv=0.2)
        dr_res_filled = fill_dr_na_by_idx2(dr_res, idx_map_df)
        dr_res_ud = dr_res_filled.dropna()

        cycle_probs_for_date_row = None
        if not dr_res_ud.empty:
            # R uses tail(dr_factor.ud, 1) - the latest row from available data up to current_date
            latest_dr_for_prob = dr_res_ud.iloc[[-1]] 
            ud_p = ud_cycle_prob(latest_dr_for_prob, idx_map_df)
            if not ud_p.empty:
                ud_res_cycle_probs_matrix = ud_cycle_map(ud_p, cyc_map_df, width=1)
                if not ud_res_cycle_probs_matrix.empty:
                    # This will be a DataFrame of one row, columns are cycle names/codes
                    cycle_probs_for_date_row = ud_res_cycle_probs_matrix.iloc[[0]]
                    # Set the index of this row to current_date before appending
                    cycle_probs_for_date_row.index = [current_date]
        
        if cycle_probs_for_date_row is not None:
            ud_final_probs_list.append(cycle_probs_for_date_row)
        else:
            # Append a row of NaNs if cycle couldn't be determined
            # Ensure columns match those from ud_cycle_map
            if not ud_final_probs_list: # First time, try to get columns
                cols = cyc_map_df['cyc_name'].unique().tolist() if 'cyc_name' in cyc_map_df.columns else [f'cycle_{i}' for i in range(8)]
            elif isinstance(ud_final_probs_list[0], pd.DataFrame): # Get cols from previous valid entry
                cols = ud_final_probs_list[0].columns
            else: # Fallback
                 cols = [f'cycle_{i}' for i in range(8)] # Fallback column names
            nan_row = pd.DataFrame(np.nan, index=[current_date], columns=cols)
            ud_final_probs_list.append(nan_row)

    if not ud_final_probs_list:
        if 'cyc_name' in cyc_map_df.columns:
            cols = cyc_map_df['cyc_name'].unique().tolist()
            return pd.DataFrame(columns=cols, dtype=float)
        return pd.DataFrame(dtype=float)
    
    final_df = pd.concat(ud_final_probs_list)
    return final_df