"""The stats_mt2_variety module supports the variety metric calculation.

Functions:
    get_variety_df: Returns a dataframe with the base data for the variety calculation.
    calc_variety: Returns a dataframe with the summary of the variety calculation and saves it to Excel.
"""
import pandas as pd
from pathlib import Path
from stats.stats_main import *

def get_variety_df(dir_data, fname, sheetname=None):
    """Returns a dataframe with the data for the variety (branches visited) for each participant.

    Args:
        dir_data (Path): Path to the directory with the data file.
        fname (string): Name of the file with the data.
        sheetname (string, optional): Name of the sheet with the data. Defaults to None.

    Returns:
        df_variety: Dataframe with variety base data.
    """
    print('Getting variety data...')

    if sheetname is None:
        sheetname = 'VARIETY-MT2-topy'                                          #default name of the spreadsheet with variety data

    df_variety = pd.read_excel(f'{dir_data}/{fname}', sheet_name=sheetname)

    print('Getting variety data - done!')
    return df_variety

def calc_variety(dir_data, df_variety, PRE, POST, FS, lvl_weights=None, save_file=True):
    """Returns a dataframe with the variety metric for each participant across each intervention moment and saves to Excel.

    Args:
        dir_data (Path): Path to the directory with the data file.
        df_variety (dataframe): Dataframe with variety base data.
        PRE (string): Tag for the pre intervention metrics/solutions.
        POST (string): Tag for the post intervention metrcis/solutions.
        FS (string): Tag for the full session metrics.
        lvl_weights (list, optional): List of weight values of each level of the tree. If None, defaults to [10, 6, 3, 1].
        save_file (bool, optional): Argument to determine if the base calculation of variety should be saved to file. Defaults to True.

    Returns:
       df_summary: Dataframe with the summary of the variety data.
    """

    print('Calculating variety metric...')

    pt_unique = df_variety['ParticipantID'].unique()                    # list of unique participants

    # preparing df for receiving values
    df_summary = df_variety[['GroupID','ParticipantID']].drop_duplicates()
    df_summary = df_summary.reset_index(drop=True)

    # columns for n {PRE, POST, FS}
    df_summary[f'n_{PRE}'] = 0
    df_summary[f'n_{POST}'] = 0
    df_summary[f'n_{FS}'] = 0

    # calculate number of solutions (basically fluency)
    for i in range(len(pt_unique)):
        df_summary.loc[i, f'n_{PRE}'] = sum((df_variety['ParticipantID'] == pt_unique[i]) & (df_variety['PrePost'] == PRE))
        df_summary.loc[i, f'n_{POST}'] = sum((df_variety['ParticipantID'] == pt_unique[i]) & (df_variety['PrePost'] == POST))
        df_summary.loc[i, f'n_{FS}'] = sum(df_variety['ParticipantID'] == pt_unique[i])

    #* initiate columns for other metrics
    # branches visited in the Physical Principle level
    df_summary[f'b_PP_{PRE}'] = 0
    df_summary[f'b_PP_{POST}'] = 0
    df_summary [f'b_PP_{FS}'] = 0

    # branches visited in the WorkingPrinciple level
    df_summary[f'b_WP_{PRE}'] = 0
    df_summary[f'b_WP_{POST}'] = 0
    df_summary [f'b_WP_{FS}'] = 0

    # branches visited in the Embodiment level
    df_summary[f'b_EM_{PRE}'] = 0
    df_summary[f'b_EM_{POST}'] = 0
    df_summary [f'b_EM_{FS}'] = 0

    # branches visited in the Detail level
    df_summary[f'b_DT_{PRE}'] = 0
    df_summary[f'b_DT_{POST}'] = 0
    df_summary [f'b_DT_{FS}'] = 0

    df_summary[f'M3_{PRE}'] = 0
    df_summary[f'M3_{POST}'] = 0
    df_summary[f'M3_{FS}'] = 0

    # weights for each level
    if lvl_weights is None:
        weights_var = [10, 6, 3, 1]
    else:
        weights_var = lvl_weights

    #* DF With Summary of values for the variety metric calc

    for i in range(len(pt_unique)):
        # getting df with participant data & subdividing into KYY/{POST}/FS
        df_PT_FS = df_variety[df_variety['ParticipantID'] == pt_unique[i]]
        df_PT_PRE = df_PT_FS[df_PT_FS['PrePost'] == f'{PRE}']
        df_PT_POST = df_PT_FS[df_PT_FS['PrePost'] == f'{POST}']

        df_summary.loc[i, f'b_PP_{FS}'] = len(df_PT_FS['PhysicalPrinciple'].unique())
        df_summary.loc[i, f'b_PP_{PRE}'] = len(df_PT_PRE['PhysicalPrinciple'].unique())
        df_summary.loc[i, f'b_PP_{POST}'] = len(df_PT_POST['PhysicalPrinciple'].unique())

        df_summary.loc[i, f'b_WP_{FS}'] = len(df_PT_FS['WorkingPrinciple'].unique())
        df_summary.loc[i, f'b_WP_{PRE}'] = len(df_PT_PRE['WorkingPrinciple'].unique())
        df_summary.loc[i, f'b_WP_{POST}'] = len(df_PT_POST['WorkingPrinciple'].unique())

        df_summary.loc[i, f'b_EM_{FS}'] = len(df_PT_FS['Embodiment'].unique())
        df_summary.loc[i, f'b_EM_{PRE}'] = len(df_PT_PRE['Embodiment'].unique())
        df_summary.loc[i, f'b_EM_{POST}'] = len(df_PT_POST['Embodiment'].unique())

        df_summary.loc[i, f'b_DT_{FS}'] = len(df_PT_FS['Detail'].unique())
        df_summary.loc[i, f'b_DT_{PRE}'] = len(df_PT_PRE['Detail'].unique())
        df_summary.loc[i, f'b_DT_{POST}'] = len(df_PT_POST['Detail'].unique())

        df_summary.loc[i, f'M3_{FS}'] = (weights_var[0]*df_summary.loc[i, f'b_PP_{FS}'] + weights_var[1]*df_summary.loc[i, f'b_WP_{FS}'] + weights_var[2]*df_summary.loc[i, f'b_EM_{FS}'] + weights_var[3]*df_summary.loc[i, f'b_DT_{FS}'])/df_summary.loc[i, f'n_{FS}']
        df_summary.loc[i, f'M3_{PRE}'] = (weights_var[0]*df_summary.loc[i, f'b_PP_{PRE}'] + weights_var[1]*df_summary.loc[i, f'b_WP_{PRE}'] + weights_var[2]*df_summary.loc[i, f'b_EM_{PRE}'] + weights_var[3]*df_summary.loc[i, f'b_DT_{PRE}'])/df_summary.loc[i, f'n_{PRE}']
        df_summary.loc[i, f'M3_{POST}'] = (weights_var[0]*df_summary.loc[i, f'b_PP_{POST}'] + weights_var[1]*df_summary.loc[i, f'b_WP_{POST}'] + weights_var[2]*df_summary.loc[i, f'b_EM_{POST}'] + weights_var[3]*df_summary.loc[i, f'b_DT_{POST}'])/df_summary.loc[i, f'n_{POST}']

    if save_file == True:
        dir_stats = Path(f'{dir_data.parent}'+r'/export/stats')
        with pd.ExcelWriter(f'{dir_stats}/stats_variety_base.xlsx') as writer:                                             # create file
            df_summary.to_excel(writer, sheet_name='variety_summary', index=False)

    print('Calculating variety metric - done!')

    return df_summary
