import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pkg_risk_budget as prb 

# --- File Paths and Constants ---
INPUT_EXCEL_PATH = 'Eg_MacroEcoCycle.XLSX' # Or '~$Eg_MacroEcoCycle.XLSX' if that is the correct one
OUTPUT_EXCEL_PATH = '0_Disp_Result_RPWT.xlsx'

# Sheets in the input Excel
SHEET_EDB = 'EDB'
SHEET_INFO = 'INFO'
SHEET_IDX_MAP = 'IDX_MAP' # Assuming this sheet exists for idx_map
SHEET_CYC_MAP = 'CYC_MAP' # Assuming this sheet exists for cyc_map
SHEET_HP_CYC_MAP = 'HP_CYC_MAP' # Assuming this sheet exists for hp_cyc_map (for HP model)

# HP Filter Lambda (as in R script)
HP_LAMBDA = 14400

# Backtest begin for historical UD cycle
BACKTEST_BEG_HIST_UD = '2012-01'

# Dynamic UD Cycle calculation parameters (from R script)
STD_TV = 0.2
SMP_NUM = 12
CALC_DT_UD = 1 # diff(1) for monthly data
UD_ROLLING_WIDTH = 3 # For udCycleMap's rolling mean

# Static HP Cycle calculation parameters
CALC_DT_HP = 1 # diff(1) for monthly data

# --- Main Script Logic ---
def main():
    # Load data from Excel
    print(f"Loading data from {INPUT_EXCEL_PATH}...")
    try:
        xls = pd.ExcelFile(INPUT_EXCEL_PATH)
        edb_df = pd.read_excel(xls, sheet_name=SHEET_EDB)
        info_df = pd.read_excel(xls, sheet_name=SHEET_INFO)
        idx_map_df = pd.read_excel(xls, sheet_name=SHEET_IDX_MAP)
        cyc_map_df = pd.read_excel(xls, sheet_name=SHEET_CYC_MAP)
        hp_cyc_map_df = pd.read_excel(xls, sheet_name=SHEET_HP_CYC_MAP) # For static HP model cycle mapping
        print("Data loaded successfully.")
    except FileNotFoundError:
        print(f"ERROR: Input Excel file not found at {INPUT_EXCEL_PATH}")
        return
    except Exception as e:
        print(f"ERROR: Could not load data from Excel: {e}")
        return

    # --- Placeholder for further steps ---
    print("info_df head:")
    print(info_df.head())
    print("\nedb_df head:")
    print(edb_df.head())
    print("\nidx_map_df head:")
    print(idx_map_df.head())
    print("\ncyc_map_df head:")
    print(cyc_map_df.head())
    print("\nhp_cyc_map_df head:")
    print(hp_cyc_map_df.head())

    # --- Data Preparation ---
    print("\nPreparing data...")
    # Melt EDB data
    edb_melted_df = edb_df.melt(id_vars='date', var_name='abbr', value_name='val')

    # Join with info_df
    # Ensure date columns are in datetime format before comparison
    info_df['update'] = pd.to_datetime(info_df['update'])
    info_df['beg'] = pd.to_datetime(info_df['beg'])
    edb_melted_df['date'] = pd.to_datetime(edb_melted_df['date'])

    merged_df = pd.merge(edb_melted_df, info_df, on='abbr', how='left')

    # Filter by date ranges specific to each indicator
    # R: filter(date>=beg, date<=update)
    # This requires row-wise comparison. Pandas query can do this if columns are correctly named.
    # merged_df.query('date >= beg and date <= update', inplace=True) # This might be slow if not careful
    # More robustly:
    filtered_df = merged_df[(merged_df['date'] >= merged_df['beg']) & (merged_df['date'] <= merged_df['update'])].copy()
    
    # Select relevant columns (similar to R's select)
    # Python equivalent of R: select(date, abbr, val, name, units, freq, src, type)
    # For now, we mostly need date, abbr, val for raw_tso
    # filtered_df = filtered_df[['date', 'abbr', 'val', 'name', 'units', 'freq', 'src', 'type']]
    # Keep all merged columns for now, select later if needed for specific dataframes

    # Create raw_tso: pivot and make time series
    # R: raw_tso <- edb %>% select(date, abbr, val) %>% na.omit() %>% spread(key=abbr, value=val) ...
    raw_tso_df = filtered_df[['date', 'abbr', 'val']].dropna()
    raw_tso_pivot = raw_tso_df.pivot_table(index='date', columns='abbr', values='val')
    
    # R: .[!duplicated(.[,c('date')]),] - this is already handled by pivot_table if date is index
    # R: arrange(date) - also handled by pivot_table setting date as index
    raw_tso_pivot = raw_tso_pivot.sort_index() # Ensure sorted index just in case

    # At this point, raw_tso_pivot is the equivalent of the R raw_tso before converting to xts
    # It's already a DataFrame with DatetimeIndex, which is the Python equivalent of xts object
    print("raw_tso_pivot created.")
    print(raw_tso_pivot.head())

    # Identify combine_input and noneed_combine indicators (R lines 80-84)
    combine_input_abbrs = info_df.loc[info_df['combined'] == 1, 'abbr'].tolist()
    noneed_combine_abbrs = info_df.loc[info_df['combined'] == 0, 'abbr'].tolist()

    # Filter raw_tso_pivot for these (ensuring columns exist)
    combine_input_cols_exist = [col for col in combine_input_abbrs if col in raw_tso_pivot.columns]
    combine_input_df = raw_tso_pivot[combine_input_cols_exist].copy()

    noneed_combine_cols_exist = [col for col in noneed_combine_abbrs if col in raw_tso_pivot.columns]
    noneed_combine_df = raw_tso_pivot[noneed_combine_cols_exist].copy()

    print("combine_input_df and noneed_combine_df created.")

    # Synthesize CMI and FIN
    # Ensure columns exist before trying to access them
    cmi_series = None
    if 'CMIB' in combine_input_df.columns and 'CMIE' in combine_input_df.columns:
        cmib_beg_date = prb.get_beg(info_df, 'CMIB')
        cmib_update_date = prb.get_update(info_df, 'CMIB')
        cmi_series = prb.combine_cmi(combine_input_df['CMIB'], combine_input_df['CMIE'], 
                                     cmib_beg_date, cmib_update_date)
        cmi_series.name = 'CMI'
        print("CMI series synthesized.")
    else:
        print("Warning: CMIB or CMIE not found in combine_input_df. CMI not synthesized.")

    fin_series = None
    if ('FIN' in combine_input_df.columns and 
        'FINC' in combine_input_df.columns and 
        'FINO' in combine_input_df.columns):
        fin_beg_date = prb.get_beg(info_df, 'FIN')
        fin_series = prb.combine_fin(combine_input_df['FIN'], combine_input_df['FINC'], 
                                     combine_input_df['FINO'], fin_beg_date)
        fin_series.name = 'FIN'
        print("FIN series synthesized.")
    else:
        print("Warning: FIN, FINC or FINO not found in combine_input_df. FIN not synthesized.")

    # Construct Growth, Inflation, Liquid DataFrames
    growth_abbrs = info_df.loc[info_df['type'] == '增长', 'abbr'].tolist()
    inflation_abbrs = info_df.loc[info_df['type'] == '通胀', 'abbr'].tolist()
    liquid_abbrs = info_df.loc[info_df['type'] == '流动性', 'abbr'].tolist()

    # Filter for existing columns in noneed_combine_df
    growth_cols_exist = [col for col in growth_abbrs if col in noneed_combine_df.columns]
    inflation_cols_exist = [col for col in inflation_abbrs if col in noneed_combine_df.columns]
    liquid_cols_exist = [col for col in liquid_abbrs if col in noneed_combine_df.columns]

    growth_df = noneed_combine_df[growth_cols_exist].copy()
    inflation_df = noneed_combine_df[inflation_cols_exist].copy()
    liquid_df = noneed_combine_df[liquid_cols_exist].copy()

    if cmi_series is not None:
        liquid_df = pd.merge(liquid_df, cmi_series.to_frame(), 
                             left_index=True, right_index=True, how='outer')
    if fin_series is not None:
        liquid_df = pd.merge(liquid_df, fin_series.to_frame(), 
                             left_index=True, right_index=True, how='outer')
    print("Growth, Inflation, Liquid DataFrames constructed.")
    print("Liquid_df columns:", liquid_df.columns.tolist())

    # Create raw_factor DataFrame
    all_factors_list = []
    # Use original lists of abbrs to ensure we reference the intended columns for dropna later
    # (before CMI/FIN might get added to liquid_df's column list directly)
    g_cols_for_dropna = [col for col in growth_abbrs if col in noneed_combine_df.columns] 
    i_cols_for_dropna = [col for col in inflation_abbrs if col in noneed_combine_df.columns]
    l_cols_for_dropna = [col for col in liquid_abbrs if col in noneed_combine_df.columns]
    # Add CMI/FIN to l_cols_for_dropna if they were synthesized
    if cmi_series is not None and cmi_series.name not in l_cols_for_dropna: l_cols_for_dropna.append(cmi_series.name)
    if fin_series is not None and fin_series.name not in l_cols_for_dropna: l_cols_for_dropna.append(fin_series.name)

    if not growth_df.empty: all_factors_list.append(growth_df)
    if not inflation_df.empty: all_factors_list.append(inflation_df)
    # liquid_df already contains CMI/FIN if they were synthesized
    if not liquid_df.empty: all_factors_list.append(liquid_df)

    if not all_factors_list:
        print("ERROR: No data for growth, inflation, or liquid factors. Cannot proceed.")
        raw_factor_df = pd.DataFrame() # Ensure it's defined for downstream checks
    else:
        raw_factor_concat = pd.concat(all_factors_list, axis=1)
        # Drop duplicate columns by name, keeping the first occurrence
        raw_factor_merged = raw_factor_concat.loc[:, ~raw_factor_concat.columns.duplicated(keep='first')].copy()

        # Drop rows where all indicators of a specific type are NA
        # Use the *_cols_for_dropna lists which refer to the intended semantic groups.
        actual_g_cols_in_rf = [col for col in g_cols_for_dropna if col in raw_factor_merged.columns]
        actual_i_cols_in_rf = [col for col in i_cols_for_dropna if col in raw_factor_merged.columns]
        actual_l_cols_in_rf = [col for col in l_cols_for_dropna if col in raw_factor_merged.columns]
        
        if actual_g_cols_in_rf:
            raw_factor_merged.dropna(subset=actual_g_cols_in_rf, how='all', inplace=True)
        if actual_i_cols_in_rf:
            raw_factor_merged.dropna(subset=actual_i_cols_in_rf, how='all', inplace=True)
        if actual_l_cols_in_rf:
            raw_factor_merged.dropna(subset=actual_l_cols_in_rf, how='all', inplace=True)

        # Down fill, no zero adjustment (zero_adj=False)
        raw_factor_df = prb.down_fill(raw_factor_merged, zero_adj=False)
        print("raw_factor_df created and filled.")
        print(raw_factor_df.info())

    # --- Dynamic UD Cycle Calculation ---
    print("\nCalculating Dynamic UD Cycle...")
    if raw_factor_df.empty:
        print("ERROR: raw_factor_df is empty. Cannot proceed with dynamic UD cycle calculation.")
        # Handle exit or return appropriate empty structures later for output
        dynamic_cycle = pd.Series(dtype=str, name='dynamic_cycle') # Placeholder
        dynamic_cycle_probs = pd.DataFrame() # Placeholder
    else:
        min_date_rf = raw_factor_df.index.min()
        max_date_rf = raw_factor_df.index.max()

        # beg.dt.dyn <- preFriday(as.Date(min(index(raw_factor)))+31)
        # Add 31 days for next month, then find previous/current Friday
        beg_dt_dyn_calc = pd.to_datetime(min_date_rf) + pd.Timedelta(days=31)
        beg_dt_dyn = prb.pre_friday(beg_dt_dyn_calc)

        # end.dt.dyn <- preFriday(as.Date(max(index(raw_factor))))
        end_dt_dyn = prb.pre_friday(max_date_rf)

        print(f"Dynamic calculation range: {beg_dt_dyn.strftime('%Y-%m-%d')} to {end_dt_dyn.strftime('%Y-%m-%d')}")

        if beg_dt_dyn > end_dt_dyn:
            print("Warning: Dynamic calculation begin date is after end date. No dynamic cycle will be computed.")
            dts_for_loop = pd.Series(dtype='datetime64[ns]')
        else:
            # dts <- seq.Date(from = beg.dt.dyn, to = end.dt.dyn, by = 1)
            dts_seq = pd.date_range(start=beg_dt_dyn, end=end_dt_dyn, freq='D')
            # dts.for.loop <- getPosChgDts(dts, beg.dt.dyn, end.dt.dyn)
            dts_for_loop = prb.get_pos_chg_dts(dts_seq, beg_dt_dyn, end_dt_dyn, freq='W')
        
        print(f"{len(dts_for_loop)} dates for dynamic loop.")
        # Placeholder for loop and results
        dynamic_prob_list = []

        if not dts_for_loop.empty:
            for current_loop_date in dts_for_loop:
                current_loop_date = pd.to_datetime(current_loop_date)
                # print(f"Processing dynamic UD for: {current_loop_date.strftime('%Y-%m-%d')}")

                # Data slicing: raw_factor up to current_loop_date
                tso_sub = raw_factor_df[raw_factor_df.index <= current_loop_date].copy()

                # Zero adjustment based on each indicator's update day (R lines 137-139)
                # Iterate through columns of tso_sub
                for col_name in tso_sub.columns:
                    # Get the specific update date for this indicator (abbr)
                    try:
                        indicator_update_date = prb.get_update(info_df, col_name)
                        # Check if this update_date is in tso_sub's index for this slice
                        if indicator_update_date in tso_sub.index:
                            if tso_sub.loc[indicator_update_date, col_name] == 0:
                                tso_sub.loc[indicator_update_date, col_name] = np.nan
                    except ValueError: # Indicator not in info_df or 'update' missing
                        # print(f"Warning: No update date info for {col_name} during zero adjustment.")
                        pass
                    except Exception as e:
                        # print(f"Warning: Error during zero adj for {col_name} on {indicator_update_date}: {e}")
                        pass        
                
                hp_res_sub = prb.hp_filter_df(tso_sub, lambda_val=HP_LAMBDA)
                # CALC_DT_UD, STD_TV, SMP_NUM are global constants now
                dr_res_sub = prb.get_direction(hp_res_sub, calc_dt=CALC_DT_UD, std_tv=STD_TV, smp_num=SMP_NUM)
                
                # Ensure idx_map_df columns are appropriate (e.g. string for names)
                idx_map_df_prepared = idx_map_df.copy()
                if 'idx_1' in idx_map_df_prepared.columns: 
                    idx_map_df_prepared['idx_1'] = idx_map_df_prepared['idx_1'].astype(str)
                if 'idx_2' in idx_map_df_prepared.columns: 
                    idx_map_df_prepared['idx_2'] = idx_map_df_prepared['idx_2'].astype(str)

                dr_res_ud_sub = prb.fill_dr_na_by_idx2(dr_res_sub, idx_map_df_prepared)
                dr_res_ud_sub = dr_res_ud_sub.dropna() # R: %>% drop_na()

                if dr_res_ud_sub.empty:
                    # print(f"No data for UD prob on {current_loop_date.strftime('%Y-%m-%d')})
                    # Create a row of NaNs with correct columns if dynamic_prob_list is empty
                    # Otherwise, use columns from a previous valid entry or cyc_map_df
                    if not dynamic_prob_list or dynamic_prob_list[-1] is None:
                        prob_cols = cyc_map_df['cyc_name'].unique().tolist() if 'cyc_name' in cyc_map_df.columns else [f'cycle_prob_{i}' for i in range(8)]
                    else:
                        prob_cols = dynamic_prob_list[-1].columns
                    nan_probs_row = pd.DataFrame(np.nan, index=[current_loop_date], columns=prob_cols)
                    dynamic_prob_list.append(nan_probs_row)
                    continue

                # R: ud_prob <- udCycleProb(dr_res_ud, idx_map)
                # The R script seems to use the *entire history* of dr_res_ud_sub available up to current_loop_date
                # for udCycleProb, not just the last row.
                ud_prob_sub = prb.ud_cycle_prob(dr_res_ud_sub, idx_map_df_prepared)

                # R: day_num <- min(nrow(ud_prob),10) # min of available history or 10
                # R: ud_prob <- tail(ud_prob,day_num) %>% apply(2,mean) %>% t() %>% as.data.frame()
                # This means take last 'day_num' rows of ud_prob_sub, average them, for current_loop_date
                day_num = min(len(ud_prob_sub), 10)
                if day_num > 0:
                    ud_prob_averaged = ud_prob_sub.tail(day_num).mean().to_frame().T # Transpose to get 1 row DF
                    ud_prob_averaged.index = [current_loop_date] # Set index to current_loop_date
                    dynamic_prob_list.append(ud_prob_averaged)
                else:
                    # print(f"Not enough history for UD prob average on {current_loop_date.strftime('%Y-%m-%d')}")
                    if not dynamic_prob_list or dynamic_prob_list[-1] is None:
                        prob_cols = cyc_map_df['cyc_name'].unique().tolist() if 'cyc_name' in cyc_map_df.columns else [f'cycle_prob_{i}' for i in range(8)]
                    else:
                        prob_cols = dynamic_prob_list[-1].columns
                    nan_probs_row = pd.DataFrame(np.nan, index=[current_loop_date], columns=prob_cols)
                    dynamic_prob_list.append(nan_probs_row)
        
        # Consolidate dynamic_prob_list
        if dynamic_prob_list:
            dynamic_prob_df_raw = pd.concat(dynamic_prob_list)
            # Ensure cyc_map_df for ud_cycle_map has string codes
            cyc_map_df_prepared = cyc_map_df.copy()
            if 'cyc_code' in cyc_map_df_prepared.columns: 
                cyc_map_df_prepared['cyc_code'] = cyc_map_df_prepared['cyc_code'].astype(str)

            # Downfill the raw probabilities (g,i,l) before mapping to 8 cycles
            # R: dynamic_prob <- downFill(dynamic_prob, F)
            dynamic_prob_df_filled = prb.down_fill(dynamic_prob_df_raw, zero_adj=False)
            dynamic_cycle_probs = prb.ud_cycle_map(dynamic_prob_df_filled, cyc_map_df_prepared, width=UD_ROLLING_WIDTH)
            dynamic_cycle = dynamic_cycle_probs.idxmax(axis=1)
            dynamic_cycle.name = 'dynamic_cycle'
            print("Dynamic UD cycle calculation complete.")
        else:
            print("No dynamic UD probabilities were calculated.")
            dynamic_cycle_probs = pd.DataFrame() # Ensure it's an empty DF
            dynamic_cycle = pd.Series(dtype=str, name='dynamic_cycle')

    # --- Static Macro Cycle Calculation ---
    print("\nCalculating Static Macro Cycles...")
    if raw_factor_df.empty:
        print("ERROR: raw_factor_df is empty. Cannot proceed with static cycle calculation.")
        # Define placeholders for outputs
        ud_cycle_static = pd.Series(dtype=str, name='ud_cycle_static')
        hp_cycle_static = pd.Series(dtype=str, name='hp_cycle_static')
        ud_cycle_hist = pd.Series(dtype=str, name='ud_cycle_hist') # Or DataFrame if it returns probs
        # Also define prob dfs if they are written to excel
        ud_cycle_probs_static = pd.DataFrame()

    else:
        hp_factor_df = prb.hp_filter_df(raw_factor_df, lambda_val=HP_LAMBDA)
        # CALC_DT_HP, STD_TV, SMP_NUM are constants
        dr_factor_df = prb.get_direction(hp_factor_df, calc_dt=CALC_DT_HP, std_tv=STD_TV, smp_num=SMP_NUM)
        print("hp_factor_df and dr_factor_df calculated.")

        # UD Static Cycle Calculation
        # Ensure idx_map_df and cyc_map_df are prepared with string types for names/codes
        idx_map_df_prepared = idx_map_df.copy()
        if 'idx_1' in idx_map_df_prepared.columns: idx_map_df_prepared['idx_1'] = idx_map_df_prepared['idx_1'].astype(str)
        if 'idx_2' in idx_map_df_prepared.columns: idx_map_df_prepared['idx_2'] = idx_map_df_prepared['idx_2'].astype(str)
        
        cyc_map_df_prepared = cyc_map_df.copy()
        if 'cyc_code' in cyc_map_df_prepared.columns: cyc_map_df_prepared['cyc_code'] = cyc_map_df_prepared['cyc_code'].astype(str)
        
        dr_factor_ud_df = prb.fill_dr_na_by_idx2(dr_factor_df, idx_map_df_prepared).dropna()
        
        if not dr_factor_ud_df.empty:
            ud_prob_static_df = prb.ud_cycle_prob(dr_factor_ud_df, idx_map_df_prepared)
            ud_cycle_probs_static = prb.ud_cycle_map(ud_prob_static_df, cyc_map_df_prepared, width=UD_ROLLING_WIDTH)
            
            if not ud_cycle_probs_static.empty:
                # R: last(...) %>% apply(1,which.max) %>% colnames(.)[.] -> name of max prob for last date
                last_date_probs = ud_cycle_probs_static.iloc[[-1]] # Get the last row as a DataFrame
                ud_cycle_static_name = last_date_probs.idxmax(axis=1).iloc[0] # Get column name of max val in that row
                ud_cycle_static_series = pd.Series([ud_cycle_static_name], index=last_date_probs.index)
                ud_cycle_static_series.name = 'ud_cycle_static' 
                ud_cycle_static = ud_cycle_static_series # Assign to the variable used later
                print(f"UD Static Cycle (last date): {ud_cycle_static_name} on {last_date_probs.index[0].strftime('%Y-%m-%d')}")
            else:
                print("Warning: ud_cycle_probs_static is empty.")
                ud_cycle_static = pd.Series(dtype=str, name='ud_cycle_static') # empty series
                ud_cycle_probs_static = pd.DataFrame() # ensure it is empty DF
        else:
            print("Warning: dr_factor_ud_df is empty after fill/dropna. Cannot calculate UD static cycle.")
            ud_cycle_static = pd.Series(dtype=str, name='ud_cycle_static')
            ud_cycle_probs_static = pd.DataFrame()

        # HP Static Cycle Calculation
        # hp_model_idx_name <- info$abbr[info$usehp==1]
        hp_model_abbrs = info_df.loc[info_df['usehp'] == 1, 'abbr'].tolist()
        
        # Filter for columns existing in dr_factor_df
        hp_model_cols_exist = [col for col in hp_model_abbrs if col in dr_factor_df.columns]
        hp_model_idx_df = dr_factor_df[hp_model_cols_exist].dropna()

        if not hp_model_idx_df.empty:
            # hp_cyc_map_df was loaded earlier
            # Ensure hp_cyc_map_df has string codes
            hp_cyc_map_df_prepared = hp_cyc_map_df.copy()
            if 'cyc_code' in hp_cyc_map_df_prepared.columns: 
                hp_cyc_map_df_prepared['cyc_code'] = hp_cyc_map_df_prepared['cyc_code'].astype(str)

            hp_cycle_static = prb.hp_cycle_map(hp_model_idx_df, hp_cyc_map_df_prepared)
            print("HP Static Cycle calculated.")
        else:
            print("Warning: hp_model_idx_df is empty. Cannot calculate HP static cycle.")
            hp_cycle_static = pd.Series(dtype=str, name='hp_cycle_static') # empty series
        
        # Historical UD Cycle (Returns DataFrame of probabilities)
        # BACKTEST_BEG_HIST_UD, HP_LAMBDA are constants
        # idx_map_df_prepared, cyc_map_df_prepared are already set up
        ud_cycle_hist_probs_df = prb.hist_ud_cycle(raw_factor_df, 
                                                   idx_map_df_prepared, 
                                                   cyc_map_df_prepared, 
                                                   lambda_val=HP_LAMBDA, 
                                                   backtest_beg_str=BACKTEST_BEG_HIST_UD)
        
        if not ud_cycle_hist_probs_df.empty:
            # The main cycle series derived from these probabilities for potential other uses
            ud_cycle_hist = ud_cycle_hist_probs_df.idxmax(axis=1)
            ud_cycle_hist.name = 'ud_cycle_hist'
            print("Historical UD Cycle (ud_cycle_hist_probs_df and ud_cycle_hist name series) calculated.")
        else:
            print("Warning: ud_cycle_hist_probs_df is empty.")
            ud_cycle_hist = pd.Series(dtype=str, name='ud_cycle_hist') # empty series
            # ud_cycle_hist_probs_df is already an empty df from the function in this case

if __name__ == '__main__':
    main() 