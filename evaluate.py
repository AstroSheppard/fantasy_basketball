import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Function to read in predictions and results for a given prediction type and league
# Index 1: week, column team, index 3 category or cats won number
input = 'fantasy_predictions'
predictions = pd.read_csv(input + '.csv', index_col=[0,1])
results = pd.read_csv('fantasy_results.csv', index_col=[0,1])
cats = results.index.get_level_values(level=1)[:9].values

brier = 0
unskilled_brier = 0
#team = '1'

pred = predictions.reset_index()
pred = pred[pred.loc[:,'Week'] != 13]
wp = pred[pred.loc[:,'Labels'].str[-3:] == 'win'].apply(pd.to_numeric, errors='ignore')
wp['Labels']=wp['Labels'].str[:-4]
wp = wp.set_index(['Week', 'Labels'])/100.
                                                        
tp = pred[pred.loc[:,'Labels'].str[-3:] == 'tie'].apply(pd.to_numeric, errors='ignore')
tp['Labels']=tp['Labels'].str[:-4]
tp = tp.set_index(['Week', 'Labels'])/100.
lp =  1.0 - wp - tp

wr = results.where(results != 0.5, 0)
tr = results.where(results == 0.5, 0)/.5
lr = results.where(results == 0.0, -1) + 1.0

un_wl = wr.where(wr < -1, .5)
un_tie = tr.where(tr < -1, 0.)

#for i, cat in enumerate(cats):
#    w = cat + '_win'
#    t = cat + '_tie'
    
#    cw = predictions.xs(w, level=1)/100.
#    ct = predictions.xs(t, level=1)/100.
#    cl = 1.0 - ct - cw
#    cr = results.xs(cat, level=1)

#    win_results = cr.copy()
#    tie_results = cr.copy()
#    lose_results = cr.copy()
#    win_results = win_results.where(win_results != 0.5, 0)
#    tie_results = tie_results.where(tie_results == 0.5, 0)/.5
#    lose_results = lose_results.where(lose_results == 0.0, -1) + 1.0
    
#    unskilled_wl = win_results.where(win_results <-1, .5)
#    unskilled_ties =  tie_results.where(tie_results < -1, 0.)
   
brier = (((wp-wr)**2)
         +  ((tp-tr)**2)
         + ((lp-lr)**2))
brier = brier/brier.count().sum()

unskilled_brier += (((un_wl-wr)**2)
                    +  ((un_tie-tr)**2)
                    + ((un_wl-lr)**2))
unskilled_brier = unskilled_brier/unskilled_brier.count().sum()

#brier = brier.sum(axis=0, level=1).sum(axis=1)
#unskilled_brier = unskilled_brier.sum(axis=0, level=1).sum(axis=1)

brier = brier.sum().sum()
unskilled_brier = unskilled_brier.sum().sum()

#print cat
#brier = brier/12./12./9.
#unskilled_brier = unskilled_brier/12./12./9.

print 'Data is from %s' % input
print 'Brier Score: %.3f' % brier
print 'Unskilled Brier Score: %.3f' % unskilled_brier
print 'BSS: %.3f' % ((unskilled_brier-brier)/unskilled_brier)



# Function to find calibration

rs = wr.melt()['value']
ps = wp.melt()['value']
idx = np.argsort(ps)
rs = rs[idx]
ps = ps[idx]

bins = np.arange(20)*.05
bins2 = np.arange(1,21)*.05
centers = (bins + bins2)/2.0
sizes = []
actual = []
for i in range(len(bins)):
    section = rs[(ps>bins[i]) & (ps<bins2[i])]
    size = len(section)
    sizes.append(size)
    actual.append(section.sum()/size)


alpha = np.array(sizes)* np.array(actual)
beta = np.array(sizes) - alpha
std = np.sqrt(alpha*beta/(alpha+beta)/(alpha+beta)/(alpha+beta+1))*1.96

plt.errorbar(centers*100, np.array(actual)*100, yerr=std*100, xerr=[2.5]*len(centers), ls='')
plt.scatter(centers*100, np.array(actual)*100, marker='o', s=sizes, label='My results')
plt.plot([0,100],[0,100], color='k', ls='--', label='Perfect calibration')
plt.xlabel('Predicted frequency of winning category')
plt.ylabel('Actual win percentage')
plt.legend()
plt.show()

plt.plot(centers, (actual-centers)/std)
plt.plot([0,1],[0,0], color='k', ls='--', label='Perfect calibration')
plt.show()
