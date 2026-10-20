
############################################################
############################################################
############################################################
############################################################


import os
import numpy as np
import pandas as pd

import time as t
from models import osESD_Detector, auto_osESD_Detector
from utils import data_aug
from utils import scores_module
from utils import plotting_modules

def osESD(df, labeled=True, value_name='value',
        timestamp_name='timestamps', anomaly_name='anomaly', size=100, condition=True, dwin=5,
        rwin=5, maxr=10, alpha=0.01, sync_stats=False, use_author_lambda=False, rep_at='loo'):

    if value_name not in df.columns:
        raise ValueError("Value column can not be found. Please specify column name with time series values as 'value_name'.")

    if labeled and anomaly_name not in df.columns:
        raise ValueError("Anomaly column can not be found. Please specify column name with time series values as 'anomaly_name'.")

    df = df.copy()
    ### Add timestamps to dataset if not labeled.
    if timestamp_name in df.columns:
        df['timestamps']=df[timestamp_name]
    else:
        df['timestamps']=[i for i in range(1,len(df)+1)]

    ### Deal with whether dataset is labeled or not.
    if labeled:
        df[['value','anomaly']]=df[[value_name,anomaly_name]]
    else:
        df['value']=df[value_name]

    T1 = t.time()
    predictions = osESD_Detector.osESD(data=list(df['value'].astype(float)),
                                    time=list(df['timestamps']),
                                    train_size=size, condition=condition,
                                    dwins=dwin, rwins=rwin,
                                    alpha=alpha, maxr=maxr,
                                    sync_stats=sync_stats,
                                    use_author_lambda=use_author_lambda,
                                    rep_at=rep_at)

    return predictions





def auto_osESD(dataset, labeled=True, value_name='value', timestamp_name='timestamps', anomaly_name='anomaly', 
         sizes=[], conditions=[], dwins=[], rwins=[], maxrs=[], alphas=[], 
         weights=[0,0,1,0], learning_length=0.2, min_max_switch=False, seed=None):
    
    if value_name not in dataset.columns:
        raise ValueError("Value column can not be found. Please specify column name with time series values as 'value_name'.")

    if labeled and anomaly_name not in dataset.columns:
        raise ValueError("Anomaly column can not be found. Please specify column name with time series values as 'anomaly_name'.")

    ### Read dataset.
    df = dataset.copy()

    ### Add timestamps to dataset if not labeled.
    if timestamp_name in df.columns:
        df['timestamps'] = df[timestamp_name]
    else:
        df['timestamps'] = [i for i in range(1, len(df) + 1)]

    ### Deal with whether dataset is labeled or not.
    if labeled:
        df[['value', 'anomaly']] = df[[value_name, anomaly_name]]
    else:
        df['value'] = df[value_name]

    ### If condition is not explicitly provided, use parameters set within 'auto_osESD' implementation.
    if sizes == [] and conditions == [] and dwins == [] and rwins == [] and maxrs == [] and alphas == [] :
        parameters = []
    else:

        if not sizes:
            sizes = [50, 100, 150, 200]

        if not conditions:
            conditions = [True, False]

        if not dwins:
            dwins = [2, 5, 10, 30]

        if not rwins:
            rwins = [4, 5, 10, 30]

        if not maxrs:
            maxrs = [3, 5, 7, 10]

        if not alphas:
            alphas = [0.001, 0.005, 0.01, 0.05]

        if min(sizes)<50:
            raise ValueError("Minimum value of windows should be above 50 for stable learning. Please adjust \"sizes\" as such.")

        if min(sizes)<min(max(rwins),max(dwins)) :
            raise ValueError("Minimum value of windows should be above maximum value of both R windows and D windows. Please adjust \"dwins\" and \"rwins\" as such.")

        sizes.sort()
        dwins.sort()
        rwins.sort()
        maxrs.sort()
        alphas.sort()

        parameters = [
            ["--WindowSizes", sizes],
            ["--AndOr", conditions],
            ["--MaxRs", maxrs],
            ["--Dwins", dwins],
            ["--Rwins", rwins],
            ["--Alphas", alphas]
        ]

    ### Run function 'osESD_Detector_auto' which will return [anomaly_list, anomaly_indices, best_parameters].
    T1 = t.time()
    tuning_results = auto_osESD_Detector.osESD_Detector_auto(database=df, data_label=labeled,
                                                             weights=weights,
                                                             par_len=learning_length,
                                                             parameters=parameters, min_max_switch=min_max_switch,
                                                             seed=seed)
    tuning_params = tuning_results[2]
    predictions = auto_osESD_Detector.run_osESD_modified(data=list(df['value'].astype(float)), time=list(df['timestamps']),
                                                        full_size=len(df), init_size=tuning_params[1],
                                                        params=tuning_params)
    T2 = t.time()

    pred_index = np.where(np.array(predictions)==1)

    return pred_index[0]


