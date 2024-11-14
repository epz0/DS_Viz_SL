#%%
from design_space.read_data import *
from design_space.dist_matrix import *
from design_space.dim_reduction import *
from design_space.design_space import *
from design_space.dspace_metrics import *
from design_space.dspace_dist_metrics import *
from design_space.dspace_viz_arrows import *
from utils.utils import *
from design_space.dspace_cluster import *


from pathlib import Path
#%%
'''

#* --- initial definitions ------
my_dir = Path(r'C:/Py/DS_Viz_Exp/data')                                                   # path to the data file
filenm = 'MASKED_DATA_analysis_v1.xlsx'                                             # name of the data file
sheetnm = 'ExpData-100R-Expanded'                                                   # sheet where the data (analysis) is
#* ------------------------------

#* reads Excel file with solutions' analysis
df_base, df_colors, labels = read_analysis(my_dir, filenm, sheetnm)

#* calculates distance matrix
n_distmatrix = calc_distmatrix(df_base, my_dir, filenm)

#* generate the embedding of the distance matrix
embedding, graph = create_embedding(my_dir, n_distmatrix)

#* plot the embedding
plot_embedding(my_dir, embedding, df_base)

#* create and plot convex hull
DS_area, pt_cvxh, df_metrics_fs, df_metrics_pre, df_metrics_post, df_ds_verts = create_cvxh(my_dir, df_base, embedding, df_colors, save_plot=False)

# set mode for metrics
mode_metrics = 'all'

#* export DS metrics to excel
export_cvxh_metrics(my_dir, 'DS_Metrics_17-10', df_metrics_fs, mode=mode_metrics, df_ch_pre_metrics=df_metrics_pre, df_ch_post_metrics=df_metrics_post)

#* get DS coverage metrics per participant
df_DS_coverage = area_summary(df_base, DS_area, df_metrics_fs, mode=mode_metrics, df_ch_pre_metrics=df_metrics_pre, df_ch_post_metrics=df_metrics_post)

#* get DS coverage alternative metrics (FS-Pre, Overlap, RAE + traditional metrics)
#! change save_plot to True in the first run
df_DS_alt_metrics  = area_alternative_metrics(df_base, pt_cvxh, DS_area, df_ds_verts, save_plot=False, save_metrics=True, dir_data=my_dir)

#* create normalised distance matrix from embeddings points embedding (for validation flow)
n_dmatrix_umap = create_dmatrix_from_embed(my_dir, embedding)
#print(n_dmatrix_umap)

#* unmask the data
df_unmsk = unmask_data(my_dir, 'MASKING_KEYS', df_base)
#print(df_unmsk)

#* calculate the distance metrics for the full session
df_dist_metrics, pt_ids = dist_metrics_fs(df_unmsk, n_distmatrix)
#print(df_dist_metrics)

#* calculate the distance metrics for the pre intervention part of the session
df_dist_metrics = dist_metrics_pre(df_unmsk, df_dist_metrics, pt_ids, n_distmatrix)
#print(df_dist_metrics)

#* calculate the distance metrics for the pre intervention part of the session
df_dist_metrics = dist_metrics_post(df_unmsk, df_dist_metrics, pt_ids, n_distmatrix)
#print(df_dist_metrics)

#* plot design space exploration (single image per participant)
plot_ds_exploration_arrows( my_dir,
                            df_unmsk,
                            embedding,
                            df_dist_metrics,
                            sol_c=df_unmsk['colors'],
                            pt_unique=pt_ids,
                            df_colors=df_colors)

#* plot incremental design space exploration (single image per participant)
plot_ds_exploration_incremental_arrows( my_dir,
                                        df_unmsk,
                                        embedding,
                                        df_dist_metrics,
                                        sol_c=df_unmsk['colors'],
                                        pt_unique=pt_ids,
                                        df_colors=df_colors)
'''
#! DOWNN
#%%

#* --- initial definitions ------
my_dir = Path(r'C:/Py/DS_Viz_Exp/data')                                                 # path to the data file
filenm = 'MASKED_DATA_analysis_v1.xlsx'                                                 # name of the data file
sheetnm = 'ExpData-100R-Expanded'                                                       # sheet where the data (analysis) is
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
save_dir = 'C:/Py/DSX_Vis/SaveFiles'
#* ------------------------------

#%%
#! get & process data

#* reads Excel file with solutions' analysis
df_base, df_colors, labels = read_analysis(my_dir, filenm, sheetname=sheetnm)

#* calculates distance matrix
n_distmatrix = calc_distmatrix(df_base, my_dir, filenm)

#* generate the embedding of the distance matrix
embedding, graph = create_embedding(my_dir, n_distmatrix, embed_name='nep', Wg='W2', NN=90, MD=0.25, densm=2)

#* unmask data
df_base, df_colors = unmask_data(my_dir, 'MASKING_KEYS', df_base, df_colors)

#* prepare main df
df_base['x_emb'] = embedding[:, 0]
df_base['y_emb'] = embedding[:, 1]
ids_m = df_base['ParticipantID'].unique()

df_col = df_colors[['P','HEX-Win']].copy()
df_base = df_base.merge(df_col, left_on='ParticipantID', right_on='P').copy()

#%%
#! cluster metrics
df_base = get_clusters(df_base, graph)

symb = list(range(1,16))
symb_ls = ['.', 'o', 'v', '<', '>',
            '1', '8',  's', 'p',
            '*','h', 'd', 'D',
            '+','2']

df_symb = pd.DataFrame({'cluster_id': symb, 'clust_symb':symb_ls})
df_base = df_base.merge(df_symb, how='left', on='cluster_id')

#%%

#* calculate the distance metrics for the full session
df_dist_metrics, pt_ids = dist_metrics_fs(df_base, n_distmatrix)
#print(df_dist_metrics)

#* calculate the distance metrics for the pre intervention part of the session
df_dist_metrics = dist_metrics_pre(df_base, df_dist_metrics, pt_ids, n_distmatrix)
#print(df_dist_metrics)

#* calculate the distance metrics for the pre intervention part of the session
df_dist_metrics = dist_metrics_post(df_base, df_dist_metrics, pt_ids, n_distmatrix)
#print(df_dist_metrics)
#%%
#* plot design space exploration (single image per participant)
plot_ds_exploration_incremental_arrows( my_dir,
                            df_base,
                            embedding,
                            df_dist_metrics,
                            sol_c=df_base['HEX-Win'],
                            pt_unique=pt_ids,
                            df_colors=df_colors,
                            markers_list=df_base['clust_symb'])
# %%
