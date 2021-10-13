import sys
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import norm, lognorm, kstest, chisquare, poisson



years = ['bbref1.csv']
data = pd.read_csv(year)
all_data = pd.DataFrame()
for i in years:
    # append all data

headers = ['MP','FG','FGA','FT','FTA','3P'
           ,'3PA', 'FG%','3P%','FT%','TRB'
           ,'AST','STL','BLK','TOV','PF','PTS']
stats = all_data[df.columns.isin(headers)]
# Should work if only stats are kept
stats=stats.dropna()
dists = np.random.poisson(stats.mean(axis=0)
                           , size=(len(threes), len(stats.mean(axis=0))))

bins=[0,1,2,3,4,5,stats['STL'].max()]
#stats.hist(bins='auto')
aa=plt.hist(stats, bins='auto')
plt.hist(normal, bins=aa[1], histtype='step')
