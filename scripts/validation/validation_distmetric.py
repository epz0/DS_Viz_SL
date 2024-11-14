"""The validation_distmetric runs the comparisons across different weights to see how solutions get spaced out.

Functions:
    get_indices_of_k_smallest: Function to reorder the distance matrix and get the points at the smallest distance from each other.
    get_indices_of_k_largest: Function to reorder the distance matrix and get the points at the largest distance from each other.
    drop_duplicated_points: Function to drop duplicated points from a list of points [(a,b), (c,d), (b,a)] --> [(a,b), (c,d)].
    get_weights: Function to get the weights for the Gower/Jaccard distances run.
    metrics_weights_comparison_specificpos: Runs the comparison accross the different weights comparing the solutions that are at specific distances from each other.
    metrics_weights_comparison_specificsols: Runs the comparison of the specific solutions distances across the different m etrics weights.
    distance_hidim_embed_distort: Runs the distortion between
"""

from pathlib import Path

import ast
import pandas as pd
import numpy as np
import scipy as sp

from scripts.design_space.read_data import read_analysis
from scripts.design_space.dist_matrix import *
from scripts.design_space.dim_reduction import *
from scripts.design_space.design_space import *
from sklearn.metrics import cohen_kappa_score, mean_squared_error
from scipy.spatial import procrustes
from itertools import combinations
from scipy import stats

def get_indices_of_k_smallest(arr, k):
    """Returns list of indices of the k smallest items in the array passed.

    Args:
        arr (matrix): Array or matrix that will be flattened and the smallest values identified.
        k (integer): Number of smallest items to be identified.

    Returns:
        list with indices corresponding to the k smallest items.
    """
    idx = np.argpartition(arr.ravel(), k)

    return np.array(np.unravel_index(idx, arr.shape))[:, range(k)].transpose().tolist()

def get_indices_of_k_largest(arr, k):
    """Returns list of indices of the k largest items in the array passed.

    Args:
        arr (matrix): Array or matrix that will be flattened and the largest values identified.
        k (integer): Number of largest items to be identified.

    Returns:
        list with indices corresponding to the k largest items. Indices may be duplicated.
    """
    idx = np.argpartition(arr.ravel(), -1*k)

    return np.array(np.unravel_index(idx, arr.shape)).transpose().tolist()[-1*k:]

def drop_duplicated_points(list_points):
    """Returns unique list of points, removing duplicates.

    Args:
        list_points (list): List with duplicated items.

    Returns:
        list_points: List with unique points.
    """    

    for j in range(len(list_points)):
        if j < len(list_points):
            pairs_ind = list_points[j].copy()
            pairs_ind.reverse()
            for k in np.arange(1, len(list_points)-j):
                if pairs_ind == list_points[-k]:
                    list_points.pop(-k)
    return list_points

def get_weights(dir_data, fname, sheetgow=None, sheetjac=None):
    """Retunrs dataframes with the Gower and Jaccard weights for the distance metric calculation.

    Args:
        dir_data (path): Path to the directory with the data file.
        fname (string): Name of the file containing the data for the metrics' weights. Expects Excel file.
        sheetgow (string): Sheet name with data for the Gower distance weights. Defaults to None.
        sheetjac (string): Sheet name with data for the Jaccard distance weights. Defaults to None.

    Returns:
        _type_: _description_
    """    
    if sheetgow is None:
        sheetgow = 'Gower_Weight'

    #* get Gower weights
    df_gowerW = pd.read_excel(f'{dir_data}/{fname}', sheet_name=sheetgow)
    #print(df_gowerW)

    if sheetjac is None:
        sheetjac = 'Jaccard_Weight'

    #* get Jaccard weights
    df_jaccardW = pd.read_excel(f'{dir_data}/{fname}', sheet_name=sheetjac)
    #print(df_jaccardW)

    return df_gowerW, df_jaccardW

def metrics_weights_comparison_specificpos(dir_data, filenm, df, sheetgow=None, sheetjac=None, save_val=True):
    """Runs the comparison of the solutions that are at different distances across the different metrics weights.

    Args:
        dir_data (path): Path to the directory with the data file.
        fname (string): Name of the file containing the data for the metrics' weights. Expects Excel file.
        df (dataframe): Dataframe with the analysis for the solutions.
        sheetgow (string): Sheet name with data for the Gower distance weights. Defaults to None.
        sheetjac (string): Sheet name with data for the Jaccard distance weights. Defaults to None.
        save_val (bool, optional): Argument to specify if the comparison should be saved. Defaults to True.
    """

    # preparing df for the summary
    df_summary_distval = pd.DataFrame(columns=['position','W1','W2','W3','W4','W5','W6','W7','W8', 'W9','W10','W11'])
    df_summary_distval['position']=['closest','perc25', 'perc50', 'perc75', 'furthest']

    df_gow_weights, df_jac_weights = get_weights(dir_data, filenm)

    g_weigthtype = []                           #* list of Gower metric weights
    j_weightval = []                            #* list of Jaccard metric weights


    print('Running validation for the different Gower/Jaccard weights...')
    #* run process (metric -> dist matrix -> get pairs -> add to df) for each metric weights
    for m in range(len(df_gow_weights['gowerW'])):
        wgts_g = ast.literal_eval(df_gow_weights['gowerW'][m])
        wgts_j = df_jac_weights['w_jac'][m]


        g_weigthtype.append(df_gow_weights['Weigth Type'][m])   # list of weight types
        j_weightval.append(wgts_j)                              # list of Jaccard weight values

        #print(g_weigthtype[m])

        #* calculates distance matrix
        n_distmatrix = calc_distmatrix(df, dir_data, filenm, gowerweight=wgts_g, jacweight=wgts_j, mult_gow=m)
        print(f'Dist Matrix with GW: {g_weigthtype[m]}, JW: {j_weightval[m]} calculated.')

        print('Getting closest solutions...')
        #! closest
        indices_sm = get_indices_of_k_smallest(n_distmatrix, 565) #559 of them are zeroes (dist between solution and self)

        pairs_ind_sm = [sublist for sublist in indices_sm if sublist[0] != sublist[1]]
        pairs_ind_sm = pairs_ind_sm[0:5]

        #print(f'sm_before {pairs_ind_sm}')

        #* drop if pair is duplicated
        pairs_ind_sm = drop_duplicated_points(pairs_ind_sm)

        #print(f'sm_after {pairs_ind_sm}')

        #* get ids and dist
        pairs_fullid_sm = []
        pairs_dist_sm = []

        # get solutions' full id
        for pair in pairs_ind_sm:
            pairs_fullid_sm.append([df.loc[pair[0],'FullID'], df.loc[pair[1],'FullID']])
            pairs_dist_sm.append(n_distmatrix[pair[0]][pair[1]])

        #* add to list combined and to df
        pairs_list=[]
        pairs_list.append(pairs_fullid_sm)
        pairs_list.append(pairs_dist_sm)

        df_summary_distval[f'W{m+1}'] = df_summary_distval[f'W{m+1}'].astype('object')
        df_summary_distval.at[0,f'W{m+1}']=pairs_list

        print('Getting furthest solutions...')
        #! furthest
        #* getting largest  distance pairs & largest distance pairs to compare screenshots
        indices_lg = get_indices_of_k_largest(n_distmatrix,5)

        #print(f'lg_before {indices_lg}')

        #* drop if pair is duplicated
        indices_lg = drop_duplicated_points(indices_lg)

        #print(f'lg_after {indices_lg}')
        pairs_ind_lg = indices_lg

        pairs_fullid_lg = []
        pairs_dist_lg = []

        #* get solutions' full id
        for pair in pairs_ind_lg:
            pairs_fullid_lg.append([df.loc[pair[0],'FullID'], df.loc[pair[1],'FullID']])
            pairs_dist_lg.append(n_distmatrix[pair[0]][pair[1]])

        #* add to list combined and to df
        pairs_list=[]
        pairs_list.append(pairs_fullid_lg)
        pairs_list.append(pairs_dist_lg)

        df_summary_distval.at[4,f'W{m+1}']=pairs_list


        print('Getting solutions at 0.25 distance...')
        #! .25
        indices_qone = get_indices_of_k_smallest(n_distmatrix, int(559*559*.5)) #559 of them are zeroes (dist between solution and self)

        pairs_ind_qone = [sublist for sublist in indices_qone if sublist[0] != sublist[1]]

        pairs_fullid_qone = []
        pairs_dist_qone = []
        pairs_id_qone_subset = []

        for pair in pairs_ind_qone:
            if abs(n_distmatrix[pair[0]][pair[1]] - 0.25) <=0.00001:
                pairs_id_qone_subset.append(pair)

        #print(f'q1 size {len(pairs_id_qone_subset)}')
        #print(f'q1_before {pairs_id_qone_subset}')

        #* drop if pair is duplicated
        pairs_id_qone_subset = drop_duplicated_points(pairs_id_qone_subset)

        #print(f'q1_after {pairs_id_qone_subset}')

        #* get solutions' full id
        for pair in pairs_id_qone_subset:
            pairs_fullid_qone.append([df.loc[pair[0],'FullID'], df.loc[pair[1],'FullID']])
            pairs_dist_qone.append(n_distmatrix[pair[0]][pair[1]])

        pairs_fullid_qone = pairs_fullid_qone[0:3]
        pairs_dist_qone = pairs_dist_qone[0:3]

        #* add to list combined and to df
        pairs_list=[]
        pairs_list.append(pairs_fullid_qone)
        pairs_list.append(pairs_dist_qone)

        df_summary_distval.at[1,f'W{m+1}'] = pairs_list

        print('Getting solutions at 0.50 distance...')
        #! .5
        indices_qtwo = get_indices_of_k_smallest(n_distmatrix, int(559*559*.85)) #559 of them are zeroes (dist between solution and self)

        pairs_ind_qtwo = [sublist for sublist in indices_qtwo if sublist[0] != sublist[1]]

        pairs_fullid_qtwo = []
        pairs_dist_qtwo = []
        pairs_id_qtwo_subset = []

        for pair in pairs_ind_qtwo:
            if abs(n_distmatrix[pair[0]][pair[1]] - 0.5) <=0.0001:
                pairs_id_qtwo_subset.append(pair)

        #print(f'q two size {len(pairs_id_qtwo_subset)}')

        #print(f'q2_before {pairs_id_qtwo_subset}')

        #* drop if pair is duplicated
        pairs_id_qtwo_subset = drop_duplicated_points(pairs_id_qtwo_subset)

        #print(f'q2_after {pairs_id_qtwo_subset}')

        #* get solutions' full id
        for pair in pairs_id_qtwo_subset:
            pairs_fullid_qtwo.append([df.loc[pair[0],'FullID'], df.loc[pair[1],'FullID']])
            pairs_dist_qtwo.append(n_distmatrix[pair[0]][pair[1]])

        pairs_fullid_qtwo = pairs_fullid_qtwo[0:3]
        pairs_dist_qtwo = pairs_dist_qtwo[0:3]

        #* add to list combined and to df
        pairs_list=[]
        pairs_list.append(pairs_fullid_qtwo)
        pairs_list.append(pairs_dist_qtwo)

        df_summary_distval.at[2,f'W{m+1}'] = pairs_list

        print('Getting solutions at 0.75 distance...')
        #! .75

        indices_qthree = get_indices_of_k_smallest(n_distmatrix, int(559*559*.99)) #559 of them are zeroes (dist between solution and self)

        pairs_ind_qthree = [sublist for sublist in indices_qthree if sublist[0] != sublist[1]]

        pairs_fullid_qthree = []
        pairs_dist_qthree = []
        pairs_id_qthree_subset = []

        for pair in pairs_ind_qthree:
            if abs(n_distmatrix[pair[0]][pair[1]] - 0.75) <=0.001:
                pairs_id_qthree_subset.append(pair)

        #print(f'q three size {len(pairs_id_qthree_subset)}')

        #print(f'q3_before {pairs_id_qthree_subset}')

        #* drop if pair is duplicated
        pairs_id_qthree_subset = drop_duplicated_points(pairs_id_qthree_subset)

        #print(f'q3_after {pairs_id_qthree_subset}')

        #* get solutions' full id
        for pair in pairs_id_qthree_subset:
            pairs_fullid_qthree.append([df.loc[pair[0],'FullID'], df.loc[pair[1],'FullID']])
            pairs_dist_qthree.append(n_distmatrix[pair[0]][pair[1]])

        pairs_fullid_qthree = pairs_fullid_qthree[0:3]
        pairs_dist_qthree = pairs_dist_qthree[0:3]

        #* add to list combined and to df
        pairs_list=[]
        pairs_list.append(pairs_fullid_qthree)
        pairs_list.append(pairs_dist_qthree)

        df_summary_distval.at[3,f'W{m+1}'] = pairs_list
        print(f'Solution list for GW: {g_weigthtype[m]}, JW: {j_weightval[m]} - done!')

    if save_val == True:
        dir_val = Path(f'{dir_data.parent}'+r'/validation')
        with pd.ExcelWriter(f'{dir_val}/DS_DistanceAnalysis.xlsx') as writer:
            # use to_excel function and specify the sheet_name and index
            # to store the dataframe in specified sheet
            df_summary_distval.to_excel(writer, sheet_name="Sol_Spec_Pos_Across_Weights", index=False)

    print('Running validation for the different Gower/Jaccard weights - done!')

def metrics_weights_comparison_specificsols(dir_data, filenm, df, list_sols, sheetgow=None, sheetjac=None, save_val=True):
    """Runs the comparison of a list of solutions across the different metrics weights.

    Args:
        dir_data (path): Path to the directory with the data file.
        filenm (string): Name of the file containing the data for the metrics' weights. Expects Excel file.
        df (dataframe): Dataframe with the analysis for the solutions.
        list_sols (list): List of solutions that will be be compared across the different metrics.
        sheetgow (string): Sheet name with data for the Gower distance weights. Defaults to None.
        sheetjac (string): Sheet name with data for the Jaccard distance weights. Defaults to None.
        save_val (bool, optional): Argument to specify if the comparison should be saved. Defaults to True.
    """

    df_gow_weights, df_jac_weights = get_weights(dir_data, filenm)

    g_weigthtype = []                           #* list of Gower metric weights
    j_weightval = []                            #* list of Jaccard metric weights

    print('Running validation for the specific solutions in different Gower/Jaccard weights...')
    #* get weights and the matrices if already exist weights

    mtx_list = []

    for m in range(len(df_gow_weights['gowerW'])):
        wgts_g = ast.literal_eval(df_gow_weights['gowerW'][m])
        wgts_j = df_jac_weights['w_jac'][m]


        g_weigthtype.append(df_gow_weights['Weigth Type'][m])   # list of weight types
        j_weightval.append(wgts_j)                              # list of Jaccard weight values

        #print(g_weigthtype[m])

        #* calculates distance matrix
        n_distmatrix = calc_distmatrix(df, dir_data, filenm, gowerweight=wgts_g, jacweight=wgts_j, mult_gow=m)
        print(f'Dist Matrix with GW: {g_weigthtype[m]}, JW: {j_weightval[m]} calculated.')

        #* transform list of solutions names into list of indices

        list_idx = []
        for sol in list_sols:
            list_idx.append(df[df['FullID']==sol].index.values[0])

        sols_size = len(list_sols)

        # create and populate matrix with the distances
        mtx_sols_ids = np.zeros(shape=(sols_size,sols_size))

        for i in range(sols_size):
            for j in range(sols_size):
                mtx_sols_ids[i][j] = n_distmatrix[list_idx[i]][list_idx[j]]

        #print(mtx_sols_ids)
        mtx_list.append([mtx_sols_ids,f'GW: {g_weigthtype[m]}, JW: {j_weightval[m]}'])

        df_mtx_sols = pd.DataFrame.from_records(mtx_sols_ids)
        df_mtx_sols.columns = list_sols

        if m == 2:
            embed_val, ugraph = create_embedding(dir_data, mtx_sols_ids, embed_name='nep', Wg='W2', NN=85, MD=0.25, densm=3)
            plot_embedding (dir_data, embed_val, df, embed_name='nep')

        if save_val == True:
            dir_val = Path(f'{dir_data.parent}'+r'/validation')

            if Path(f'{dir_val}/DS_DistSpecSolAnalysis.xlsx').is_file() == True:
                with pd.ExcelWriter(f'{dir_val}/DS_DistSpecSolAnalysis.xlsx', mode='a', if_sheet_exists='replace') as writer:        # appends to existing file and overwrite sheet if exists
                    df_mtx_sols.to_excel(writer, sheet_name=df_gow_weights['WTp'][m], index=False)
            else:
                with pd.ExcelWriter(f'{dir_val}/DS_DistSpecSolAnalysis.xlsx') as writer:                                             # create file
                    df_mtx_sols.to_excel(writer, sheet_name=df_gow_weights['WTp'][m], index=False)

    # read mtx from validation study
    df_val = pd.read_excel(f'{dir_data}/validation_study.xlsx', sheet_name='PVL5_mtx_c_n')

    val_mtx = df_val.to_numpy()

    # compare valid mtx and individual mtx
    pc_list=[]
    for mt in range(len(mtx_list)):
        print(mtx_list[mt])
        mtx_hidim = mtx_list[mt][0]
        print(len(mtx_hidim))
        pcorrel = sp.stats.mstats.pearsonr(val_mtx, mtx_hidim)

        pc_list.append([pcorrel, mtx_list[mt][1]])

    df_pc = pd.DataFrame(pc_list)
    with pd.ExcelWriter(f'{dir_val}/DS_Hidim_v_Valid.xlsx') as writer:                                             # create file
        df_pc.to_excel(writer, sheet_name='Mtx_C_N', index=False)

    print('Running validation for the specific solutions in different Gower/Jaccard weights - done!')
    return embed_val

def distance_hidim_embed_distort(dir_data, filenm, df, mult_runs=False, NN_ls=None, MD_ls=None, Dens_ls=None):
    """Calculates the distortion given by embedding the multidimensional space into a 2D plane.

    Args:
        dir_data (path): Path to the directory with the data file.
        filenm (string): Name of the file containing the data for the metrics' weights. Expects Excel file.
        df (dataframe): Dataframe with the analysis for the solutions.
        mult_runs (bool, optional): Argument to specify if multiple runs will be performed. Defaults to False.
        NN_ls (float, optional): List of Number of Neighbors parameters to be passed onto the UMAP. Defaults to pre-specified list.
        MD_ls (float, optional): List of Number of Neighbors parameters to be passed onto the UMAP. Defaults to pre-specified list.
    """

    df_gow_weights, df_jac_weights = get_weights(dir_data, filenm)

    g_weigthtype = []                           #* list of Gower metric weights
    j_weightval = []                            #* list of Jaccard metric weights

    hd_dmatrix_lst = []                         #* list of hidim distance matrices
    embed_lst = []                              #* list of embeddings
    embed_dmatrix_lst = []                      #* list of embed distance matrices
    distort_list = []                           #* list of distorts (%)

    print('Running hidim/embed dmatrix validation...')
    #* run process (metric -> dist matrix -> get pairs -> add to df) for each metric weights
    for m in range(len(df_gow_weights['gowerW'])):
        wgts_g = ast.literal_eval(df_gow_weights['gowerW'][m])
        wgts_j = df_jac_weights['w_jac'][m]


        g_weigthtype.append(df_gow_weights['Weigth Type'][m])   # list of weight types
        j_weightval.append(wgts_j)                              # list of Jaccard weight values

        #print(g_weigthtype[m])

        #* calculates distance matrix
        n_distmatrix = calc_distmatrix(df, dir_data, filenm, gowerweight=wgts_g, jacweight=wgts_j, mult_gow=m)
        hd_dmatrix_lst.append(n_distmatrix)
        print(f'Dist Matrix with GW: {g_weigthtype[m]}, JW: {j_weightval[m]} calculated/retrieved.')

        #* calculates/retrieves embedding
        embed, emb_graph = create_embedding(dir_data, n_distmatrix, embed_name=(df_gow_weights['WTp'][m]))
        embed_lst.append(embed)
        print('embedding done')

        #* calculates/retrieves dmatrix from embedding
        n_dmatrix_embed =  create_dmatrix_from_embed(dir_data, embed)
        embed_dmatrix_lst.append(n_dmatrix_embed)
        print('embedding done')

        #! calc distort
        #* spread, absolute
        #* abs(D[hidim] - D[umap])
        #* --> closer to zero --> better
        pearsoncorrel = sp.stats.mstats.pearsonr(n_distmatrix, n_dmatrix_embed)
        spread_abs = abs(n_distmatrix - n_dmatrix_embed)

        distort_umap = spread_abs.mean()*100/n_distmatrix.mean()
        distort_list.append([distort_umap, pearsoncorrel])

    df_distort = pd.DataFrame(distort_list).T
    df_distort.columns = df_gow_weights['WTp']

    dir_val = Path(f'{dir_data.parent}'+r'/validation')
    with pd.ExcelWriter(f'{dir_val}/DS_Distort_HD_Embed.xlsx') as writer:                                             # create file
        df_distort.to_excel(writer, sheet_name='Weights_Distort', index=False)

    #* evals diff NN, MDs for each Weight Type
    #* takes a long time (10*9*6*12 UMAPs will be calculalted)
    if mult_runs is True:
        summary_list=[]

        if NN_ls is None:
            NN_ls = range(15, 180, 15)                                  #n=10

        if MD_ls is None:
            MD_ls = [0, 0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4]     #n=9

        if Dens_ls is None:
            Dens_ls = [0.1, 1, 2, 3, 4, 5] #TODO ADD DENSMAP TO LOOP    #n=6


        for m in range(len(df_gow_weights['gowerW'])):                  #n=11
                for neig in NN_ls:
                    for mind in MD_ls:
                        for dens in Dens_ls:
                            embedding_umap, DS_graph = create_embedding(dir_data, hd_dmatrix_lst[m], embed_name=f"nep_{(df_gow_weights['WTp'][m])}", NN=neig, MD=mind, densm=dens)
                            n_dmatrix_embed =  create_dmatrix_from_embed(dir_data, embedding_umap, embed_name=f"nep_{(df_gow_weights['WTp'][m])}", NN=neig, MD=mind, Dens=dens)

                            #! calc distort
                            pearsoncorrel = sp.stats.mstats.pearsonr(hd_dmatrix_lst[m], n_dmatrix_embed)
                            mse = mean_squared_error(hd_dmatrix_lst[m], n_dmatrix_embed)

                            summary_list.append(f'{df_gow_weights["WTp"][m]}, NN= {neig}, MD= {mind}, dens= {dens}, mse={mse}, pearsoncorre={pearsoncorrel}')

        df_multdistort = pd.DataFrame(summary_list)
        with pd.ExcelWriter(f'{dir_val}/DS_Distort_HD_Embed_mult.xlsx') as writer:                                             # create file
            df_multdistort.to_excel(writer, sheet_name='Mult_Distort', index=False)

    print(df_distort)

    print('Running hidim/embed dmatrix validation - done!')
    #print(df_distort)

def compare_participant_dmatrices(dir_data, filenm, sheetpA, sheetpB):

    """Runs the pearson correlation to compare two participants matrices.

    Args:
        dir_data (path): Path to the directory with the data file.
        filenm (string): Name of the file containing the data for the metrics' weights. Expects Excel file.
        sheetpA (string): Name of the worksheet cointaining the information for participant A.
        sheetpB (string): Name of the worksheet cointaining the information for participant B.
    """

    print('Running validation comparing two participants...')
    #* get weights and the matrices if already exist weights


    # read mtx from validation study - Participant A
    df_valA = pd.read_excel(f'{dir_data}/{filenm}.xlsx', sheet_name=f'{sheetpA}')
    val_mtx_PA = df_valA.to_numpy()

    # read mtx from validation study - Participant B
    df_valB = pd.read_excel(f'{dir_data}/{filenm}.xlsx', sheet_name=f'{sheetpB}')
    val_mtx_PB = df_valB.to_numpy()

    pcorrel = sp.stats.mstats.pearsonr(val_mtx_PA, val_mtx_PB)

    print(f'Pearson correlation Part A vs. Part B = {pcorrel}')
    print('Running validation comparing two participants - done!')

def cohen_kappa(dir_data, filenm, spartA, spartB):

    """Runs the cohen kappa correlation to compare two participants lists of distances.

    Args:
        dir_data (path): Path to the directory with the data file.
        filenm (string): Name of the file containing the data for the metrics' weights. Expects Excel file.
        sheetpA (string): Name of the worksheet cointaining the information for participant A.
        sheetpB (string): Name of the worksheet cointaining the information for participant B.
    """

    print(f'Running Cohen kappa for participants...')
    #* get list of distances

    # read list from validation study - Participant i
    df_valA = pd.read_excel(f'{dir_data}/{filenm}.xlsx', sheet_name=spartA)
    dptA = df_valA['dist'].copy()

    df_valB = pd.read_excel(f'{dir_data}/{filenm}.xlsx', sheet_name=spartB)
    dptB = df_valB['dist'].copy()

    kappa = cohen_kappa_score(dptA,dptB)

    print(f'Cohen kappa {spartA} vs {spartB} = {kappa:2f}')
    print(f'Running Cohen kappa for participants - done!')

def procrustes_parts(dir_data, filenm, npart, specificsols=False):
    """Runs the Procrustes comparison between solutions.

    Args:
        dir_data (path): Path to the directory with the data file.
        filenm (string): Name of the file containing the data for the metrics' weights. Expects Excel file.
        npart (integer): Number of participants in the validation experiment.
        specificsols (list, optional): List of distances for the specific solutions to compare. Defaults to False.
    """
    print(f'Running procrustes analysis between participants (comparing vs embed = {specificsols})...')

    # list for participants/embedding array [x,y values for each of the 10 solutions]
    sol_pos = []

    ebd = 0
    if specificsols is not False:
        sol_pos.append(specificsols)
        ebd = 1


    for i in range(1,npart+1):
        # read list from validation study - Participant i
        df_pos = pd.read_excel(f'{dir_data}/{filenm}.xlsx', sheet_name=f'procrustes_PVL{i}')
        df_pos = df_pos.drop(['id'], axis=1).copy()
        sol_pos.append(df_pos.to_numpy())

    combs = []
    for cb in combinations(range(1,npart+1+ebd),2):
        print(cb)

    for combo in combinations(sol_pos,2):
        combs.append(combo)
        mtx1, mtx2, disp = procrustes(combo[0],combo[1])
        print(f'disparity: {disp:.2f}')

def spearmancorrel(dir_data, filenm, spartA, spartB):
    """Runs the Spearman correlation to compare two participants lists of distances.

    Args:
        dir_data (path): Path to the directory with the data file.
        filenm (string): Name of the file containing the data for the metrics' weights. Expects Excel file.
        sheetpA (string): Name of the worksheet cointaining the information for participant A.
        sheetpB (string): Name of the worksheet cointaining the information for participant B.
    """

    print(f'Running Spearman correlation for participants...')
    #* get list of distances

    # read list from validation study - Participant i
    df_valA = pd.read_excel(f'{dir_data}/{filenm}.xlsx', sheet_name=spartA)
    dptA = df_valA['dist_n'].copy()

    df_valB = pd.read_excel(f'{dir_data}/{filenm}.xlsx', sheet_name=spartB)
    dptB = df_valB['dist_n'].copy()

    spcorr = stats.spearmanr(np.array(dptA), np.array(dptB), alternative='greater')

    print(f'Spearman correlation {spartA} vs {spartB} = {spcorr}')
    print(f'Running Spearman correlation for participants - done!')

def mse_val(dir_data, filenm, spartA, spartB):
    """Runs the MSE to compare two participants lists of distances.

    Args:
        dir_data (path): Path to the directory with the data file.
        filenm (string): Name of the file containing the data for the metrics' weights. Expects Excel file.
        sheetpA (string): Name of the worksheet cointaining the information for participant A.
        sheetpB (string): Name of the worksheet cointaining the information for participant B.
    """

    print(f'Running MSE for participants...')
    #* get list of distances

    # read list from validation study - Participant i
    df_valA = pd.read_excel(f'{dir_data}/{filenm}.xlsx', sheet_name=spartA)
    dptA = df_valA['dist_n'].copy()

    df_valB = pd.read_excel(f'{dir_data}/{filenm}.xlsx', sheet_name=spartB)
    dptB = df_valB['dist_n'].copy()

    mse = mean_squared_error(np.array(dptA), np.array(dptB))

    print(f'MSE {spartA} vs {spartB} = {mse}')
    print(f'Running MSE for participants - done!')


    '''
    with densmap
    if Dens_ls is None:
            Dens_ls = [0.1, 1, 2, 3, 4, 5]

        for m in range(len(df_gow_weights['gowerW'])):
            for dlamb in Dens_ls:
                for neig in NN_ls:
                    for mind in MD_ls:
                        embedding_umap, DS_graph = create_embedding(dir_data, hd_dmatrix_lst[m], embed_name=(df_gow_weights['WTp'][m]), NN=neig, MD=mind, densm=dlamb)
                        n_dmatrix_embed =  create_dmatrix_from_embed(dir_data, embedding_umap, embed_name=(df_gow_weights['WTp'][m]), NN=neig, MD=mind, Dens=dlamb)

                        #! calc distort
                        pearsoncorrel = sp.stats.mstats.pearsonr(hd_dmatrix_lst[m], n_dmatrix_embed)
                        mse = mean_squared_error(hd_dmatrix_lst[m], n_dmatrix_embed)

                        summary_list.append(f'{df_gow_weights["WTp"][m]}, NN: {neig}, MD: {mind}, densmap: {dlamb}, mse={mse}, pearsoncorre={pearsoncorrel}')

    '''