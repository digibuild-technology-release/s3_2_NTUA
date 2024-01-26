import pandas as pd
import numpy as np
from decipy import executors as exe


def r_third_classification(df):
    max = df['RATE'].max()
    min = df['RATE'].min()
    range_rate = max - min
    interval_size = range_rate / 3
    labels = ['Low', 'Moderate', 'High']
    df['Class'] = pd.cut(df['RATE'], bins=[-0.1, min + interval_size, min + 2*interval_size, 1.1], labels=labels)
    df['R_RATE'] = 1 - df['RATE']
    return df

def ahp_weights_calculation(matrix):
    n = len(matrix)
    normalized_matrix = matrix / matrix.sum(axis=0)
    column_weights = normalized_matrix.sum(axis=1) / n
    row_weights = column_weights / column_weights.sum()

    return row_weights

def standard_vikor(df):
    alternatives = ['A1', 'A2', 'A3', 'A4', 'A5', 'A6', 'A7', 'A8', 'A9', 'A10', 'A11', 'A12', 'A13', 'A14', 'A15',
                    'A16', 'A17', 'A18', 'A19', 'A20', 'A21', 'A22', 'A23', 'A24']
    criteria = ['C1', 'C2', 'C3', 'C4', 'C5']
    beneficial = [True, True, False, False, False]
    ahp_matrix = np.array([
        [1, 4, 1, 1/9, 6],
        [1 / 4, 1, 1 / 7, 1/9, 1],
        [1, 7, 1, 1/9, 2],
        [9, 9, 9, 1, 3],
        [1 / 6, 5, 1 / 2, 1 / 3, 1]
    ])

    decision_matrix = np.array([
        df['res'].values,
        df['hydro'].values,
        df['load'].values,
        df['energy'].values,
        df['losses'].values,
    ])

    '''
    Configure MCDM Executor
    '''
    ahp_weights = ahp_weights_calculation(ahp_matrix)
    decision_matrix = np.transpose(decision_matrix)
    xij = pd.DataFrame(decision_matrix, index=alternatives, columns=criteria)
    kwargs = {
        'data': xij,
        'beneficial': beneficial,
        'weights': ahp_weights,
        'rank_reverse': True,
        'rank_method': "ordinal"
    }

    vikor = exe.Vikor(**kwargs)

    result_df = r_third_classification(vikor.dataframe.copy())

    r = result_df['RATE'].values
    i_rate = result_df['R_RATE'].values
    rank = result_df['RANK'].values
    cls = result_df['Class'].values

    df['rate'] = r
    df['inverted_rate'] = i_rate
    df['rank'] = rank
    df['co2_class'] = cls
    return df[['datetime', 'rate', 'inverted_rate', 'rank', 'co2_class']]

