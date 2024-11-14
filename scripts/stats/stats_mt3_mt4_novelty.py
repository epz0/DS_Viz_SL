"""The stats_mt3_mt4_novelty module supports the novelty (global/local) metric calculation.

Functions:
    get_novelty_df: Returns a dataframe with the base data for the novelty calculation.
"""
import pandas as pd
from pathlib import Path
from stats.stats_main import *


def get_novelty_df(dir_data, fname, sheetname=None):
    """Returns a dataframe with the data for the novelty (global/local) for each participant.

    Args:
        dir_data (Path): Path to the directory with the data file.
        fname (string): Name of the file with the data.
        sheetname (string, optional): Name of the sheet with the data. Defaults to None.

    Returns:
        df_novel: Dataframe with novelty (global/local) base data.
    """
    print('Getting novelty (global/local) data...')

    if sheetname is None:
        sheetname = 'Novelty-MT3-ALL-topy'                                          #default name of the spreadsheet with novelty data

    df_novel = pd.read_excel(f'{dir_data}/{fname}', sheet_name=sheetname)

    print('Getting novelty (global/local) data - done!')
    return df_novel