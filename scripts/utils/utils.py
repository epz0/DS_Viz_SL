"""The utils module unmasks the data based on a file passed with the masking keys.

Functions:
    unmask_data: Function that unmasks the data, returning the unmasked dataframe.
"""
#%%
import pandas as pd
from pathlib import Path
import numpy as np
import json
import math
from scipy.spatial import ConvexHull
import shapely.geometry
from collections import Counter

#%%

#%%
def unmask_data(dir_data, key_name, df, df_colors=None):
    """Returns dataframes with the data unmasked given an masking key.

    Args:
        dir_data (path): Path to the directory with the data file.
        key_name (string): Name of the file that contais the masking keys. Expects a xlsx file.
        df (dataframe): Main dataframe with the dump from the spreadsheet.
        df_colors (dataframe): Dataframe with color scheme for the participants. Defaults to None.


    Returns:
        df_unmasked: Dataframe with all main data, and with the unmasking applied to it.
        df_colors_unm: Dataframe with the color scheme with the unmasking applied to it.
    """
    print('Reading masking keys from file...')
    solkey = pd.read_excel(f'{dir_data}/{key_name}.xlsx', sheet_name='SolutionMasking')
    partkey = pd.read_excel(f'{dir_data}/{key_name}.xlsx', sheet_name='ParticipantMasking')
    groupkey = pd.read_excel(f'{dir_data}/{key_name}.xlsx', sheet_name='GroupMasking')
    prepostkey = pd.read_excel(f'{dir_data}/{key_name}.xlsx', sheet_name='PrePostMasking')

    print('Masking keys read, unmasking the data... ')
    df_unmasked = pd.merge(left=df,
                    right=solkey,
                    left_on='SolutionID',
                    right_on='RandomID_Sol',
                    how='left')

    df_unmasked = pd.merge(left=df_unmasked,
                    right=partkey,
                    left_on='ParticipantID',
                    right_on='RandomID_PT',
                    how='left').copy()

    df_unmasked = pd.merge(left=df_unmasked,
                    right=groupkey,
                    left_on='GroupID',
                    right_on='RandomID_Group',
                    how='left').copy()

    df_unmasked = pd.merge(left=df_unmasked,
                    right=prepostkey,
                    left_on='PrePost',
                    right_on='RandomID_PrePost',
                    how='left').copy()

    df_unmasked = df_unmasked.drop(columns=['RandomID_PrePost', 'RandomID_Group', 'RandomID_PT', 'RandomID_Sol', 'Description_Group'])

    if df_colors is not None:
        df_colors_unm = pd.merge(left=df_colors,
                        right=partkey,
                        left_on='P',
                        right_on='RandomID_PT',
                        how='left').copy()
        print('Unmasking the data done!')
        return df_unmasked, df_colors_unm

    print('Unmasking the data done!')
    return df_unmasked


def solutions_summary(dir_data, saveExcel=True):
    """Returns a df with the summary of all solutions available as save files (json).

    Args:
        dir_data (string): Path to the parent folder where the save files are
        saveExcel (bool, optional): Defines if a excel file dumping the df should be saved. Defaults to True.

    Returns:
        df_sols: Df summarising the solutions found.
    """

    #! finding solutions' save files
    print('Summarising solutions...')
    pth = Path(dir_data)

    ls_solf = []

    for p in pth.rglob("*.json"):
        ls_solf.append([p.parent, p.stem])

    df_sols = pd.DataFrame(ls_solf, columns=['path', 'fullid_orig']).drop(columns=['path'])
    df_sols['fullid_orig'] = df_sols['fullid_orig'].str.replace('-0','-')

    #df_sols[['PT','IntID','SolID']] = df_sols['PT'].str.split('-',expand=True)
    #df_sols['SolID'] = df_sols['SolID'].astype(int)
    df_sols[['TLength','NSegm','NJoint', 'Cost']] = ''

    #! getting summary info from solutions' save files
    for n, sol in enumerate(ls_solf):
        #read file (layout json)
        df = pd.read_json(f'{sol[0]}/{sol[1]}.json')

        df_Anchor=df.iloc[1,10]
        df_Edge=df.iloc[3,10]
        df_Joints=df.iloc[2,10]
        df_Phase=df.iloc[4,10]

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

        #! get values & add to df_sols
        total_length = df_MatSummary['EdgeSize'].sum()
        total_segments = df_MatSummary['NumSegments'].sum()
        total_joints = len(df_AncJon)
        total_cost = df_MatSummary['CostTotal'].sum()

        df_sols.loc[n,'TLength'] = total_length
        df_sols.loc[n,'NSegm'] = total_segments
        df_sols.loc[n,'NJoint'] = total_joints
        df_sols.loc[n,'Cost'] = total_cost

    if saveExcel == True:
        df_sols.to_excel(f'{dir_data}/solutions_sumary.xlsx')
    print('Summarising solutions done!')
    return df_sols


def cv_hull_vertices(x, y):
    """Retrns convex hull metrics and vertices.

    Args:
        x (list): List of x coordinates.
        y (list): List of y coordinates.

    Returns:
        x_vtx: List of x coordinates for the convex hull vertices.
        y_vtx: List of y coordinates for the convex hull vertices.
        cvxh_area: Area of the convex hull.
    """
    points = np.array(list(zip(x,y)))
    hull = ConvexHull(points)

    x_vtx = points[hull.vertices, 0]
    y_vtx = points[hull.vertices, 1]

    cvxh_area = hull.volume

    return x_vtx, y_vtx, cvxh_area

def solutions_to_dataset(dir_data, saveExcel=True): #! deprecated
    """Returns a df with the summary of all solutions available as save files (json).

    Args:
        dir_data (string): Path to the parent folder where the save files are
        saveExcel (bool, optional): Defines if a excel file dumping the df should be saved. Defaults to True.

    Returns:
        df_sols: Df summarising the solutions found.
    """

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
    return df_sols

#%% DATASET CREATION

def count_non_repeated_elements(lst):
    # Count occurrences of each element
    element_counts = Counter(lst)
    # Filter elements that appear only once
    non_repeated_elements = [element for element, count in element_counts.items() if count == 1]
    # Return the number of non-repeated elements
    return len(non_repeated_elements)

def create_dataset(dir_data, saveExcel=True):
    """Processes all solutions available as save files (json) and returns a df.

    Args:
        dir_data (string): Path to the parent folder where the save files are
        saveExcel (bool, optional): Defines if a Excel file dumping the df should be saved. Defaults to True.

    Returns:
        df_sols: Df summarising the solutions found.
    """

    #! finding solutions' save files
    print('Creating dataset from saved solutions...')

    #folder_path = r"C:\Py\DS_Viz_Exp\viz\savefiles"
    pth = Path(dir_data)

    ls_solf = []

    for p in pth.rglob("*.json"):
        ls_solf.append([p.parent, p.stem])

    df_sols = pd.DataFrame(ls_solf, columns=['path', 'fullid_orig']).drop(columns=['path'])
    df_sols['fullid_orig'] = df_sols['fullid_orig'].str.replace('-0','-')

    df_sols['fullID'] = df_sols['fullid_orig']

    df_sols[['fullid_orig','OriginalID_PrePost', 'OriginalID_Sol']]=df_sols['fullid_orig'].str.split('-',expand=True)

    df_sols.rename({'fullid_orig': 'OriginalID_PT'}, axis=1, inplace=True)

    df_sols['OriginalID_PT'] = df_sols.apply(lambda row: row.OriginalID_PT if row.OriginalID_PT[0] == 'P' else
                                            'GALL', axis=1)

    ls_ctrl = ['P_022', 'P_010', 'P_003','P_026','P_014','P_018','P_020','P_005','P_029','P_008']
    ls_str = ['P_017', 'P_030','P_001','P_004','P_012','P_009','P_013','P_021','P_028','P_024', 'P_00x', 'P_00y', 'P_00w', 'P_00k']
    ls_unst = ['P_007', 'P_027', 'P_016', 'P_006', 'P_019', 'P_015', 'P_011', 'P_023', 'P_002', 'P_025',]

    df_sols['OriginalID_Group'] = ['CTRL' if id in ls_ctrl else ('STRC' if id in ls_str else ('UNST' if id in ls_unst else 'GALL')) for id in df_sols['OriginalID_PT']]


    'P_001-Pre-1'
    'P_00k-Pst-12'




    #! preparing df for summary

    #* general
    df_sols[['TLength','NSegm','NJoint','TCost', 'Stress']] = 0

    #* materials
    df_sols[['NSegmRoad','LenRoad','NSegmReinfRoad','LenReinfRoad','NSegmWood','LenWood','NSegmSteel','LenSteel']] = 0

    #* anchors
    df_sols[['LeftAnc','MidAnc','RightAnc', 'NSegmLeftAnc', 'NSegmMidAnc','NSegmRightAnc']] = 0

    #* joints
    df_sols[['LargestYJoint', 'SmallestYJoint', 'LargestXJoint', 'SmallestXJoint']] = 0
    df_sols[['NJointBelowWater', 'NJointBoatRegion','NJointSingleSegment']] = 0
    df_sols[['BraceLeftWall', 'BraceRightWall']] = 0

    #* metrics
    df_sols[['StructDensity', 'THeight', 'TSpan']] = 0 # 2*segm /(joints*(joints - 1))

    #* connections
    df_sols[['NConnecSupRoad','NConnecRoadRoad','NConnecSupSup']] = 0

    #* avg angles
    df_sols[['AvgAngleAll','AvgAngleRoad','AvgAngleReinfRoad','AvgAngleWood', 'AvgAngleSteel']] = 0
    df_sols[['MaxAngleAll','MaxAngleRoad','MaxAngleReinfRoad','MaxAngleWood', 'MaxAngleSteel']]= 0
    df_sols[['MinAngleAll','MinAngleRoad','MinAngleReinfRoad','MinAngleWood', 'MinAngleSteel']]= 0

    waterlevel = 3.25
    boatshape = shapely.geometry.Polygon(
        [
            (10, 2.35),
            (8.9, 2.75),
            (7.9, 3.3),
            (7.9, 3.45),
            (8.9, 2.85),
            (8.9, 5.15),
            (9.4, 6.25),
            (10.6, 6.25),
            (11.1, 5.15),
            (11.1, 2.85),
            (12.1, 3.45),
            (12.1, 3.3),
            (11.1, 2.75),
        ]

    )

    #! getting summary info from solutions' save files
    for n, sol in enumerate(ls_solf):
        #read file (layout json)
        fname = sol[1]                                  # filename
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
        df_MatSummary['Materials']= ''
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
        #* Stress (relevant for RT)
        if '-S_' in fname:
            Mstress = float(fname.split('-')[-1].replace('S_',''))
            df_sols.loc[n,'Stress'] = Mstress
        else:
            df_sols.loc[n,'Stress'] = 0

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
            leftanc_used = 1
            df_sols.loc[n,'LeftAnc'] = 1

            nsleftanc = df_Edge['m_NodeAGuid'].to_list().count(leftanc_id) + df_Edge['m_NodeBGuid'].to_list().count(leftanc_id)
            leftancroad = df_Edge[(df_Edge['m_NodeAGuid']==leftanc_id) | (df_Edge['m_NodeBGuid']==leftanc_id)]['m_MaterialType'].to_list().count(1)
            leftancrroad = df_Edge[(df_Edge['m_NodeAGuid']==leftanc_id) | (df_Edge['m_NodeBGuid']==leftanc_id)]['m_MaterialType'].to_list().count(2)
            leftancwood = df_Edge[(df_Edge['m_NodeAGuid']==leftanc_id) | (df_Edge['m_NodeBGuid']==leftanc_id)]['m_MaterialType'].to_list().count(3)
            leftancsteel = df_Edge[(df_Edge['m_NodeAGuid']==leftanc_id) | (df_Edge['m_NodeBGuid']==leftanc_id)]['m_MaterialType'].to_list().count(4)

        else:
            leftanc_used = 0
            df_sols.loc[n,'LeftAnc'] = 0

            nsleftanc = 0
            leftancroad = 0
            leftancrroad = 0
            leftancwood = 0
            leftancsteel = 0

        df_sols.loc[n,'NSegmLeftAnc'] = nsleftanc
        df_sols.loc[n,'LeftAncRoad'] = leftancroad
        df_sols.loc[n,'LeftAncReinfRoad'] = leftancrroad
        df_sols.loc[n,'LeftAncWood'] = leftancwood
        df_sols.loc[n,'LeftAncSteel'] = leftancsteel


        if rightanc_id in df_Edge['m_NodeAGuid'].to_list() or rightanc_id in df_Edge['m_NodeBGuid'].to_list():
            rightanc_used = 1
            df_sols.loc[n,'RightAnc'] = 1
            df_sols.loc[n,'NSegmRightAnc'] = df_Edge['m_NodeAGuid'].to_list().count(rightanc_id) + df_Edge['m_NodeBGuid'].to_list().count(rightanc_id)
            df_sols.loc[n,'RightAncRoad'] = df_Edge[(df_Edge['m_NodeAGuid']==rightanc_id) | (df_Edge['m_NodeBGuid']==rightanc_id)]['m_MaterialType'].to_list().count(1)
            df_sols.loc[n,'RightAncReinfRoad'] = df_Edge[(df_Edge['m_NodeAGuid']==rightanc_id) | (df_Edge['m_NodeBGuid']==rightanc_id)]['m_MaterialType'].to_list().count(2)
            df_sols.loc[n,'RightAncWood'] = df_Edge[(df_Edge['m_NodeAGuid']==rightanc_id) | (df_Edge['m_NodeBGuid']==rightanc_id)]['m_MaterialType'].to_list().count(3)
            df_sols.loc[n,'RightAncSteel'] = df_Edge[(df_Edge['m_NodeAGuid']==rightanc_id) | (df_Edge['m_NodeBGuid']==rightanc_id)]['m_MaterialType'].to_list().count(4)
        else:
            rightanc_used = 0
            df_sols.loc[n,'RightAnc'] = 0
            df_sols.loc[n,'NSegmRightAnc'] = 0
            df_sols.loc[n,'RightAncRoad'] = 0
            df_sols.loc[n,'RightAncReinfRoad'] = 0
            df_sols.loc[n,'RightAncWood'] = 0
            df_sols.loc[n,'RightAncSteel'] = 0

        if midanc_id in df_Edge['m_NodeAGuid'].to_list() or midanc_id in df_Edge['m_NodeBGuid'].to_list():
            midanc_used = 1
            df_sols.loc[n,'MidAnc'] = 1
            df_sols.loc[n,'NSegmMidAnc'] = df_Edge['m_NodeAGuid'].to_list().count(midanc_id) + df_Edge['m_NodeBGuid'].to_list().count(midanc_id)
            df_sols.loc[n,'MidAncRoad'] = df_Edge[(df_Edge['m_NodeAGuid']==midanc_id) | (df_Edge['m_NodeBGuid']==midanc_id)]['m_MaterialType'].to_list().count(1)
            df_sols.loc[n,'MidAncReinfRoad'] = df_Edge[(df_Edge['m_NodeAGuid']==midanc_id) | (df_Edge['m_NodeBGuid']==midanc_id)]['m_MaterialType'].to_list().count(2)
            df_sols.loc[n,'MidAncWood'] = df_Edge[(df_Edge['m_NodeAGuid']==midanc_id) | (df_Edge['m_NodeBGuid']==midanc_id)]['m_MaterialType'].to_list().count(3)
            df_sols.loc[n,'MidAncSteel'] = df_Edge[(df_Edge['m_NodeAGuid']==midanc_id) | (df_Edge['m_NodeBGuid']==midanc_id)]['m_MaterialType'].to_list().count(4)

        else:
            midanc_used = 0
            df_sols.loc[n,'MidAnc'] = 0
            df_sols.loc[n,'NSegmMidAnc'] = 0
            df_sols.loc[n,'MidAncRoad'] = 0
            df_sols.loc[n,'MidAncReinfRoad'] = 0
            df_sols.loc[n,'MidAncWood'] = 0
            df_sols.loc[n,'MidAncSteel'] = 0


        #* joints
        if leftanc_used == 0:
            df_AncJon.drop(0, inplace=True) # drop left anchor from df_AncJon

        if rightanc_used == 0:
            df_AncJon.drop(1, inplace=True) # drop right anchor from df_AncJon

        if midanc_used == 0:
            df_AncJon.drop(2, inplace=True) # drop right anchor from df_AncJon

        df_sols.loc[n,'LargestYJoint'] = df_AncJon['m_Pos.y'].max()
        df_sols.loc[n,'SmallestYJoint'] = df_AncJon['m_Pos.y'].min()
        df_sols.loc[n,'LargestXJoint'] = df_AncJon['m_Pos.x'].max()
        df_sols.loc[n,'SmallestXJoint'] = df_AncJon['m_Pos.x'].min()
        df_sols.loc[n,'BraceLeftWall'] = ((df_Joints['m_Pos.x'] <= 0.3) & (df_Joints['m_Pos.y'] < 5)).sum()
        df_sols.loc[n,'BraceRightWall'] = ((df_Joints['m_Pos.x'] >= 13.7) & (df_Joints['m_Pos.y'] < 5.75)).sum()
        df_sols.loc[n,'NJointBelowWater'] = (df_Joints['m_Pos.y']<=waterlevel).sum()

        # joints in the boat area
        nboatarea = 0
        all_joints = list(zip(df_Joints['m_Pos.x'],df_Joints['m_Pos.y']))
        for j in all_joints:
            if shapely.geometry.Point(j).within(boatshape):
                nboatarea = nboatarea +1

        df_sols.loc[n,'NJointBoatRegion'] = nboatarea

        # joints with single segment
        all_segs = df_Edge['m_NodeAGuid'].to_list() + df_Edge['m_NodeBGuid'].to_list()
        nsingleseg = count_non_repeated_elements(all_segs)
        df_sols.loc[n,'NJointSingleSegment'] = nsingleseg

        #* metrics
        df_sols.loc[n,'StructDensity'] = 2*nseg/(njoin*(njoin-1))
        df_sols.loc[n,'THeight'] = df_AncJon['m_Pos.y'].max() - df_AncJon['m_Pos.y'].min()
        df_sols.loc[n,'TSpan'] = df_AncJon['m_Pos.x'].max() - df_AncJon['m_Pos.x'].min()

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


        #* angles ALL
        ls_joints = df_AncJon['m_Guid']
        ls_angles = []
        df_EdgeAngle = df_Edge.copy()

        for nd in ls_joints:
            df_ss = df_EdgeAngle[(df_EdgeAngle['m_NodeAGuid']==nd) | (df_Edge['m_NodeBGuid']==nd)]

            if len(df_ss) >= 1:
                df_EdgeAngle.drop(df_ss.index, inplace=True) # update df_edges to not duplicate the segments

                df_ss.reset_index(drop=True, inplace=True) # reset index of subset for the loop

                for sg in range(len(df_ss.index)):
                    x1 = df_ss.loc[sg,'nAx']
                    x2 = df_ss.loc[sg,'nBx']
                    y1 = df_ss.loc[sg,'nAy']
                    y2 = df_ss.loc[sg,'nBy']
                    ls_angles.append(math.degrees(math.atan((y2-y1)/(x2-x1)))) #degrees


        ls_abs_angles = [abs(ele) for ele in ls_angles] # get absolute values
        if ls_abs_angles == []:
            df_sols.loc[n,'AvgAngleAll'] = 0
            df_sols.loc[n,'MaxAngleAll'] = 0
            df_sols.loc[n,'MinAngleAll'] = 0
        else:
            df_sols.loc[n,'AvgAngleAll'] = np.average(ls_abs_angles)
            df_sols.loc[n,'MaxAngleAll'] = np.max(ls_abs_angles)
            df_sols.loc[n,'MinAngleAll'] = np.min(ls_abs_angles)


        #* angles ROAD
        ls_joints = df_AncJon['m_Guid']
        ls_angles_r = []
        df_EdgeAngle_r = df_Edge.copy()

        for nd in ls_joints:
            df_ss_r = df_EdgeAngle_r[((df_EdgeAngle_r['m_NodeAGuid']==nd) | (df_EdgeAngle_r['m_NodeBGuid']==nd)) & (df_EdgeAngle_r['m_MaterialType']==1)]
            if len(df_ss_r) >= 1:
                df_EdgeAngle_r.drop(df_ss_r.index, inplace=True) # update df_edges to not duplicate the segments

                df_ss_r.reset_index(drop=True, inplace=True) # reset index of subset for the loop

                for sg in range(len(df_ss_r.index)):
                    x1 = df_ss_r.loc[sg,'nAx']
                    x2 = df_ss_r.loc[sg,'nBx']
                    y1 = df_ss_r.loc[sg,'nAy']
                    y2 = df_ss_r.loc[sg,'nBy']
                    ls_angles_r.append(math.degrees(math.atan((y2-y1)/(x2-x1)))) #degrees

        ls_abs_angles_r = [abs(ele) for ele in ls_angles_r] # get absolute values

        if ls_abs_angles_r == []:
            df_sols.loc[n,'AvgAngleRoad'] = 0
            df_sols.loc[n,'MaxAngleRoad'] = 0
            df_sols.loc[n,'MinAngleRoad'] = 0
        else:
            df_sols.loc[n,'AvgAngleRoad'] = np.average(ls_abs_angles_r)
            df_sols.loc[n,'MaxAngleRoad'] = np.max(ls_abs_angles_r)
            df_sols.loc[n,'MinAngleRoad'] = np.min(ls_abs_angles_r)

        #* angles REINF ROAD
        ls_joints = df_AncJon['m_Guid']
        ls_angles_rr = []
        df_EdgeAngle_rr = df_Edge.copy()

        for nd in ls_joints:
            df_ss_rr = df_EdgeAngle_rr[((df_EdgeAngle_rr['m_NodeAGuid']==nd) | (df_EdgeAngle_rr['m_NodeBGuid']==nd)) & (df_EdgeAngle_rr['m_MaterialType']==2)]
            if len(df_ss_rr) >= 1:
                df_EdgeAngle_rr.drop(df_ss_rr.index, inplace=True) # update df_edges to not duplicate the segments

                df_ss_rr.reset_index(drop=True, inplace=True) # reset index of subset for the loop

                for sg in range(len(df_ss_rr.index)):
                    x1 = df_ss_rr.loc[sg,'nAx']
                    x2 = df_ss_rr.loc[sg,'nBx']
                    y1 = df_ss_rr.loc[sg,'nAy']
                    y2 = df_ss_rr.loc[sg,'nBy']
                    ls_angles_rr.append(math.degrees(math.atan((y2-y1)/(x2-x1)))) #degrees

        ls_abs_angles_rr = [abs(ele) for ele in ls_angles_rr] # get absolute values

        if ls_abs_angles_rr == []:
            df_sols.loc[n,'AvgAngleReinfRoad'] = 0
            df_sols.loc[n,'MaxAngleReinfRoad'] = 0
            df_sols.loc[n,'MinAngleReinfRoad'] = 0
        else:
            df_sols.loc[n,'AvgAngleReinfRoad'] = np.average(ls_abs_angles_rr)
            df_sols.loc[n,'MaxAngleReinfRoad'] = np.max(ls_abs_angles_rr)
            df_sols.loc[n,'MinAngleReinfRoad'] = np.min(ls_abs_angles_rr)

        #* angles WOOD
        ls_joints = df_AncJon['m_Guid']
        ls_angles_w = []
        df_EdgeAngle_w = df_Edge.copy()

        for nd in ls_joints:
            df_ss_w = df_EdgeAngle_w[((df_EdgeAngle_w['m_NodeAGuid']==nd) | (df_EdgeAngle_w['m_NodeBGuid']==nd)) & (df_EdgeAngle_w['m_MaterialType']==3)]
            if len(df_ss_w) >= 1:
                df_EdgeAngle_w.drop(df_ss_w.index, inplace=True) # update df_edges to not duplicate the segments

                df_ss_w.reset_index(drop=True, inplace=True) # reset index of subset for the loop

                for sg in range(len(df_ss_w.index)):
                    x1 = df_ss_w.loc[sg,'nAx']
                    x2 = df_ss_w.loc[sg,'nBx']
                    y1 = df_ss_w.loc[sg,'nAy']
                    y2 = df_ss_w.loc[sg,'nBy']
                    ls_angles_w.append(math.degrees(math.atan((y2-y1)/(x2-x1)))) #degrees

        ls_abs_angles_w = [abs(ele) for ele in ls_angles_w] # get absolute values

        if ls_abs_angles_w == []:
            df_sols.loc[n,'AvgAngleWood'] = 0
            df_sols.loc[n,'MaxAngleWood'] = 0
            df_sols.loc[n,'MinAngleRoad'] = 0
        else:
            df_sols.loc[n,'AvgAngleWood'] = np.average(ls_abs_angles_w)
            df_sols.loc[n,'MaxAngleWood'] = np.max(ls_abs_angles_w)
            df_sols.loc[n,'MinAngleWood'] = np.min(ls_abs_angles_w)

        #* angles STEEL
        ls_joints = df_AncJon['m_Guid']
        ls_angles_s = []
        df_EdgeAngle_s = df_Edge.copy()

        for nd in ls_joints:
            df_ss_s = df_EdgeAngle_s[((df_EdgeAngle_s['m_NodeAGuid']==nd) | (df_EdgeAngle_s['m_NodeBGuid']==nd)) & (df_EdgeAngle_s['m_MaterialType']==4)]
            if len(df_ss_s) >= 1:
                df_EdgeAngle_s.drop(df_ss_s.index, inplace=True) # update df_edges to not duplicate the segments

                df_ss_s.reset_index(drop=True, inplace=True) # reset index of subset for the loop

                for sg in range(len(df_ss_s.index)):
                    x1 = df_ss_s.loc[sg,'nAx']
                    x2 = df_ss_s.loc[sg,'nBx']
                    y1 = df_ss_s.loc[sg,'nAy']
                    y2 = df_ss_s.loc[sg,'nBy']
                    ls_angles_s.append(math.degrees(math.atan((y2-y1)/(x2-x1)))) #degrees

        ls_abs_angles_s = [abs(ele) for ele in ls_angles_s] # get absolute values

        if ls_abs_angles_s == []:
            df_sols.loc[n,'AvgAngleSteel'] = 0
            df_sols.loc[n,'MaxAngleSteel'] = 0
            df_sols.loc[n,'MinAngleSteel'] = 0
        else:
            df_sols.loc[n,'AvgAngleSteel'] = np.average(ls_abs_angles_s)
            df_sols.loc[n,'MaxAngleSteel'] = np.max(ls_abs_angles_s)
            df_sols.loc[n,'MinAngleSteel'] = np.min(ls_abs_angles_s)


    if saveExcel == True:
        df_sols.to_excel(f'{pth}/dataset_quant.xlsx')
        df_sols.to_csv(f'{pth}/dataset_quant.csv')
        print('Dataset saved!')

    print('Dataset generated!')
    return df_sols

# %% ADDING SOLUTION TO DATASET

def count_non_repeated_elements(lst):
    # Count occurrences of each element
    element_counts = Counter(lst)
    # Filter elements that appear only once
    non_repeated_elements = [element for element, count in element_counts.items() if count == 1]
    # Return the number of non-repeated elements
    return len(non_repeated_elements)

def add_solution_to_dataset(orig_dataset, fjson_path, save_path, saveExcel=True, savename='dataset_updated'):

    if Path(f'{save_path}/{savename}.xlsx').exists() == True:
        curr_dataset = read_updated_dataset(save_path, f_name=savename)
        print('run n+1 time')
    else:
        curr_dataset = orig_dataset.copy()
        print('run first time')

    curr_dataset.loc[len(curr_dataset.index)]=0
    n = len(curr_dataset)-1

    #! finding solutions' save files
    print('Adding new solution to dataset...')

    file_path = fjson_path
    pth = Path(file_path)

    fname = pth.stem.replace('-0','-')

    waterlevel = 3.25
    boatshape = shapely.geometry.Polygon(
        [
            (10, 2.35),
            (8.9, 2.75),
            (7.9, 3.3),
            (7.9, 3.45),
            (8.9, 2.85),
            (8.9, 5.15),
            (9.4, 6.25),
            (10.6, 6.25),
            (11.1, 5.15),
            (11.1, 2.85),
            (12.1, 3.45),
            (12.1, 3.3),
            (11.1, 2.75),
        ]
    )

    #! getting summary info from solution save file

    df = pd.read_json(f'{pth}')

    print(f'Extracting inf from {fname}.json')

    df_Anchor=df.iloc[0,7]
    df_Edge=df.iloc[1,7]
    df_Joints=df.iloc[2,7]
    df_Phase=df.iloc[3,7]

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
    df_MatSummary['Materials']= ''
    df_MatSummary['AvgSize']= df_Edge.groupby('m_MaterialType')['EdgeSize'].mean()
    df_MatSummary['NumSegments']= df_Edge.groupby('m_MaterialType')['EdgeSize'].count()


    for i in range(len(df_MatSummary.index)):
        matType=MatDict[str(df_MatSummary.iloc[i,1])][0]
        matLen=df_MatSummary.iloc[i,0]
        df_MatSummary.iloc[i,2]= matLen * matType
        df_MatSummary.iloc[i,3]= MatDict[str(df_MatSummary.iloc[i,1])][1]

    nseg = df_MatSummary['NumSegments'].sum()
    njoin = len(set(df_Edge['m_NodeAGuid'].to_list() + df_Edge['m_NodeBGuid'].to_list()))



    #! get values & add to df_sols
    #* Stress (relevant for RT)
    if '-S_' in fname:
        Mstress = float(fname.split('-')[-1].replace('S_',''))
        curr_dataset.loc[n,'Stress'] = Mstress
    else:
        curr_dataset.loc[n,'Stress'] = 0

    #* general
    curr_dataset.loc[n,'TLength'] = df_MatSummary['EdgeSize'].sum()
    curr_dataset.loc[n,'NSegm'] = nseg
    curr_dataset.loc[n,'NJoint'] = njoin
    curr_dataset.loc[n,'TCost'] = df_MatSummary['CostTotal'].sum()

    #* materials
    mat_used = df_MatSummary.index.to_list()
    if 1 in mat_used:
        curr_dataset.loc[n,'NSegmRoad'] = df_MatSummary.loc[1,'NumSegments']
        curr_dataset.loc[n,'LenRoad'] = df_MatSummary.loc[1,'EdgeSize']
    else:
        curr_dataset.loc[n,'NSegmRoad'] = 0
        curr_dataset.loc[n,'LenRoad'] = 0

    if 2 in mat_used:
        curr_dataset.loc[n,'NSegmReinfRoad'] = df_MatSummary.loc[2,'NumSegments']
        curr_dataset.loc[n,'LenReinfRoad'] = df_MatSummary.loc[2,'EdgeSize']
    else:
        curr_dataset.loc[n,'NSegmReinfRoad'] = 0
        curr_dataset.loc[n,'LenReinfRoad'] = 0

    if 3 in mat_used:
        curr_dataset.loc[n,'NSegmWood'] = df_MatSummary.loc[3,'NumSegments']
        curr_dataset.loc[n,'LenWood'] = df_MatSummary.loc[3,'EdgeSize']
    else:
        curr_dataset.loc[n,'NSegmWood'] = 0
        curr_dataset.loc[n,'LenWood'] = 0

    if 4 in mat_used:
        curr_dataset.loc[n,'NSegmSteel'] = df_MatSummary.loc[4,'NumSegments']
        curr_dataset.loc[n,'LenSteel'] = df_MatSummary.loc[4,'EdgeSize']
    else:
        curr_dataset.loc[n,'NSegmSteel'] = 0
        curr_dataset.loc[n,'LenSteel'] = 0

    #* anchors
    leftanc_id = df_Anchor.loc[0,'m_Guid']
    rightanc_id = df_Anchor.loc[1,'m_Guid']
    midanc_id = df_Anchor.loc[2,'m_Guid']

    if leftanc_id in df_Edge['m_NodeAGuid'].to_list() or leftanc_id in df_Edge['m_NodeBGuid'].to_list():
        leftanc_used = 1
        curr_dataset.loc[n,'LeftAnc'] = 1

        nsleftanc = df_Edge['m_NodeAGuid'].to_list().count(leftanc_id) + df_Edge['m_NodeBGuid'].to_list().count(leftanc_id)
        leftancroad = df_Edge[(df_Edge['m_NodeAGuid']==leftanc_id) | (df_Edge['m_NodeBGuid']==leftanc_id)]['m_MaterialType'].to_list().count(1)
        leftancrroad = df_Edge[(df_Edge['m_NodeAGuid']==leftanc_id) | (df_Edge['m_NodeBGuid']==leftanc_id)]['m_MaterialType'].to_list().count(2)
        leftancwood = df_Edge[(df_Edge['m_NodeAGuid']==leftanc_id) | (df_Edge['m_NodeBGuid']==leftanc_id)]['m_MaterialType'].to_list().count(3)
        leftancsteel = df_Edge[(df_Edge['m_NodeAGuid']==leftanc_id) | (df_Edge['m_NodeBGuid']==leftanc_id)]['m_MaterialType'].to_list().count(4)

    else:
        leftanc_used = 0
        curr_dataset.loc[n,'LeftAnc'] = 0

        nsleftanc = 0
        leftancroad = 0
        leftancrroad = 0
        leftancwood = 0
        leftancsteel = 0

    curr_dataset.loc[n,'NSegmLeftAnc'] = nsleftanc
    curr_dataset.loc[n,'LeftAncRoad'] = leftancroad
    curr_dataset.loc[n,'LeftAncReinfRoad'] = leftancrroad
    curr_dataset.loc[n,'LeftAncWood'] = leftancwood
    curr_dataset.loc[n,'LeftAncSteel'] = leftancsteel


    if rightanc_id in df_Edge['m_NodeAGuid'].to_list() or rightanc_id in df_Edge['m_NodeBGuid'].to_list():
        rightanc_used = 1
        curr_dataset.loc[n,'RightAnc'] = 1
        curr_dataset.loc[n,'NSegmRightAnc'] = df_Edge['m_NodeAGuid'].to_list().count(rightanc_id) + df_Edge['m_NodeBGuid'].to_list().count(rightanc_id)
        curr_dataset.loc[n,'RightAncRoad'] = df_Edge[(df_Edge['m_NodeAGuid']==rightanc_id) | (df_Edge['m_NodeBGuid']==rightanc_id)]['m_MaterialType'].to_list().count(1)
        curr_dataset.loc[n,'RightAncReinfRoad'] = df_Edge[(df_Edge['m_NodeAGuid']==rightanc_id) | (df_Edge['m_NodeBGuid']==rightanc_id)]['m_MaterialType'].to_list().count(2)
        curr_dataset.loc[n,'RightAncWood'] = df_Edge[(df_Edge['m_NodeAGuid']==rightanc_id) | (df_Edge['m_NodeBGuid']==rightanc_id)]['m_MaterialType'].to_list().count(3)
        curr_dataset.loc[n,'RightAncSteel'] = df_Edge[(df_Edge['m_NodeAGuid']==rightanc_id) | (df_Edge['m_NodeBGuid']==rightanc_id)]['m_MaterialType'].to_list().count(4)
    else:
        rightanc_used = 0
        curr_dataset.loc[n,'RightAnc'] = 0
        curr_dataset.loc[n,'NSegmRightAnc'] = 0
        curr_dataset.loc[n,'RightAncRoad'] = 0
        curr_dataset.loc[n,'RightAncReinfRoad'] = 0
        curr_dataset.loc[n,'RightAncWood'] = 0
        curr_dataset.loc[n,'RightAncSteel'] = 0

    if midanc_id in df_Edge['m_NodeAGuid'].to_list() or midanc_id in df_Edge['m_NodeBGuid'].to_list():
        midanc_used = 1
        curr_dataset.loc[n,'MidAnc'] = 1
        curr_dataset.loc[n,'NSegmMidAnc'] = df_Edge['m_NodeAGuid'].to_list().count(midanc_id) + df_Edge['m_NodeBGuid'].to_list().count(midanc_id)
        curr_dataset.loc[n,'MidAncRoad'] = df_Edge[(df_Edge['m_NodeAGuid']==midanc_id) | (df_Edge['m_NodeBGuid']==midanc_id)]['m_MaterialType'].to_list().count(1)
        curr_dataset.loc[n,'MidAncReinfRoad'] = df_Edge[(df_Edge['m_NodeAGuid']==midanc_id) | (df_Edge['m_NodeBGuid']==midanc_id)]['m_MaterialType'].to_list().count(2)
        curr_dataset.loc[n,'MidAncWood'] = df_Edge[(df_Edge['m_NodeAGuid']==midanc_id) | (df_Edge['m_NodeBGuid']==midanc_id)]['m_MaterialType'].to_list().count(3)
        curr_dataset.loc[n,'MidAncSteel'] = df_Edge[(df_Edge['m_NodeAGuid']==midanc_id) | (df_Edge['m_NodeBGuid']==midanc_id)]['m_MaterialType'].to_list().count(4)

    else:
        midanc_used = 0
        curr_dataset.loc[n,'MidAnc'] = 0
        curr_dataset.loc[n,'NSegmMidAnc'] = 0
        curr_dataset.loc[n,'MidAncRoad'] = 0
        curr_dataset.loc[n,'MidAncReinfRoad'] = 0
        curr_dataset.loc[n,'MidAncWood'] = 0
        curr_dataset.loc[n,'MidAncSteel'] = 0


    #* joints
    if leftanc_used == 0:
        df_AncJon.drop(0, inplace=True) # drop left anchor from df_AncJon

    if rightanc_used == 0:
        df_AncJon.drop(1, inplace=True) # drop right anchor from df_AncJon

    if midanc_used == 0:
        df_AncJon.drop(2, inplace=True) # drop right anchor from df_AncJon

    curr_dataset.loc[n,'LargestYJoint'] = df_AncJon['m_Pos.y'].max()
    curr_dataset.loc[n,'SmallestYJoint'] = df_AncJon['m_Pos.y'].min()
    curr_dataset.loc[n,'LargestXJoint'] = df_AncJon['m_Pos.x'].max()
    curr_dataset.loc[n,'SmallestXJoint'] = df_AncJon['m_Pos.x'].min()
    curr_dataset.loc[n,'BraceLeftWall'] = ((df_Joints['m_Pos.x'] <= 0.3) & (df_Joints['m_Pos.y'] < 5)).sum()
    curr_dataset.loc[n,'BraceRightWall'] = ((df_Joints['m_Pos.x'] >= 13.7) & (df_Joints['m_Pos.y'] < 5.75)).sum()
    curr_dataset.loc[n,'NJointBelowWater'] = (df_Joints['m_Pos.y']<=waterlevel).sum()

    # joints in the boat area
    nboatarea = 0
    all_joints = list(zip(df_Joints['m_Pos.x'],df_Joints['m_Pos.y']))
    for j in all_joints:
        if shapely.geometry.Point(j).within(boatshape):
            nboatarea = nboatarea +1

    curr_dataset.loc[n,'NJointBoatRegion'] = nboatarea

    # joints with single segment
    all_segs = df_Edge['m_NodeAGuid'].to_list() + df_Edge['m_NodeBGuid'].to_list()
    nsingleseg = count_non_repeated_elements(all_segs)
    curr_dataset.loc[n,'NJointSingleSegment'] = nsingleseg

    #* metrics
    curr_dataset.loc[n,'StructDensity'] = 2*nseg/(njoin*(njoin-1))
    curr_dataset.loc[n,'THeight'] = df_AncJon['m_Pos.y'].max() - df_AncJon['m_Pos.y'].min()
    curr_dataset.loc[n,'TSpan'] = df_AncJon['m_Pos.x'].max() - df_AncJon['m_Pos.x'].min()

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

    curr_dataset.loc[n,'NConnecSupRoad'] = ncsuproad
    curr_dataset.loc[n,'NConnecRoadRoad'] = ncroadroad
    curr_dataset.loc[n,'NConnecSupSup'] = ncsupsup

    #* angles ALL
    ls_joints = df_AncJon['m_Guid']
    ls_angles = []
    df_EdgeAngle = df_Edge.copy()

    for nd in ls_joints:
        df_ss = df_EdgeAngle[(df_EdgeAngle['m_NodeAGuid']==nd) | (df_Edge['m_NodeBGuid']==nd)]

        if len(df_ss) >= 1:
            df_EdgeAngle.drop(df_ss.index, inplace=True) # update df_edges to not duplicate the segments

            df_ss.reset_index(drop=True, inplace=True) # reset index of subset for the loop

            for sg in range(len(df_ss.index)):
                x1 = df_ss.loc[sg,'nAx']
                x2 = df_ss.loc[sg,'nBx']
                y1 = df_ss.loc[sg,'nAy']
                y2 = df_ss.loc[sg,'nBy']
                ls_angles.append(math.degrees(math.atan((y2-y1)/(x2-x1)))) #degrees


    ls_abs_angles = [abs(ele) for ele in ls_angles] # get absolute values
    if ls_abs_angles == []:
        curr_dataset.loc[n,'AvgAngleAll'] = 0
        curr_dataset.loc[n,'MaxAngleAll'] = 0
        curr_dataset.loc[n,'MinAngleAll'] = 0
    else:
        curr_dataset.loc[n,'AvgAngleAll'] = np.average(ls_abs_angles)
        curr_dataset.loc[n,'MaxAngleAll'] = np.max(ls_abs_angles)
        curr_dataset.loc[n,'MinAngleAll'] = np.min(ls_abs_angles)


    #* angles ROAD
    ls_joints = df_AncJon['m_Guid']
    ls_angles_r = []
    df_EdgeAngle_r = df_Edge.copy()

    for nd in ls_joints:
        df_ss_r = df_EdgeAngle_r[((df_EdgeAngle_r['m_NodeAGuid']==nd) | (df_EdgeAngle_r['m_NodeBGuid']==nd)) & (df_EdgeAngle_r['m_MaterialType']==1)]
        if len(df_ss_r) >= 1:
            df_EdgeAngle_r.drop(df_ss_r.index, inplace=True) # update df_edges to not duplicate the segments

            df_ss_r.reset_index(drop=True, inplace=True) # reset index of subset for the loop

            for sg in range(len(df_ss_r.index)):
                x1 = df_ss_r.loc[sg,'nAx']
                x2 = df_ss_r.loc[sg,'nBx']
                y1 = df_ss_r.loc[sg,'nAy']
                y2 = df_ss_r.loc[sg,'nBy']
                ls_angles_r.append(math.degrees(math.atan((y2-y1)/(x2-x1)))) #degrees

    ls_abs_angles_r = [abs(ele) for ele in ls_angles_r] # get absolute values

    if ls_abs_angles_r == []:
        curr_dataset.loc[n,'AvgAngleRoad'] = 0
        curr_dataset.loc[n,'MaxAngleRoad'] = 0
        curr_dataset.loc[n,'MinAngleRoad'] = 0
    else:
        curr_dataset.loc[n,'AvgAngleRoad'] = np.average(ls_abs_angles_r)
        curr_dataset.loc[n,'MaxAngleRoad'] = np.max(ls_abs_angles_r)
        curr_dataset.loc[n,'MinAngleRoad'] = np.min(ls_abs_angles_r)

    #* angles REINF ROAD
    ls_joints = df_AncJon['m_Guid']
    ls_angles_rr = []
    df_EdgeAngle_rr = df_Edge.copy()

    for nd in ls_joints:
        df_ss_rr = df_EdgeAngle_rr[((df_EdgeAngle_rr['m_NodeAGuid']==nd) | (df_EdgeAngle_rr['m_NodeBGuid']==nd)) & (df_EdgeAngle_rr['m_MaterialType']==2)]
        if len(df_ss_rr) >= 1:
            df_EdgeAngle_rr.drop(df_ss_rr.index, inplace=True) # update df_edges to not duplicate the segments

            df_ss_rr.reset_index(drop=True, inplace=True) # reset index of subset for the loop

            for sg in range(len(df_ss_rr.index)):
                x1 = df_ss_rr.loc[sg,'nAx']
                x2 = df_ss_rr.loc[sg,'nBx']
                y1 = df_ss_rr.loc[sg,'nAy']
                y2 = df_ss_rr.loc[sg,'nBy']
                ls_angles_rr.append(math.degrees(math.atan((y2-y1)/(x2-x1)))) #degrees

    ls_abs_angles_rr = [abs(ele) for ele in ls_angles_rr] # get absolute values

    if ls_abs_angles_rr == []:
        curr_dataset.loc[n,'AvgAngleReinfRoad'] = 0
        curr_dataset.loc[n,'MaxAngleReinfRoad'] = 0
        curr_dataset.loc[n,'MinAngleReinfRoad'] = 0
    else:
        curr_dataset.loc[n,'AvgAngleReinfRoad'] = np.average(ls_abs_angles_rr)
        curr_dataset.loc[n,'MaxAngleReinfRoad'] = np.max(ls_abs_angles_rr)
        curr_dataset.loc[n,'MinAngleReinfRoad'] = np.min(ls_abs_angles_rr)

    #* angles WOOD
    ls_joints = df_AncJon['m_Guid']
    ls_angles_w = []
    df_EdgeAngle_w = df_Edge.copy()

    for nd in ls_joints:
        df_ss_w = df_EdgeAngle_w[((df_EdgeAngle_w['m_NodeAGuid']==nd) | (df_EdgeAngle_w['m_NodeBGuid']==nd)) & (df_EdgeAngle_w['m_MaterialType']==3)]
        if len(df_ss_w) >= 1:
            df_EdgeAngle_w.drop(df_ss_w.index, inplace=True) # update df_edges to not duplicate the segments

            df_ss_w.reset_index(drop=True, inplace=True) # reset index of subset for the loop

            for sg in range(len(df_ss_w.index)):
                x1 = df_ss_w.loc[sg,'nAx']
                x2 = df_ss_w.loc[sg,'nBx']
                y1 = df_ss_w.loc[sg,'nAy']
                y2 = df_ss_w.loc[sg,'nBy']
                ls_angles_w.append(math.degrees(math.atan((y2-y1)/(x2-x1)))) #degrees

    ls_abs_angles_w = [abs(ele) for ele in ls_angles_w] # get absolute values

    if ls_abs_angles_w == []:
        curr_dataset.loc[n,'AvgAngleWood'] = 0
        curr_dataset.loc[n,'MaxAngleWood'] = 0
        curr_dataset.loc[n,'MinAngleRoad'] = 0
    else:
        curr_dataset.loc[n,'AvgAngleWood'] = np.average(ls_abs_angles_w)
        curr_dataset.loc[n,'MaxAngleWood'] = np.max(ls_abs_angles_w)
        curr_dataset.loc[n,'MinAngleWood'] = np.min(ls_abs_angles_w)

    #* angles STEEL
    ls_joints = df_AncJon['m_Guid']
    ls_angles_s = []
    df_EdgeAngle_s = df_Edge.copy()

    for nd in ls_joints:
        df_ss_s = df_EdgeAngle_s[((df_EdgeAngle_s['m_NodeAGuid']==nd) | (df_EdgeAngle_s['m_NodeBGuid']==nd)) & (df_EdgeAngle_s['m_MaterialType']==4)]
        if len(df_ss_s) >= 1:
            df_EdgeAngle_s.drop(df_ss_s.index, inplace=True) # update df_edges to not duplicate the segments

            df_ss_s.reset_index(drop=True, inplace=True) # reset index of subset for the loop

            for sg in range(len(df_ss_s.index)):
                x1 = df_ss_s.loc[sg,'nAx']
                x2 = df_ss_s.loc[sg,'nBx']
                y1 = df_ss_s.loc[sg,'nAy']
                y2 = df_ss_s.loc[sg,'nBy']
                ls_angles_s.append(math.degrees(math.atan((y2-y1)/(x2-x1)))) #degrees

    ls_abs_angles_s = [abs(ele) for ele in ls_angles_s] # get absolute values

    if ls_abs_angles_s == []:
        curr_dataset.loc[n,'AvgAngleSteel'] = 0
        curr_dataset.loc[n,'MaxAngleSteel'] = 0
        curr_dataset.loc[n,'MinAngleSteel'] = 0
    else:
        curr_dataset.loc[n,'AvgAngleSteel'] = np.average(ls_abs_angles_s)
        curr_dataset.loc[n,'MaxAngleSteel'] = np.max(ls_abs_angles_s)
        curr_dataset.loc[n,'MinAngleSteel'] = np.min(ls_abs_angles_s)

    savepth = Path(r"C:\Py\DS_Viz_Exp\viz\savefiles")

    if saveExcel == True:
        curr_dataset.to_excel(f'{savepth}/{savename}.xlsx')
        curr_dataset.to_csv(f'{savepth}/{savename}.csv')

    print('Adding solution to dataset done!')
    return curr_dataset

#%% READ DATASET

def read_dataset(dir_data, f_name):
    df_dataset = pd.read_excel(f'{dir_data}/{f_name}.xlsx')
    df_dataset.drop(columns=df_dataset.columns[0], axis=1, inplace=True)
    return df_dataset

def read_updated_dataset(dir_data, f_name='dataset_updated'):
    df_upd = pd.read_excel(f'{dir_data}/{f_name}.xlsx')
    df_upd.drop(columns=df_upd.columns[0], axis=1, inplace=True)
    return df_upd

#pth = Path(r"C:\Py\DS_Viz_Exp\viz\savefiles")


#%%
'''
filep = r"C:\Py\DS_Viz_Exp\data\json\P0111.json"
ds_dir = Path(r"C:\Py\DS_Viz_Exp\viz\savefiles")

dataset = read_dataset(ds_dir, 'dataset_quant')

#%%

try:
    updated_dataset
except NameError:
    updated_dataset = add_solution_to_dataset(dataset,filep)
    print('run first time')
else:
    updated_dataset = add_solution_to_dataset(updated_dataset,filep)
    print('run n+1 time')




#%%

folder_path = r"C:\Py\DS_Viz_Exp\viz\savefiles"
dataset = create_dataset(folder_path)

# %%

#! finding solutions' save files
print('Creating dataset from saved solutions...')

folder_path = r"C:\Py\DS_Viz_Exp\viz\savefiles"
pth = Path(folder_path)

ls_solf = []

for p in pth.rglob("*.json"):
    ls_solf.append([p.parent, p.stem])

df_sols = pd.DataFrame(ls_solf, columns=['path', 'fullid_orig']).drop(columns=['path'])
df_sols['fullid_orig'] = df_sols['fullid_orig'].str.replace('-0','-')

#* general
df_sols[['TLength','NSegm','NJoint','TCost', 'Stress']] = 0

#* materials
df_sols[['NSegmRoad','LenRoad','NSegmReinfRoad','LenReinfRoad','NSegmWood','LenWood','NSegmSteel','LenSteel']] = 0

#* anchors
df_sols[['LeftAnc','MidAnc','RightAnc', 'NSegmLeftAnc', 'NSegmMidAnc','NSegmRightAnc']] = 0

#* joints
df_sols[['LargestYJoint', 'SmallestYJoint', 'LargestXJoint', 'SmallestXJoint']] = 0
df_sols[['NJointBelowWater', 'NJointBoatRegion','NJointSingleSegment']] = 0
df_sols[['BraceLeftWall', 'BraceRightWall']] = 0

#* metrics
df_sols[['StructDensity', 'THeight', 'TSpan']] = 0 # 2*segm /(joints*(joints - 1))

#* connections
df_sols[['NConnecSupRoad','NConnecRoadRoad','NConnecSupSup']] = 0

#* avg angles
df_sols[['AvgAngleAll','AvgAngleRoad','AvgAngleReinfRoad','AvgAngleWood', 'AvgAngleSteel']] = 0
df_sols[['MaxAngleAll','MaxAngleRoad','MaxAngleReinfRoad','MaxAngleWood', 'MaxAngleSteel']]= 0
df_sols[['MinAngleAll','MinAngleRoad','MinAngleReinfRoad','MinAngleWood', 'MinAngleSteel']]= 0

waterlevel = 3.25
boatshape = shapely.geometry.Polygon(
    [
        (10, 2.35),
        (8.9, 2.75),
        (7.9, 3.3),
        (7.9, 3.45),
        (8.9, 2.85),
        (8.9, 5.15),
        (9.4, 6.25),
        (10.6, 6.25),
        (11.1, 5.15),
        (11.1, 2.85),
        (12.1, 3.45),
        (12.1, 3.3),
        (11.1, 2.75),
    ]

)

#! getting summary info from solutions' save files
for n, sol in enumerate(ls_solf):
    #read file (layout json)
    fname = sol[1]                                  # filename
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
    df_MatSummary['Materials']= ''
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
    #* Stress (relevant for RT)
    if '-S_' in fname:
        Mstress = float(fname.split('-')[-1].replace('S_',''))
        df_sols.loc[n,'Stress'] = Mstress
    else:
        df_sols.loc[n,'Stress'] = 0

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
        leftanc_used = 1
        df_sols.loc[n,'LeftAnc'] = 1

        nsleftanc = df_Edge['m_NodeAGuid'].to_list().count(leftanc_id) + df_Edge['m_NodeBGuid'].to_list().count(leftanc_id)
        leftancroad = df_Edge[(df_Edge['m_NodeAGuid']==leftanc_id) | (df_Edge['m_NodeBGuid']==leftanc_id)]['m_MaterialType'].to_list().count(1)
        leftancrroad = df_Edge[(df_Edge['m_NodeAGuid']==leftanc_id) | (df_Edge['m_NodeBGuid']==leftanc_id)]['m_MaterialType'].to_list().count(2)
        leftancwood = df_Edge[(df_Edge['m_NodeAGuid']==leftanc_id) | (df_Edge['m_NodeBGuid']==leftanc_id)]['m_MaterialType'].to_list().count(3)
        leftancsteel = df_Edge[(df_Edge['m_NodeAGuid']==leftanc_id) | (df_Edge['m_NodeBGuid']==leftanc_id)]['m_MaterialType'].to_list().count(4)

    else:
        leftanc_used = 0
        df_sols.loc[n,'LeftAnc'] = 0

        nsleftanc = 0
        leftancroad = 0
        leftancrroad = 0
        leftancwood = 0
        leftancsteel = 0

    df_sols.loc[n,'NSegmLeftAnc'] = nsleftanc
    df_sols.loc[n,'LeftAncRoad'] = leftancroad
    df_sols.loc[n,'LeftAncReinfRoad'] = leftancrroad
    df_sols.loc[n,'LeftAncWood'] = leftancwood
    df_sols.loc[n,'LeftAncSteel'] = leftancsteel


    if rightanc_id in df_Edge['m_NodeAGuid'].to_list() or rightanc_id in df_Edge['m_NodeBGuid'].to_list():
        rightanc_used = 1
        df_sols.loc[n,'RightAnc'] = 1
        df_sols.loc[n,'NSegmRightAnc'] = df_Edge['m_NodeAGuid'].to_list().count(rightanc_id) + df_Edge['m_NodeBGuid'].to_list().count(rightanc_id)
        df_sols.loc[n,'RightAncRoad'] = df_Edge[(df_Edge['m_NodeAGuid']==rightanc_id) | (df_Edge['m_NodeBGuid']==rightanc_id)]['m_MaterialType'].to_list().count(1)
        df_sols.loc[n,'RightAncReinfRoad'] = df_Edge[(df_Edge['m_NodeAGuid']==rightanc_id) | (df_Edge['m_NodeBGuid']==rightanc_id)]['m_MaterialType'].to_list().count(2)
        df_sols.loc[n,'RightAncWood'] = df_Edge[(df_Edge['m_NodeAGuid']==rightanc_id) | (df_Edge['m_NodeBGuid']==rightanc_id)]['m_MaterialType'].to_list().count(3)
        df_sols.loc[n,'RightAncSteel'] = df_Edge[(df_Edge['m_NodeAGuid']==rightanc_id) | (df_Edge['m_NodeBGuid']==rightanc_id)]['m_MaterialType'].to_list().count(4)
    else:
        rightanc_used = 0
        df_sols.loc[n,'RightAnc'] = 0
        df_sols.loc[n,'NSegmRightAnc'] = 0
        df_sols.loc[n,'RightAncRoad'] = 0
        df_sols.loc[n,'RightAncReinfRoad'] = 0
        df_sols.loc[n,'RightAncWood'] = 0
        df_sols.loc[n,'RightAncSteel'] = 0

    if midanc_id in df_Edge['m_NodeAGuid'].to_list() or midanc_id in df_Edge['m_NodeBGuid'].to_list():
        midanc_used = 1
        df_sols.loc[n,'MidAnc'] = 1
        df_sols.loc[n,'NSegmMidAnc'] = df_Edge['m_NodeAGuid'].to_list().count(midanc_id) + df_Edge['m_NodeBGuid'].to_list().count(midanc_id)
        df_sols.loc[n,'MidAncRoad'] = df_Edge[(df_Edge['m_NodeAGuid']==midanc_id) | (df_Edge['m_NodeBGuid']==midanc_id)]['m_MaterialType'].to_list().count(1)
        df_sols.loc[n,'MidAncReinfRoad'] = df_Edge[(df_Edge['m_NodeAGuid']==midanc_id) | (df_Edge['m_NodeBGuid']==midanc_id)]['m_MaterialType'].to_list().count(2)
        df_sols.loc[n,'MidAncWood'] = df_Edge[(df_Edge['m_NodeAGuid']==midanc_id) | (df_Edge['m_NodeBGuid']==midanc_id)]['m_MaterialType'].to_list().count(3)
        df_sols.loc[n,'MidAncSteel'] = df_Edge[(df_Edge['m_NodeAGuid']==midanc_id) | (df_Edge['m_NodeBGuid']==midanc_id)]['m_MaterialType'].to_list().count(4)

    else:
        midanc_used = 0
        df_sols.loc[n,'MidAnc'] = 0
        df_sols.loc[n,'NSegmMidAnc'] = 0
        df_sols.loc[n,'MidAncRoad'] = 0
        df_sols.loc[n,'MidAncReinfRoad'] = 0
        df_sols.loc[n,'MidAncWood'] = 0
        df_sols.loc[n,'MidAncSteel'] = 0


    #* joints
    if leftanc_used == 0:
        df_AncJon.drop(0, inplace=True) # drop left anchor from df_AncJon

    if rightanc_used == 0:
        df_AncJon.drop(1, inplace=True) # drop right anchor from df_AncJon

    if midanc_used == 0:
        df_AncJon.drop(2, inplace=True) # drop right anchor from df_AncJon

    df_sols.loc[n,'LargestYJoint'] = df_AncJon['m_Pos.y'].max()
    df_sols.loc[n,'SmallestYJoint'] = df_AncJon['m_Pos.y'].min()
    df_sols.loc[n,'LargestXJoint'] = df_AncJon['m_Pos.x'].max()
    df_sols.loc[n,'SmallestXJoint'] = df_AncJon['m_Pos.x'].min()
    df_sols.loc[n,'BraceLeftWall'] = ((df_Joints['m_Pos.x'] <= 0.3) & (df_Joints['m_Pos.y'] < 5)).sum()
    df_sols.loc[n,'BraceRightWall'] = ((df_Joints['m_Pos.x'] >= 13.7) & (df_Joints['m_Pos.y'] < 5.75)).sum()
    df_sols.loc[n,'NJointBelowWater'] = (df_Joints['m_Pos.y']<=3.25).sum()

    # joints in the boat area
    nboatarea = 0
    all_joints = list(zip(df_Joints['m_Pos.x'],df_Joints['m_Pos.y']))
    for j in all_joints:
        if shapely.geometry.Point(j).within(boatshape):
            nboatarea = nboatarea +1

    df_sols.loc[n,'NJointBoatRegion'] = nboatarea

    # joints with single segment
    all_segs = df_Edge['m_NodeAGuid'].to_list() + df_Edge['m_NodeBGuid'].to_list()
    nsingleseg = count_non_repeated_elements(all_segs)
    df_sols.loc[n,'NJointSingleSegment'] = nsingleseg

    #* metrics
    df_sols.loc[n,'StructDensity'] = 2*nseg/(njoin*(njoin-1))
    df_sols.loc[n,'THeight'] = df_AncJon['m_Pos.y'].max() - df_AncJon['m_Pos.y'].min()
    df_sols.loc[n,'TSpan'] = df_AncJon['m_Pos.x'].max() - df_AncJon['m_Pos.x'].min()

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

    #df_sols.at[n,'NodesXPos'] = df_AncJon[df_AncJon['m_Guid'].isin(nodelist)]['m_Pos.x'].to_list()
    #df_sols.at[n,'NodesYPos'] = df_AncJon[df_AncJon['m_Guid'].isin(nodelist)]['m_Pos.y'].to_list()

    #* angles ALL
    ls_joints = df_AncJon['m_Guid']
    ls_angles = []
    df_EdgeAngle = df_Edge.copy()

    for nd in ls_joints:
        df_ss = df_EdgeAngle[(df_EdgeAngle['m_NodeAGuid']==nd) | (df_Edge['m_NodeBGuid']==nd)]

        if len(df_ss) >= 1:
            df_EdgeAngle.drop(df_ss.index, inplace=True) # update df_edges to not duplicate the segments

            df_ss.reset_index(drop=True, inplace=True) # reset index of subset for the loop

            for sg in range(len(df_ss.index)):
                x1 = df_ss.loc[sg,'nAx']
                x2 = df_ss.loc[sg,'nBx']
                y1 = df_ss.loc[sg,'nAy']
                y2 = df_ss.loc[sg,'nBy']
                ls_angles.append(math.degrees(math.atan((y2-y1)/(x2-x1)))) #degrees


    ls_abs_angles = [abs(ele) for ele in ls_angles] # get absolute values
    if ls_abs_angles == []:
        df_sols.loc[n,'AvgAngleAll'] = 0
        df_sols.loc[n,'MaxAngleAll'] = 0
        df_sols.loc[n,'MinAngleAll'] = 0
    else:
        df_sols.loc[n,'AvgAngleAll'] = np.average(ls_abs_angles)
        df_sols.loc[n,'MaxAngleAll'] = np.max(ls_abs_angles)
        df_sols.loc[n,'MinAngleAll'] = np.min(ls_abs_angles)


    #* angles ROAD
    ls_joints = df_AncJon['m_Guid']
    ls_angles_r = []
    df_EdgeAngle_r = df_Edge.copy()

    for nd in ls_joints:
        df_ss_r = df_EdgeAngle_r[((df_EdgeAngle_r['m_NodeAGuid']==nd) | (df_EdgeAngle_r['m_NodeBGuid']==nd)) & (df_EdgeAngle_r['m_MaterialType']==1)]
        if len(df_ss_r) >= 1:
            df_EdgeAngle_r.drop(df_ss_r.index, inplace=True) # update df_edges to not duplicate the segments

            df_ss_r.reset_index(drop=True, inplace=True) # reset index of subset for the loop

            for sg in range(len(df_ss_r.index)):
                x1 = df_ss_r.loc[sg,'nAx']
                x2 = df_ss_r.loc[sg,'nBx']
                y1 = df_ss_r.loc[sg,'nAy']
                y2 = df_ss_r.loc[sg,'nBy']
                ls_angles_r.append(math.degrees(math.atan((y2-y1)/(x2-x1)))) #degrees

    ls_abs_angles_r = [abs(ele) for ele in ls_angles_r] # get absolute values

    if ls_abs_angles_r == []:
        df_sols.loc[n,'AvgAngleRoad'] = 0
        df_sols.loc[n,'MaxAngleRoad'] = 0
        df_sols.loc[n,'MinAngleRoad'] = 0
    else:
        df_sols.loc[n,'AvgAngleRoad'] = np.average(ls_abs_angles_r)
        df_sols.loc[n,'MaxAngleRoad'] = np.max(ls_abs_angles_r)
        df_sols.loc[n,'MinAngleRoad'] = np.min(ls_abs_angles_r)

    #* angles REINF ROAD
    ls_joints = df_AncJon['m_Guid']
    ls_angles_rr = []
    df_EdgeAngle_rr = df_Edge.copy()

    for nd in ls_joints:
        df_ss_rr = df_EdgeAngle_rr[((df_EdgeAngle_rr['m_NodeAGuid']==nd) | (df_EdgeAngle_rr['m_NodeBGuid']==nd)) & (df_EdgeAngle_rr['m_MaterialType']==2)]
        if len(df_ss_rr) >= 1:
            df_EdgeAngle_rr.drop(df_ss_rr.index, inplace=True) # update df_edges to not duplicate the segments

            df_ss_rr.reset_index(drop=True, inplace=True) # reset index of subset for the loop

            for sg in range(len(df_ss_rr.index)):
                x1 = df_ss_rr.loc[sg,'nAx']
                x2 = df_ss_rr.loc[sg,'nBx']
                y1 = df_ss_rr.loc[sg,'nAy']
                y2 = df_ss_rr.loc[sg,'nBy']
                ls_angles_rr.append(math.degrees(math.atan((y2-y1)/(x2-x1)))) #degrees

    ls_abs_angles_rr = [abs(ele) for ele in ls_angles_rr] # get absolute values

    if ls_abs_angles_rr == []:
        df_sols.loc[n,'AvgAngleReinfRoad'] = 0
        df_sols.loc[n,'MaxAngleReinfRoad'] = 0
        df_sols.loc[n,'MinAngleReinfRoad'] = 0
    else:
        df_sols.loc[n,'AvgAngleReinfRoad'] = np.average(ls_abs_angles_rr)
        df_sols.loc[n,'MaxAngleReinfRoad'] = np.max(ls_abs_angles_rr)
        df_sols.loc[n,'MinAngleReinfRoad'] = np.min(ls_abs_angles_rr)

    #* angles WOOD
    ls_joints = df_AncJon['m_Guid']
    ls_angles_w = []
    df_EdgeAngle_w = df_Edge.copy()

    for nd in ls_joints:
        df_ss_w = df_EdgeAngle_w[((df_EdgeAngle_w['m_NodeAGuid']==nd) | (df_EdgeAngle_w['m_NodeBGuid']==nd)) & (df_EdgeAngle_w['m_MaterialType']==3)]
        if len(df_ss_w) >= 1:
            df_EdgeAngle_w.drop(df_ss_w.index, inplace=True) # update df_edges to not duplicate the segments

            df_ss_w.reset_index(drop=True, inplace=True) # reset index of subset for the loop

            for sg in range(len(df_ss_w.index)):
                x1 = df_ss_w.loc[sg,'nAx']
                x2 = df_ss_w.loc[sg,'nBx']
                y1 = df_ss_w.loc[sg,'nAy']
                y2 = df_ss_w.loc[sg,'nBy']
                ls_angles_w.append(math.degrees(math.atan((y2-y1)/(x2-x1)))) #degrees

    ls_abs_angles_w = [abs(ele) for ele in ls_angles_w] # get absolute values

    if ls_abs_angles_w == []:
        df_sols.loc[n,'AvgAngleWood'] = 0
        df_sols.loc[n,'MaxAngleWood'] = 0
        df_sols.loc[n,'MinAngleRoad'] = 0
    else:
        df_sols.loc[n,'AvgAngleWood'] = np.average(ls_abs_angles_w)
        df_sols.loc[n,'MaxAngleWood'] = np.max(ls_abs_angles_w)
        df_sols.loc[n,'MinAngleWood'] = np.min(ls_abs_angles_w)

    #* angles STEEL
    ls_joints = df_AncJon['m_Guid']
    ls_angles_s = []
    df_EdgeAngle_s = df_Edge.copy()

    for nd in ls_joints:
        df_ss_s = df_EdgeAngle_s[((df_EdgeAngle_s['m_NodeAGuid']==nd) | (df_EdgeAngle_s['m_NodeBGuid']==nd)) & (df_EdgeAngle_s['m_MaterialType']==4)]
        if len(df_ss_s) >= 1:
            df_EdgeAngle_s.drop(df_ss_s.index, inplace=True) # update df_edges to not duplicate the segments

            df_ss_s.reset_index(drop=True, inplace=True) # reset index of subset for the loop

            for sg in range(len(df_ss_s.index)):
                x1 = df_ss_s.loc[sg,'nAx']
                x2 = df_ss_s.loc[sg,'nBx']
                y1 = df_ss_s.loc[sg,'nAy']
                y2 = df_ss_s.loc[sg,'nBy']
                ls_angles_s.append(math.degrees(math.atan((y2-y1)/(x2-x1)))) #degrees

    ls_abs_angles_s = [abs(ele) for ele in ls_angles_s] # get absolute values

    if ls_abs_angles_s == []:
        df_sols.loc[n,'AvgAngleSteel'] = 0
        df_sols.loc[n,'MaxAngleSteel'] = 0
        df_sols.loc[n,'MinAngleSteel'] = 0
    else:
        df_sols.loc[n,'AvgAngleSteel'] = np.average(ls_abs_angles_s)
        df_sols.loc[n,'MaxAngleSteel'] = np.max(ls_abs_angles_s)
        df_sols.loc[n,'MinAngleSteel'] = np.min(ls_abs_angles_s)

saveExcel = True
if saveExcel == True:
    df_sols.to_excel(f'{pth}/dataset_quant.xlsx')
    df_sols.to_csv(f'{pth}/dataset_quant.csv')

print('Summarising solutions done!')
'''