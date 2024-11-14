'''The viz_run module allows plotting of density plots for different settings.
'''

from design_space.dspace_viz_density import *

from pathlib import Path

from design_space.read_data import read_analysis
from design_space.dist_matrix import *
from design_space.dim_reduction import *
from design_space.dspace_dist_metrics import *
from design_space.dspace_metric_novelty import *

#* --- initial definitions ------
my_dir = Path(r'C:/Py/DS_Viz_Exp/data')                                                   # path to the data file
filenm = 'MASKED_DATA_analysis_v1.xlsx'                                             # name of the data file
sheetnm = 'ExpData-100R-Expanded'                                                   # sheet where the data (analysis) is
#* ------------------------------

#* --- create folder structure ---
Path(f'{my_dir.parent}/experimental/viz').mkdir(parents=True,exist_ok=True)             # folder export/stats
#* ------------------------------

dir_exviz = Path(f'{my_dir.parent}'+r'/experimental/viz')

#* reads Excel file with solutions' analysis
df_base, df_colors, labels = read_analysis(my_dir, filenm, sheetname=sheetnm)

#* calculates distance matrix
n_distmatrix = calc_distmatrix(df_base, my_dir, filenm)

#* generate the embedding of the distance matrix
embedding, graph = create_embedding(my_dir, n_distmatrix)

#! 1 prep
df_kde, lim_x, lim_y = prep_density(df_base, embedding)

#! 2 setup ax
axibase = multiplot_stp(lim_x, lim_y)

'''
#! vars
nr=5
nc=6
prm = 'ParticipantID'
lv = 100
cm = 'inferno'
ft = f'Density Plot for {prm}'
fl = f'DensR_{prm}_{lv}_{cm}.png'

#! 3 multiplot kde
multiplot_kde_cvh(  my_dir,
                    df_kde,
                    df_colors,
                    lim_x,
                    lim_y,
                    nrows=nr,
                    ncols=nc,
                    axbase=axibase,
                    param=prm,
                    lvls=lv,
                    cmapn=cm,
                    kde=True,
                    cvxh=False,
                    precvh=False,
                    postcvh=False,
                    allscatter=False,
                    figtitle=ft,
                    fn=fl
                )


#! DISCS

#* get dist matrix NOT normalised
dmatx = create_dmatrix_from_embed(my_dir, embedding, norm=False)

# unmask the data
df_unmsk = unmask_data(my_dir, 'MASKING_KEYS', df_base)

#* unmasked list of participants ids
pt_ids = df_unmsk['OriginalID_PT'].unique().tolist()
pt_ids.pop(-1)

#* calculate the distance metrics for the full session/pre/post
df_dist_metrics, pt_ids = dist_metrics_fs(df_unmsk, dmatx)
df_dist_metrics = dist_metrics_pre(df_unmsk, df_dist_metrics, pt_ids, dmatx)
df_dist_metrics = dist_metrics_post(df_unmsk, df_dist_metrics, pt_ids, dmatx)

#! vars Discs
nr=5
nc=6
bgcol = 'white'
ft = f'Discs on Points [r = avg dist] for each Participant'
fl = f'Disc_{bgcol}.png'

multiplot_discs(    my_dir,
                    df_kde,
                    df_dist_metrics,
                    df_colors,
                    lim_x,
                    lim_y,
                    nrows=nr,
                    ncols=nc,
                    axbase=axibase,
                    bg=bgcol,
                    cvxh=True,
                    precvh=False,
                    postcvh=False,
                    allscatter=True,
                    figtitle=ft,
                    fn=fl
                )


df_nov = novelty_from_density(  my_dir,
                                df_kde,
                                lim_x,
                                lim_y,
                                plot=True
                            )

print(df_nov)

'''

#! novelty from NN



novel_nn = novelty_from_neig(my_dir, df_base, embedding, delta=.7, save_df=True, save_plot=True)

# novelty_nn_study(my_dir, embedding, x_fixed=False)
