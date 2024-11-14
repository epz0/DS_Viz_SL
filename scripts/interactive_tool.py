#%%

from dash import Dash, html, dcc, Input, Output, callback, State, Patch, ctx
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash.exceptions import PreventUpdate
import plotly.figure_factory as ff

import numpy as np
from scipy.spatial import Delaunay
from pathlib import Path
import matplotlib.pyplot as plt
from scipy.spatial import ConvexHull
import shapely.geometry

from scripts.utils.utils import *
from scripts.design_space.read_data import read_analysis
from scripts.design_space.dist_matrix import *
from scripts.design_space.dim_reduction import *
from scripts.design_space.dspace_dist_metrics import *
from scripts.design_space.design_space import *
from scripts.design_space.dspace_metrics import *
from scripts.design_space.dspace_metric_novelty import *
from scripts.design_space.dspace_viz_density import *
from scripts.design_space.dspace_cluster import *
from scripts.design_space.dspace_viz_landscape import *

#* --- initial definitions ------
cwd = Path.cwd()
my_dir = cwd.joinpath('data')                                                # path to the data file
filenm = 'MASKED_DATA_analysis_v1.xlsx'                                                 # name of the data file
sheetnm = 'ExpData-100R-Expanded'                                                       # sheet where the data (analysis) is
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
save_dir = cwd.joinpath('data').joinpath('json')
#* ------------------------------

#%%
#! get & process data

print(cwd)
#* reads Excel file with solutions' analysis
df_base, df_colors, labels = read_analysis(my_dir, filenm, sheetname=sheetnm)

#* calculates distance matrix
n_distmatrix = calc_distmatrix(df_base, my_dir, filenm)

#* generate the embedding of the distance matrix
embedding, graph = create_embedding(my_dir, n_distmatrix, embed_name='nep', Wg='W2', NN=85, MD=0.25, densm=3    )

#* unmask data
df_base, df_colors = unmask_data(my_dir, 'MASKING_KEYS', df_base, df_colors)

#* prepare main df
df_base['x_emb'] = embedding[:, 0]
df_base['y_emb'] = embedding[:, 1]
ids_m = df_base['ParticipantID'].unique()

df_col = df_colors[['P','HEX-Win']].copy()
df_base = df_base.merge(df_col, left_on='ParticipantID', right_on='P').copy()

#* sort NaNs from gallery
df_base['OriginalID_PT'] = df_base.apply(   lambda row: row.OriginalID_PT if str(row.OriginalID_PT) != 'nan' else
                                            'GALL', axis=1)

df_base['OriginalID_Group'] = df_base.apply(   lambda row: row.OriginalID_Group if str(row.OriginalID_Group) != 'nan' else
                                            'GALL', axis=1)

df_base['OriginalID_Sol'] = df_base.apply(   lambda row: row.OriginalID_Sol if str(row.OriginalID_Sol) != 'nan' else
                                            row.SolutionID, axis=1)

df_base['OriginalID_PrePost'] = df_base.apply(   lambda row: row.OriginalID_PrePost if str(row.OriginalID_PrePost) != 'nan' else
                                            'GALL', axis=1)

ids = sorted(list(df_base['OriginalID_PT'].unique())) #! --> goes to dropdown in chart

#* core attributes
# solution
df_base['ca_sol'] = df_base.apply(  lambda row: row.type + ' | ' + str(row.numAnchorsUsed) +
                                    ' anchors', axis=1)

df_base['ca_deck'] = df_base.apply( lambda row: row.deckType_2 + ' | shape: ' + row.deckShape_1 +
                                    ' ' + row.deckShape_2 + ' ' + row.deckShape_3 + ' ' + row.deckShape_4
                                    if row.deckType_2 == 'fully_connected' else
                                    row.deckType_1 + ' ' + row.deckType_2 + ' | shape: ' + row.deckShape_1 +
                                    ' ' + row.deckShape_2 + ' ' + row.deckShape_3 + ' ' + row.deckShape_4,
                                    axis=1).str.replace(' -','')

df_base['ca_str'] = df_base.apply(  lambda row: row.structurePosition_Top + ' ' + row.structurePosition_Rock +
                                    ' ' + row.structurePosition_Bottom + ' | shape: ' + row.structureShape_1 +
                                    ' ' + row.structureShape_2 + ' | size: ' + row.structureSize,
                                    axis=1).str.replace(' no_structure','').str.replace('_structure','').str.replace('-','').str.replace('no ','')

df_base['ca_rck'] = df_base.apply(  lambda row: row.rockSupportShape + ' | ' + row.rockSupportMat
                                    if row.rockSupportShape != 'no_support' else
                                    row.rockSupportShape, axis=1)

df_base['ca_road'] = df_base.apply( lambda row: 'road' if row.materialRoad == 'yes' else
                                    '-no-', axis=1)

df_base['ca_rroad'] = df_base.apply( lambda row: 'reinforced road' if row.materialReinfRoad == 'yes' else
                                    '-no-', axis=1)

df_base['ca_wood'] = df_base.apply( lambda row: 'wood' if row.materialWood == 'yes' else
                                    '-no-', axis=1)

df_base['ca_steel'] = df_base.apply( lambda row: 'steel' if row.materialSteel == 'yes' else
                                    '-no-', axis=1)

df_base['ca_mtr'] = df_base.apply(  lambda row: row.ca_road + ' ' + row.ca_rroad + ' ' + row.ca_wood +
                                    ' ' + row.ca_steel, axis=1).str.replace('-no- ','').str.replace(' -no-','')

df_base['ca_perf'] = df_base.apply( lambda row: 0 if row.result == 'fail' else 1, axis=1)

df_base['performance'] = df_base.apply( lambda row: row.ca_perf * (15000/row.budgetUsed), axis=1)

df_base['fullid_orig'] = df_base.apply( lambda row: row.OriginalID_PT + '-' + row.OriginalID_PrePost + '-' +
                                        str(row.OriginalID_Sol), axis=1).str.replace('.0','')

#! get solution summary
df_sol = solutions_summary(save_dir, saveExcel=False)
df_base = df_base.merge(df_sol, how='left', on='fullid_orig')

# sort NaNs
df_base['TLength'] = df_base.apply(   lambda row: row.TLength if str(row.TLength) != 'nan' else
                                            'N/A', axis=1)
df_base['NSegm'] = df_base.apply(   lambda row: row.NSegm if str(row.NSegm) != 'nan' else
                                            'N/A', axis=1)
df_base['NJoint'] = df_base.apply(   lambda row: row.NJoint if str(row.NJoint) != 'nan' else
                                            'N/A', axis=1)

#%%
#! get creativity metrics

#! distance metrics
#* distance matrix from embed
n_distmatrix_emb = create_dmatrix_from_embed(my_dir, embedding, norm=False)                 # get dist matrix from embedding

df_dist_emb, pt_unq = dist_metrics_fs(df_base, n_distmatrix_emb)                # distance summary embedding FS
df_dist_emb = dist_metrics_pre(df_base, df_dist_emb, pt_unq, n_distmatrix_emb)  # distance summary embedding PRE
df_dist_emb = dist_metrics_post(df_base, df_dist_emb, pt_unq, n_distmatrix_emb) # distance summary embedding POST

df_dist_emb = df_dist_emb.drop(columns=['OriginalID_Group', 'maxdist_FS', 'maxdist_PRE', 'maxdist_PST',
                                        'dist_PRE_POST', 'avgdist_FS', 'avgdist_PRE', 'avgdist_PST'])

df_base = df_base.merge(df_dist_emb, how='left', on='OriginalID_PT')

# sort NaNs
nan_cols = df_dist_emb.columns[1:].tolist()

for col in nan_cols:
    df_base[col] = df_base.apply(   lambda row: row[col] if str(row[col]) != 'nan' else
                                                'N/A', axis=1)

#! area metrics
#* create and plot convex hull
DS_area, pt_cvxh, df_metrics_fs, df_metrics_pre, df_metrics_post, df_ds_verts = create_cvxh(my_dir, df_base, embedding, df_colors, save_plot=False)

# set mode for metrics
mode_metrics = 'all'

#* get DS coverage metrics per participant
df_DS_coverage = area_summary(df_base, DS_area, df_metrics_fs, mode=mode_metrics, df_ch_pre_metrics=df_metrics_pre, df_ch_post_metrics=df_metrics_post)
df_DS_coverage = df_DS_coverage.drop(columns=['GroupID', 'Area-KYY', 'Area-ZSB', 'Area-FS'])

df_base = df_base.merge(df_DS_coverage, how='left', on='ParticipantID')
df_base = df_base.rename(columns={'Area-Perc-KYY': 'Area-Perc-PRE', 'Area-Perc-ZSB': 'Area-Perc-POST'})

# sort NaNs
df_base['Area-Perc-PRE'] = df_base.apply(   lambda row: row['Area-Perc-PRE'] if str(row['Area-Perc-PRE']) != 'nan' else
                                            'N/A', axis=1)
df_base['Area-Perc-POST'] = df_base.apply(   lambda row: row['Area-Perc-POST'] if str(row['Area-Perc-POST']) != 'nan' else
                                            'N/A', axis=1)
df_base['Area-Perc-FS'] = df_base.apply(   lambda row: row['Area-Perc-FS'] if str(row['Area-Perc-FS']) != 'nan' else
                                            'N/A', axis=1)

#! novelty metrics

# novelty from density plot
df_kde, lim_x, lim_y = prep_density(df_base, embedding)

df_novel = novelty_from_density(my_dir, df_kde, lim_x, lim_y)
df_novel = df_novel.drop(columns=['GroupID', 'ParticipantID', 'GroupID', 'PrePost',
                                    'result', 'type', 'x_emb', 'y_emb'])

df_base = df_base.merge(df_novel, how='left', on='FullID')

# novelty number of neighbors
novel_nn = novelty_from_neig(my_dir, df_base, embedding, delta=0.9)
novel_nn = novel_nn.drop(columns=['GroupID', 'ParticipantID', 'GroupID', 'PrePost',
                                    'result', 'type', 'x_emb', 'y_emb'])

df_base = df_base.merge(novel_nn, how='left', on='FullID')

#! cluster metrics
df_base = get_clusters(df_base, graph)
#%%
symb = list(range(1,17))
symb_ls = ['circle', 'diamond', 'cross', 'x', 'pentagon',
            'hexagon', 'star',  'hexagram', 'star-triangle-up',
            'star-triangle-down','star-square', 'star-diamond', 'diamond-tall',
            'diamond-wide','circle-open','square']

df_symb = pd.DataFrame({'cluster_id': symb, 'clust_symb':symb_ls})
df_base = df_base.merge(df_symb, how='left', on='cluster_id')

tot_clust = []
pre_clust = []
post_clust = []
for pt in ids[1:]:
    tot_clust.append(len(df_base[df_base['OriginalID_PT']==pt]['cluster_id'].unique()))
    pre_clust.append(len(df_base[(df_base['OriginalID_PT']==pt) & (df_base['OriginalID_PrePost']=='Pre')]['cluster_id'].unique()))
    post_clust.append(len(df_base[(df_base['OriginalID_PT']==pt) & (df_base['OriginalID_PrePost']=='Pst')]['cluster_id'].unique()))

df_clust_summ = pd.DataFrame({'OriginalID_PT': ids[1:], 'n_clusters': tot_clust,
                                'n_clusters_pre': pre_clust, 'n_clusters_post': post_clust})

df_base = df_base.merge(df_clust_summ, how='left', on='OriginalID_PT')

df_base['hovertxt'] = df_base.apply(lambda row: f"<b>{row['OriginalID_PT']} | Sol. {row['OriginalID_Sol']}</b><br>{row['OriginalID_PrePost']} | {row['result']}" , axis=1).str.replace('.0','')

#plot_landscape(my_dir, df_base, embedding)

#%% #! PLOTS
#! create plot main DS
fig_DS = go.Figure()

#! add cvx hull
#* full DS cvxh
# get vertices and area
fullds_xvt, fullds_yvt, cvarea = cv_hull_vertices(x=df_base['x_emb'], y=df_base['y_emb'])
DS_Area = cvarea    #! DS total area

# add cvx hull
# convexhull full DS
fig_DS.add_trace(go.Scatter(    x=fullds_xvt,
                                y=fullds_yvt,
                                mode='lines',
                                fill='toself',
                                hoverinfo='skip',
                                marker=dict(
                                    size=8,
                                    color='rgba(240,240,240,0.5)'
                                ),
                                name='full_cvxh'),
                            )

#! add traces for individual cvxhulls
def hex_rgba(h, alpha):
    h=h.lstrip('#')
    rgb_v = tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
    rgba_v = f'({rgb_v[0]}, {rgb_v[1]}, {rgb_v[2]}, {alpha})'
    return rgba_v

for pt in ids:
    x_vals = list(df_base[df_base['OriginalID_PT'] == pt]['x_emb'])
    y_vals = list(df_base[df_base['OriginalID_PT'] == pt]['y_emb'])


    # 2D array of points that make up convex hull
    cvh_vtx = np.array(shapely.geometry.MultiPoint(
        [xy for xy in zip(x_vals, y_vals)]).convex_hull.exterior.coords)

    c_fill_cvxh = hex_rgba(list(df_base[df_base['OriginalID_PT'] == pt]['HEX-Win'])[0], 0.1)
    c_fill_line = hex_rgba(list(df_base[df_base['OriginalID_PT'] == pt]['HEX-Win'])[0], 0.3)

    #pt_xvt, pt_yvt, cvarea = cv_hull_vertices(x=x_vals, y=y_vals)

    fig_DS.add_trace(go.Scatter(x=cvh_vtx[:,0],
                                y=cvh_vtx[:,1],
                                mode='lines',
                                fill='toself',
                                hoverinfo='skip',
                                line=dict(
                                    color=f'rgba{c_fill_line}', width=1
                                ),
                                fillcolor=f'rgba{c_fill_cvxh}',
                                name=f'{pt}_cvxh'),
                            )

#! add arrows
for pt in ids[1:31]:
    df_pt_sorted = df_base[df_base['OriginalID_PT'] == pt].sort_values(by='OriginalID_Sol')
    x_vs = df_pt_sorted['x_emb'].reset_index(drop=True)
    y_vs = df_pt_sorted['y_emb'].reset_index(drop=True)

    c_fill_line = hex_rgba(list(df_base[df_base['OriginalID_PT'] == pt]['HEX-Win'])[0], 0.5)

    fig_DS.add_trace(go.Scatter(x=x_vs,
                                y=y_vs,
                                mode='lines+markers',
                                hoverinfo='skip',
                                marker= dict(   symbol="arrow-up",
                                                size=8,
                                                angleref="previous",
                                                color=f'rgba{c_fill_line}'),
                                name=f'{pt}_arrows')
                                )


#! full set of points
fig_DS.add_trace(go.Scatter(    x=df_base['x_emb'],
                                y=df_base['y_emb'],
                                #customdata=,
                                hovertemplate=df_base['hovertxt'],
                                mode='markers',
                                marker=dict(
                                size=7,
                                color=df_base['HEX-Win'],
                                symbol=df_base['clust_symb'],
                                line=dict(color=df_base['HEX-Win'])),
                                name=''),
                            )


# update graph layout
fig_DS.update_layout(   autosize=False,
                        width=725,
                        height=650,
                        margin=dict(
                            l=25,
                            r=25,
                            b=25,
                            t=25,
                            pad=2
                        ),
                        #xaxis=dict(scaleanchor='x', scaleratio=0.5),
                        #yaxis=dict(scaleanchor='x', scaleratio=0.425),
                        showlegend=False,
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor='white'
                        )



#! create performance graph

fig_PF = go.Figure()

fig_PF.add_vline(x=5.5, line_width=2, line_dash="dash", line_color="darkgrey")

for pt in ids[1:31]:
    x_vals = list(range(1, len(df_base[df_base['OriginalID_PT'] == pt])+1))
    y_vals = df_base[df_base['OriginalID_PT'] == pt].sort_values(by='OriginalID_Sol')['performance'].to_list()
    clust_sym = df_base[df_base['OriginalID_PT'] == pt].sort_values(by='OriginalID_Sol')['clust_symb'].to_list()

    cl = df_base[df_base['OriginalID_PT'] == pt ]['HEX-Win'].to_list()[0]

    fig_PF.add_trace(go.Scatter(x=x_vals,
                                y=y_vals,
                                mode='lines+markers',
                                name=pt,
                                opacity=0.7,
                                line=dict(color=cl),
                                marker=dict(
                                size=7,
                                color=cl,
                                symbol=clust_sym,
                                line=dict(color=cl)),
                                )
    )

fig_PF.add_hline(y=1, line_width=2, line_dash="dot", line_color="black")

fig_PF.update_layout(   autosize=True,
                        #width=725,
                        height=300,
                        margin=dict(
                            l=5,
                            r=5,
                            b=5,
                            t=5,
                            pad=2
                        ),
                        xaxis = dict(
                            tickmode = 'linear',
                            dtick = 1),
                        showlegend=False,
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor='white'
                        )

ls_trace_id = []
for i, trace in enumerate(fig_PF['data']):
    ls_trace_id.append([trace['name'], i])
print('here')
#%% #!DASH LAYOUT
app = Dash(__name__, external_stylesheets=external_stylesheets)
server = app.server

# app layout
app.layout = html.Div([ #! Div 1 - BG
    html.Div([ #! Div 2 - Title
        html.H3('DS-Viz Interactive Tool | GAP Dataset')],
        style={'width': '74%', 'display': 'inline-block'}),

    html.Div([ #! Div 3 - Reach Out
        html.A('more info', href='https://doi.org/10.17863/CAM.105967', target='_blank'),
        ' | ',
        html.A('github', href='https://github.com/epz0/DS_Viz', target='_blank'),
        ' | ',
        html.A('email', href='mailto:ep650@cam.ac.uk', target='_blank')],
        style={'width': '24%', 'textAlign': 'right', 'float':'right', 'display': 'inline-block'}),

    html.Div([ #! Div 4 - Main DS Viz
        html.Div([ #! Div 5 - Checkbox show elements
            html.Label('Show:'),
            dcc.Checklist(  ['Points', 'Arrows', 'Areas'],
                            ['Points', 'Arrows', 'Areas'],
                            id='show-element-type',                                             #! defines what traces to add to the scatter
                            labelStyle={'display': 'inline-block', 'marginTop': '5px','marginRight': '10px' }
                        )],
            style={'width': '49%', 'float': 'left', 'display': 'inline-block'}),

        html.Div([ #! Div 6 - Dropdown show participants
            html.Label('Participants:'),
            dcc.Dropdown(   ids,
                            'Show participants...',
                            multi=True,
                            id='show-participant',                                              #! defines what traces to add to the scatter
                        )],
            style={'width': '35%', 'float': 'right', 'display': 'inline-block'}),

        html.Div([ #! Div 7 - DS Chart
            dcc.Graph(
                id='main-ds-viz',
                figure=fig_DS,
                style={'width': '99vw', 'height': '83vw'}
            )],
            style={'width': '99%', 'float': 'right', 'display': 'inline-block'})

    ],
    id = "main-div",
    style={'width': '49%', 'float': 'left', 'display': 'inline-block'}), #! close Div 4

    html.Div([ #! Div 8 - Detail Panels

        html.Div([ #! Div 9 - Solution Overview

            html.Div([ #! Div 9.1 - Participant, Group, Intervention

                html.Div([ #! Div 9.1.1 - Participant
                'Participant: ',
                html.Label('P_XXX',
                            id= 'participant-id',
                            style={'display': 'inline-block'})
                ],
                style={'width': '32%', 'textAlign': 'left', 'float': 'left', 'display': 'inline-block'}),

                html.Div([ #! Div 9.1.2 - Group
                'Group: ',
                html.Label('CTRL',
                            id= 'group-id',
                            style={'display': 'inline-block'})
                ],
                style={'width': '32%', 'textAlign': 'center', 'display': 'inline-block'}),

                html.Div([ #! Div 9.1.3 - Intervention
                html.Label('PRE',
                            id= 'intervention-id',
                            style={'display': 'inline-block'}),
                ' intervention'
                ],
                style={'width': '32%', 'textAlign': 'right', 'float': 'right', 'display': 'inline-block'}),
            ],
            style={'width': '99%', 'display': 'inline-block'}), #! close Div 9.1

        html.Div([ #! Div 9.2 - Solution
            html.H5("Solution_",
                    style={'textAlign': 'center', 'display': 'inline-block'}),

            html.H5("99",
                    id='solution-id',
                    style={'textAlign': 'center','display': 'inline-block'})
        ],
        style={'width': '99%', 'textAlign': 'center', 'display': 'inline-block'}), #! close Div 9.2

            html.Div([ #! Div 9.3 - Result, Cost, Max Stress
                html.Div([ #! Div 9.3.1 - Result
                    'Result: ',
                    html.Label('FAIL',
                                id= 'result-id',
                                style={'display': 'inline-block'})
                    ],
                    style={'width': '32%', 'textAlign': 'left', 'float': 'left', 'display': 'inline-block'}),

                    html.Div([ #! Div 9.3.2 - Cost
                    'Cost: $ ',
                    html.Label('99,999.9',
                                id= 'cost-id',
                                style={'display': 'inline-block'})
                    ],
                    style={'width': '32%', 'textAlign': 'center', 'display': 'inline-block'}),

                    html.Div([ #! Div 9.3.3 - Max Stres
                    'Max Stress (%): ',
                    html.Label('100.0',
                                id= 'max-stress-id',
                                style={'display': 'inline-block'})
                    ],
                    style={'width': '32%', 'textAlign': 'right', 'float': 'right', 'display': 'inline-block'}),
                ],
                style={'width': '99%', 'display': 'inline-block'}), #! close Div 9.3

            html.Div([ #! Div 9.4 - Total length, #nodes, # segments
                html.Div([ #! Div 9.4.1 - Result
                    'Total length (m): ',
                    html.Label('99.9',
                                id= 'total-length-id',
                                style={'display': 'inline-block'})
                    ],
                    style={'width': '32%', 'textAlign': 'left', 'float': 'left', 'display': 'inline-block'}),

                    html.Div([ #! Div 9.4.2 - nodes
                    '# nodes: ',
                    html.Label('99',
                                id= 'nnodes-id',
                                style={'display': 'inline-block'})
                    ],
                    style={'width': '32%', 'textAlign': 'center', 'display': 'inline-block'}),

                    html.Div([ #! Div 9.4.3 - segments
                    '# segments: ',
                    html.Label('99',
                                id= 'nsegments-id',
                                style={'display': 'inline-block'})
                    ],
                    style={'width': '32%', 'textAlign': 'right', 'float': 'right', 'display': 'inline-block'}),
                ],
                style={'width': '99%', 'display': 'inline-block'}), #! close Div 9.4

        ],
        style={'width': '99%', 'display': 'inline-block'}), #! close Div 9

        html.Br(),
        html.Br(),

        html.Div([ #! Div 10 - Solution Screenshot
            html.Div([ #! Div 11 - radio abstract/screenshot
                        dcc.RadioItems(
                        ['Screenshot'],
                        'Screenshot',
                        id='solution-image-type',
                        labelStyle={'display': 'inline-block', 'marginTop': '5px','marginRight': '10px'},
                    )
                    ],
                    style={'width': '99%', 'float': 'left', 'display': 'inline-block'}),

            html.Img(
                style={'width': '95%'},
                id='image-src-id',
                src='https://raw.githubusercontent.com/epz0/bridgespace/main/img/P_001-Pre-01.png')
                ],

        style={'width': '49%', 'display': 'inline-block'}), #! close Div 10


        html.Div([ #! Div 12 - Solution Details
            html.H6('Core Attributes'),

            html.Div([ #! Div 12.1 Solution
                'Solution: ',
                html.Label('bridge | 3 anchors',
                    id= 'ca-solution-id',
                    style={'display': 'inline-block'})
            ],
            style={'width': '99%', 'display': 'inline-block'}), #! close Div 12.1

            html.Div([ #! Div 12.2 Deck
                'Deck: ',
                html.Label('missing middle | shape: straight, ramp, declined',
                    id= 'ca-deck-id',
                    style={'display': 'inline-block'})
            ],
            style={'width': '99%', 'display': 'inline-block'}), #! close Div 12.2

            html.Div([ #! Div 12.3 Structure
                'Structure: ',
                html.Label('top, rock, bottom | shape: standard truss, other | size: medium',
                    id= 'ca-structure-id',
                    style={'display': 'inline-block'})
            ],
            style={'width': '99%', 'display': 'inline-block'}), #! close Div 12.3

            html.Div([ #! Div 12.4 Rock Support
                'Rock Support: ',
                html.Label('multiple beams, multiple materials',
                    id= 'ca-rocksupport-id',
                    style={'display': 'inline-block'})
            ],
            style={'width': '99%', 'display': 'inline-block', 'verticalAlign':'top'}), #! close Div 12.4

            html.Div([ #! Div 12.5 Materials
                'Materials: ',
                html.Label('road, reinforced road, wood, steel',
                    id= 'ca-material-id',
                    style={'display': 'inline-block'})
            ],
            style={'width': '99%', 'display': 'inline-block'}), #! close Div 12.5
        ],
        style={'width': '49%', 'display': 'inline-block'}), #! Close Div 12

        html.Br(),
        html.Br(),

        html.Div([ #! Div 13 - performance plot
            dcc.Graph(
                id='performance-graph',
                figure=fig_PF,
            )

            ], style={'width': '49%', 'height':'75%', 'float':'left', 'verticalAlign': 'top', 'display': 'inline-block'}), #! close Div 13

        html.Div([ #! Div 14 - metrics
            html.H6('Space Exploration / Creativity metrics'),

            html.Div([ #! Div 14.1 Area
                'Area explored | Tot.: ',
                html.Label('Atot',
                    id= 'metrics-area-total-id',
                    style={'display': 'inline-block'}),
                    ' | Pre: ',
                html.Label('Apre',
                    id= 'metrics-area-pre-id',
                    style={'display': 'inline-block'}),
                ' | Post: ',
                html.Label('Apost',
                    id= 'metrics-area-post-id',
                    style={'display': 'inline-block'}),
            ], style={'width': '99%', 'display': 'inline-block'}), #! close Div 14.1

            html.Div([ #! Div 14.2 Distance
                'Distance travel. | Total: ',
                html.Label('Dtot',
                    id= 'metrics-distance-total-id',
                    style={'display': 'inline-block'}),
                ' | Pre: ',
                html.Label('Dpre',
                    id= 'metrics-distance-pre-id',
                    style={'display': 'inline-block'}),
                ' | Post: ',
                html.Label('Dtot',
                    id= 'metrics-distance-post-id',
                    style={'display': 'inline-block'}),
            ], style={'width': '99%', 'display': 'inline-block'}), #! close Div 14.2

            html.Div([ #! Div 14.4 Number of Clusters
                '# Clusters visit. | Total: ',
                html.Label('Clst',
                    id= 'metrics-clusters-id',
                    style={'display': 'inline-block'}),
                ' | Pre: ',
                html.Label('Cpre',
                    id= 'metrics-clusters-pre-id',
                    style={'display': 'inline-block'}),
                ' | Post: ',
                html.Label('Ctot',
                    id= 'metrics-clusters-post-id',
                    style={'display': 'inline-block'}),
            ], style={'width': '99%', 'display': 'inline-block'}), #! close Div 14.4

            html.Div([ #! Div 14.3 Novelty
                'Novelty | Neighbors: ',
                html.Label('Nneig',
                    id= 'metrics-novelty-neig-id',
                    style={'display': 'inline-block'}),
                ' | Denstity: ',
                html.Label('Ndens',
                    id= 'metrics-novelty-dens-id',
                    style={'display': 'inline-block'}),

            ], style={'width': '99%', 'display': 'inline-block'}), #! close Div 14.3


            html.Div([ #! Div 14.5 Performance
                'Solution Performance: ',
                html.Label('XXX',
                    id= 'metrics-performance-id',
                    style={'display': 'inline-block'})
            ], style={'width': '99%', 'display': 'inline-block'}), #! close Div 14.5

            ], style={'width': '49%', 'display': 'inline-block'}), #! close Div 14


        dcc.Interval(
        id='interval-component',
        interval=1*1000,  # Check every second
        n_intervals=0
        ),
        ],

        style={'width': '49%', 'float': 'right', 'display': 'inline-block'}) #! Close Div 8

]) #! Close Div 1


#! CALLBACKS

#! --------------- screenshot update
@callback(
    Output('image-src-id', 'src'),              #* 11.
    Input('main-ds-viz', 'clickData'),
    Input('performance-graph', 'clickData'),
    prevent_initial_call=True)

#!!!!!!!!!!!!!!!!!!!!!!!!!!
def update_solution_screenshot(clickData_m, clickData_p):
    last_click = ctx.triggered_id

    #idx = clickData_m['points'][0]['pointIndex']
    #pat_id = df_base.loc[idx,'OriginalID_PT']

    if last_click == 'main-ds-viz':
        clickedSol = clickData_m['points'][0]['pointIndex']

    elif last_click == 'performance-graph':
        x_perf = clickData_p['points'][0]['x']
        pat_id = ids[clickData_p['points'][0]['curveNumber']+1]
        pat_id_n = clickData_p['points'][0]['curveNumber']

        if x_perf is None:
            PreventUpdate
        else:
            clickedSol = df_base[(df_base['OriginalID_PT'] == pat_id) & (df_base['OriginalID_Sol'] == x_perf)].index[0]
            selecSol = x_perf-1

    if clickedSol is None:
        raise PreventUpdate
    else:
        image_link = df_base.loc[clickedSol,'videoPreview']
        return image_link

#! --------------- participant info update
@callback(
    Output('participant-id', 'children'),       #* 9.1.1
    Output('group-id', 'children'),             #* 9.1.2
    Output('intervention-id', 'children'),      #* 9.1.3

    Output('solution-id', 'children'),          #* 9.2

    Output('result-id', 'children'),            #* 9.3.1
    Output('cost-id', 'children'),              #* 9.3.2
    Output('max-stress-id', 'children'),        #* 9.3.3

    Input('main-ds-viz', 'clickData'),
    Input('performance-graph', 'clickData'),
    prevent_initial_call=True)

def update_participantinfo(clickData_m, clickData_p):
    last_click = ctx.triggered_id

    #idx = clickData_m['points'][0]['pointIndex']
    #pat_id = df_base.loc[idx,'OriginalID_PT']

    if last_click == 'main-ds-viz':
        clickedSol = clickData_m['points'][0]['pointIndex']

    elif last_click == 'performance-graph':
        x_perf = clickData_p['points'][0]['x']
        pat_id = ids[clickData_p['points'][0]['curveNumber']+1]
        pat_id_n = clickData_p['points'][0]['curveNumber']

        if x_perf is None:
            PreventUpdate
        else:
            clickedSol = df_base[(df_base['OriginalID_PT'] == pat_id) & (df_base['OriginalID_Sol'] == x_perf)].index[0]
            selecSol = x_perf-1

    if clickedSol is None:
        raise PreventUpdate
    else:
        pt_id = df_base.loc[clickedSol,'OriginalID_PT']
        gp_id = df_base.loc[clickedSol,'OriginalID_Group']
        int_id = df_base.loc[clickedSol,'OriginalID_PrePost']
        sol = df_base.loc[clickedSol,'OriginalID_Sol']
        res = df_base.loc[clickedSol,'result']
        cost = df_base.loc[clickedSol,'budgetUsed']
        cost = f'{cost:,}'
        mst = df_base.loc[clickedSol,'maxStress']
        mst = f'{mst:.1f}'
        return pt_id, gp_id, int_id, sol, res, cost, mst

#! ------------- solution info update
@callback(
    Output('total-length-id', 'children'),      #* 9.4.1
    Output('nnodes-id', 'children'),            #* 9.4.2
    Output('nsegments-id', 'children'),         #* 9.4.3

    Output('ca-solution-id', 'children'),       #* 12.1
    Output('ca-deck-id', 'children'),           #* 12.2
    Output('ca-structure-id', 'children'),      #* 12.3
    Output('ca-rocksupport-id', 'children'),    #* 12.4
    Output('ca-material-id', 'children'),       #* 12.5

    Input('main-ds-viz', 'clickData'),
    Input('performance-graph', 'clickData'),
    prevent_initial_call=True)

def update_solutioninfo(clickData_m, clickData_p):
    last_click = ctx.triggered_id

    #idx = clickData_m['points'][0]['pointIndex']
    #pat_id = df_base.loc[idx,'OriginalID_PT']

    if last_click == 'main-ds-viz':
        clickedSol = clickData_m['points'][0]['pointIndex']

    elif last_click == 'performance-graph':
        x_perf = clickData_p['points'][0]['x']
        pat_id = ids[clickData_p['points'][0]['curveNumber']+1]
        pat_id_n = clickData_p['points'][0]['curveNumber']

        if x_perf is None:
            PreventUpdate
        else:
            clickedSol = df_base[(df_base['OriginalID_PT'] == pat_id) & (df_base['OriginalID_Sol'] == x_perf)].index[0]
            selecSol = x_perf-1

    if clickedSol is None:
        raise PreventUpdate
    else:
        ca_sol_id = df_base.loc[clickedSol,'ca_sol']
        ca_deck_id = df_base.loc[clickedSol,'ca_deck']
        ca_str_id = df_base.loc[clickedSol,'ca_str']
        ca_rck_id = df_base.loc[clickedSol,'ca_rck']
        ca_mtr_id = df_base.loc[clickedSol,'ca_mtr']

        tlength_id = df_base.loc[clickedSol,'TLength']
        if isinstance(tlength_id, str) == False:
            tlength_id = f'{tlength_id:.1f}'

        nodes_id = df_base.loc[clickedSol,'NSegm']
        segms_id = df_base.loc[clickedSol,'NJoint']

        return tlength_id, nodes_id, segms_id, ca_sol_id, ca_deck_id, ca_str_id, ca_rck_id, ca_mtr_id


#! --------------- participant info update
@callback(
    Output('metrics-area-total-id', 'children'),        #* 14.1
    Output('metrics-area-pre-id', 'children'),          #* 14.1
    Output('metrics-area-post-id', 'children'),         #* 14.1

    Output('metrics-distance-total-id', 'children'),    #* 14.2
    Output('metrics-distance-pre-id', 'children'),      #* 14.2
    Output('metrics-distance-post-id', 'children'),     #* 14.2

    Output('metrics-novelty-neig-id', 'children'),      #* 14.3
    Output('metrics-novelty-dens-id', 'children'),      #* 14.3

    Output('metrics-clusters-id', 'children'),          #* 14.4
    Output('metrics-clusters-pre-id', 'children'),      #* 14.4
    Output('metrics-clusters-post-id', 'children'),     #* 14.4

    Output('metrics-performance-id', 'children'),       #* 14.5


    Input('main-ds-viz', 'clickData'),
    Input('performance-graph', 'clickData'),
    prevent_initial_call=True)

def update_creativityinfo(clickData_m, clickData_p):
    last_click = ctx.triggered_id

    #idx = clickData_m['points'][0]['pointIndex']
    #pat_id = df_base.loc[idx,'OriginalID_PT']

    if last_click == 'main-ds-viz':
        clickedSol = clickData_m['points'][0]['pointIndex']

    elif last_click == 'performance-graph':
        x_perf = clickData_p['points'][0]['x']
        pat_id = ids[clickData_p['points'][0]['curveNumber']+1]
        pat_id_n = clickData_p['points'][0]['curveNumber']


        if x_perf is None:
            PreventUpdate
        else:
            clickedSol = df_base[(df_base['OriginalID_PT'] == pat_id) & (df_base['OriginalID_Sol'] == x_perf)].index[0]
            selecSol = x_perf-1

    if clickedSol is None:
        raise PreventUpdate
    else:
        gall = df_base.loc[clickedSol,'GroupID']
        if gall == 'Gallery':
            atot = f"{df_base.loc[clickedSol,'Area-Perc-FS']}"
            apre = f"{df_base.loc[clickedSol,'Area-Perc-PRE']}"
            apost = f"{df_base.loc[clickedSol,'Area-Perc-POST']}"
            dtot = f"{df_base.loc[clickedSol,'totaldist_FS']}"
            dpre = f"{df_base.loc[clickedSol,'totaldist_PRE']}"
            dpost = f"{df_base.loc[clickedSol,'totaldist_PST']}"
            clust = 'N/A'
            clust_pre = 'N/A'
            clust_post = 'N/A'

        else:
            perf = f"{df_base.loc[clickedSol,'performance']:.2f}"
            atot = f"{df_base.loc[clickedSol,'Area-Perc-FS']:.1f}%"
            apre = f"{df_base.loc[clickedSol,'Area-Perc-PRE']:.1f}%"
            apost = f"{df_base.loc[clickedSol,'Area-Perc-POST']:.1f}%"
            dtot = f"{df_base.loc[clickedSol,'totaldist_FS']:.1f}"
            dpre = f"{df_base.loc[clickedSol,'totaldist_PRE']:.1f}"
            dpost = f"{df_base.loc[clickedSol,'totaldist_PST']:.1f}"
            clust = f"{df_base.loc[clickedSol,'n_clusters']:.0f}"
            clust_pre = f"{df_base.loc[clickedSol,'n_clusters_pre']:.0f}"
            clust_post = f"{df_base.loc[clickedSol,'n_clusters_post']:.0f}"

        novneig = f"{df_base.loc[clickedSol,'novel_nn']:.2f}"
        novdens = f"{df_base.loc[clickedSol,'novelty_norm']:.2f}"

        perf = f"{df_base.loc[clickedSol,'performance']:.2f}"

        return atot, apre, apost, dtot, dpre, dpost, novneig, novdens, clust, clust_pre, clust_post, perf


#! ---------- performance chart update on solution clicked --> showing only trace for participant
@callback(
    Output('performance-graph', 'figure'),      #* 13

    Input('main-ds-viz', 'clickData'),
    Input('performance-graph', 'clickData'),

    State('performance-graph', 'figure'),
    prevent_initial_call=True)

def update_performance_graph(clickData_m, clickData_p, fig_state):
    # traces 0-30 for each participant

    last_click = ctx.triggered_id
    patched_figure = Patch()

    #idx = clickData_m['points'][0]['pointIndex'] #when click on the cvx area (not on point, raises error)
    #if idx is None:
    #    PreventUpdate
    #else:
    #    pat_id = df_base.loc[idx,'OriginalID_PT']

    # get right solution from performance graph
    if last_click == 'main-ds-viz':
        clickedSol = clickData_m['points'][0]['pointIndex']
        pat_id = df_base.loc[clickedSol,'OriginalID_PT']
        pat_id_n = ids.index(pat_id)-1

        #print(clickedSol)
        if clickedSol is None:
            PreventUpdate
        else:
            if df_base.loc[clickedSol,'OriginalID_PT'] != 'GALL':
                selecSol = df_base.loc[clickedSol,'OriginalID_Sol']-1 #?????

    elif last_click == 'performance-graph':
        x_perf = clickData_p['points'][0]['x']
        pat_id = ids[clickData_p['points'][0]['curveNumber']+1]
        pat_id_n = clickData_p['points'][0]['curveNumber']


        if x_perf is None:
            PreventUpdate
        else:
            clickedSol = df_base[(df_base['OriginalID_PT'] == pat_id) & (df_base['OriginalID_Sol'] == x_perf)].index[0]
            selecSol = x_perf-1
            #print(x_perf, clickedSol)

    if clickedSol is None:
        print('clicksol none')
        raise PreventUpdate
    else:
        pt_focus = df_base.loc[clickedSol,'OriginalID_PT']

        if pt_focus == 'GALL':

            for tr in range(30):
                patched_figure['data'][tr]['visible'] = 'legendonly'

            #move vline to (0,0)
            patched_figure['layout']['shapes'][0]['x0']=0
            patched_figure['layout']['shapes'][0]['x1']=0

            return patched_figure

        else:
            #trace_id = [elm for elm in ls_trace_id if elm[0] == pt_focus][0][1]

            #patched_figure['data'].clear()

            #moving vline to intervention point
            int_pt = len(df_base[(df_base['OriginalID_PT']==pt_focus) & (df_base['OriginalID_PrePost']=='Pre')])+0.5
            patched_figure['layout']['shapes'][0]['x0']=int_pt
            patched_figure['layout']['shapes'][0]['x1']=int_pt

            for tr in range(30):
                patched_figure['data'][tr]['visible'] = 'legendonly'

            patched_figure['data'][pat_id_n]['visible'] = True
            #patched_figure['data'].append(fig_PF['data'][trace_id])

            updated_size = [14 if n == selecSol else 8 for n in range(len(df_base[df_base['OriginalID_PT'] == pat_id]))]
            #updated_type = ['square-x-open' if m == selecSol else df_base.loc[m, 'clust_symb'] for m in list(df_base[df_base['OriginalID_PT']==pat_id].copy().sort_values(by='OriginalID_Sol').index)]
            updated_line = [2 if k == selecSol else 0 for k in range(len(df_base[df_base['OriginalID_PT'] == pat_id]))]

            patched_figure['data'][pat_id_n]['marker']['size'] = updated_size
            #patched_figure['data'][trace_id]['marker']['symbol'] = updated_type
            patched_figure['data'][pat_id_n]['marker']['line']['width'] = updated_line

            return patched_figure

#! ----------- main chart update on solution clicked --> highlight
@callback(
    Output('main-ds-viz', 'figure'),                    #* 13

    Input('main-ds-viz', 'clickData'),
    Input('performance-graph', 'clickData'),
    Input('show-element-type', 'value'),
    Input('show-participant', 'value'),

    State('main-ds-viz', 'figure'),
    prevent_initial_call=True
    )

def update_main_graph(clickData_m, clickData_p, ckb_value, pt_selec, fig_state):
    # trace 0 - full cvx hull
    # trace 1-31 - pt/gallery cvx hull
    # trace 32-61 - pt arrows
    # trace 62 - full scatter with symbols for clusters

    #! add cvx hull
    last_click = ctx.triggered_id
    #print(ckb_value)

    #idx = clickData_m['points'][0]['pointIndex']

    #pat_id = df_base.loc[idx,'OriginalID_PT']

    #! highlight/on click get right solution from performance graph
    if last_click == 'main-ds-viz':
        clickedSol = clickData_m['points'][0]['pointIndex']
        pat_id = df_base.loc[clickedSol,'OriginalID_PT']

    elif last_click == 'performance-graph':
        x_perf = clickData_p['points'][0]['x']
        pat_id = ids[clickData_p['points'][0]['curveNumber']+1]
        #print(pat_id)
        clickedSol = df_base[(df_base['OriginalID_PT'] == pat_id) & (df_base['OriginalID_Sol'] == x_perf)].index[0]

    elif last_click == 'show-participant':
        clickedSol = 'filter-pt'
        print(pt_selec)

    elif last_click == 'show-element-type':
        clickedSol = 'filter-element'

    if clickedSol is None:
        raise PreventUpdate

    elif clickedSol == 'filter-pt':
        ls_ptnum = []

        patched_figure = Patch()

        # check if pt filter activated
        if pt_selec != 'Select...':

            #initialise list of visible traces
            vis_traces = [0,62]

            #remove arrows & areas if not ptc
            for p in pt_selec:
                ls_ptnum.append(ids.index(p))

            for p_n in ls_ptnum:
                vis_traces.append(p_n+1)                                    # add pt cvx hull trace
                if p_n != 0:
                    vis_traces.append(p_n+31)                               # add pt arrow trace

            updated_visibility = [True if n in vis_traces else 'legendonly' for n in range(63)] #todo

            if 'Areas' not in ckb_value:
                for av in list(range(1,32)):
                    updated_visibility[av] = 'legendonly'

            if 'Arrows' not in ckb_value:
                for av in list(range(32,62)):
                    updated_visibility[av] = 'legendonly'

            if 'Points' not in ckb_value:
                updated_visibility[62] = 'legendonly'

            for tr in range(63): #todo
                patched_figure['data'][tr]['visible'] = updated_visibility[tr]

        elif pt_selec is None:
            for tr in range(63): #todo
                patched_figure['data'][tr]['visible'] = True

        return patched_figure

    elif clickedSol == 'filter-element':
        patched_figure = Patch()

        arrow_viz = []
        for arrv in list(range(32,62)):
            arrow_viz.append(patched_figure['data'][arrv]['visible'])

        if 'Points' in ckb_value:
            patched_figure['data'][62]['visible'] = True
        else:
            patched_figure['data'][62]['visible'] = 'legendonly'

        #areas
        if 'Areas' in ckb_value:
            if not pt_selec or pt_selec == 'Show participants...':
                for av in list(range(1,32)):
                    patched_figure['data'][av]['visible'] = True
            else:
                area_viz = []
                ls_aviz = []
                for p in pt_selec:
                    ls_aviz.append(ids.index(p))

                for p_n in ls_aviz:
                    area_viz.append(p_n+1)                                    # add pt cvx hull trace

                upd_vis = [True if n in area_viz else 'legendonly' for n in range(1,32)] #todo

                for av in list(range(1,32)):
                    patched_figure['data'][av]['visible'] = upd_vis[av-1]
        else:
            for av in list(range(1,32)):
                patched_figure['data'][av]['visible'] = 'legendonly'

        #arrows
        if 'Arrows' in ckb_value:
            if not pt_selec or pt_selec == 'Show participants...':
                for av in list(range(32,62)):
                    patched_figure['data'][av]['visible'] = True
            else:
                arr_viz = []
                ls_arrviz = []
                for p in pt_selec:
                    ls_arrviz.append(ids.index(p))

                for p_n in ls_arrviz:
                    if p_n != 0:
                        arr_viz.append(p_n+31)                                    # add pt cvx hull trace

                upd_vis = [True if n in arr_viz else 'legendonly' for n in range(32,62)] #todo

                for av in list(range(32,62)):
                    patched_figure['data'][av]['visible'] = upd_vis[av-32]
        else:
            for av in list(range(32,62)):
                patched_figure['data'][av]['visible'] = 'legendonly'

        return patched_figure

    else:
        patched_figure = Patch()

        updated_size = [18 if n == clickedSol else 8 for n in range(len(df_base) )]
        updated_type = ['square-x-open' if m == clickedSol else df_base.loc[m, 'clust_symb'] for m in range(len(df_base))]
        updated_line = [2 if k == clickedSol else 0 for k in range(len(df_base) )]

        patched_figure['data'][62]['marker']['size'] = updated_size
        patched_figure['data'][62]['marker']['symbol'] = updated_type
        patched_figure['data'][62]['marker']['line']['width'] = updated_line

        return patched_figure


if __name__ == '__main__':
    app.run_server(debug=True, use_reloader=False)


