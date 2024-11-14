"""The validation_run module supports the validation of different metrics/choices.
"""
#%%
import pandas as pd
import numpy as np
from pathlib import Path

from stats.stats_main import *

from utils.utils import *
from design_space.read_data import *
from design_space.dist_matrix import *
from design_space.dim_reduction import *

from validation.validation_distmetric import *
from validation.validation_areametric import *
from validation.validation_viz import *

#* --- initial definitions ------
my_dir = Path(r'C:/Py/DS_Viz_Exp/data')                                             # path to the data file
filenm = 'MASKED_DATA_analysis_v1.xlsx'                                             # name of the data file
sheetnm = 'ExpData-100R-Expanded'                                                   # sheet where the data (analysis) is
#* ------------------------------

#* --- create folder structure ---
Path(f'{my_dir.parent}/validation').mkdir(parents=True,exist_ok=True)             # folder export/stats
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

#%%
#! ---------- DISTANCE WEIGHTS VALIDATION ----------
#* procedure:
#       1. get df with solutions' analysis                                                           (read_analysis)
#       2. run comparison of metrics'weights retrieving pairs of solutions' at specific distances    (metrics_weights_comparison_specificpos)
#       3. run comparison of metrics'weights for a specific list of solutions                        (metrics_weights_comparison_specificsols)
#       4. run distortion hidim/embedding for each weight, set of UMAP parameters                    ()

#* 1. reads Excel file with solutions' analysis
df_base, df_colors, labels = read_analysis(my_dir, filenm, sheetnm)
#%%
#* 2. run comparison specific distance positions [0, 0.25, 0.5, 0.75, 1]
#metrics_weights_comparison_specificpos(my_dir, filenm, df_base)

#* 3. run comparison for specific list of solutions
'''
ls_sols = [ 'P_M8L-ZSB-S_8O8',
            'P_V1M-ZSB-S_4U3',
            'P_O7W-ZSB-S_8O8',
            'P_O7W-ZSB-S_3B9',
            'P_T4B-KYY-S_0M4',
            'P_L4V-KYY-S_9E0',
            'P_H7P-ZSB-S_1J8',
            'P_V2A-ZSB-S_0T2',
            'P_A6W-ZSB-S_0T2',
            'P_A4T-KYY-S_1Q4',
        ]
'''

ls_sols_2 = [   'P_I7A-KYY-S_3X6', #P01_S08
                'ENaG2',
                'VPZgQ',
                'VeP9n',
                'Ag5q6',
                'P_P8M-KYY-S_0M4', #P09_S03
                'P_Z2A-ZSB-S_0M4'
            ]

#embed_list = metrics_weights_comparison_specificsols(my_dir, filenm, df_base, ls_sols)

# compare_participant_dmatrices(my_dir, 'validation_study', 'PVL4_mtx_c_n', 'PVL5_mtx_c_n')

# procrustes_parts(my_dir, 'validation_study', 5)

# spearmancorrel(my_dir, 'validation_study', 'embed', 'dist_PVL5')

#mse_val(my_dir, 'validation_study', 'dist_PVL4', 'dist_PVL5')

#* 4. distort hidim/embed validation [takes long (~6h30 for 6.5K combinations)]
#distance_hidim_embed_distort(my_dir, filenm, df_base, mult_runs=True)

#plot_embedding(my_dir, df_base, embed=None, embed_name='nep', Wg='W2', NN=85, MD=0.25, densm=3)

#! ---------- AREA SENSITIVITY VALIDATION ----------
area_sensitivity_weights(my_dir, filenm, df_base, df_colors)

#! ---------- SOLUTIONS IN PLOT VIZ VALIDATION ----------
#plot_spec_sols_difweights(my_dir, filenm, df_base, ls_sols_2, df_colors)

#plot_spec_sols_difparams(my_dir, filenm, df_base, ls_sols_2, df_colors)
# %%
