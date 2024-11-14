"""The stats_main module has the ancova wrapper from statsmodels, saving the results to excel.

Functions:
    ancova_stat: Main function that calculates the ancova and saves the outcomet to an Excel file.

Example:
    statsmodel syntax for anconva: y ~ z + x
    y = outcome for the particular metric
    z = groups for comparison (CG, IntA, IntB)
    x = covariate (numerical variable)
    so for the fluency metric we have the following model:
        n_Post ~ GroupID + n_Pre, where:
            y = n_Post (outcome)
            z = GroupID (groups)
            x = n_Pre (covar)
"""
import pandas as pd

from pathlib import Path
from statsmodels.formula.api import ols
from statsmodels.stats.anova import anova_lm


def ancova_stat(dir_data, df_data, y, z, x, metric_name, sht_name=None):
    """Run ancova analysis across groups for the selected metric and saves the output to an Excel file.

    Args:
        dir_data (path): Path to data file. Will save in /export/stats.
        df_data (dataframe): Dataframe with the data to be used in the comparison. Must contain at least 3 columns (outcome, covar, group).
        y (float): Outcome measured for the particular metric.
        z (string): Categorical group for the comparison.
        x (float): Covariate variable.
        metric_name (string): Name of the metric being calculated at the moment (becomes the Excel file name).
        sht_name (string, optional): Name of the specific comparison being run. Defaults to y-z-x.
    """

    # default directory
    dir_stats = Path(f'{dir_data.parent}'+r'/export/stats')

    # default sheet name
    if sht_name is None:
        sht_name = f'{y}-{z}-{x}'

    print(f'Calculating the {metric_name} metric for {sht_name}...')

    formula = f'{y} ~ {z} + {x}'
    lm = ols(formula, df_data).fit()

    stats = anova_lm(lm)                                                                                                    # dataframe

    # check if file exists
    if Path(f'{dir_stats}/stats_{metric_name}.xlsx').is_file() == True:
        with pd.ExcelWriter(f'{dir_stats}/stats_{metric_name}.xlsx', mode='a', if_sheet_exists='replace') as writer:        # appends to existing file and overwrite sheet if exists
            stats.to_excel(writer, sheet_name=sht_name, index=False)
    else:
        with pd.ExcelWriter(f'{dir_stats}/stats_{metric_name}.xlsx') as writer:                                             # create file
            stats.to_excel(writer, sheet_name=sht_name, index=False)

    print(f'Calculating the {metric_name} metric for {sht_name} - done!')