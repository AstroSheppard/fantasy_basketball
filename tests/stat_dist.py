import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import norm, lognorm
import sys

bbm = pd.read_csv('BBM_PlayerRankings.csv',index_col=3)
logs = ['s/g', 'p/g', 'r/g', 'a/g', 'to/g', 'b/g']
new = pd.DataFrame()
new['3V']=bbm['3V']
new['fg%']=bbm['fg%V']
new['ft%']=bbm['ft%V']
for item in logs:
    steals = bbm[item].values
    #steals[steals == 0.0]+=.01
    #mean = steals.mean()
    #std = steals.std()
    logmean = np.log(steals).mean()
    logstd = np.log(steals).std()
    new[item+'_lognorm']=(np.log(bbm[item])-logmean)/logstd

new['to/g_lognorm']*=-1.0
new['logval']=new.mean(axis=1)
new['value']=bbm['Value']
new['change'] = new['logval']-new['value']
values=new.iloc[:,-3:]
print values.sort_values('logval',ascending=False)
sss

nbins = 20
normal = np.random.normal(mean, std, size=10000)
lognormal = np.random.lognormal(logmean, logstd, size=10000)
a = plt.hist(steals, bins=nbins, density= True, histtype='bar', label='data')
plt.hist(normal, bins=a[1], histtype='step', label='norm',density= True)[0]
plt.hist(lognormal, bins=a[1], histtype='step', label='lognorm',density= True)[0]
plt.legend()
plt.show()

normal = np.random.normal(mean, std, size=len(steals))
lognormal = np.random.lognormal(logmean, logstd, size=len(steals))
nbins=10
a = plt.hist(steals, bins=nbins, histtype='bar', label='data')
norm = plt.hist(normal, bins=a[1], histtype='step', label='norm')[0]
lognorm = plt.hist(lognormal, bins=a[1], histtype='step', label='lognorm')[0]
plt.show()

print 'Normal assumption: ', np.sum((a[0]-norm)**2/a[0])/(nbins-1)
print 'Log normal assumption', np.sum((a[0]-lognorm)**2/a[0])/(nbins-1)


