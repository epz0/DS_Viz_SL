#%%
import json
import math
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from pathlib import Path
import numpy as np
from utils.utils import *
import matplotlib.pyplot as plt

pd.options.display.width = 0

#read level layout file
with open(r'C:\Py\DS_Viz_Exp\viz\14mLayout.json','r') as f:
    data = json.load(f)
#print(data)

df_Data = pd.json_normalize(data)
#print(df_Data)

#get columns to dfs
dfZedVehicles = pd.json_normalize(data['m_ZedAxisVehicles'])
#print(dfZedVehicles)

df_Vehicles = pd.json_normalize(data['m_Vehicles'])
#print(df_Vehicles)

df_StopTrig = pd.json_normalize(data['m_VehicleStopTriggers'])
#print(df_StopTrig)

df_Terrain = pd.json_normalize(data['m_TerrainStretches'])
#print(df_Terrain)

df_Rocks = pd.json_normalize(data['m_Rocks'])
#print(df_Rocks)

df_Water = pd.json_normalize(data['m_WaterBlocks'])
#print(df_Water)

df_Pillars = pd.json_normalize(data['m_Pillars'])
#print(df_Pillars)

df_Bridge = pd.json_normalize(data['m_Bridge'])
#print(df_Bridge)

#sorting out Budget Info
df_Budget = df_Data.filter(like='m_Budget').T
#print(df_Budget)

#sorting out configs df
df_Cfg = df_Data.filter(items=['m_IsModded', 'm_Version','m_ThemeStubKey']).T
df_Setting = df_Data.filter(like='m_Settings').T
df_Wksp = df_Data.filter(like='m_Workshop').T
df_Config = pd.concat([df_Budget,df_Cfg,df_Setting])
#print(df_Config)

###! get json files --> df
folder_path = r"C:\Py\DS_Viz_Exp\viz\savefiles"  # Replace with the actual folder path

folder = Path(folder_path)
df = pd.DataFrame(columns=["File Name"])  # Create an empty DataFrame
name_list = []
name_list_png = []

for file_path in folder.glob("**/*.json"):
    file_name = file_path.stem
    name_list.append(file_name)


df = pd.DataFrame(name_list,  columns=["PID"])
df[['ID', 'PrePost', 'SolNum']] = df.PID.str.split("-", expand = True)
#df[['Num', 'PType']] = df.ID.str.split("_", expand = True)
df['json_f'] = df['PID']
df['PID'] = df['PID'].str.replace('-0','-')


df = df.join(pd.DataFrame(
    {
        'LRoad': 0,
        'LReinforcedRoad': 0,
        'LWood': 0,
        'LSteel': 0,
        'AvgSupSize': 0,
        'NSegRoad': 0,
        'NSegReinforcedRoad': 0,
        'NSegWood': 0,
        'NSegSteel': 0,
        'TotalLength': 0,
        'NJoints': 0,
        'timestamp':0
    }, index=df.index
))

df_summary = solutions_summary(folder_path, saveExcel=False)
df_summary = df_summary.rename(columns={'fullid_orig':'PID'})
df = df.merge(df_summary, how='left', on='PID')


# %% #### READ SAVE FILE #####
#df = df[156:158]

for index, row in df.iterrows():
    filej = sorted(folder.glob(f"**/{row['json_f']}.json"))[0]
    #print(filej.name)
    #print(index)

    #! STEP 1 - load solution json & get basic data
    with open(filej,'r') as f:
        data = json.load(f)

    timestamp = data['m_DisplayName']
    budget_sol = data['m_Budget']

    #! STEP 2 - Get bridge info from data to transform in dfs
    anchors = data['m_Bridge']['m_Anchors']
    joints = data['m_Bridge']['m_Joints']
    edges = data['m_Bridge']['m_Edges']

    df_Anchor= pd.json_normalize(anchors)
    df_Joints=pd.json_normalize(joints)
    df_Edge=pd.json_normalize(edges)

    # merging anchors & joints dfs (same info/structure)
    df_AncJon= pd.concat([df_Anchor,df_Joints],ignore_index=True)

    #! STEP 3 - Extracting info from dfs
    # a) x,y position of anchors and joints
    xDict = dict(zip(df_AncJon.loc[:,'m_Guid'], df_AncJon.loc[:,'m_Pos.x']))
    yDict = dict(zip(df_AncJon.loc[:,'m_Guid'], df_AncJon.loc[:,'m_Pos.y']))

    # b) add columns to edges df to combine info - which edge connects to
    #    which anchor/joint
    # x,y coordinates for first point (A)
    df_Edge['nAx']=''
    df_Edge['nAy']=''
    df_Edge['nAx']=df_Edge['m_NodeAGuid'].map(xDict)
    df_Edge['nAy']=df_Edge['m_NodeAGuid'].map(yDict)

    # x,y coordinates for second point (B)
    df_Edge['nBx']=''
    df_Edge['nBy']=''
    df_Edge['nBx']=df_Edge['m_NodeBGuid'].map(xDict)
    df_Edge['nBy']=df_Edge['m_NodeBGuid'].map(yDict)

    # column for the edge lenght
    df_Edge['EdgeSize']=''
    for i in range(len(df_Edge.index)):
        x0=df_Edge.iloc[i,6]
        y0=df_Edge.iloc[i,7]
        x1=df_Edge.iloc[i,8]
        y1=df_Edge.iloc[i,9]

        df_Edge.iloc[i,df_Edge.columns.get_loc('EdgeSize')]= math.sqrt((x0-x1)**2+(y0-y1)**2)


    #! STEP 4 - Materials info

    #dict of materials {id, name, line width, color}
    MatDict = {
            '1':[200,'road',7,'rgb(41,36,33)'], #ivory black
            '2':[400,'reinforced road',7,'rgb(112,128,144)'], #slategray
            '3':[180, 'wood',5,'rgb(244,164,96)'], #sandybrown
            '4':[450, 'steel',6,'rgb(178,34,34)'], #mediumvioletred
            '5':[220, 'rope',3,'rgb(218,165,32)'], #golden rod
            '6':[400, 'cable',3,'rgb(105,105,105)'], #dimgray
            '7':[450, 'hydro',4,'rgb(30,144,255)'], #dodgerblue
            '8':[330, 'spring',4,'rgb(255,215,0)'] #gold
        }

    #! STEP 8 - Abstract Representation of Solution

    #* create shapes from level layout
    fig = px.scatter(df_AncJon, x='m_Pos.x',y='m_Pos.y',color='m_IsAnchor',symbol='m_IsAnchor') #

    #* 7 ANCHORS
    # LEFT ANCHOR
    fig.add_shape(type="path",
        path='M -0.225 4.5 L 0 5 L 0.225 4.5 L -0.225 4.5 L -0.28125 4.325 M -0.1125 4.5 L -0.16875 4.325 M 0 4.5 L -0.05625 4.325 M 0.1125 4.5 L 0.05625 4.325 M 0.225 4.5 L 0.16875 4.325',
        line_color='rgba(53,53,53,1)',
        fillcolor='rgba(211,211,211,1)')

    # RIGHT ANCHOR
    fig.add_shape(type="path",
        path='M 13.775 5.25 L 14 5.75 L 14.225 5.25 L 13.775 5.25 L 13.71875 5.075 M 13.8875 5.25 L 13.83125 5.075 M 14 5.25 L 13.94375 5.075 M 14.1125 5.25 L 14.05625 5.075 M 14.225 5.25 L 14.16875 5.075',
        line_color='rgba(53,53,53,1)',
        fillcolor='rgba(211,211,211,1)')

    # MID ANCHOR
    fig.add_shape(type="path",
        path='M 5.775 3.5 L 6 4 L 6.225 3.5 L 5.775 3.5 L 5.71875 3.325 M 5.8875 3.5 L 5.83125 3.325 M 6 3.5 L 5.94375 3.325 M 6.1125 3.5 L 6.05625 3.325 M 6.225 3.5 L 6.16875 3.325',
        line_color='rgba(53,53,53,1)',
        fillcolor='rgba(211,211,211,1)')

    fig.update_yaxes(
        scaleanchor = "x",
        scaleratio = 1,
    )

    #* traces!
    fig.update_traces(marker={'size': 12, 'opacity': 0.9}, textfont_size=14)

    #* creating the actual bridge from save file

    for i in range(len(df_Edge.index)):
        matID = df_Edge.iloc[i,0]
        match matID:
            case 1:
                matColor = MatDict['1'][3]
                matWidth = MatDict['1'][2]
            case 2:
                matColor = MatDict['2'][3]
                matWidth = MatDict['2'][2]
            case 3:
                matColor = MatDict['3'][3]
                matWidth = MatDict['3'][2]
            case 4:
                matColor = MatDict['4'][3]
                matWidth = MatDict['4'][2]
            case 5:
                matColor = MatDict['5'][3]
                matWidth = MatDict['5'][2]
            case 6:
                matColor = MatDict['6'][3]
                matWidth = MatDict['6'][2]
            case 7:
                matColor = MatDict['7'][3]
                matWidth = MatDict['7'][2]
            case 8:
                matColor = MatDict['8'][3]
                matWidth = MatDict['8'][2]
            case _:
                matColor = 'magenta'
                matWidth = 3

        fig.add_shape(type="line",
            xref="x", yref="y",
            x0=df_Edge.iloc[i,6], y0=df_Edge.iloc[i,7], x1=df_Edge.iloc[i,8], y1=df_Edge.iloc[i,9],
            line=dict(color=matColor, width=matWidth), opacity=1
                    )

    fig.data = fig.data[::-1]

    fig.update_yaxes(
        scaleanchor = "x",
        scaleratio = 1,
    )

    fig.update_layout(yaxis_visible=False, yaxis_showticklabels=False)
    fig.update_layout(xaxis_visible=False, xaxis_showticklabels=False)
    fig.update_layout(plot_bgcolor='white', paper_bgcolor='rgba(0,0,0,0)', showlegend=False, hovermode=False)
    fig.update_traces(visible='legendonly', selector=dict(name="True"))

    #fig.show()
    pth = r'C:/Py/DS_Viz_Exp/viz/experimental'
    fig.write_image(f'{pth}/{row["PID"]}.svg', format="svg", width=1200, height=675, scale=2)
    print(f'{row["PID"]} done')

    #fig.write_html(f"{row['PID']}_Structure.html")


#%% PLOT FULL POSTER
import matplotlib.image as mpimg
import matplotlib.gridspec as gridspec
#%%
folder_path = r"C:/Py/DS_Viz_Exp/viz/experimental"  # Replace with the actual folder path

folder = Path(folder_path)
df_img = pd.DataFrame(columns=["File Name"])  # Create an empty DataFrame
name_list = []
name_list_png = []

for file_path in folder.glob("**/*.png"):
    file_name = f'{folder_path}/{file_path.name}'
    name_list.append(file_name)

#%%

plt.figure(figsize=(106.66,60)) # specifying the overall grid size
gs1 = gridspec.GridSpec(25,25)
gs1.update(wspace=0, hspace=-0.15)
for i in range(625):
    plt.subplot(gs1[i])    # the number of images in the grid is 25*25 (625)
    img = mpimg.imread(name_list[i])
    imgcr = img[120:1190,160:2240,:]
    plt.imshow(imgcr)
    plt.gca().set_axis_off()
plt.savefig('banner_hd_2.svg', bbox_inches='tight',format='svg') #dpi=600)
#plt.show()
#%%
#%% PLOT FULL POSTER SVG
import matplotlib.image as mpimg
import matplotlib.gridspec as gridspec
#%%
folder_path = r"C:/Py/DS_Viz_Exp/viz/experimental"  # Replace with the actual folder path

folder = Path(folder_path)
df_img = pd.DataFrame(columns=["File Name"])  # Create an empty DataFrame
name_list = []
name_list_png = []

for file_path in folder.glob("**/*.svg"):
    file_name = f'{folder_path}/{file_path.name}'
    name_list.append(file_name)

#%%

plt.figure(figsize=(106.66,60)) # specifying the overall grid size
gs1 = gridspec.GridSpec(25,25)
gs1.update(wspace=0, hspace=-0.15)
for i in range(625):
    plt.subplot(gs1[i])    # the number of images in the grid is 25*25 (625)
    img = mpimg.imread(name_list[i])
    imgcr = img[120:1190,160:2240,:]
    plt.imshow(imgcr)
    plt.gca().set_axis_off()
plt.savefig('banner_hd.svg', bbox_inches='tight',format='svg') #dpi=600)
#plt.show()

# %% FULL ABSTRACT


df = df[156:158]

for index, row in df.iterrows():
    filej = sorted(folder.glob(f"**/{row['PID']}.json"))[0]
    #print(filej.name)
    #print(index)

    #! STEP 1 - load solution json & get basic data
    with open(filej,'r') as f:
        data = json.load(f)

    timestamp = data['m_DisplayName']
    budget_sol = data['m_Budget']

    #! STEP 2 - Get bridge info from data to transform in dfs
    anchors = data['m_Bridge']['m_Anchors']
    joints = data['m_Bridge']['m_Joints']
    edges = data['m_Bridge']['m_Edges']

    df_Anchor= pd.json_normalize(anchors)
    df_Joints=pd.json_normalize(joints)
    df_Edge=pd.json_normalize(edges)

    # merging anchors & joints dfs (same info/structure)
    df_AncJon= pd.concat([df_Anchor,df_Joints],ignore_index=True)

    #! STEP 3 - Extracting info from dfs
    # a) x,y position of anchors and joints
    xDict = dict(zip(df_AncJon.loc[:,'m_Guid'], df_AncJon.loc[:,'m_Pos.x']))
    yDict = dict(zip(df_AncJon.loc[:,'m_Guid'], df_AncJon.loc[:,'m_Pos.y']))

    # b) add columns to edges df to combine info - which edge connects to
    #    which anchor/joint
    # x,y coordinates for first point (A)
    df_Edge['nAx']=''
    df_Edge['nAy']=''
    df_Edge['nAx']=df_Edge['m_NodeAGuid'].map(xDict)
    df_Edge['nAy']=df_Edge['m_NodeAGuid'].map(yDict)

    # x,y coordinates for second point (B)
    df_Edge['nBx']=''
    df_Edge['nBy']=''
    df_Edge['nBx']=df_Edge['m_NodeBGuid'].map(xDict)
    df_Edge['nBy']=df_Edge['m_NodeBGuid'].map(yDict)

    # column for the edge lenght
    df_Edge['EdgeSize']=''
    for i in range(len(df_Edge.index)):
        x0=df_Edge.iloc[i,6]
        y0=df_Edge.iloc[i,7]
        x1=df_Edge.iloc[i,8]
        y1=df_Edge.iloc[i,9]

        df_Edge.iloc[i,df_Edge.columns.get_loc('EdgeSize')]= math.sqrt((x0-x1)**2+(y0-y1)**2)


    #! STEP 4 - Materials info

    #dict of materials {id, name, line width, color}
    MatDict = {
            '1':[200,'road',6,'rgb(41,36,33)'], #ivory black
            '2':[400,'reinforced road',6,'rgb(112,128,144)'], #slategray
            '3':[180, 'wood',4,'rgb(244,164,96)'], #sandybrown
            '4':[450, 'steel',5,'rgb(178,34,34)'], #mediumvioletred
            '5':[220, 'rope',3,'rgb(218,165,32)'], #golden rod
            '6':[400, 'cable',3,'rgb(105,105,105)'], #dimgray
            '7':[450, 'hydro',4,'rgb(30,144,255)'], #dodgerblue
            '8':[330, 'spring',4,'rgb(255,215,0)'] #gold
        }

    #! STEP 8 - Abstract Representation of Solution

    #* create shapes from level layout
    fig = px.scatter(df_AncJon, x='m_Pos.x',y='m_Pos.y',color='m_IsAnchor',symbol='m_IsAnchor') #

    #* 1 zed vehicle
    zVehicX = dfZedVehicles.iloc[0,dfZedVehicles.columns.get_loc('m_Pos.x')]
    zVehicY = dfZedVehicles.iloc[0,dfZedVehicles.columns.get_loc('m_Pos.y')]-.60

    fig.add_shape(type="path",
        path='M 9 2.65 L 11 2.65 L 12 3.4 L 11 3.4 L 11 5.4 L 10.5 6.2 L 9.5 6.2 L 9 5.4 L 9 3.4 L 8 3.4Z',
        fillcolor="rgba(220,20,60,0.2)",
        line_color="rgba(178,34,34,0.1)",
        )

    #* 2 vehicle
    xDesloc = -1
    cPosX = df_Vehicles.iloc[0,df_Vehicles.columns.get_loc('m_Pos.x')] +xDesloc
    cPosY = df_Vehicles.iloc[0,df_Vehicles.columns.get_loc('m_Pos.y')]

    fig.add_shape(type="circle",
        x0=cPosX, y0=cPosY, x1=cPosX+1.5, y1=cPosY+1.5,
        fillcolor="rgba(143,188,143,0.2)",
        line_color="rgba(85,107,47,0.15)",
    )

    fig.add_shape(type="path",
        path='M -1.5 5.36 L -0.75 5.86 L -1.5 6.36Z',
        fillcolor="rgba(143,188,143,0.2)",
        line_color="rgba(85,107,47,0.15)",
    )
    '''
    fig.add_scatter(x=[cPosX+1.5,cPosX+1.9,cPosX+1.5],#multiply by scale
                    y=[cPosY+0.5,cPosY+0.75,cPosY+1],#multiply by scale
                    fill='toself',
                    fillcolor="rgba(143,188,143,0.2)",
                    line_color="rgba(85,107,47,0.15)")
    '''
    #* 3 stop trig
    stopTrigX = df_StopTrig.iloc[0,df_StopTrig.columns.get_loc('m_Pos.x')]
    stopTrigY = df_StopTrig.iloc[0,df_StopTrig.columns.get_loc('m_Pos.y')]

    fig.add_shape(type="rect",
        x0=stopTrigX-1.5, y0=stopTrigY, x1=stopTrigX+0.2-1.5, y1=stopTrigY+0.9,
        line=dict(color="rgba(255,140,0,0.2)"),
                fillcolor='rgba(210,105,30,0.15)')

    fig.add_shape(type="rect",
        x0=stopTrigX-1.5, y0=stopTrigY+0.9, x1=stopTrigX+0.8-1.5, y1=stopTrigY+0.9+0.6,
        line=dict(color="rgba(255,140,0,0.2)"),
                fillcolor='rgba(210,105,30,0.15)')

    #* 4 terrain
    terrainBase = 4
    terrainHeight =5.1
    rightSide = df_Terrain.iloc[0,df_Terrain.columns.get_loc('m_Flipped')]
    rightTerrainPos = df_Terrain.iloc[0,df_Terrain.columns.get_loc('m_Pos.x')]
    heightGain= df_Terrain.iloc[0,df_Terrain.columns.get_loc('m_HeightAdded')]

    fig.add_shape(type="rect",
        x0=-1*terrainBase, y0=0, x1=0, y1=terrainHeight,
        line=dict(color='rgba(0,100,0,0.3)'),
                fillcolor='rgba(210,105,30,0.15)')

    fig.add_shape(type="rect",
        x0=rightTerrainPos, y0=0, x1=rightTerrainPos+terrainBase, y1=terrainHeight+heightGain,
        line=dict(color='rgba(0,100,0,0.3)'),
                fillcolor='rgba(210,105,30,0.15)')

    #* 5 water
    fig.add_shape(type="rect",
        x0=0, y0=0, x1=14, y1=3.25,
        line=dict(color='rgba(32,178,170,0.2)'),
        fillcolor='rgba(175,238,238,0.15)')

    #* 6 pillars
    fig.add_shape(type="rect",
        x0=5.5, y0=0, x1=6.5, y1=4,
        line=dict(color='rgba(119,136,153,0.2)'),
        fillcolor='rgba(211,211,211,0.15)')

    #* 7 ANCHORS
    # LEFT ANCHOR
    fig.add_shape(type="path",
        path='M -0.325 4.25 L 0 5 L 0.325 4.25 L -0.325 4.25 L -0.375 4.075 M -0.1625 4.25 L -0.2125 4.075 M 0 4.25 L -0.05 4.075 M 0.1625 4.25 L 0.1125 4.075 M 0.325 4.25 L 0.275 4.075',
        line_color='rgba(53,53,53,1)',
        fillcolor='rgba(211,211,211,1)')

    # RIGHT ANCHOR
    fig.add_shape(type="path",
        path='M 13.675 5 L 14 5.75 L 14.325 5 L 13.675 5 L 13.59375 4.825 M 13.8375 5 L 13.75625 4.825 M 14 5 L 13.91875 4.825 M 14.1625 5 L 14.08125 4.825 M 14.325 5 L 14.24375 4.825',
        line_color='rgba(53,53,53,1)',
        fillcolor='rgba(211,211,211,1)')

    # MID ANCHOR
    fig.add_shape(type="path",
        path='M 5.675 3.25 L 6 4 L 6.325 3.25 L 5.675 3.25 L 5.59375 3.075 M 5.8375 3.25 L 5.75625 3.075 M 6 3.25 L 5.91875 3.075 M 6.1625 3.25 L 6.08125 3.075 M 6.325 3.25 L 6.24375 3.075',
        line_color='rgba(53,53,53,1)',
        fillcolor='rgba(211,211,211,1)')

    #* 7 label
    fig.add_scatter(x=[-3.75],
                    y=[.75],
                    mode='text',
                    fill='toself',
                    fillcolor="rgba(0,0,0,1)",
                    line_color="rgba(0,0,0,1)",
                    text=f"<b>{row['PID']}<br>Budget used: $ {row['Cost']:,.1f}<br>Total Length: {row['TLength']:,.1f}</b>",
                    textposition='middle right',
                    )

    fig.update_yaxes(
        scaleanchor = "x",
        scaleratio = 1,
    )

    #* traces!
    fig.update_traces(marker={'size': 12, 'opacity': 0.9}, textfont_size=14)

    #* creating the actual bridge from save file

    for i in range(len(df_Edge.index)):
        matID = df_Edge.iloc[i,0]
        match matID:
            case 1:
                matColor = MatDict['1'][3]
                matWidth = MatDict['1'][2]
            case 2:
                matColor = MatDict['2'][3]
                matWidth = MatDict['2'][2]
            case 3:
                matColor = MatDict['3'][3]
                matWidth = MatDict['3'][2]
            case 4:
                matColor = MatDict['4'][3]
                matWidth = MatDict['4'][2]
            case 5:
                matColor = MatDict['5'][3]
                matWidth = MatDict['5'][2]
            case 6:
                matColor = MatDict['6'][3]
                matWidth = MatDict['6'][2]
            case 7:
                matColor = MatDict['7'][3]
                matWidth = MatDict['7'][2]
            case 8:
                matColor = MatDict['8'][3]
                matWidth = MatDict['8'][2]
            case _:
                matColor = 'magenta'
                matWidth = 3

        fig.add_shape(type="line",
            xref="x", yref="y",
            x0=df_Edge.iloc[i,6], y0=df_Edge.iloc[i,7], x1=df_Edge.iloc[i,8], y1=df_Edge.iloc[i,9],
            line=dict(color=matColor, width=matWidth), opacity=1
                    )

    fig.data = fig.data[::-1]

    fig.update_yaxes(
        scaleanchor = "x",
        scaleratio = 1,
    )

    fig.update_layout(yaxis_visible=False, yaxis_showticklabels=False)
    fig.update_layout(xaxis_visible=False, xaxis_showticklabels=False)
    fig.update_layout(plot_bgcolor='white', paper_bgcolor='rgba(0,0,0,0)', showlegend=False, hovermode=False)

    fig.show()
    pth = r'C:/Py/DS_Viz_Exp/viz/experimental'
    fig.write_image(f'{pth}/{row["PID"]}.png', format="png", width=1800, height=900, scale=1)
    #fig.write_html(f"{row['PID']}_Structure.html")
# %%
