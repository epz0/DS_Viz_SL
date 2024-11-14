''' The stats_run module runs the statistics to compare the groups across the different metrics.
'''

from pathlib import Path

from stats.stats_main import *
from stats.stats_mt1_fluency import *
from stats.stats_mt2_variety import *
from stats.stats_mt3_mt4_novelty import *

#* --- initial definitions ------
my_dir = Path(r'C:/DSX_Viz/data')                                                   # path to the data file
filenm = 'MASKED_DATA_analysis_v1.xlsx'                                             # name of the data file
sheetnm = 'ExpData-100R-Expanded'                                                   # sheet where the data (analysis) is
#* ------------------------------

#* --- create folder structure ---
Path(f'{my_dir.parent}/export/stats').mkdir(parents=True,exist_ok=True)             # folder export/stats
#* ------------------------------

#* ---- module variables ----
GA = 'VZ'
GB = 'XX'
GC = 'NI'
PRE = 'KYY'
POST = 'ZSB'
FS = 'FS'
NOV = ['Global','Local']
#* --------------------------

#! ---------------------------------------------------------------
#! --------------------- TRADITIONAL METRICS ---------------------
#! ---------------------------------------------------------------

#! ---------------- FLUENCY MT1 ----------------
# get df_fluency
df_fluency = get_fluency_df(my_dir, filenm)

# run fluency comparison across all groups
# create list of data for those comparisons
# following format: [y, z, x, sht]

#* A. Comparison among all groups
print('Calculating fluency ancova across all groups...')

lst_fluency_all_gp =    [[f'n_{POST}', 'GroupID', f'n_{PRE}', 'All_Pre_v_Post'],
                            [f'n_{FS}', 'GroupID', f'n_{PRE}', 'All_Pre_v_FS']]

for i in range(len(lst_fluency_all_gp)):
    ancova_stat(my_dir, df_fluency, lst_fluency_all_gp[i][0], lst_fluency_all_gp[i][1], lst_fluency_all_gp[i][2], 'fluency_MT1', lst_fluency_all_gp[i][3])

print('Calculating fluency ancova across all groups - done!')

#* B. Comparison combining two groups at a time
# run fluency comparison combining groups
# create list of data for those comparisons
# following format: [df, y, z, x, sht]

print('Calculating fluency ancova combining groups...')
df_A = df_fluency.copy()
df_A['GroupID'] = df_A['GroupID'].replace([GB,GC], f'{GB}-{GC}')

df_B = df_fluency.copy()
df_B['GroupID'] = df_B['GroupID'].replace([GA,GC], f'{GA}-{GC}')

df_C = df_fluency.copy()
df_C['GroupID'] = df_C['GroupID'].replace([GA,GB], f'{GA}-{GB}')

lst_fluency_all_gp_comb = [[df_A, f'n_{POST}', 'GroupID', f'n_{PRE}', f'{GA}_v_{GB}-{GC}_Pre_v_Post'],
                            [df_A, f'n_{FS}', 'GroupID', f'n_{PRE}', f'{GA}_v_{GB}-{GC}_Pre_v_FS'],
                            [df_B, f'n_{POST}', 'GroupID', f'n_{PRE}', f'{GB}_v_{GA}-{GC}_Pre_v_Post'],
                            [df_B, f'n_{FS}', 'GroupID', f'n_{PRE}', f'{GB}_v_{GA}-{GC}_Pre_v_FS'],
                            [df_C, f'n_{POST}', 'GroupID', f'n_{PRE}', f'{GC}_v_{GA}-{GB}_Pre_v_Post'],
                            [df_C, f'n_{FS}', 'GroupID', f'n_{PRE}', f'{GC}_v_{GA}-{GB}_Pre_v_FS']]

for i in range(len(lst_fluency_all_gp_comb)):
    ancova_stat(my_dir, lst_fluency_all_gp_comb[i][0],
                        lst_fluency_all_gp_comb[i][1],
                        lst_fluency_all_gp_comb[i][2],
                        lst_fluency_all_gp_comb[i][3],
                        'fluency_MT1',
                        lst_fluency_all_gp_comb[i][4])

print('Calculating fluency ancova combining groups - done!')

#! ---------------------------------------------


#! ---------------- VARIETY MT2 ----------------
# get df_var
df_var = get_variety_df(my_dir, filenm)

# get df with var metric for each participant
df_var_metric = calc_variety(my_dir, df_var, PRE, POST, FS)
print(df_var_metric.columns)

#* A. Comparison among all groups
print('Calculating variety ancova across all groups...')

lst_variety_all_gp = [[f'M3_{POST}', 'GroupID', f'M3_{PRE}', 'All_Pre_v_Post'],
                            [f'M3_{FS}', 'GroupID', f'M3_{PRE}', 'All_Pre_v_FS']]

for i in range(len(lst_variety_all_gp)):
    ancova_stat(my_dir, df_var_metric, lst_variety_all_gp[i][0], lst_variety_all_gp[i][1], lst_variety_all_gp[i][2], 'variety_MT2', lst_variety_all_gp[i][3])

print('Calculating variety ancova across all groups - done!')

#* B. Comparison combining two groups at a time
# run variety comparison combining groups
# create list of data for those comparisons
# following format: [df, y, z, x, sht]

print('Calculating fluency ancova combining groups...')
df_A = df_var_metric.copy()
df_A['GroupID'] = df_A['GroupID'].replace([GB,GC], f'{GB}-{GC}')

df_B = df_var_metric.copy()
df_B['GroupID'] = df_B['GroupID'].replace([GA,GC], f'{GA}-{GC}')

df_C = df_var_metric.copy()
df_C['GroupID'] = df_C['GroupID'].replace([GA,GB], f'{GA}-{GB}')

lst_variety_all_gp_comb = [[df_A, f'M3_{POST}', 'GroupID', f'M3_{PRE}', f'{GA}_v_{GB}-{GC}_Pre_v_Post'],
                            [df_A, f'M3_{FS}', 'GroupID', f'M3_{PRE}', f'{GA}_v_{GB}-{GC}_Pre_v_FS'],
                            [df_B, f'M3_{POST}', 'GroupID', f'M3_{PRE}', f'{GB}_v_{GA}-{GC}_Pre_v_Post'],
                            [df_B, f'M3_{FS}', 'GroupID', f'M3_{PRE}', f'{GB}_v_{GA}-{GC}_Pre_v_FS'],
                            [df_C, f'M3_{POST}', 'GroupID', f'M3_{PRE}', f'{GC}_v_{GA}-{GB}_Pre_v_Post'],
                            [df_C, f'M3_{FS}', 'GroupID', f'M3_{PRE}', f'{GC}_v_{GA}-{GB}_Pre_v_FS']]

for i in range(len(lst_variety_all_gp_comb)):
    ancova_stat(my_dir, lst_variety_all_gp_comb[i][0],
                        lst_variety_all_gp_comb[i][1],
                        lst_variety_all_gp_comb[i][2],
                        lst_variety_all_gp_comb[i][3],
                        'variety_MT2',
                        lst_variety_all_gp_comb[i][4])

print('Calculating variety ancova combining groups - done!')
#! -------------------------------------------------


#! ---------------- NOVELTY MT3-MT4 ----------------
# get df for novelty (global/local)
df_novel = get_novelty_df(my_dir, filenm)
#print(df_novel.columns)
# run novelty_global comparison across all groups

#* A. Comparison among all groups
print('Calculating novelty (global/local) ancova across all groups...')

lst_novel_all_gp = []

for n in range(len(NOV)):
    lst_novel_all_gp.append([f'Avg_M1_{POST}_{NOV[n]}', 'GroupID', f'Avg_M1_{PRE}_{NOV[n]}', f'All_Pre_v_Post_{NOV[n]}'])

    for i in range(len(lst_novel_all_gp)):
        ancova_stat(my_dir, df_novel, lst_novel_all_gp[i][0], lst_novel_all_gp[i][1], lst_novel_all_gp[i][2], 'novelty_MT3-MT4', lst_novel_all_gp[i][3])

print('Calculating novelty (global) ancova across all groups - done!')

#* B. Comparison combining two groups at a time
# run novelty comparison combining groups
# create list of data for those comparisons
# following format: [df, y, z, x, sht]

print('Calculating novelty (global/local) ancova combining groups...')
df_A = df_novel.copy()
df_A['GroupID'] = df_A['GroupID'].replace([GB,GC], f'{GB}-{GC}')

df_B = df_novel.copy()
df_B['GroupID'] = df_B['GroupID'].replace([GA,GC], f'{GA}-{GC}')

df_C = df_novel.copy()
df_C['GroupID'] = df_C['GroupID'].replace([GA,GB], f'{GA}-{GB}')

lst_grp_comb = [[df_A, f'{GA}v{GB}-{GC}'],
                [df_B, f'{GB}v{GA}-{GC}'],
                [df_C, f'{GC}v{GA}-{GB}']]

lst_novel_all_gp_comb = []

for n in range(len(NOV)):
    for gp in range(len(lst_grp_comb)):
        lst_novel_all_gp_comb.append([lst_grp_comb[gp][0], f'Avg_M1_{POST}_{NOV[n]}', 'GroupID', f'Avg_M1_{PRE}_{NOV[n]}', f'{lst_grp_comb[gp][1]}_PrePost{NOV[n]}'])

for i in range(len(lst_novel_all_gp_comb)):
    ancova_stat(my_dir, lst_novel_all_gp_comb[i][0],
                        lst_novel_all_gp_comb[i][1],
                        lst_novel_all_gp_comb[i][2],
                        lst_novel_all_gp_comb[i][3],
                        'novelty_MT3-MT4',
                        lst_novel_all_gp_comb[i][4])

print('Calculating novelty (global/local) ancova combining groups - done!')

#! ---------------------------------------------------------------

