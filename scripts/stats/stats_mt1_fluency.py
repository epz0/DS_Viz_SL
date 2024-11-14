"""The stats_mt1_fluency module supports the fluency calculation.

Functions:
    get_fluency_df: Main function that gets a dataframe with the fluency data from Excel.
"""

import pandas as pd
from pathlib import Path
from stats.stats_main import *


def get_fluency_df(dir_data, fname, sheetname=None):
    """Returns a dataframe with the data for the fluency (count of solutions) for each participant.

    Args:
        dir_data (Path): Path to the directory with the data file.
        fname (string): Name of the file with the data.
        sheetname (string, optional): Name of the sheet with the data. Defaults to None.
    Returns:
        df_fluency: Dataframe with fluency data.
    """

    if sheetname is None:
        sheetname = 'Fluency-MT1-topy'                                          #default name of the spreadsheet with fluency data

    df_fluency = pd.read_excel(f'{dir_data}/{fname}', sheet_name=sheetname)
    df_fluency = df_fluency.rename(columns={'Fluency MT1[KYY]': 'n_KYY', 'Fluency MT1[ZSB]': 'n_ZSB', 'Fluency MT1[Session]': 'n_FS'})
    return df_fluency
