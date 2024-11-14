#%%
import pandas as pd
from pathlib import Path
import numpy as np
import json
import math
from scipy.spatial import ConvexHull

dir_data = 'C:\Py\DSX_Vis\SaveFiles'
saveExcel = True

#%%



#! finding solutions' save files
print('Creating dataset from saved solutions...')
pth = Path(dir_data)

ls_solf = []

for p in pth.rglob("*.json"):
    ls_solf.append([p.parent, p.stem])

df_sols = pd.DataFrame(ls_solf, columns=['path', 'fullid_orig']).drop(columns=['path'])
df_sols['fullid_orig'] = df_sols['fullid_orig'].str.replace('-0','-')

#df_sols[['PT','IntID','SolID']] = df_sols['PT'].str.split('-',expand=True)
#df_sols['SolID'] = df_sols['SolID'].astype(int)

#* general
df_sols[['TLength','NSegm','NJoint','TCost']] = ''

#* materials
df_sols[['NSegmRoad','LenRoad','NSegmReinfRoad','LenReinfRoad','NSegmWood','LenWood','NSegmSteel','LenSteel']] = ''

#* anchors
df_sols[['LeftAnc','MidAnc','RightAnc', 'NSegmLeftAnc', 'NSegmMidAnc','NSegmRightAnc']] = ''
#df_sols[['LenLeftAnc', 'LenMidAnc','LenRightAnc']] = ''

#* material in anchors
df_sols[['LeftAncRoad','LeftAncReinfRoad','LeftAncWood', 'LeftAncSteel']] = ''
df_sols[['MidAncRoad','MidAncReinfRoad','MidAncWood', 'MidAncSteel']] = ''
df_sols[['RightAncRoad','RightAncReinfRoad','RightAncWood', 'RightAncSteel']] = ''

#* metrics
df_sols['StructDensity'] = ''

#* connections
df_sols[['NConnecSupRoad','NConnecRoadRoad','NConnecSupSup']] = ''

#* avg angles
df_sols[['AvgAngleSupRoad','AvgAngleRoadRoad','AvgAngleSupSup']] = ''

#* nodes [x,y]
df_sols[['NodesXPos','NodesYPos']] = ''
df_sols['NodesXPos'] = df_sols['NodesXPos'].astype('object')
df_sols['NodesYPos'] = df_sols['NodesYPos'].astype('object')

#! getting summary info from solutions' save files
for n, sol in enumerate(ls_solf):
    #read file (layout json)
    df = pd.read_json(f'{sol[0]}/{sol[1]}.json')

    df_Anchor=df.iloc[0,10]
    df_Edge=df.iloc[1,10]
    df_Joints=df.iloc[2,10]
    df_Phase=df.iloc[3,10]

    df_Anchor= pd.json_normalize(df_Anchor)
    df_Joints=pd.json_normalize(df_Joints)
    df_Edge=pd.json_normalize(df_Edge)

    df_AncJon= pd.concat([df_Anchor,df_Joints],ignore_index=True)

    xDict = dict(zip(df_AncJon.loc[:,'m_Guid'], df_AncJon.loc[:,'m_Pos.x']))
    yDict = dict(zip(df_AncJon.loc[:,'m_Guid'], df_AncJon.loc[:,'m_Pos.y']))

    #initialise the columns
    df_Edge['nAx']=''
    df_Edge['nAy']=''
    df_Edge['nBx']=''
    df_Edge['nBy']=''
    df_Edge['EdgeSize']=''

    df_Edge['nAx']=df_Edge['m_NodeAGuid'].map(xDict)
    df_Edge['nAy']=df_Edge['m_NodeAGuid'].map(yDict)

    df_Edge['nBx']=df_Edge['m_NodeBGuid'].map(xDict)
    df_Edge['nBy']=df_Edge['m_NodeBGuid'].map(yDict)

    for i in range(len(df_Edge.index)):
        x0=df_Edge.iloc[i,6]
        y0=df_Edge.iloc[i,7]
        x1=df_Edge.iloc[i,8]
        y1=df_Edge.iloc[i,9]

        df_Edge.iloc[i,df_Edge.columns.get_loc('EdgeSize')]= math.sqrt((x0-x1)**2+(y0-y1)**2)

    df_MatSummary=df_Edge.groupby('m_MaterialType')['EdgeSize'].sum()
    df_MatSummary = pd.DataFrame(df_MatSummary)

    MatDict = { #id, name, line width, color
        '1':[200,'road',5,'rgb(139,69,19)'], #saddlebrown
        '2':[400,'reinforced road',5,'rgb(255,140,0 )'], #dark orange
        '3':[180, 'wood',3,'rgb(222,184,135)'], #burly wood
        '4':[450, 'steel',4,'rgb(178,34,34)'], #mediumvioletred
        '5':[220, 'rope',2,'rgb(218,165,32)'], #golden rod
        '6':[400, 'cable',1,'rgb(105,105,105)'], #dimgray
        '7':[450, 'hydro',4,'rgb(30,144,255)'], #dodgerblue
        '8':[330, 'spring',5,'rgb(255,215,0)'] #gold
    }

    df_MatSummary['MatType']=df_MatSummary.index
    df_MatSummary['CostTotal']= ''
    df_MatSummary['Materials']=''
    df_MatSummary['AvgSize']= df_Edge.groupby('m_MaterialType')['EdgeSize'].mean()
    df_MatSummary['NumSegments']= df_Edge.groupby('m_MaterialType')['EdgeSize'].count()

    #print(df_MatSummary.info())

    #print(df_MatSummary)

    for i in range(len(df_MatSummary.index)):
        matType=MatDict[str(df_MatSummary.iloc[i,1])][0]
        matLen=df_MatSummary.iloc[i,0]
        df_MatSummary.iloc[i,2]= matLen * matType
        df_MatSummary.iloc[i,3]= MatDict[str(df_MatSummary.iloc[i,1])][1]


    nseg = df_MatSummary['NumSegments'].sum()
    njoin = len(set(df_Edge['m_NodeAGuid'].to_list() + df_Edge['m_NodeBGuid'].to_list()))

    #! get values & add to df_sols

    #* general
    df_sols.loc[n,'TLength'] = df_MatSummary['EdgeSize'].sum()
    df_sols.loc[n,'NSegm'] = nseg
    df_sols.loc[n,'NJoint'] = njoin
    df_sols.loc[n,'TCost'] = df_MatSummary['CostTotal'].sum()

    #* materials
    mat_used = df_MatSummary.index.to_list()
    if 1 in mat_used:
        df_sols.loc[n,'NSegmRoad'] = df_MatSummary.loc[1,'NumSegments']
        df_sols.loc[n,'LenRoad'] = df_MatSummary.loc[1,'EdgeSize']
    else:
        df_sols.loc[n,'NSegmRoad'] = 0
        df_sols.loc[n,'LenRoad'] = 0

    if 2 in mat_used:
        df_sols.loc[n,'NSegmReinfRoad'] = df_MatSummary.loc[2,'NumSegments']
        df_sols.loc[n,'LenReinfRoad'] = df_MatSummary.loc[2,'EdgeSize']
    else:
        df_sols.loc[n,'NSegmReinfRoad'] = 0
        df_sols.loc[n,'LenReinfRoad'] = 0

    if 3 in mat_used:
        df_sols.loc[n,'NSegmWood'] = df_MatSummary.loc[3,'NumSegments']
        df_sols.loc[n,'LenWood'] = df_MatSummary.loc[3,'EdgeSize']
    else:
        df_sols.loc[n,'NSegmWood'] = 0
        df_sols.loc[n,'LenWood'] = 0

    if 4 in mat_used:
        df_sols.loc[n,'NSegmSteel'] = df_MatSummary.loc[4,'NumSegments']
        df_sols.loc[n,'LenSteel'] = df_MatSummary.loc[4,'EdgeSize']
    else:
        df_sols.loc[n,'NSegmSteel'] = 0
        df_sols.loc[n,'LenSteel'] = 0

    #* anchors
    leftanc_id = df_Anchor.loc[0,'m_Guid']
    rightanc_id = df_Anchor.loc[1,'m_Guid']
    midanc_id = df_Anchor.loc[2,'m_Guid']

    if leftanc_id in df_Edge['m_NodeAGuid'].to_list() or leftanc_id in df_Edge['m_NodeBGuid'].to_list():
        df_sols.loc[n,'LeftAnc'] = 1
        df_sols.loc[n,'NSegmLeftAnc'] = df_Edge['m_NodeAGuid'].to_list().count(leftanc_id) + df_Edge['m_NodeBGuid'].to_list().count(leftanc_id)
        df_sols.loc[n,'LeftAncRoad'] = df_Edge[(df_Edge['m_NodeAGuid']==leftanc_id) | (df_Edge['m_NodeBGuid']==leftanc_id)]['m_MaterialType'].to_list().count(1)
        df_sols.loc[n,'LeftAncReinfRoad'] = df_Edge[(df_Edge['m_NodeAGuid']==leftanc_id) | (df_Edge['m_NodeBGuid']==leftanc_id)]['m_MaterialType'].to_list().count(2)
        df_sols.loc[n,'LeftAncWood'] = df_Edge[(df_Edge['m_NodeAGuid']==leftanc_id) | (df_Edge['m_NodeBGuid']==leftanc_id)]['m_MaterialType'].to_list().count(3)
        df_sols.loc[n,'LeftAncSteel'] = df_Edge[(df_Edge['m_NodeAGuid']==leftanc_id) | (df_Edge['m_NodeBGuid']==leftanc_id)]['m_MaterialType'].to_list().count(4)
    else:
        df_sols.loc[n,'LeftAnc'] = 0
        df_sols.loc[n,'NSegmLeftAnc'] = 0
        df_sols.loc[n,'LeftAncRoad'] = 0
        df_sols.loc[n,'LeftAncReinfRoad'] = 0
        df_sols.loc[n,'LeftAncWood'] = 0
        df_sols.loc[n,'LeftAncSteel'] = 0

    if rightanc_id in df_Edge['m_NodeAGuid'].to_list() or rightanc_id in df_Edge['m_NodeBGuid'].to_list():
        df_sols.loc[n,'RightAnc'] = 1
        df_sols.loc[n,'NSegmRightAnc'] = df_Edge['m_NodeAGuid'].to_list().count(rightanc_id) + df_Edge['m_NodeBGuid'].to_list().count(rightanc_id)
        df_sols.loc[n,'RightAncRoad'] = df_Edge[(df_Edge['m_NodeAGuid']==rightanc_id) | (df_Edge['m_NodeBGuid']==rightanc_id)]['m_MaterialType'].to_list().count(1)
        df_sols.loc[n,'RightAncReinfRoad'] = df_Edge[(df_Edge['m_NodeAGuid']==rightanc_id) | (df_Edge['m_NodeBGuid']==rightanc_id)]['m_MaterialType'].to_list().count(2)
        df_sols.loc[n,'RightAncWood'] = df_Edge[(df_Edge['m_NodeAGuid']==rightanc_id) | (df_Edge['m_NodeBGuid']==rightanc_id)]['m_MaterialType'].to_list().count(3)
        df_sols.loc[n,'RightAncSteel'] = df_Edge[(df_Edge['m_NodeAGuid']==rightanc_id) | (df_Edge['m_NodeBGuid']==rightanc_id)]['m_MaterialType'].to_list().count(4)
    else:
        df_sols.loc[n,'RightAnc'] = 0
        df_sols.loc[n,'NSegmRightAnc'] = 0
        df_sols.loc[n,'RightAncRoad'] = 0
        df_sols.loc[n,'RightAncReinfRoad'] = 0
        df_sols.loc[n,'RightAncWood'] = 0
        df_sols.loc[n,'RightAncSteel'] = 0

    if midanc_id in df_Edge['m_NodeAGuid'].to_list() or midanc_id in df_Edge['m_NodeBGuid'].to_list():
        df_sols.loc[n,'MidAnc'] = 1
        df_sols.loc[n,'NSegmMidAnc'] = df_Edge['m_NodeAGuid'].to_list().count(midanc_id) + df_Edge['m_NodeBGuid'].to_list().count(midanc_id)
        df_sols.loc[n,'MidAncRoad'] = df_Edge[(df_Edge['m_NodeAGuid']==midanc_id) | (df_Edge['m_NodeBGuid']==midanc_id)]['m_MaterialType'].to_list().count(1)
        df_sols.loc[n,'MidAncReinfRoad'] = df_Edge[(df_Edge['m_NodeAGuid']==midanc_id) | (df_Edge['m_NodeBGuid']==midanc_id)]['m_MaterialType'].to_list().count(2)
        df_sols.loc[n,'MidAncWood'] = df_Edge[(df_Edge['m_NodeAGuid']==midanc_id) | (df_Edge['m_NodeBGuid']==midanc_id)]['m_MaterialType'].to_list().count(3)
        df_sols.loc[n,'MidAncSteel'] = df_Edge[(df_Edge['m_NodeAGuid']==midanc_id) | (df_Edge['m_NodeBGuid']==midanc_id)]['m_MaterialType'].to_list().count(4)

    else:
        df_sols.loc[n,'MidAnc'] = 0
        df_sols.loc[n,'NSegmMidAnc'] = 0
        df_sols.loc[n,'MidAncRoad'] = 0
        df_sols.loc[n,'MidAncReinfRoad'] = 0
        df_sols.loc[n,'MidAncWood'] = 0
        df_sols.loc[n,'MidAncSteel'] = 0

    #* metrics
    df_sols.loc[n,'StructDensity'] = nseg/njoin

    #* connections
    ncsuproad = 0
    ncsupsup = 0
    ncroadroad = 0
    nodelist = list(set(df_Edge['m_NodeAGuid'].to_list() + df_Edge['m_NodeBGuid'].to_list()))

    for node in nodelist:
        ls = df_Edge[(df_Edge['m_NodeAGuid']==node) | (df_Edge['m_NodeBGuid']==node)]['m_MaterialType'].to_list()

        if (1 in ls or 2 in ls) & (3 in ls or 4 in ls):
            ncsuproad = ncsuproad + 1
        elif (1 in ls and 2 in ls) or ls.count(1) >=2 or ls.count(2)>=2:
            ncroadroad = ncroadroad + 1
        elif (3 in ls and 4 in ls) or ls.count(3) >=2 or ls.count(4)>=2:
            ncsupsup = ncsupsup + 1

    df_sols.loc[n,'NConnecSupRoad'] = ncsuproad
    df_sols.loc[n,'NConnecRoadRoad'] = ncroadroad
    df_sols.loc[n,'NConnecSupSup'] = ncsupsup

    df_sols.at[n,'NodesXPos'] = df_AncJon[df_AncJon['m_Guid'].isin(nodelist)]['m_Pos.x'].to_list()
    df_sols.at[n,'NodesYPos'] = df_AncJon[df_AncJon['m_Guid'].isin(nodelist)]['m_Pos.y'].to_list()


if saveExcel == True:
    df_sols.to_excel(f'{dir_data}/dataset_quant.xlsx')

print('Summarising solutions done!')



# %%
