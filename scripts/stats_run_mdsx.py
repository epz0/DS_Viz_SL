"""The stats_run_mdsx module supports the calculation of the mdsx metrics (total, max, avg) distances and DSarea.
"""

from pathlib import Path

from stats.stats_main import *

from utils.utils import *
from design_space.read_data import *
from design_space.dist_matrix import *
from design_space.dim_reduction import *
from design_space.design_space import *
from design_space.dspace_metrics import *
from design_space.dspace_dist_metrics import *
from design_space.dspace_viz_arrows import *

#* --- initial definitions ------
my_dir = Path(r'C:/DSX_Viz/data')                                                   # path to the data file
filenm = 'MASKED_DATA_analysis_v1.xlsx'                                             # name of the data file
sheetnm = 'ExpData-100R-Expanded'                                                   # sheet where the data (analysis) is
#* ------------------------------

#* --- create folder structure ---
Path(f'{my_dir.parent}/export/stats').mkdir(parents=True,exist_ok=True)             # folder export/stats
#* ------------------------------

#* ---- module variables ----
MODE_METRICS = 'all'

#* masked
GA = 'VZ'
GB = 'XX'
GC = 'NI'
PRE = 'KYY'
POST = 'ZSB'
FS = 'FS'

#* unmasked
GA_U = 'UF'
GB_U = 'CG'
GC_U = 'SF'
PRE_U = 'PRE'
POST_U = 'PST'
FS_U = 'FS'
MDSX_D = ['total', 'max', 'avg']
#* --------------------------

#! ----------------------------------------------------------------
#! --------------- DESIGN SPACE EXPLORATION METRICS ---------------
#! ----------------------------------------------------------------

#! ---------- MDSX-1/2/3 TOTAL/MAX/AVG DISTANCE ----------
#* procedure:
#       1.  get df with solutions' analysis         (read_analysis)
#       2a. unmask the data                         (unmask_data)
#       2b. calculate distance matrix               (calc_distmatrix)
#*      3.  calculate metrics with HiDim distmatrix (dist_metrics_fs, pre, post)
#       3a. run aconva                              (ancova_stat)
#       4.  create embedding                        (create_embedding)
#       5.  calculate distance matrix from embed    (create_dmatrix_from_embed)
#*      6.  calculate metrics with Embed distmatrix (dist_metrics_fs, pre, post)
#       6a. run ancova                              (ancova_stat)


#* 1. reads Excel file with solutions' analysis
df_base, df_colors, labels = read_analysis(my_dir, filenm, sheetnm)

#* 2a. unmask the data
df_unmsk = unmask_data(my_dir, 'MASKING_KEYS', df_base)
#print(df_unmsk)

#* 2b. calculates distance matrix
n_distmatrix = calc_distmatrix(df_base, my_dir, filenm)

#* 3. calculate the distance metrics for the full session/pre/post
df_dist_metrics, pt_ids = dist_metrics_fs(df_unmsk, n_distmatrix)
#print(df_dist_metrics)

df_dist_metrics = dist_metrics_pre(df_unmsk, df_dist_metrics, pt_ids, n_distmatrix)
#print(df_dist_metrics)

df_dist_metrics = dist_metrics_post(df_unmsk, df_dist_metrics, pt_ids, n_distmatrix)
#print(df_dist_metrics.columns)

# 3a. run ancova
#* A. Comparison among all groups
print('Calculating distance [hidim] (total/max/avg) ancova across all groups...')

lst_mdsx_d_all_gp = []
lst_pst_fs = [f'{POST_U}', f'{FS_U}']

for m in range(len(lst_pst_fs)):
    for n in range(len(MDSX_D)):
        lst_mdsx_d_all_gp.append([f'{MDSX_D[n]}dist_{lst_pst_fs[m]}', 'OriginalID_Group', f'{MDSX_D[n]}dist_{PRE_U}', f'All_Pre_v_{lst_pst_fs[m]}_{MDSX_D[n]}'])
#print(lst_mdsx_d_all_gp)

for i in range(len(lst_mdsx_d_all_gp)):
    ancova_stat(my_dir, df_dist_metrics, lst_mdsx_d_all_gp[i][0], lst_mdsx_d_all_gp[i][1], lst_mdsx_d_all_gp[i][2], 'distance_HIDIM_MDSX1-2-3', lst_mdsx_d_all_gp[i][3])

#* B. Comparison combining intervention groups
# run mdsx 1, 2, 3 comparison combining UF+SF groups
# single comparison CG v UF+SF

df_comb = df_dist_metrics.copy()
df_comb['OriginalID_Group'] = df_comb['OriginalID_Group'].replace([GA,GC], f'{GA}-{GC}')
#print(df_comb)

lst_mdsx_d_comb_gp = []
lst_pst_fs = [f'{POST_U}', f'{FS_U}']

for m in range(len(lst_pst_fs)):
    for n in range(len(MDSX_D)):
        lst_mdsx_d_comb_gp.append([f'{MDSX_D[n]}dist_{lst_pst_fs[m]}', 'OriginalID_Group', f'{MDSX_D[n]}dist_{PRE_U}', f'Comb_Pre_v_{lst_pst_fs[m]}_{MDSX_D[n]}'])
#print(lst_mdsx_d_comb_gp)

for i in range(len(lst_mdsx_d_comb_gp)):
    ancova_stat(my_dir, df_comb, lst_mdsx_d_comb_gp[i][0], lst_mdsx_d_comb_gp[i][1], lst_mdsx_d_comb_gp[i][2], 'distance_HIDIM_MDSX1-2-3', lst_mdsx_d_comb_gp[i][3])

print('Calculating distance [hidim] (total/max/avg) ancova across all groups - done!')

print('Calculating distance [embed] (total/max/avg) ancova combined groups...')

# 4. generate the embedding of the distance matrix
embedding, graph = create_embedding(my_dir, n_distmatrix)

# 5. create normalised distance matrix from embeddings points embedding (for validation flow)
n_dmatrix_umap = create_dmatrix_from_embed(my_dir, embedding, norm=False)

#* 6. calculate the distance metrics for the full session/pre/post
df_dist_metric_emb, pt_ids = dist_metrics_fs(df_unmsk, n_dmatrix_umap)
#print(df_dist_metric_emb)

df_dist_metric_emb = dist_metrics_pre(df_unmsk, df_dist_metric_emb, pt_ids, n_dmatrix_umap)
#print(df_dist_metric_emb)

df_dist_metric_emb = dist_metrics_post(df_unmsk, df_dist_metric_emb, pt_ids, n_dmatrix_umap)
#print(df_dist_metric_emb.columns)

#* export to excel
dir_exp = Path(f'{my_dir.parent}/export/stats')

with pd.ExcelWriter(f'{dir_exp}/DistanceMetrics.xlsx') as writer:                                             # create file
            df_dist_metric_emb.to_excel(writer, sheet_name='Dist_Metrics_Embed', index=False)
            df_dist_metrics.to_excel(writer, sheet_name='Dist_Metrics_HiDim', index=False)


#* A. Comparison among all groups

lst_mdsx_d_all_gp_emb = []
lst_pst_fs = [f'{POST_U}', f'{FS_U}']

for m in range(len(lst_pst_fs)):
    for n in range(len(MDSX_D)):
        lst_mdsx_d_all_gp_emb.append([f'{MDSX_D[n]}dist_{lst_pst_fs[m]}', 'OriginalID_Group', f'{MDSX_D[n]}dist_{PRE_U}', f'All_Pre_v_{lst_pst_fs[m]}_{MDSX_D[n]}'])
#print(lst_mdsx_d_all_gp_emb)

for i in range(len(lst_mdsx_d_all_gp_emb)):
    ancova_stat(my_dir, df_dist_metrics, lst_mdsx_d_all_gp_emb[i][0], lst_mdsx_d_all_gp_emb[i][1], lst_mdsx_d_all_gp_emb[i][2], 'distance_EMBED_MDSX1-2-3', lst_mdsx_d_all_gp_emb[i][3])

#* B. Comparison combining intervention groups
# run mdsx 1, 2, 3 comparison combining UF+SF groups
# single comparison CG v UF+SF

df_comb_emb = df_dist_metrics.copy()
df_comb_emb['OriginalID_Group'] = df_comb_emb['OriginalID_Group'].replace([GA,GC], f'{GA}-{GC}')
#print(df_comb_emb)

lst_mdsx_d_comb_gp_emb = []
lst_pst_fs = [f'{POST_U}', f'{FS_U}']

for m in range(len(lst_pst_fs)):
    for n in range(len(MDSX_D)):
        lst_mdsx_d_comb_gp_emb.append([f'{MDSX_D[n]}dist_{lst_pst_fs[m]}', 'OriginalID_Group', f'{MDSX_D[n]}dist_{PRE_U}', f'Comb_Pre_v_{lst_pst_fs[m]}_{MDSX_D[n]}'])
#print(lst_mdsx_d_comb_gp_emb)

for i in range(len(lst_mdsx_d_comb_gp_emb)):
    ancova_stat(my_dir, df_comb_emb, lst_mdsx_d_comb_gp_emb[i][0], lst_mdsx_d_comb_gp_emb[i][1], lst_mdsx_d_comb_gp_emb[i][2], 'distance_EMBED_MDSX1-2-3', lst_mdsx_d_comb_gp_emb[i][3])

print('Calculating distance [embed] (total/max/avg) ancova combined groups - done!')

#! ---------------------------------------------
'''
#! ---------- MDSX-4 Area ----------
#* procedure:
#       1. get df with solutions' analysis  [done]      (read_analysis)
#       2. unmask the data                  [done]      (unmask_data)
#       3. calculate distance matrix        [done]      (calc_distmatrix)
#       4. create embedding                 [done]      (create_embedding)
#       5. create convex hull                           (create_cvxh)
#*      6. get area alternative metrics                 (area_alternative_metrics)
#       7. run ancova                                   (ancova_stat)

print('Calculating area (MDSX-4) ancova across all groups...')

#* 5. create and plot convex hull
DS_area, pt_cvxh, df_metrics_fs, df_metrics_pre, df_metrics_post, df_ds_verts = create_cvxh(my_dir, df_base, embedding, df_colors, save_plot=False)

#* 6. get DS coverage alternative metrics (FS-Pre, Overlap, RAE + traditional metrics)
# df_DS_alt_metrics is masked
df_DS_alt_metrics  = area_alternative_metrics(df_base, pt_cvxh, DS_area, df_ds_verts, save_plot=False, save_metrics=True, dir_data=my_dir)
#print(df_DS_alt_metrics.columns)

#* A.   Comparison among all groups
#* A.1  Area Pre vs. Area Post
ancova_stat(my_dir, df_DS_alt_metrics, f'Area{POST}', 'GroupID', f'Area{PRE}', 'area_MDSX4', f'All_Area_Pre_v_Post')

#* A.2  Area Pre vs. Area Post
ancova_stat(my_dir, df_DS_alt_metrics, 'ExtraExp', 'GroupID', f'Area{PRE}', 'area_MDSX4', f'All_Pre_v_ExtraExp')

#* A.3  Area Pre (%) vs. RAE (%)
ancova_stat(my_dir, df_DS_alt_metrics, 'RAE_perc', 'GroupID', f'Area{PRE}_perc', 'area_MDSX4', f'All_PreP_v_RAEP')

print('Calculating area (MDSX-4) ancova across all groups - done!')

print('Calculating area (MDSX-4) combining groups...')

#* B. Comparison combining two groups at a time
# run MDSX4 comparison combining groups
# create list of data for those comparisons
# following format: [df, y, z, x, sht]

lst_grp_comb = []

df_A = df_DS_alt_metrics.copy()
df_A['GroupID'] = df_A['GroupID'].replace([GB,GC], f'{GB}-{GC}')

df_B = df_DS_alt_metrics.copy()
df_B['GroupID'] = df_B['GroupID'].replace([GA,GC], f'{GA}-{GC}')

df_C = df_DS_alt_metrics.copy()
df_C['GroupID'] = df_C['GroupID'].replace([GA,GB], f'{GA}-{GB}')

lst_grp_comb = [[df_A, f'{GA}v{GB}-{GC}'],
                [df_B, f'{GB}v{GA}-{GC}'],
                [df_C, f'{GC}v{GA}-{GB}']]

for g in range(len(lst_grp_comb)):
    #* A.1  Area Pre vs. Area Post
    ancova_stat(my_dir, lst_grp_comb[g][0], f'Area{POST}', 'GroupID', f'Area{PRE}', 'area_MDSX4', f'C_{lst_grp_comb[g][1]}_Area_PrevPost')

    #* A.2  Area Pre vs. Area Post
    ancova_stat(my_dir, lst_grp_comb[g][0], 'ExtraExp', 'GroupID', f'Area{PRE}', 'area_MDSX4', f'C_{lst_grp_comb[g][1]}_PrevExExp')

    #* A.3  Area Pre (%) vs. RAE (%)
    ancova_stat(my_dir, lst_grp_comb[g][0], 'RAE_perc', 'GroupID', f'Area{PRE}_perc', 'area_MDSX4', f'C_{lst_grp_comb[g][1]}_PreP_v_RAEP')

print('Calculating area (MDSX-4) combining groups - done!')
#! ---------------------------------------------


'''

