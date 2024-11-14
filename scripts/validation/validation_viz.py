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

from scripts.design_space.read_data import read_analysis
from scripts.design_space.dist_matrix import *
from scripts.design_space.dim_reduction import *
from scripts.design_space.design_space import *
from scripts.validation.validation_distmetric import *

def plot_spec_sols_difweights(dir_data, filenm, df, list_sols, df_colors, sheetgow=None, sheetjac=None, save_val=True):
    """PLots a list of solutions across the different metrics weights.

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

    #* transform list of solutions names into list of indices
    list_idx = []
    for sol in list_sols:
        list_idx.append(df[df['FullID']==sol].index.values[0])

    # set figure size & basic params
    fig, ax = plt.subplots(3,4, layout='tight', figsize=(54, 40))

    print('Plotting list of solutions in different Gower/Jaccard weights UMAP...')
    #* get weights and the matrices if already exist weights
    for m in range(len(df_gow_weights['gowerW'])):
        wgts_g = ast.literal_eval(df_gow_weights['gowerW'][m])
        wgts_j = df_jac_weights['w_jac'][m]


        g_weigthtype.append(df_gow_weights['Weigth Type'][m])   # list of weight types
        j_weightval.append(wgts_j)                              # list of Jaccard weight values

        #print(g_weigthtype[m])

        #* calculates distance matrix
        n_distmatrix = calc_distmatrix(df, dir_data, filenm, gowerweight=wgts_g, jacweight=wgts_j, mult_gow=m)
        print(f'Dist Matrix with GW: {g_weigthtype[m]}, JW: {j_weightval[m]} calculated.')


        sols_size = len(list_sols)

        #* calculates/retrieves embedding
        embed, emb_graph = create_embedding(dir_data, n_distmatrix, embed_name=(df_gow_weights['WTp'][m]), NN=85, MD=0.25, densm=3)
        #embed, emb_graph = create_embedding(dir_data, n_distmatrix,embed_name='nep', Wg='W2', NN=85, MD=0.25, densm=3)

        print('embedding done')


        #! PLOT UMAP DIFF VALUES [validation umap parameters]

        ax_cfg = fig.add_subplot(3, 4, (m+1))

        # plot points
        scatter = ax_cfg.scatter(embed[:, 0],embed[:, 1], c='grey') #c=result

        '''# add labels to the points
        for label, x, y in zip(labels, embedding_tsne[:,0], embedding_tsne[:,1]):
            plt.annotate(label, (x,y), xycoords = 'data')
        '''
        #print(list_idx)

        for vtx in list_idx:
                print(vtx)
                ax_cfg.plot(embed[vtx, 0], embed[vtx, 1], 'P', mec='k', color='red', lw=3, markersize=12)

            # add labels
                x = embed[vtx, 0]
                y = embed[vtx, 1]
                ax_cfg.annotate(vtx, (x,y), xycoords = 'data')
                ax_cfg.set_xticklabels([])
                ax_cfg.set_yticklabels([])
    #!hereeee
    fig.suptitle('Different UMAP embeddings weights', fontsize=12, fontweight='bold')

    for (i, axi) in zip(range(len(df_gow_weights['WTp'])), ax.flat):
            axi.title.set_text(f'Weight Type {df_gow_weights["WTp"][i]}')

    plt.axis('off')

    plt.show()


def plot_spec_sols_difparams(dir_data, filenm, df, list_sols, df_colors, save_val=True):

    """PLots a list of solutions across the different metrics weights.

    Args:
        dir_data (path): Path to the directory with the data file.
        filenm (string): Name of the file containing the data for the metrics' weights. Expects Excel file.
        df (dataframe): Dataframe with the analysis for the solutions.
        list_sols (list): List of solutions that will be be compared across the different metrics.
        sheetgow (string): Sheet name with data for the Gower distance weights. Defaults to None.
        sheetjac (string): Sheet name with data for the Jaccard distance weights. Defaults to None.
        save_val (bool, optional): Argument to specify if the comparison should be saved. Defaults to True.
    """

    #* transform list of solutions names into list of indices
    list_idx = []
    for sol in list_sols:
        list_idx.append(df[df['FullID']==sol].index.values[0])

    print('Plotting list of solutions in different UMAP params...')

    MD_ls = [0.1, 0.25, 0.4]
    NN_ls = [40, 85, 115]
    dens_ls = [0.1, 3, 5]

    sols_size = len(list_sols)
    n_distmatrix = calc_distmatrix(df, dir_data, filenm)
    plt.rcParams["figure.figsize"] = (7.5,7.5)

    #* get params
    for m in MD_ls:
        for n in NN_ls:
            for d in dens_ls:

                #* calculates/retrieves embedding
                embed, emb_graph = create_embedding(dir_data, n_distmatrix, embed_name='nep', NN=n, MD=m, densm=d)

                print(f'embedding NN={n}, MD={m}, dens={d} done')

                #! PLOT UMAP DIFF VALUES [validation umap parameters]
                fig, ax = plt.subplots(layout='tight')


                # plot points
                scatter = ax.scatter(embed[:, 0],embed[:, 1], c='grey') #c=result

                '''# add labels to the points
                for label, x, y in zip(labels, embedding_tsne[:,0], embedding_tsne[:,1]):
                    plt.annotate(label, (x,y), xycoords = 'data')
                '''
                #print(list_idx)

                # List of colors
                colors = ['red', 'green', 'blue', 'orange', 'purple', 'brown', 'pink']

                # List of marker types
                markers = ['s', '^', 'D', 'P', '*', 'X', 'v']


                for i in range(len(list_idx)):
                        print(i)
                        ax.plot(embed[list_idx[i], 0], embed[list_idx[i], 1], marker=markers[i], mec='k', color=colors[i], lw=2, markersize=19)

                    # add labels
                        x = embed[list_idx[i], 0]
                        y = embed[list_idx[i], 1]
                        ax.annotate(list_idx[i], (x,y), xycoords = 'data')
                        ax.set_xticklabels([])
                        ax.set_yticklabels([])

                #!hereeee
                #fig.suptitle(f'UMAP embedding | Params: NN={n}, MD={m}, dens={d}', fontsize=12, fontweight='bold')

                plt.axis('off')

                #plt.title(f'DS Viz | Params: NN={n}, MD={m}, dens={d}', fontsize=12, fontweight='bold')
                plt.savefig(f'{dir_data}/DS_NN={n}_MD={m}_dens={d}.png', dpi=300, bbox_inches='tight')
                plt.savefig(f'{dir_data}/DS_NN={n}_MD={m}_dens={d}.svg', dpi=300, bbox_inches='tight')
                plt.close()

