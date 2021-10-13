

from urllib2 import urlopen
# from urllib.requests import urlopen
import bs4
from bs4 import BeautifulSoup as bs
import pandas as pd
import numpy as np
import re
import sys
from datetime import date
import datetime
import matplotlib.pyplot as plt
import itertools

def get_matchup(team1, team2, week, league='51329'):
    """get current matchup totals"""
    # 107260 for 2018
    temp="https://basketball.fantasysports.yahoo.com/nba/{l}/matchup?date=totals&week={w}&mid1={t1}&mid2={t2}"
    url=temp.format(w=str(week), t1=team1, t2=team2, l=league)
    html=urlopen(url)
    soup =bs(html,'html.parser')
    headers=[th.getText() for th in soup.findAll('tr')[2].findAll('th')][:-1]
    data_rows = soup.findAll('tr')[3:5]
    past = [[td.getText() for td in data_rows[i].findAll('td')[:-1]]
               for i in range(len(data_rows))]
    matchup=pd.DataFrame(past,columns=headers)
    fgm=[]
    ftm=[]
    fga=[]
    fta=[]
    for i, row in matchup.iterrows():
        gm,hold,ga=row['FGM/A*'].partition('/')
        tm,hold,ta=row['FTM/A*'].partition('/')
        fgm.append(gm)
        ftm.append(tm)
        fga.append(ga)
        fta.append(ta)
    matchup['FGM']=fgm
    matchup['FGA']=fga
    matchup['FTM']=ftm
    matchup['FTA']=fta
    matchup=matchup.drop(axis=1, labels=['FGM/A*','FTM/A*'])
    matchup.columns=matchup.columns.str.replace('%','_perc')
    matchup=matchup[:].apply(pd.to_numeric, errors='ignore')
    matchup['Team']=['1',team2]
    matchup1 = matchup.copy()
    
    temp="https://basketball.fantasysports.yahoo.com/nba/{l}/matchup?date=totals&week={w}&mid1={t1}&mid2={t2}"
    url=temp.format(w=str(week), t1=team2, t2=team1, l=league)
    html=urlopen(url)
    soup =bs(html,'html.parser')
    headers=[th.getText() for th in soup.findAll('tr')[2].findAll('th')][:-1]
    data_rows = soup.findAll('tr')[3:5]
    past = [[td.getText() for td in data_rows[i].findAll('td')[:-1]]
               for i in range(len(data_rows))]
    matchup=pd.DataFrame(past,columns=headers)
    fgm=[]
    ftm=[]
    fga=[]
    fta=[]
    for i, row in matchup.iterrows():
        gm,hold,ga=row['FGM/A*'].partition('/')
        tm,hold,ta=row['FTM/A*'].partition('/')
        fgm.append(gm)
        ftm.append(tm)
        fga.append(ga)
        fta.append(ta)
    matchup['FGM']=fgm
    matchup['FGA']=fga
    matchup['FTM']=ftm
    matchup['FTA']=fta
    matchup=matchup.drop(axis=1, labels=['FGM/A*','FTM/A*'])
    matchup.columns=matchup.columns.str.replace('%','_perc')
    matchup=matchup[:].apply(pd.to_numeric, errors='ignore')
    matchup['Team']=['1',team1]
    matchup2 = matchup.copy()

    matchup = pd.DataFrame()
    matchup[team2] = matchup2.iloc[1,:]
    matchup[team1] = matchup1.iloc[1,:]
    matchupx = matchup.T
    matchup = matchupx.set_index('Team')
    return matchup
       

#def trade(team1, team2, players1, players2, fas=None):
    """Test affect of trade. fas is for if the amount of players 
    in the trade is uneven and you'd pick up a FA."""
    #read in team1 and team 2's rosters. Switch players 1 and 2, and sum. Use in get_all() to see
    # how trade affects rankings
#    return 1

def get_fas(sort, proj, player, league='51329', date=None, trade=False):
    """Get list of top 125 FAs sorted and give per game stats (ie, divided by the entire season"""

    # if proj == 'proj' or proj == 'proj_opp':
    #     urltemp = 'https://basketball.fantasysports.yahoo.com/nba/{l}/2/playerswatch' \
    #               '?&status=A&stat1={proj}&jsenabled=1'
    #     key = {'proj': 'P&stat2=P', 'proj_opp':'O'}
 
    urltemp = "https://basketball.fantasysports.yahoo.com/nba/{l}/players?&sort={sort}" \
              "&status=A&pos=P&stat1={proj}&jsenabled=1&count={count}"

    key={'current':'AR&sdir=1', 'pre':'OR&sdir=1'
         , 'owned':'R_PO&sdir=1','3pm':'10&sdir=1'
         , 'pts':'11&sdir=1', 'reb': '12&sdir=1'
         , 'ast':'13&sdir=1', 'st':'14&sdir=1'
         , 'blk':'15&sdir=1', 'TO':'16&sdir=0'
         , 'proj':'S_PSR', 'next7':'S_PS7', 'avg':'S_AS_2019'
         , 'opp':'O_O', 'avg30' : 'S_AL30'}
 
    df=pd.DataFrame()
    c=0

    while True:
        # if proj == 'proj' or proj == 'proj_opp':
        #     url = urltemp.format(l=league, proj=key[proj])
        # else:
        url=urltemp.format(sort=key[sort], proj=key[proj], count=c, l=league)
        html=urlopen(url)
        soup =bs(html,'html.parser')
        headers=[th.getText() for th in soup.findAll('tr')[2].findAll('th')]
        headers=headers[:-1]
        data_rows = soup.findAll('tr')[1:]
        player_data = [[td.getText() for td in data_rows[i].findAll('td')[:-1]]
                       for i in range(len(data_rows))]
        player_data=[p for p in player_data if len(p)==len(headers)]
        pdd=np.asarray(player_data)
        pdd[:,1]=[name.split('\n')[3].rpartition('-')[0].strip()[:-3].strip()
                   for name in pdd[:,1]]
        one=pd.DataFrame(pdd, columns=headers)
        df=df.append(one, ignore_index=True)
        if player in df['Players'].values:
            break
        c+=25

    df.columns=df.columns.str.replace('%','_perc')
    df.columns=df.columns.str.replace('*','')
   # df['Players']=[name.split('\n')[3].rpartition('-')[0].strip()[:-3].strip()
   #                for name in df['Players'].values]
    if proj == 'opp':
        inp=date[5:]
        m,d=inp.split('-')
        day=str(int(m))+'/'+str(int(d))
        df['Today']=df[day]!=''
        df=pd.concat([df['Players'],df['Today']], axis=1)
    else:
        fgm=[]
        ftm=[]
        fga=[]
        fta=[]
        for i, row in df.iterrows():
            gm,hold,ga=row['FGM/A'].partition('/')
            tm,hold,ta=row['FTM/A'].partition('/')
            fgm.append(gm)
            ftm.append(tm)
            fga.append(ga)
            fta.append(ta)
        df['FGM']=fgm
        df['FGA']=fga
        df['FTM']=ftm
        df['FTA']=fta
        df.replace('-', value=0.0, inplace=True)
        # drop columns to match format of team stats
        
        if proj=='avg' or proj=='avg30':
            d=[0,2,3,4,5,6,7,8,9,10,11,13]
            df=df.drop(axis=1, labels=[df.columns[i] for i in d])
            df=df[:].apply(pd.to_numeric, errors='ignore')
        else:
            d=[0,1,2,6,9,10,12,14, 18,21]
            df=df.drop(axis=1, labels
                       =[df.columns.sort_values(ascending=False)[i] for i in d])
            df=df[:].apply(pd.to_numeric, errors='ignore')
            df.loc[:,'3PTM':]=df.loc[:,'3PTM':].div(df['GP'],axis=0)
            df=df.dropna()
        if trade == False:
            df=df.drop(labels=['GP'], axis=1)
        if player not in df['Players'].values:
            sys.exit('Player not in FA list. Check spelling and use \'I. LastName\' format')

    
    return df[df['Players']==player].iloc[0,1:]

    
def get_team(team, type, league='51329', date=None, drops=None,
             include_bench=False, injured=True, trade = []):

    url_temp="https://basketball.fantasysports.yahoo.com/nba/{id}/{team}{type}"
    team=team

    key1={'r':'?stat1=P&stat2=PSR'
          ,'proj': 'stat1=P&stat2=P', 'o':'stat1=O'
          , 'avg':'stat1=AS&stat2=AS_2019'
          , 'avg_30': 'stat1=AS&stat2=AL30'}
    day='/team?&date={day}&'
    if date!=None:
        day=day.format(day=date)
        link=day+key1[type]
    else:
        link='?'+key1[type]
        
    url=url_temp.format(id=league, team=team, type=link)
    html=urlopen(url)

    soup =bs(html,'html.parser')
    headers=[th.getText() for th in soup.findAll('tr')[2].findAll('th')]
    headers=headers[:-1]
    data_rows = soup.findAll('tr')[1:]
    player_data = [[td.getText() for td in data_rows[i].findAll('td')[:-1]]
                   for i in range(len(data_rows))]
    for player in player_data:
        if len(player)>4:
            del player[4]
    player_data=[player for player in player_data if len(player)==len(headers)]
            
    # Clean up data
    df=pd.DataFrame(player_data, columns=headers)
    try:
        df=df.drop(axis=1, labels=['Action', 'Forecast', 'Opp', 'Status'])
    except KeyError:
        df=df.drop(axis=1, labels=['Action', 'Opp', 'Status'])
    stats=df.drop(axis=1, labels=['Pre-Season', 'Current', '% Started'])
    stats.columns=stats.columns.str.replace('%','_perc')
    names = []
    inj = []

    for name in stats['Players'].values:
        names.append(name.split('\n')[2].rpartition('-')[0][:-4].strip())
        inj.append(name.split('\n')[5]=='Injured')
    stats['Players']=names
    stats['Inj']=inj

    # stats['Players']=[name.split('\n')[2].split('-')[0][:-4].strip()
    #              for name in stats['Players'].values]
    
    fgm=[]
    ftm=[]
    fga=[]
    fta=[]
    for i, row in stats.iterrows():
        gm,hold,ga=row['FGM/A*'].partition('/')
        tm,hold,ta=row['FTM/A*'].partition('/')
        fgm.append(gm)
        ftm.append(tm)
        fga.append(ga)
        fta.append(ta)
    stats['FGM']=fgm
    stats['FGA']=fga
    stats['FTM']=ftm
    stats['FTA']=fta
    stats.replace('-', value=0.0, inplace=True)
    stats=stats.drop(axis=1, labels=['FGM/A*','FTM/A*'])
    stats=stats.set_index('Pos')
    stats=stats[:].apply(pd.to_numeric, errors='ignore')

    # For avg stats projections, need to check if a game is played that day
    if type == 'avg' or type == 'avg_30':
        # First drop extra axes
        stats=stats.drop(axis=1, labels=['MPG', 'GP*'])
        if date != None:
            url=url_temp.format(id=league, team=team, type=day+key1['o'])
            html=urlopen(url)

            soup =bs(html,'html.parser')
            headers=[th.getText() for th in soup.findAll('tr')[2].findAll('th')]
            headers=headers[:-1]
            data_rows = soup.findAll('tr')[1:]
            player_data = [[td.getText() for td in data_rows[i].findAll('td')[:-1]]
                           for i in range(len(data_rows))]
    
            for player in player_data:
                if len(player)>4:
                    del player[4]
            player_data=[player for player in player_data if len(player)==len(headers)]
            
            # Clean up data
            opps=pd.DataFrame(player_data, columns=headers)
            opps['Players']=[name.split('\n')[2].rpartition('-')[0].strip()[:-3].strip()
                             for name in opps['Players'].values]
            inp=date[5:]
            m,d=inp.split('-')
            day=str(int(m))+'/'+str(int(d))
            opps['Today']=opps[day]!=''
            opps=pd.concat([opps['Players'],opps['Today']], axis=1).set_index('Players')
            stats=stats.join(opps, on='Players')
        
        
    if date != None:
        if include_bench==False:
            stats=stats.loc[:'Util',:]
        else:
            if team != '2' and team != '9':
                stats=stats.loc[:'BN',:]
        
    else:
        if team != '2':
            stats=stats.loc[:'BN',:]

            
    try:
        if drops != None:
            stats=stats[stats['Players'] != drops]
    except ValueError:
        for drop in drops:
            stats=stats[stats['Players'] != drop]

    #print stats['Players']
    #####
    # if date  == '2019-12-07':
    #     stats=stats[stats['Players'] != 'Lonzo Ball']
    #     stats=stats[stats['Players'] != 'Maxi Kleber']
    #stats=stats[stats['Players'] != 'Montrezl Harrell']
    #stats=stats[stats['Players'] != 'Nerlens Noel']
    #stats=stats[stats['Players'] != 'Spencer Dinwiddie']
    #stats=stats[stats['Players'] != 'Paul George']
    #stats=stats[stats['Players'] != 'LeBron James']
    #stats=stats[stats['Players'] != 'Jarrett Allen']
    #stats=stats[stats['Players'] != 'Taurean Prince']
    # stats=stats[stats['Players'] != 'Nerlens Noel']
    # stats=stats[stats['Players'] != 'Mohamed Bamba']
    # stats=stats[stats['Players'] != 'Domantas Sabonis']
    # stats=stats[stats['Players'] != 'LaMarcus Aldridge']
    #####


    if len(trade) != 0:
        person = pd.DataFrame()
        for tp in trade:
            person = pd.concat([person, stats[stats.loc[:,'Players'] == tp]])
            stats = stats[stats.loc[:,'Players'] != tp]
    if type == 'avg' or type == 'avg_30':
        if injured == True:
            stats = stats[stats['Today'] == True]
            stats = stats[stats['Inj'] == False]
            stats = stats.drop('Inj', axis=1)
            team = stats.iloc[:,1:-1].sum().astype(float)
        else:
            stats = stats.drop('Inj', axis=1)
            team = stats.iloc[:,1:].sum().astype(float)
    else:
        stats = stats.drop('Inj', axis=1)
        team=stats.iloc[:,1:].sum().astype(float)
    try:
        team['FG_perc']=team['FGM']/team['FGA']
        team['FT_perc']=team['FTM']/team['FTA']
    except RuntimeWarning:
        sys.exit('Runtime error')

    if len(trade) != 0:
        return [team, person]
    else:
        return team
    # Now we have, in a good format, all the projected stats for 
  

def matchup(team1, team2, week, start=0, end=7,
            type='proj', league='51329', fas=None, drops=None,
            include_bench=True, sim=False):
    """ Last input is a dict of fas and drops by date"""

    # Should I account for minutes and rates separetely? This way I can acct for correlation between
    # blks and pts and stls due to playing time
    
    days=[str(date.today()+datetime.timedelta(days=x)) for x in range(start, end)]
    if drops == None:
        drops = [None]*len(days)
    if fas == None:
        fas = [None]*len(days)
        
    drops = dict(zip(days, drops))
    fas = dict(zip(days, fas))
    
    t1=pd.Series()
    t2=pd.Series()
    for i, dates in enumerate(days):
        print dates
        t1=t1.add(get_team(team1, type, league=league, date=dates,
                           drops=drops[dates],
                           include_bench=include_bench), fill_value=0)
        if fas[dates] != None:
            game_check=int(get_fas('owned','opp', fas[dates], date=dates,
                                   league=league)['Today'])
            free=get_fas('owned',type, fas[dates], league=league)*game_check
            t1=t1.add(free, fill_value=0)
        #else:
        #    t1=t1.add(get_team(team1, type, date=dates,
        #                       league=league,
        #                       include_bench=include_bench), fill_value=0)
        t2=t2.add(get_team(team2, type, date=dates, league=league,
                           include_bench=include_bench), fill_value=0)

    #kein=[1,1,1,6.2,5.3,1.6,.6,.5,.8,2.4,5.9,.4,.6]
    #x,x,3, pts, reb, ast, st, blk, to, fgm, fga, ftm, fta
    #dd=np.array([1,1,0,0,0,0,0,0,0,0,-1,0,0])
    #dd=np.array([1,1,.6,6.8,3.3,3.3,1.4,.5,1.7,2.6,5.8,1.1, 1.3])
    #jp=np.array([1,1,3.1,44.3,17.4,16.0,6.2,2.3,6.2,16.3,38.2,8.7,11.1])
    #dd=np.array([1,1,1.3,11.5,6.8,1.1,.6,.3,1.2,4.3,10.2,1.6,2.1])*1.0
    #kein=dj
    #kein=dd
    #kk=pd.Series(kein)
    #kk.index=t1.index
    #t1=t1.add(kk)
    t1['FG_perc']=t1['FGM']/t1['FGA']
    t1['FT_perc']=t1['FTM']/t1['FTA']
    t2['FG_perc']=t2['FGM']/t2['FGA']
    t2['FT_perc']=t2['FTM']/t2['FTA']
    if t1['FGA']==0:
        t1[:]=0
    if t2['FGA']==0:
        t2[:]=0
    t1['Team']=team1
    t2['Team']=team2
    matchup=pd.concat([t1,t2], axis=1).T.set_index('Team')
    current=get_matchup(team1, team2, week, league=league)
    current=current.replace('-',0)
    current=current.replace('\*','', regex=True).astype(float)
    total=matchup.add(current, fill_value=0)
    total['FG_perc']=total['FGM']/total['FGA']
    total['FT_perc']=total['FTM']/total['FTA']
    total=total.drop(axis=1, labels=['FGM','FGA','FTM','FTA'])
    temp=total.T
    temp['Margin']=(temp[team1]-temp[team2]).astype(float)
    temp.iloc[:2,2]=temp.iloc[:2,2].round(4)
    temp.iloc[:2,2]=temp.iloc[:2,2].round(4)
    temp.iloc[2:,2]=temp.iloc[2:,2].round(1)
    temp.iloc[2:,2]=temp.iloc[2:,2].round(1)
    total=temp.T
    to=np.ones(total.shape[1]).astype(bool)
    to[-1]=False
    total['Score']='NaN'
    total.loc[team1,'Score']=((total.loc[team1,:'TO']>total.loc[team2,:'TO'])==to).sum()
    total.loc[team2,'Score']=((total.loc[team2,:'TO']>total.loc[team1,:'TO'])==to).sum()

    #fas=get_fas('st','remaining')

    matchup['2PM']=matchup['FGM']-matchup['3PTM']
    matchup['FTO']=matchup['FTA']-matchup['FTM']
    matchup['FGO']=matchup['FGA']-matchup['FGM']
    
    t1=matchup.loc[team1,:].astype(int)
    t2=matchup.loc[team2,:].astype(int)
    n=100000
    d1=np.random.poisson(t1.values, size=(n,t1.shape[0]))
    d2=np.random.poisson(t2.values, size=(n,t2.shape[0]))
    df1=pd.DataFrame(d1, columns=t1.index)
    df2=pd.DataFrame(d2, columns=t2.index)
    df1['FGM']=df1['2PM']+df1['3PTM']
    df1['FGA']=df1['FGO']+df1['FGM']
    df1['FTA']=df1['FTO']+df1['FTM']
    df1['PTS']=3*df1['3PTM']+2*df1['2PM']+df1['FTM']
    df1=df1.drop(axis=1, labels=['2PM', 'FTO','FGO'])
    df2['FGM']=df2['2PM']+df2['3PTM']
    df2['FGA']=df2['FGO']+df2['FGM']
    df2['FTA']=df2['FTO']+df2['FTM']
    df2['PTS']=3*df2['3PTM']+2*df2['2PM']+df2['FTM']
    df2=df2.drop(axis=1, labels=['2PM', 'FTO','FGO'])

    df1=df1.add(current.loc[team1,:])
    df2=df2.add(current.loc[team2,:])
    df1['FG_perc']=df1['FGM']/df1['FGA']
    df1['FT_perc']=df1['FTM']/df1['FTA']
    df2['FG_perc']=df2['FGM']/df2['FGA']
    df2['FT_perc']=df2['FTM']/df2['FTA']
    df1=df1.drop(['FGM','FTM','FGA', 'FTA'], axis=1)
    df2=df2.drop(['FGM','FTM','FGA', 'FTA'], axis=1)
    err1=df1.std(axis=0)
    err2=df2.std(axis=0)
    err=np.sqrt(err1**2+err2**2).round(2)
    err.name='Margin Error'
    #err[:2]=err[:2].round(4)
    #err[2:]=err[2:].round(2)
    total=total.append(err)
    total.loc[:,'FG_perc':'FT_perc']= (total.loc[:,'FG_perc':'FT_perc']*100).astype(float).round(2)

    win=(df1>df2).astype(int)
    win['TO']=(df1['TO']<df2['TO']).astype(int)
    tie=(df1==df2).astype(int)
    result=win+0.5*tie
    wins=result.sum(axis=1)
    
    
    weights= np.ones_like(wins)/float(len(wins))
    hold=plt.hist(wins, bins=np.arange(0,20)/2.-.25, weights=weights)
    freq=hold[0]*100
    num=hold[1][:-1]+.25
    outcome=pd.Series(freq, index=num).round(2)
    perc_win=(win.sum(axis=0)/n*100.).round(2)
    perc_win.name='Win'
    perc_tie=(tie.sum(axis=0)/n*100.).round(2)
    perc_tie.name='Tie'
    perc=pd.concat([perc_win, perc_tie], axis=1)
    ev=np.round(np.sum(outcome/100.*np.arange(19)/2.),3)
    
    print 'Odds of finishing with each point amount:'
    print outcome
    print
    print 'Odds of winning each category:'
    print perc
    print
    print 'Projected Results (averages):'
    print total
    print 
    print 'Expected Points: %.2f ' % ev
    print 'Win: %.2f%%' %  outcome[outcome.index>=5].sum()
    print 'Lose: %.2f%%' %  outcome[outcome.index<4.5].sum()
    print 'Tie: %.2f%%' %  outcome[4.5]
    print
    if sim == True:
        return wins
    else:
        return [outcome, perc]
    

def get_all(week=19, type='r', league='51329', inj=False):
    # TRADES: Can only do 1 for 1 trades, but can do multiple teams.
    # Set the players coming from each team, and note the team they will
    # go to. 

    ## Later: can add actual schedule to go with averages, can go through every actual matchup
    ## , can account for injured guys, use hashtag instead of yahoo
    teams=np.arange(1,13)
    weeks_left = 26-week
    avg = pd.DataFrame()
    proj = pd.DataFrame()
    avg_30 = pd.DataFrame()

    # issue where 2 for 1 trades with fa, especially for rubio or fvv involving gordon, are weirdly high
    avg_trades = pd.DataFrame()
    proj_trades = pd.DataFrame()
    avg_30_trades = pd.DataFrame()
    trades = np.zeros((12,5)).astype(int).astype(str)
    #trades[1, 0] = 'Aaron Gordon'
    #trades[1, 1] = 'Alec Burks' 
    #trades[0, 0] = 'Andre Drummond'
    #trades[6, 0] = 'Ricky Rubio'
    trade_teams = np.zeros(12).astype(str)
    #trade_teams[1] = '1'
    #trade_teams[0] = '2'

    avg_fas = pd.DataFrame()
    proj_fas = pd.DataFrame()
    avg_30_fas = pd.DataFrame()
    fas_teams = np.zeros(12).astype(int).astype(str)
    drops = np.zeros((12, 5)).astype(int).astype(str)

    #fas_teams[1] = 'D. Dedmon'
    # drops[1, 0] = 'Patrick Beverley'
    #drops[1, 1] = ''

    for num, i in enumerate(teams):
        print i
        if drops[num, 0] == '0':
            drop = None
        else:
            drop = drops[num]
            
        trade_list = trades[num, trades[num,:] != '0']
        if len(trade_list) != 0:
            proj_series, proj_players = get_team(str(i), 'r', league=league,
                                                 include_bench=True,
                                                 injured=inj, trade=trade_list, drops=drop)
            avg_series, avg_players = get_team(str(i), 'avg', league=league,
                                               include_bench=True, injured=inj,
                                               trade=trade_list, drops=drop)
            avg_30_series, avg_30_players = get_team(str(i), 'avg_30', league=league,
                                                     include_bench=True, injured=inj,
                                                     trade=trade_list, drops=drop)

        
            proj_players['Team'] = trade_teams[num]
            proj_trades = proj_trades.append(proj_players,
                                             ignore_index=True)
            avg_players['Team'] = trade_teams[num]
            avg_trades = avg_trades.append(avg_players,
                                           ignore_index=True)
            avg_30_players['Team'] = trade_teams[num]
            avg_30_trades = avg_30_trades.append(avg_30_players,
                                                 ignore_index=True)
        else:
            proj_series = get_team(str(i), 'r', league=league,
                                   include_bench=True, injured=inj, drops=drop)
            avg_series = get_team(str(i), 'avg', league=league,
                                  include_bench=True, injured=inj, drops=drop)
            avg_30_series = get_team(str(i), 'avg_30', league=league,
                                     include_bench=True, injured=inj, drops=drop)
            
        if fas_teams[num] != '0':
            af = get_fas('owned', 'avg', fas_teams[num], trade=True)
            a30f = get_fas('owned', 'avg30', fas_teams[num], trade=True)
            pf = get_fas('owned', 'proj', fas_teams[num], trade=True)
            pf = pf * pf['GP']
            pf = pf.drop('GP')
            

            pf['Team']=str(i)
            proj_fas=proj_fas.append(pf, ignore_index=True)
            af['Team'] = str(i)
            avg_fas=avg_fas.append(af, ignore_index=True)
            a30f['Team'] = str(i)
            avg_30_fas=avg_30_fas.append(a30f, ignore_index=True)


        #if drops[num] != '0':
        #     stats = stats[stats.loc[:,'Players'] != tp]
        #    avg_series
        #    avg_30_series

        proj_series['Team']=str(i)
        proj=proj.append(proj_series, ignore_index=True)
        avg_series['Team']=str(i)
        avg=avg.append(avg_series, ignore_index=True)
        avg_30_series['Team']=str(i)
        avg_30=avg_30.append(avg_30_series, ignore_index=True)


    proj=proj.set_index('Team')
    avg=avg.set_index('Team')
    avg_30=avg_30.set_index('Team')
    if np.any(trades != '0'):
        proj_trades = proj_trades.set_index('Team').drop(['Inj', 'Players'], axis=1).groupby('Team').sum()
        avg_trades=avg_trades.set_index('Team').drop(['Inj', 'Players'], axis=1).groupby('Team').sum()
        avg_30_trades=avg_30_trades.set_index('Team').drop(['Inj', 'Players'], axis=1).groupby('Team').sum()

        print proj_trades
    if np.any(fas_teams != '0'):
        proj_fas = proj_fas.set_index('Team')
        avg_fas = avg_fas.set_index('Team')
        avg_30_fas = avg_30_fas.set_index('Team')

    print avg_30_fas
    print avg_fas
    print proj_fas
    
    print proj_trades
    print avg_trades
    print avg_30_trades
    # Group avg trades by team first and sum them
    avg = avg.add(avg_trades, fill_value=0)
    avg_30 = avg_30.add(avg_30_trades, fill_value=0)
    proj = proj.add(proj_trades, fill_value=0)
    avg = avg.add(avg_fas, fill_value=0)
    avg_30 = avg_30.add(avg_30_fas, fill_value=0)
    proj = proj.add(proj_fas, fill_value=0)
    proj=proj/weeks_left
    nGames = 3.17 # average per week. Will vary team to team
    avg = avg * nGames
    avg_30 = avg_30 * nGames
    
    # Weighted average helps balance future projections (which
    # have games expected to play weighed in), actual performance
    # (since projections can be wild), and recent trends.
    paa = 0.5*proj + 0.4*avg + 0.1*avg_30
    
    paa['FG_perc'] = paa['FGM']/paa['FGA']
    paa['FT_perc'] = paa['FTM']/paa['FTA']
    weekly=paa.drop(axis=1, labels=['FGA','FTM', 'FGM', 'FTA' ])
    weekly=weekly.drop(axis=1, labels=[])
    # weekly.loc[:,'FG_perc':'FT_perc']*=weeks_left
    contenders = weekly.drop(['3', '4','5','7', '8', '1','10'])
    print contenders

    #contenders=all.drop(axis=1, labels=['FGA','FTM', 'FGM', 'FTA', 'FG_perc', 'FT_perc'])
    #contenders = contenders.drop(['4','5','7','10'])
    zscores=(contenders-contenders.mean(axis=0))/contenders.std(axis=0)
    #zscores=(contenders-contenders.mean(axis=0))/np.sqrt(contenders)
    # Flesh the above out: diff divided by uncertainty and not std...
    zscores['TO'] *= -1
    zscores[zscores > 3] = 3
    zscores[zscores < -3] = -3
    zscores['Total'] =  zscores.sum(axis=1)
    ranks = contenders.rank(axis=0, ascending=False)
    ranks.loc[:,'TO'] = 9 - ranks.loc[:,'TO']
    print ranks
    print zscores

    team_nums = np.arange(1,13).astype(str)
    
    paa['2PM']=paa['FGM']-paa['3PTM']
    paa['FTO']=paa['FTA']-paa['FTM']
    paa['FGO']=paa['FGA']-paa['FGM']

    paa.index = paa.index.astype(int)
    paa = paa.sort_values('Team')
    paa.index = paa.index.astype(str)
    
    #t1=all.loc[team1,:].astype(int)
    #t2=matchup.loc[team2,:].astype(int)
    n=100000
    d1=np.random.poisson(paa.values, size=(n,paa.shape[0], paa.shape[1]))
    df = pd.DataFrame(columns=paa.columns)
    for i in range(d1.shape[1]):
        df_team = pd.DataFrame(d1[:,i,:], columns=paa.columns, index=[team_nums[i]]*n)
        df = pd.concat([df, df_team], axis=0)
        print team_nums[i]
    
    #d2=np.random.poisson(t2.values, size=(n,t2.shape[0]))
    #df1=pd.DataFrame(d1, columns=all.columns)
    #df2=pd.DataFrame(d2, columns=t2.index)
    df['FGM']=df['2PM']+df['3PTM']
    df['FGA']=df['FGO']+df['FGM']
    df['FTA']=df['FTO']+df['FTM']
    df['PTS']=3*df['3PTM']+2*df['2PM']+df['FTM']
    df=df.drop(axis=1, labels=['2PM', 'FTO','FGO'])

    df['FG_perc']=df['FGM']/df['FGA']
    df['FT_perc']=df['FTM']/df['FTA']
    df=df.drop(['FGM','FTM','FGA', 'FTA'], axis=1)

    gen = itertools.combinations(team_nums, r=2)
    evs = pd.DataFrame(index=team_nums, columns=team_nums)
    win_perc = pd.DataFrame(index=team_nums, columns=team_nums)
    
    wins_dist = pd.DataFrame(index=np.repeat(team_nums, n), columns=team_nums)
    bad_combos = [('1', '2'), ('1','11'), ('1', '12'), ('1','3'), ('1', '4'), ('1','5'),('1','6'),('1','7'),
                  ('2', '10'), ('2', '11'), ('2','12'), ('2', '3'), ('2','4'), ('2','5'), ('2','6'), ('3','4'),('4','11'),
                  ('5','10'), ('6','9'), ('7', '8'), ('3','12'), ('6','11'), ('7','10'), ('7','11'), ('8','10'),
                  ('3', '9'), ('3','10'), ('3','11'), ('4','8'),('4','9'), ('8','9'),('3','5'), ('4','12'), ('8','11'),
                  ('4','10'),('5','7'),('5','8'),('5','9'),('6','12'), ('9','12'), ('9','10'),
                  ('6','7'),('6','8'), ('7','12'), ('7','9'),  ('5','11'),
                  ('6','10'), ('8','12'),('1','8'), ('2','7'), ('3', '6'), ('4','5'),
                  ('9','11'),('10','12')]

    combos = [('2','8'), ('1','9'),('3','7'),('4','6'),('5','12'),('10','11'),('2','9')
              ,('1','10'),('3','8'),('4','7'),('5','6'),('11','12')]
    for i, combo in enumerate(combos):
        team1 = combo[0]
        team2 = combo[1]
        if i<6:
            wins = matchup(team1, team2, 19, end=4, sim=True)
        else:
            wins = matchup(team1, team2, 20, start=4, end=11, sim=True)
            
        wins2 = 9 - wins
        wins.index = [team1]*n
        wins2.index = [team2]*n
        wins_dist.loc[team1,team2]=wins
        wins_dist.loc[team2,team1]=wins2
    totals_dist = wins_dist.sum(axis=1)
    groups = totals_dist.groupby(totals_dist.index).apply(list)
    score_dist = pd.DataFrame(data=np.stack(groups.values).T, columns=groups.index)

        
    """for combo in gen:
        if combo in bad_combos:
            print 'bad'
            print combo
            pass
        else:
            print combo
            team1 = combo[0]
            team2 = combo[1]
            df1 = df.loc[team1,:].reset_index()
            df2 = df.loc[team2,:].reset_index()

            win=(df1>df2).astype(int)
            win['TO']=(df1['TO']<df2['TO']).astype(int)
            tie=(df1==df2).astype(int)
            result=win+0.5*tie
            wins=result.sum(axis=1)
            
            ev = wins.mean().round(3)
            ev2 = 9.0 - ev

            
        
            # weights= np.ones_like(wins)/float(len(wins))
            # hold=plt.hist(wins, bins=np.arange(0,20)/2.-.25, weights=weights)
            # freq=hold[0]*100
            # num=hold[1][:-1]+.25
            # outcome=pd.Series(freq, index=num).round(2)
            # perc_win=(win.sum(axis=0)/n*100.).round(2)
            # perc_win.name='Win'
            # perc_tie=(tie.sum(axis=0)/n*100.).round(2)
            # perc_tie.name='Tie'
            # perc=pd.concat([perc_win, perc_tie], axis=1).drop('index')
            # ev=np.round(np.sum(outcome/100.*np.arange(19)/2.),3)
            # ev2 = 9.0 - ev
            perc_win = ((wins >= 4.5).sum()/float(n)*100).round(2)
            #perc_tie = ((wins == 4.5).sum()/float(n)*100).round(2)
            evs.loc[team2,team1] = ev
            evs.loc[team1,team2] = ev2
            win_perc.loc[team2,team1] = perc_win
            win_perc.loc[team1,team2] = 100. - perc_win 
            
            wins2 = 9 - wins
            wins.index = [team1]*n
            wins2.index = [team2]*n
            wins_dist.loc[team1,team2]=wins
            wins_dist.loc[team2,team1]=wins2
            

    
    evs['Avg'] = evs.mean(axis=0)
    evs['Avg_win_perc'] = win_perc.mean(axis=0)
    print evs.sort_values('Avg', ascending=False)
    """
    # Column is EV for that team vs index team
    totals_dist = wins_dist.sum(axis=1)
    groups = totals_dist.groupby(totals_dist.index).apply(list)
    score_dist = pd.DataFrame(data=np.stack(groups.values).T, columns=groups.index)


    current =  [78.5, 93, 74, 68, 74.5, 78.5, 77.5, 80.5, 93, 58, 95.5, 100]
    current = pd.Series(data=current, index = np.arange(1,13).astype(str))
    score_dist = score_dist + current

    score_means = score_dist.mean().sort_values(ascending=False)
    print score_means
    print score_dist.std().sort_values(ascending=False)
    season_rank = score_dist.rank(axis=1, ascending=False, method='first')

    reg_win = ((season_rank==1.).sum()/n*100.).round(2).sort_values(ascending=False)
    reg_tie =  ((season_rank==1.5).sum()/n*100.).round(2).sort_values(ascending=False)
    playoff = ((season_rank<7.).sum()/n*100.).round(2).sort_values(ascending=False)
    bye = ((season_rank<2.5).sum()/n*100.).round(2).sort_values(ascending=False)
    reg_cash = reg_win + reg_tie*.5
    #print "Reg EV:",  reg_cash
    #print "Playoff percent:",  playoff
    #score_dist.hist(bins=12, density=True)
    #plt.show()
    #score_dist.rank(axis=1, ascending=False).hist(bins=12, density=True)
    #plt.show()

    playoff_ev = playoff.copy() - playoff.copy()
    print "now do playoff teams only"

    bad_combos=[]
    for i, seed in season_rank.iterrows():
        seeds = seed[seed<7].astype(int)
        remainder = seed[seed>=7].index.values.astype(str)
        #seeds= pd.Series(seeds.index.values, index=seeds.astype(int))
        # Create win_perc matrix
        #wp = np.zeros((6,6))
        # populate the rest of the array
    
        playoff_teams = seeds.index
        team_nums = np.sort(playoff_teams.values.astype(int)).astype(str)
        gen = itertools.combinations(team_nums, r=2)
        # evs = pd.DataFrame(index=team_nums, columns=team_nums)
        # win_perc = pd.DataFrame(index=team_nums, columns=team_nums)

        # wins_dist = pd.DataFrame(index=np.repeat(team_nums, n), columns=team_nums)
        
        for combo in gen:
            #if combo not in bad_combos:
            #    pass
            if combo in bad_combos:
                pass
            else:
                #bad_combos.remove(combo)  
                bad_combos.append(combo)
                team1 = combo[0]
                team2 = combo[1]
                df1 = df.loc[team1,:].reset_index()
                df2 = df.loc[team2,:].reset_index()
                
                win=(df1>df2).astype(int)
                win['TO']=(df1['TO']<df2['TO']).astype(int)
                tie=(df1==df2).astype(int)
                result=win+0.5*tie
                wins=result.sum(axis=1)

            
                #ev = wins.mean().round(3)
                #ev2 = 9.0 - ev
                
                # weights= np.ones_like(wins)/float(len(wins))
                # hold=plt.hist(wins, bins=np.arange(0,20)/2.-.25, weights=weights)
                # freq=hold[0]*100
                # num=hold[1][:-1]+.25
                # outcome=pd.Series(freq, index=num).round(2)
                # perc_win=(win.sum(axis=0)/n*100.).round(2)
                # perc_win.name='Win'
                # perc_tie=(tie.sum(axis=0)/n*100.).round(2)
                # perc_tie.name='Tie'
                # perc=pd.concat([perc_win, perc_tie], axis=1).drop('index')
                # ev=np.round(np.sum(outcome/100.*np.arange(19)/2.),3)
                # ev2 = 9.0 - ev
                if seeds[team1] > seeds[team2]:
                    perc_win = ((wins >= 4.5).sum()/float(n)*100).round(2)
                else:
                    perc_win = ((wins >= 5.0).sum()/float(n)*100).round(2)
                #evs.loc[team2,team1] = ev
                #evs.loc[team1,team2] = ev2
                win_perc.loc[team2,team1] = perc_win
                win_perc.loc[team1,team2] = 100. - perc_win
            
                #wins2 = 9 - wins
                #wins.index = [team1]*n
                #wins2.index = [team2]*n
                #wins_dist.loc[team1,team2]=wins
                #wins_dist.loc[team2,team1]=wins2

        wp = win_perc.loc[seeds.index,seeds.index]
        mapper = dict(zip(seeds.index.values, seeds.values))
        seed_wp = wp.rename(index=mapper, columns=mapper)
        cols = seed_wp.columns.sort_values()
        seed_wp = seed_wp[cols].sort_index().T
        ws = (seed_wp/100.).astype(float).fillna(0)
        fs = np.zeros(6)
        ls = np.zeros(6)

        # Finals odds
        fs[0] = ws.loc[1, 4]*ws.loc[4, 5] + ws.loc[1, 5]*(1 - ws.loc[4, 5])
        fs[1] = ws.loc[2, 3]*ws.loc[3, 6] + ws.loc[2, 6]*(1 - ws.loc[3, 6])
        fs[2] = ws.loc[3, 6]*ws.loc[3, 2]
        fs[3] = ws.loc[4, 5]*ws.loc[4, 1]
        fs[4] = ws.loc[5, 4]*ws.loc[5, 1]
        fs[5] = ws.loc[6, 3]*ws.loc[6, 2]

        # 3rd place game odds
        ls[0] = 1 - fs[0]
        ls[1] = 1 - fs[1]
        ls[2] = ws.loc[3, 6] * ws.loc[2, 3]
        ls[3] = ws.loc[4, 5] * ws.loc[1, 4]
        ls[4] = ws.loc[5, 4] * ws.loc[1, 5]
        ls[5] = ws.loc[6, 3] * ws.loc[2, 6]

        # Set up array to zero out certain win probs to make dot product work
        zz = np.ones((6, 6))
        zz[0, 3:5] = 0
        zz[3:5, 0] = 0
        zz[1, 2] = 0
        zz[1, 5] = 0
        zz[2, 1] = 0
        zz[2, 5] = 0
        zz[3, 4] = 0
        zz[4, 3] = 0
        zz[5, 1:3] = 0

        ws = ws * zz

        # finsihing odds

        champ = ws.dot(fs) * fs
        runner = ws.T.dot(fs) * fs
        bronze = ws.dot(ls) * ls

        # Expected values

        playoff_money = champ*300. + runner*150. + bronze*50.
        invert_mapper = {v: k for k, v in mapper.iteritems()}
        playoff_money = playoff_money.rename(index=invert_mapper)
        others = pd.Series(index = remainder).fillna(0)
        playoff_ev = playoff_ev + playoff_money.append(others)
        
    playoff_ev = playoff_ev/n
    gross = playoff_ev + reg_cash
    profit = gross - 50
    #evs['Avg'] = evs.mean(axis=0)
    #evs['Avg_win_perc'] = win_perc.mean(axis=0)
    #print evs.sort_values('Avg', ascending=False)
    # Column is EV for that team vs index team
    #totals_dist = wins_dist.sum(axis=1)
    #groups = totals_dist.groupby(totals_dist.index).apply(list)
    #score_dist = pd.DataFrame(data=np.stack(groups.values).T, columns=groups.index)

 
    #current =  [61, 63, 56, 48, 48, 53, 54, 61, 69, 41, 68, 69]
    #current = pd.Series(data=current, index = np.arange(1,13).astype(str))
    #score_dist = score_dist + current

    #score_means = score_dist.mean().sort_values(ascending=False)
    #print score_means
    #print score_dist.std().sort_values(ascending=False)
    #season_rank = score_dist.rank(axis=1, ascending=False)

    #cash = ((season_rank<4.).sum()/n*100.).round(2).sort_values(ascending=False)
    #win = ((season_rank==1.).sum()/n*100.).round(2).sort_values(ascending=False)
    #second = ((season_rank==2.).sum()/n*100.).round(2).sort_values(ascending=False)
    #third = ((season_rank==3.).sum()/n*100.).round(2).sort_values(ascending=False)
    #tie1 = ((season_rank==1.5).sum()/n).round(2).sort_values(ascending=False)
    #tie2 = ((season_rank==2.5).sum()/n).round(2).sort_values(ascending=False)
    #tie3 = ((season_rank==3.5).sum()/n).round(2).sort_values(ascending=False)

    ## Figure out later
   # profit_win = win/100.*300 + second/100.*150 + third/100.*50 
    #profit_tie = tie1*450/2.0 + tie2*100. + tie3*25.
    #playoff_profit = (profit_win + profit_tie)*playoff/100.

    #print "Top 3:",  cash
    print "Playoff percent:",  playoff
    print "Regular Season EV", reg_cash
    print "Total EV", gross
    print "Net EV", profit
    # print "Bye odds", bye
    # score_dist.hist(bins=12, density=True)
    # plt.show()
    #score_dist.rank(axis=1, ascending=False).hist(bins=12, density=True)
    #plt.show()
    
    ss
   
    return paa

#def sim(t1, t2, week, start=0, end=7, n=100000,fas=None,drops=None, ngames=None):
#    """ This only knows current roster and current matchup totals, so running during 
#    games will be inaccurate. Any FAs/drops - even if already made - need to be input"""
#    g1=get_games(team=t1,start=start, end=end, adds=fas, drops=drops, ngames=ngames)
#    g2=get_games(team=t2,start=start, end=end)
#    s1=get_avg(team=t1, fas=fas)
#    s2=get_avg(team=t2)
#    d1=get_dist(s1, g1, n=n)
#    d2=get_dist(s2, g2, n=n)
#    current=get_matchup(t1, t2, week)

#    err1=d1.std()
#    err1.name=t1
#    err2=d2.std()
#    err2.name=t2
#    errs=pd.concat((err1,err2),axis=1).T
#    errs=errs.drop(['FGM','FTM','FGA', 'FTA'], axis=1).round(3)
    
#    d1=d1.add(current.loc[t1,:])
#    d2=d2.add(current.loc[t2,:])
#    d1['FG_perc']=d1['FGM']/d1['FGA']
#    d1['FT_perc']=d1['FTM']/d1['FTA']
#    d2['FG_perc']=d2['FGM']/d2['FGA']
#    d2['FT_perc']=d2['FTM']/d2['FTA']
#    d1=d1.drop(['FGM','FTM','FGA', 'FTA'], axis=1)
#    d2=d2.drop(['FGM','FTM','FGA', 'FTA'], axis=1)
#    result=(d1>d2).astype(int)
#    result['TO']=1-result['TO']
#    wins=result.sum(axis=1)
#    weights= np.ones_like(wins)/float(len(wins))
#    hold=plt.hist(wins, bins=np.arange(0,11)-.5, weights=weights)
#    freq=hold[0]*100
#    num=hold[1][:-1]+.5
#    outcome=pd.Series(freq, index=num).round(2)
#    perc=(result.sum(axis=0)/n*100.).round(2)
#    ev=np.sum(outcome/100.*np.arange(10))
#    print outcome
#    print perc
#    print errs
    
#    return ev

#def get_dist(avgs,games, n=100000):
#    #get total remaining games for each player, and averages for each stat for each player
    #set means=averages*games (using FGM, FTM, FGA, FTA)
    #avgs is a dataframe  n_players rows and nstats+1 columns (last column is number of games
    # games is the number of games for each player
#    avgs=avgs.join(games)
#    avgs=avgs[avgs.loc[:,'Today'] != 0]
#    avgs=avgs.multiply(avgs['Today'], axis=0)
#    avgs=avgs.drop(['Today'], axis=1)
#    players=np.random.poisson(avgs.values, size=(n,avgs.shape[0],avgs.shape[1]))
#    team=np.sum(players, axis=1)
#    df=pd.DataFrame(team, columns=avgs.columns)
#    df['FG_perc']=df['FGM']/df['FGA']
#    df['FT_perc']=df['FTM']/df['FTA']
#    return df
    # sum over all players to get total in each stat for each simulation: should be 1e5 x nstats
    # return this array

# def predictions()
#"""For each mathchup and each day, not % of winning each cat, and % of winning total amount. Then add result
#at end of week."""
# Index is week, then day, then cat/result


# def corr()
#    """Read in like 10 players stats for every game, scatter plots (corner?) 
#    between every pair of stats to find correlations"""

#def brier():
    #update brier score for this program based on wins and losses



    
#Daily projections actually do pretty well. Compare daily to season projected and season avg
# Season projections either don't change or change every week. 

# Get trade analyzer working

# Read in all players, search for correlations between stats

#def get_players():
    
#def get_games(team='10', start=0, end=7, league='51329',
#              drops=None, adds=None, ngames=None):
#    """ Gets total reamining games for every player on roster. If dropping someone, input there name
#    in drops (format: drops=[[players dropped today], [players dropped tomorrow], etc.]
#    To account for FAs, give list of FAs in adds (fas=[FA1, FA2, etc]) and the number of games the will play 
#    (count this manually: ngames=[1,2,1...])"""
#    days=[str(date.today()+datetime.timedelta(days=x)) for x in range(start,end)]

#    url_temp="https://basketball.fantasysports.yahoo.com/nba/{id}/{team}/team?&date={day}&stat1=O"

#    total=pd.DataFrame()
#    team=team

#    if adds != None:
#        fas=pd.DataFrame(zip(adds,ngames), columns=['p','Today']).set_index('p')
#    if drops != None:
#        drops=dict(zip(days, drops))
#    else:
#        drops=dict(zip(days,[None]*len(days)))

#    for day in days:
#        url=url_temp.format(id=league, team=team, day=day)
#        html=urlopen(url)
#        soup =bs(html,'html.parser')
#        headers=[th.getText() for th in soup.findAll('tr')[2].findAll('th')]
#        headers=headers[:-1]
#        data_rows = soup.findAll('tr')[1:]
#        player_data = [[td.getText() for td in data_rows[i].findAll('td')[:-1]]
#                       for i in range(len(data_rows))]
#        for player in player_data:
#            if len(player)>4:
#                del player[4]
#        player_data=[player for player in player_data if len(player)==len(headers)]
        
        # Clean up data
#        opps=pd.DataFrame(player_data, columns=headers)
#        opps['Players']=[name.split('\n')[2].rpartition('-')[0].strip()[:-3].strip()
#                         for name in opps['Players'].values]
#        inp=day[5:]
#        m,d=inp.split('-')
#        inp=m+'/'+str(int(d))
#        opps['Today']=(opps[inp]!='').astype(int)
#        opps=opps.set_index('Pos')
#        opps.loc['BN':,'Today']=0
#        if drops[day] != None:
#            for dr in drops[day]:
#                opps.loc[opps['Players'] == dr,'Today']=0
#        opps=pd.concat([opps['Players'],opps['Today']], axis=1).set_index('Players')
#        total=total.add(opps, fill_value=0)
#    if adds != None:
#        total=total.append(fas)
#    return total

#def get_avg(team='10', fas=None):
    
#    url_temp="https://basketball.fantasysports.yahoo.com/nba/{id}/{team}?stat1=AS&stat2=AS_2018"

#    item='51329'
#    team=team
        
#    url=url_temp.format(id=item, team=team)
#    html=urlopen(url)

#    soup =bs(html,'html.parser')
#    headers=[th.getText() for th in soup.findAll('tr')[2].findAll('th')]
#    headers=headers[:-1]
#    data_rows = soup.findAll('tr')[1:]
#    player_data = [[td.getText() for td in data_rows[i].findAll('td')[:-1]]
#                   for i in range(len(data_rows))]
#    for player in player_data:
#        if len(player)>4:
#            del player[4]
#    player_data=[player for player in player_data if len(player)==len(headers)]
            
    # Clean up data
#    df=pd.DataFrame(player_data, columns=headers)
#    df=df.drop(axis=1, labels=['Action', 'Forecast', 'Opp', 'Status'])
#    stats=df.drop(axis=1, labels=['Pre-Season', 'Current', '% Started'])
#    stats.columns=stats.columns.str.replace('%','_perc')
#    stats['Players']=[name.partition('Player Note\n')[2].partition('-')[0][:-4].strip()
#                      for name in stats['Players'].values]
#    fgm=[]
#    ftm=[]
#    fga=[]
#    fta=[]
#    for i, row in stats.iterrows():
#        gm,hold,ga=row['FGM/A*'].partition('/')
#        tm,hold,ta=row['FTM/A*'].partition('/')
#        fgm.append(gm)
#        ftm.append(tm)
#        fga.append(ga)
#        fta.append(ta)
#    stats['FGM']=fgm
#    stats['FGA']=fga
#    stats['FTM']=ftm
#    stats['FTA']=fta
#    stats.replace('-', value=0.0, inplace=True)
#    stats=stats.drop(axis=1, labels=['FGM/A*','FTM/A*','FG_perc','FT_perc','MPG','GP*', 'Pos'])
#    stats=stats.set_index('Players')
#    stats=stats[:].apply(pd.to_numeric, errors='ignore')

#    if fas != None:
#        for fa in fas:
#            df=get_fas('owned','avg',fa, league=league)
#            df.name=fa
#            df=df.drop(['FG_perc','FT_perc'])
#            stats=stats.append(df)
#    
#    return stats

def record_predictions(week, team1s, team2s,
                       league='51329', mock=False, bench=True,
                       type='proj'):
    """ Record predictions for all matchups at start of
    each week
    """
    # Remember to update matchups, or do auto at some point
    if mock == False:
        teams = np.arange(1,13).astype(str)
    else:
        teams = np.arange(1,5).astype(str)
    hold = pd.DataFrame(columns=teams)
    for i in range(len(team1s)):
        outcome, perc = matchup(team1s[i], team2s[i], week,
                                league=league, include_bench=bench, type=type)
        data = np.append(outcome.values, np.append(perc['Win'].values,
                                                   perc['Tie'].values))
        data2 = np.append(outcome.values[::-1],
                          np.append(100-perc['Win'].values-perc['Tie'].values,
                                    perc['Tie'].values))
        hold[teams1[i]] = data
        hold[teams2[i]] = data2

    hold['Week'] = week
    hold['Labels'] = outcome.index.astype(str).append(perc.index+'_win').append(perc.index + '_tie')
    hold=hold.set_index(['Week', 'Labels'])
    
    #saving = int(raw_input('Did you set up correct matchups ' \
    #                       'and days for the week? '))
    saving = 1
    if saving == 1:
        try:
            if mock == False:
                if type == 'proj':
                    preds = pd.read_csv('fantasy_predictions.csv', index_col=[0, 1])
                    preds = preds.append(hold)
                    preds.to_csv('fantasy_predictions.csv')
                elif type == 'avg':
                    preds = pd.read_csv('fantasy_predictions_avg.csv', index_col=[0, 1])
                    preds = preds.append(hold)
                    preds.to_csv('fantasy_predictions_avg.csv')
                else:
                    preds = pd.read_csv('fantasy_predictions_avg_30.csv', index_col=[0, 1])
                    preds = preds.append(hold)
                    preds.to_csv('fantasy_predictions_avg_30.csv')
            else:
                if type == 'proj':
                    preds = pd.read_csv('mock_fantasy_predictions.csv', index_col=[0, 1])
                    preds = preds.append(hold)
                    preds.to_csv('mock_fantasy_predictions.csv')
                elif type == 'avg':
                    preds = pd.read_csv('mock_fantasy_predictions_avg.csv', index_col=[0, 1])
                    preds = preds.append(hold)
                    preds.to_csv('mock_fantasy_predictions_avg.csv')
                else:
                    preds = pd.read_csv('mock_fantasy_predictions_avg_30.csv', index_col=[0, 1])
                    preds = preds.append(hold)
                    preds.to_csv('mock_fantasy_predictions_avg_30.csv')
        except IOError:
            if mock == False:
                if type == 'proj':
                    hold.to_csv('fantasy_predictions.csv')
                elif type == 'avg':
                    hold.to_csv('fantasy_predictions_avg.csv')
                else:
                    hold.to_csv('fantasy_predictions_avg_30.csv')
            else:
                if type == 'proj':
                    hold.to_csv('mock_fantasy_predictions.csv')
                elif type == 'avg':
                    hold.to_csv('mock_fantasy_predictions_avg.csv')
                else:
                    hold.to_csv('mock_fantasy_predictions_avg_30.csv')
    return 1

def record_results(week, team1s, team2s, league='51329', mock=False):
    if mock == False:
        teams = np.arange(1,13).astype(str)
    else:
        teams = np.arange(1,5).astype(str)
    hold = pd.DataFrame(columns=teams)
    for i in range(len(team1s)):
        match = get_matchup(team1s[i], team2s[i], week, league=league)
        match = match.iloc[:,:-4]
        for j in range(2):
            for k in range(2):
                if isinstance(match.iloc[j, k], unicode):
                    if match.iloc[j,k].endswith('*'):
                        match.iloc[j,k]=float(match.iloc[j,k][:-1])+.001
        ties = match.loc[team1s[i],:] == match.loc[team2s[i],:]
        results = (match.loc[team1s[i],:] > match.loc[team2s[i],:]).astype(float)
        results[-1] = float((not results[-1]))
        results[ties == True] = 0.5
        hold[team1s[i]] = results
        hold[team2s[i]] = 1.0 - results
    hold['Week']=week
    hold['Labels']=hold.index
    hold=hold.set_index(['Week', 'Labels'])

    try:
        if mock == False:
            preds = pd.read_csv('fantasy_results.csv', index_col=[0,1])
            preds = preds.append(hold)
            preds.to_csv('fantasy_results.csv')
        else:
            preds = pd.read_csv('mock_fantasy_results.csv', index_col=[0,1])
            preds = preds.append(hold)
            preds.to_csv('mock_fantasy_results.csv')
    except IOError:
        if mock == False:
            hold.to_csv('fantasy_results.csv')
        else:
            hold.to_csv('mock_fantasy_results.csv')
    return hold



if __name__ == '__main__':
    week = sys.argv[1]
    pre_week = str(int(week) - 1)
    teams1 = np.array([2, 1, 9, 3, 4, 10]).astype(str)
    teams2 = np.array([7, 8, 11, 6, 5, 12]).astype(str)
    league = '51329'
    mock=False
    #record_results(pre_week, teams1, teams2, league=league, mock=mock)
    print "Results recorded for league %s" % league

    #league = '137124'
    #teams1 = np.array([1, 3]).astype(str)
    #teams2 = np.array([2, 4]).astype(str)
    #mock=True
    #record_results(pre_week, teams1, teams2, league=league, mock=mock)
    #print "Results recorded for league %s" % league
    #league = '51329'
    #mock=False

    teams1 = np.array([2, 1, 10, 3, 4, 5]).astype(str)
    teams2 = np.array([8, 9, 11, 7, 6, 12]).astype(str)
    record_predictions(week, teams1, teams2, league=league, mock=mock)
    print "Predictions recorded for league %s" % league
    print
    print
    record_predictions(week, teams1, teams2, league=league, mock=mock, type='avg')
    print "Average predictions recorded for league %s" % league
    print
    print
    record_predictions(week, teams1, teams2,
                       league=league, mock=mock, type='avg_30')
    print "30-day average predictions recorded for league %s" % league
    print
    print
    sys.exit()
    league = '137124'
    teams1 = np.array([1, 3]).astype(str)
    teams2 = np.array([2, 4]).astype(str)
    mock=True
    record_predictions(week, teams1, teams2, league=league, mock=mock, bench=False)
    print "Predictions recorded for league %s" % league
    print
    print
    record_predictions(week, teams1, teams2, league=league, mock=mock, type='avg')
    print "Average predictions recorded for league %s" % league
    print
    print
    record_predictions(week, teams1, teams2,
                       league=league, mock=mock, type='avg_30')
    print "30-day average predictions recorded for league %s" % league
    print
    print


    
