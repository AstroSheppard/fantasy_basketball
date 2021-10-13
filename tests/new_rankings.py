import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from scipy.optimize import minimize

import emcee
import corner


# Program that takes hashtag basketball rankings and attempts to find the
# correct weights to recreate their rankings. Finds z-scores using all players
# then attempts to weight based on FTA and FGA. 
def loglike(params, x, y):
    #weights=np.ones(9)
    #weights[-2]=params[0]
    #weights[-1]=params[1]
    model = np.sum(x*params, axis=1)
    return -.5 * np.sum((y - model)**2)

def log_prior(theta):
    if np.all(theta>0) and np.all(theta<2.5):
        return 0
    else:
        return -np.inf

def log_prob(theta, x, y):
    lp = log_prior(theta)
    if not np.isfinite(lp):
        return -np.inf
    else:
        return lp + loglike(theta, x, y)

hashtag = pd.read_csv('hashtag2.csv', index_col=[0])

players = [" ".join(p.split()[:2]) for p in hashtag.loc[:,'PLAYER'].values]
hashtag['PLAYER']=players
hashtag=hashtag[hashtag['PLAYER'] != 'PLAYER']
fgp = [f.split()[0] for f in hashtag['FG%'].values]
fgm = [f.split()[1].split('/')[0][1:] for f in hashtag['FG%'].values]
fga = [f.split()[1].split('/')[1][:-1] for f in hashtag['FG%'].values]
ftp = [f.split()[0] for f in hashtag['FT%'].values]
ftm = [f.split()[1].split('/')[0][1:] for f in hashtag['FT%'].values]
fta = [f.split()[1].split('/')[1][:-1] for f in hashtag['FT%'].values]

hashtag['FG_perc'] = fgp
hashtag['FT_perc'] = ftp
hashtag['FGM'] = fgm
hashtag['FGA'] = fga
hashtag['FTM'] = ftm
hashtag['FTA'] = fta
hashtag = hashtag.drop(['FG%', 'FT%', 'TEAM'], axis=1)
hashtag=hashtag[:].apply(pd.to_numeric, errors='ignore')
hashtag=hashtag.set_index('PLAYER')

zscores=((hashtag.iloc[:,3:-4] -
         hashtag.iloc[:,3:-4].mean(axis=0)) /
         hashtag.iloc[:,3:-4].std(axis=0))

zscores.loc[:,'TO']*=-1
zscores=zscores.drop('TOTAL', axis=1)
# Weight the percentages
fta = hashtag['FTA']
fga = hashtag['FGA']

zscores.loc[:,'FT_perc']=zscores.loc[:,'FT_perc']*fta
zscores.loc[:,'FG_perc']=zscores.loc[:,'FG_perc']*fga

#zscores['Total'] = zscores.sum(axis=1)
#zscores=zscores.sort_values('Total', ascending=False)
#print zscores
#sss

#sys.exit()
data = zscores.iloc[:,:].values
weights = np.ones(9)
#weights=np.array([.5,.5])
y = hashtag.iloc[:,-7].values
print y

nll = lambda *args: -loglike(*args)
soln = minimize(nll, weights, args=(data, y))
fit_weights = soln.x
print fit_weights

pos = np.ones((32, 9)) + 1e-2*np.random.randn(32,9)
nwalkers, ndim = pos.shape
sampler = emcee.EnsembleSampler(nwalkers, ndim, log_prob,
                                args=(data, y))
sampler.run_mcmc(pos, 30000)
samples = sampler.chain

for i in range(ndim):
    for j in range(nwalkers):
        plt.plot(sampler.chain[j, :, i])
    plt.show()

samples = sampler.chain[:,5000:, :].reshape((-1, ndim))
fig = corner.corner(samples, labels=zscores.columns, show_titles=True,
                    quantiles=[.16, .5, .84])
fig.show()
sss
# zscores['Total'] = (zscores*fit_weights).sum(axis=1)
print zscores.sort_values('Total', ascending=False)
ssss
