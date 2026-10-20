
from sys import maxsize as M
import time as t

from . import osESD_Test
from . import osESD_Transform

from utils import scores_module
from utils.data_aug import math_round
from utils.data_aug import contaminate
from utils.data_aug import add_timestamp

def osESD_Detector_auto(database, data_label, weights, par_len, parameters, min_max_switch):

    if (sum(weights)<=0):
        raise Exception("Weight value must be above 0.")

    s = sum(weights)
    w = []
    for i in weights:
        w.append(i/s)
    weights=w

    if (parameters==[]):
        print("No parameters detected, will use basic default for tuning.")
        parameters = [
            ["--WindowSizes", [50, 100, 150, 200]],
            ["--AndOr", [1, 0]],
            ["--MaxRs", [3, 5, 7, 10]],
            ["--Dwins", [2, 5, 10, 30]],
            ["--Rwins", [4, 5, 10, 30]],
            ["--Alphas", [0.001, 0.005, 0.01, 0.05]]
        ]

        # parameters = [
        #     ["--WindowSizes", [50, 100]],
        #     ["--AndOr", [1, 0]],
        #     ["--MaxRs", [3, 5]],
        #     ["--Dwins", [2, 5]],
        #     ["--Rwins", [4]],
        #     ["--Alphas", [0.001]]
        # ]

    elif (min_max_switch):
        print("Parameters expanded according to Min and Max input values")
        A1 = [parameters[0][1][0]]
        A2 = [1, 0]
        A3 = [parameters[2][1][0]]
        A4 = [parameters[3][1][0]]
        A5 = [parameters[4][1][0]]
        A6 = [parameters[5][1][0]]

        Interval = 3
        for i in range(1, Interval + 1):
            A1.append(int((parameters[0][1][0] * (Interval - i) + parameters[0][1][1] * i) / Interval))
        for i in range(1, Interval + 1):
            A3.append(int((parameters[2][1][0] * (Interval - i) + parameters[2][1][1] * i) / Interval))
        for i in range(1, Interval + 1):
            A4.append(int((parameters[3][1][0] * (Interval - i) + parameters[3][1][1] * i) / Interval))
        for i in range(1, Interval + 1):
            A5.append(int((parameters[4][1][0] * (Interval - i) + parameters[4][1][1] * i) / Interval))
        for i in range(1, Interval + 1):
            A6.append((parameters[5][1][0] * (Interval - i) + parameters[5][1][1] * i) / Interval)
        parameters = [
            ["--WindowSizes", A1],
            ["--AndOr", A2],
            ["--MaxRs", A3],
            ["--Dwins", A4],
            ["--Rwins", A5],
            ["--Alphas", A6]
        ]

    else :
        print("Will use suggested parameters.")

    par_len = int(len(database)*par_len)

    try:
        time = list(database['timestamps'])
    except:
        time = [i for i in range(1,len(database)+1)]

    if data_label :
        data = list(database['value'].astype(float))
        anoms = list(database['anomaly'])
        par_anoms = list(anoms[:par_len])
    else:
        cont_data = contaminate(database['value'],0.05,0.02,'ber')
        data = list(cont_data['value'][:par_len].astype(float))
        anoms = list(cont_data['anomaly'])
        par_anoms = list(anoms[:par_len])


    Max_Score1 = -M
    Max_Score2 = -M
    Max_Score3 = -M
    Max_Score4 = -M
    Max_Score5 = -M

    Max_Pars1 = []
    Max_Pars2 = []
    Max_Pars3 = []
    Max_Pars4 = []
    Max_Pars5 = []

    Total_length = 1
    for mult in range(6):
        Total_length *= len(parameters[mult][1])

    param_idx=0
    print("Process : [ {} / {} ]".format(1, Total_length))
    for win_size in parameters[0][1]:
        for andor in parameters[1][1]:
            for maxr in parameters[2][1]:
                for dwin in parameters[3][1]:
                    for rwin in parameters[4][1]:
                        for alpha in parameters[5][1]:
                            param_idx+=1
                            if (param_idx)%(Total_length//4)==0:
                                print("Process : [ {} / {} ]".format(param_idx,Total_length))
                            win_size = min(win_size, int(par_len*0.1))
                            new_pars = [andor,win_size,maxr,dwin,rwin,alpha]
                            t1 = t.time()
                            anomal_preds = run_osESD_modified(data=data,time=time,
                                                     full_size=par_len,init_size=win_size,
                                                     params=new_pars)
                            t2 = t.time()
                            # scores = Precision_Recall_f1score(par_anoms, anomal_preds)
                            scores = scores_module.Precision_Recall_f1score(par_anoms, anomal_preds)
                            # print(scores)
                            run_time = t2-t1
                            scores.append(-run_time)
                            Score=0
                            for s,w in zip(scores, weights):
                                Score+=s*w

                            if Score > Max_Score1:
                                Max_Score1, Score = Score, Max_Score1
                                Max_Pars1, new_pars = new_pars, Max_Pars1
                            if Score > Max_Score2:
                                Max_Score2, Score = Score, Max_Score2
                                Max_Pars2, new_pars = new_pars, Max_Pars2
                            if Score > Max_Score3:
                                Max_Score3, Score = Score, Max_Score3
                                Max_Pars3, new_pars = new_pars, Max_Pars3
                            if Score > Max_Score4:
                                Max_Score4, Score = Score, Max_Score4
                                Max_Pars4, new_pars = new_pars, Max_Pars4
                            if Score > Max_Score5:
                                Max_Score5, Score = Score, Max_Score5
                                Max_Pars5, new_pars = new_pars, Max_Pars5

                            # print(Max_Score1,Max_Score2,Max_Score3,Max_Score4,Max_Score5)

    print("Now doing second step.")

    ADD = 4
    new_params=[]
    new_params.append(Max_Pars1)
    for i in range(1, ADD):
        new_param = [math_round((Max_Pars1[0] * (ADD - i) + Max_Pars2[0] * i) / ADD)]
        for x, y in zip(Max_Pars1[1:-1], Max_Pars2[1:-1]):
            new_param.append(int((x * (ADD - i) + y * i) / ADD))
        new_param.append((Max_Pars1[-1] * (ADD - i) + Max_Pars2[-1] * i) / ADD)
        new_params.append(new_param)

    new_params.append(Max_Pars2)
    for i in range(1, ADD):
        new_param = [math_round((Max_Pars1[0] * (ADD - i) + Max_Pars5[0] * i) / ADD)]
        for x, y in zip(Max_Pars1[1:-1], Max_Pars5[1:-1]):
            new_param.append(int((x * (ADD - i) + y * i) / ADD))
        new_param.append((Max_Pars1[-1] * (ADD - i) + Max_Pars5[-1] * i) / ADD)
        new_params.append(new_param)

    new_params.append(Max_Pars5)
    for i in range(1, ADD):
        new_param = [math_round((Max_Pars2[0] * (ADD - i) + Max_Pars5[0] * i) / ADD)]
        for x, y in zip(Max_Pars2[1:-1], Max_Pars5[1:-1]):
            new_param.append(int((x * (ADD - i) + y * i) / ADD))
        new_param.append((Max_Pars2[-1] * (ADD - i) + Max_Pars5[-1] * i) / ADD)
        new_params.append(new_param)


    Final_Score = -1
    # second_step_idx=0
    for param in new_params:
        t1 = t.time()
        anomal_preds = run_osESD_modified(data=data,time=time,full_size=par_len,
                                 init_size=param[1],params=param)
        t2 = t.time()
        scores = scores_module.Precision_Recall_f1score(par_anoms,anomal_preds)
        # scores = Precision_Recall_f1score(par_anoms, anomal_preds)
        run_time = t2-t1
        scores.append(-run_time)
        Score = 0
        for s,w in zip(scores, weights):
            Score+=s*w
        if Score>Final_Score:
            Final_Param = param
            Final_Score = Score

    t1 = t.time()
    final_anomaly_index= run_osESD_modified(data=list(database['value']), time=time, full_size=len(data),
                                    init_size=Final_Param[1], params=Final_Param)
    t2 = t.time()
    final_anomaly_preds = []
    # print(Final_Param)
    for i in range(Final_Param[1]+1,len(final_anomaly_index)):
        if final_anomaly_index[i]==1:
            final_anomaly_preds.append(i)
    return final_anomaly_index, final_anomaly_preds, Final_Param

def run_osESD_modified(data, time, full_size, init_size, params):
    rwins=params[4]
    train_data = data[:init_size]
    online_data = data[init_size:full_size]
    train_time = time[:init_size]
    online_time = time[init_size:full_size]
    c_ins = osESD_Transform.TCHA(data=train_data, time=train_time, wins=params[3])
    r_ins = osESD_Transform.TRES(data=train_data, time=train_time, wins=rwins)
    SESD_TCHA = osESD_Test.SESD(data=c_ins.vec.copy(), alpha=params[5], maxr=params[2])
    SESD_TRES = osESD_Test.SESD(data=r_ins.vec.copy(), alpha=params[5], maxr=params[2])
    anomaly_index = []
    for i in range(len(online_data)):
        ranom = SESD_TRES.test(r_ins.update(online_data[i], online_time[i]))
        canom = SESD_TCHA.test(c_ins.update(online_data[i], online_time[i]))
        if params[0] == 0:
            function_ = canom or ranom
        else:
            function_ = canom and ranom
        if function_:
            anomaly_index.append(i + init_size)
            rep = r_ins.loo_prediction()
            c_ins.replace(rep)
            r_ins.replace(rep)
    pred_outlier = [0 for _ in range(full_size)]
    for anom_index in anomaly_index:
        pred_outlier[anom_index]=1
    return list(pred_outlier)

