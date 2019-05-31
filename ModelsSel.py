# -*- coding: utf-8 -*-
"""
Created on Fri May 31 19:06:58 2019

@author: Guilherme
"""

from sklearn.ensemble import RandomForestRegressor, BaggingRegressor, GradientBoostingRegressor, AdaBoostRegressor
from gplearn_MLAA.genetic import SymbolicRegressor
from sklearn.model_selection import GridSearchCV, cross_val_score
from sklearn import metrics
from sklearn.model_selection import KFold
from sklearn.metrics import mean_squared_error,mean_absolute_error
import pandas as pd
import numpy as np
from sklearn.pipeline import Pipeline
import itertools
import copy

### MODELS
class model_runner():
        
    def __init__(self,training,labels,testing,seed,metric = 'neg_mean_absolute_error',cv = 5):
        
        self.training = training.drop(labels, axis = 1)
        self.labels = training[labels]
        self.testing = testing.drop(labels, axis = 1)
        self.labels_t = testing[labels]
        self.seed = seed
        self.metric = metric
        self.cv = cv
        self.best_params = []



            
        #Hyper Parameter Optimization
        edda_params = [{"deme_size": 50, "p_gsgp_demes": 0.0, "maturation": 5, "p_mutation": 1.0, "gsm_ms": -1.0}] * 1
        selection = []
        selection.append({'selection':'destabilization_tournament','des_probs':0.1})
        selection.append({'selection':'destabilization_tournament','des_probs':0.5})
        selection.append({'selection':'destabilization_tournament','des_probs':0.9})
        selection.append({'selection':'nested_tournament','num':3})
        selection.append({'selection':'nested_tournament','num':4})
        selection.append({'selection':'nested_tournament','num':5})
        selection.append('ranking')
        selection.append('double_tournament')
        selection.append('roulette')
        selection.append('semantic_tournament')
        p_crossover=[0.1] * 10
        p_subtree=[0.9] * 10
        rs = [self.seed] * 10
        param_grid_gp = {
               'edda_params':edda_params,
               'selection':selection,
               'p_crossover': p_crossover,
               'p_subtree_mutation': p_subtree,
               'random_state':rs}
        
        model = self.gridSearchGp(param_grid_gp)

        preds = model.predict(self.testing)
        self.scoreDict = {'score':mean_absolute_error(self.labels_t, preds)}
    
    def gridSearchGp(self,param_grid):
        
        parameters = list(param_grid.values())
        comb = []
        for i in range(len(parameters[0])):
            t =  {}
            for j in param_grid.keys():
                t[j] = param_grid[j][i]
            comb.append(t)
        kf = KFold(5)
        gp_results = {}
        for c in range(len(comb)):
            gp_results[c] = []
        for c in range(len(comb)):
            combination_results = []
            cx = copy.deepcopy(comb)
            if c == 0 or c == 1 or c == 2:
                var = cx[c]['selection']
                cx[c]['selection'] = var['selection']
                cx[c]['destabilization_probs'] = var['des_probs']
            elif c == 3 or c== 4 or c == 5:
                var = cx[c]['selection']
                cx[c]['selection'] = var['selection']
                cx[c]['num'] = var['num']
            comb[c] = cx[c]
            for train_index, test_index in kf.split(self.training):
                est_gp = SymbolicRegressor(**comb[c])
                est_gp.fit(self.training.iloc[train_index], self.labels.iloc[train_index])
                preds = est_gp.predict(self.training.iloc[test_index])   
                combination_results.append(mean_absolute_error(self.labels.iloc[test_index], preds))
            gp_results[c] = combination_results
        
        best = comb[getBestParam(gp_results)]
        self.best_params = best
        estimator = SymbolicRegressor(**best)
        estimator.fit(self.training,self.labels)
        return estimator
    
def getBestParam(results):
    best = 0
    for key in results.keys():
        mean_best = np.mean(results[best])
        mean_curr = np.mean(results[key])
        
        if mean_best + np.std(results[best]) > mean_curr + np.std(results[key]):
            if np.sum(results[key] < mean_best)/len(results[key]) >= 0.8:
                best = key
    return best
        