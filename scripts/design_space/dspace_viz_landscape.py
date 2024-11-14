from pathlib import Path
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from scipy.spatial import ConvexHull
from matplotlib.colors import to_rgba, LinearSegmentedColormap, ListedColormap
import matplotlib.colors as mcolors
from matplotlib import cm
from mpl_toolkits.mplot3d import Axes3D
from scripts.design_space.dspace_viz_density import *
from scipy import stats, integrate

def plot_landscape(dir_data, df, embed, mode='line', save_plot=True):

    dir_exviz = Path(f'{dir_data.parent}'+r'/experimental/viz')

    if mode != 'line' and mode != 'landscape' and mode!='point':
        print ('Error - mode must be either <line>, <point> or <landscape>')
    else:
        perf = df['performance'].copy()
        n_perf = normalize(perf,0,1)
        x_emb = embed[:,0]
        y_emb = embed[:,1]

        fig, axes = plt.subplots(layout='constrained', figsize=(15, 15), subplot_kw={"projection": "3d"})

        if mode == 'line':
            axes.stem(x_emb, y_emb, n_perf, markerfmt='ob', linefmt='C7:', basefmt='C7:')
            plt.title(f'Design Space and Performance (z-axis) as {mode} plot')

        elif mode == 'landscape':
            surf = axes.plot_trisurf(x_emb, y_emb, n_perf, cmap=cm.viridis,linewidth=0, antialiased=True)
            axes.scatter3D(xs=x_emb, ys=y_emb, zs=n_perf)
            fig.colorbar(surf, shrink=0.25, aspect=5)

            plt.title(f'Design Space and Performance (z-axis) as {mode} plot')

        else:
            axes.scatter3D(xs=x_emb, ys=y_emb, zs=n_perf,cmap=cm.viridis)
            plt.title(f'Design Space and Performance (z-axis) as {mode} plot')


        print('done!')

        if save_plot == True:
            plt.savefig(f'{dir_exviz}/DS_Perf_{mode}.tiff', dpi=300, bbox_inches='tight')
            plt.savefig(f'{dir_exviz}/DS_Perf_{mode}.svg', format='svg', dpi=300, bbox_inches='tight')
            plt.close()

    plt.show()

def plot_heatmap(dir_data, dmatrix, cm='viridis', save_plot=True ):

    dir_exviz = Path(f'{dir_data.parent}'+r'/experimental/viz')

    fig, axes = plt.subplots(layout='constrained', figsize=(15, 15))

    plt.imshow(dmatrix, cmap=cm)

    plt.title( "Distance Heatmap" )


    if save_plot == True:
        plt.savefig(f'{dir_exviz}/DS_HM_{cm}.png', dpi=300, bbox_inches='tight')
        plt.savefig(f'{dir_exviz}/DS_HM_{cm}.svg', dpi=300, bbox_inches='tight')
        plt.close()

    plt.show()