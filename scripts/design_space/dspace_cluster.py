#%%
import argparse
import pandas as pd
from pathlib import Path
import igraph
import plotly.express as px
from datetime import datetime
import math
import random
import plotly.graph_objects as go
from plotly.validators.scatter.marker import SymbolValidator


from scripts.utils.utils import *
from scripts.design_space.read_data import read_analysis
from scripts.design_space.dist_matrix import *
from scripts.design_space.dim_reduction import *
from scripts.design_space.dspace_dist_metrics import *
from scripts.design_space.design_space import *
from scripts.design_space.dspace_metrics import *
from scripts.design_space.dspace_metric_novelty import *
from scripts.design_space.dspace_viz_density import *

#* --- initial definitions ------
my_dir = Path(r'C:/Py/DS_Viz_Exp/data')                                                 # path to the data file
filenm = 'MASKED_DATA_analysis_v1.xlsx'                                                 # name of the data file
sheetnm = 'ExpData-100R-Expanded'                                                       # sheet where the data (analysis) is
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
save_dir = 'C:\Py\DSX_Vis\SaveFiles'
#* ------------------------------
'''
#! get & process data
#* reads Excel file with solutions' analysis
df_base, df_colors, labels = read_analysis(my_dir, filenm, sheetname=sheetnm)

#* calculates distance matrix
n_distmatrix = calc_distmatrix(df_base, my_dir, filenm)

#* generate the embedding of the distance matrix
embedding, graph = create_embedding(my_dir, n_distmatrix, Wg='W2', NN=115, MD=0.15, densm=2)

df_base['x_emb'] = embedding[:, 0]
df_base['y_emb'] = embedding[:, 1]

#%%
# Perform Leiden clustering
random.seed(42)

Gm = graph

# List of tuples (res, max_clust_number)
results = []
# List of resolution parameters
res_list = []
# List of max_clust_number
nr_clust_list = []
# Previous number of cluster
previous_n_clust = 0

for i in range(150):
    random.seed(42)
    res_var = 0.0005 * i
    clusters = Gm.community_leiden(objective_function='CPM',
                                    weights='weight',
                                    resolution=res_var,
                                    n_iterations=-1)

    clusters = pd.Series(clusters.membership, index=Gm.vs["name"]).sort_index().values

    # Current number of clusters
    curr_n_clust = len(set(clusters))
    print(f'RES: {res_var:.4f} | PREVIOUS (max): {previous_n_clust} | CURRENT: {curr_n_clust}')

    # Appends tuple (res, maximum value either current number or previous)
    results.append((res_var, max([curr_n_clust, previous_n_clust])))
    res_list.append(res_var)
    # Appends value of maximum either current number or previous
    nr_clust_list.append(max([curr_n_clust, previous_n_clust]))
    # Updates value of maximum either current or previous
    previous_n_clust = max([curr_n_clust, previous_n_clust])

    # Plot variation of res vs number clusters
    df_results = pd.DataFrame(results)
    fig = sns.scatterplot(x=df_results[0], y=df_results[1])
    plt.xlabel('Resolution')
    plt.ylabel('Max number of clusters')
    plt.savefig(f'{save_dir}/clust_res_var.jpeg')

# Find a possible resolution
# Extract all max cluster numbers found
set_nr_clust = set(nr_clust_list)

# Count occurrence of each max cluster number
counts = [nr_clust_list.count(number) for number in set_nr_clust]

# Find max streak
max_streak = max(counts)

# Index of max streak initiation
pos = counts.index(max_streak)

# Find resolution of same index
optimum_res = res_list[pos]
res = optimum_res
print(f'Suggested resoltion parameter: {res:.4f}')
#%%
# create actual clusters based on the best res parameter
Gm = graph
random.seed(42)
clusters = Gm.community_leiden(objective_function='CPM',
                                weights='weight',
                                resolution=0.05,
                                n_iterations=-1)

# Extract series of cluster_id
clusters_ls = pd.Series(clusters.membership, index=Gm.vs["name"]).sort_index().values


print(f'TOTAL clusters identified = {len(set(clusters_ls))}')

# Add cluster_id column to pd peaks df
df_base['cluster_id'] = clusters_ls

df_base['cluster_id'] = df_base.apply(lambda row: row.cluster_id + 1, axis=1)

#df_peaks = df_peaks.sort_values(by=['cluster_id'])

#%%

#  function: To plot the clusters
def plot_clusters(df, fig_dir):

    symb_ls = [200, 202, 203, 204, 213, 214, 217, 218, 219, 220, 221, 222, 223, 224]

    # Get datetime to save clustering html
    now = datetime.now()
    dt = now.strftime("%d_%m_%Y_%H_%M_%S")

    # Read cluster_id as strings to create categorical coloring
    df['cluster_id'] = df['cluster_id'].astype(str)

    #colors = px.colors.qualitative.Alphabet
    #colors.remove(colors[8])
    #colors += px.colors.qualitative.Dark24

    # Identify ranges for plotting the axes
    min_x = min(df.x_emb)
    min_y = min(df.y_emb)
    max_x = max(df.x_emb)
    max_y = max(df.y_emb)

    # Make go plot

    fig_DS = go.Figure()

    # add points
    fig_DS.add_trace(go.Scatter(    x=df['x_emb'],
                                    y=df['y_emb'],
                                    mode='markers',
                                    marker=dict(
                                    size=5,
                                    color=df['colors'],
                                    symbol=symb_ls
                                ),
                                name='all_pts'),
                                )

    # update graph layout
    fig_DS.update_layout(   autosize=False,
                            width=725,
                            height=610,
                            margin=dict(
                                l=25,
                                r=25,
                                b=25,
                                t=25,
                                pad=2
                            ),
                            showlegend=True,
                            paper_bgcolor="rgba(0,0,0,0)",
                            plot_bgcolor='white'
                            )












    fig = go.Scatter(mode='markers', x=df_base['x_emb'], y=df_base['y_emb'],
                    marker_color=colors,
                    marker_symbol=symb_ls,
                    #color_discrete_sequence=colors,
                    #hover_data=['FullID','result','cluster_id'],
                    #width=750,
                    #height=750
                    )
    # Change size of data points
    fig.update_traces(marker={'size': 4})

    # Fix the size of figure legend
    fig.update_layout(legend={'itemsizing': 'constant'},
                        xaxis_range=[math.floor(min_x),math.ceil(max_x)],
                        yaxis_range=[math.floor(min_y),math.ceil(max_y)])
    fig.write_html(f"{fig_dir}/clust_leiden_{dt}.html")









plot_clusters(df_base, save_dir)

#%%

'''
def get_clusters(df, grph):
    random.seed(42)
    clusters = grph.community_leiden(objective_function='CPM',
                                    weights='weight',
                                    resolution=0.05,
                                    n_iterations=-1)

    # Extract series of cluster_id
    clusters_ls = pd.Series(clusters.membership, index=grph.vs["name"]).sort_index().values


    print(f'TOTAL clusters identified = {len(set(clusters_ls))}')

    # Add cluster_id column to pd peaks df
    df['cluster_id'] = clusters_ls
    df['cluster_id'] = df.apply(lambda row: row.cluster_id + 1, axis=1)

    return df
