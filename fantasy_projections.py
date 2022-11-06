from urllib.request import urlopen
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
import configparser

from extra import get_hashtag
    
    

def get_standings(league='81947', nTeams=14):
    url = "https://basketball.fantasysports.yahoo.com/nba/46134"
    html = urlopen(url)
    soup = bs(html,'html.parser')
    headers = [th.getText() for th in soup.findAll('thead')[0].findAll('th')]
    data_rows = soup.findAll('tr')[1:nTeams+1]
    all_teams = []
    all_wins = []
    for i, item in enumerate(data_rows):
        team = item.a.get('href').split('/')[-1]
        all_teams.append(team)
        record = item.findAll('td')[2].getText()
        wins = int(record.split('-')[0]) + 0.5*int(record.split('-')[2])
        all_wins.append(wins)
    # Sort teams to be in the normal 1-14 format. 
    df = pd.Series(all_wins, index=all_teams)
    return df
    
def get_matchup(team1, team2, week, league='81947'):
    """Function to retrieve the current matchup totals
    between any two teams.
    """
    # 107260 for 2018
    # 51329 for 2019

    # Set up beautiful soup to read in the matchup table
    temp = "https://basketball.fantasysports.yahoo.com/" \
           "nba/{l}/matchup?date=totals&week={w}&mid1={t1}&mid2={t2}"
    url = temp.format(w=str(week), t1=team1, t2=team2, l=league)
    html = urlopen(url)
    soup = bs(html,'html.parser')
    # Get each header in the correct table
    headers = [th.getText() for th in soup.findAll('tr')[1].findAll('th')][:-1]
    # Isolate the important data
    data_rows = soup.findAll('tr')[2:4]
    past = [[td.getText() for td in data_rows[i].findAll('td')[:-1]]
            for i in range(len(data_rows))]
    # Put matchup data in dataframe, clean data.
    matchup = pd.DataFrame(past,columns=headers)
    fgm = []
    ftm = []
    fga = []
    fta = []
    for i, row in matchup.iterrows():
        gm, hold, ga = row['FGM/A*'].partition('/')
        tm, hold, ta = row['FTM/A*'].partition('/')
        fgm.append(gm)
        ftm.append(tm)
        fga.append(ga)
        fta.append(ta)
    matchup['FGM'] = fgm
    matchup['FGA'] = fga
    matchup['FTM'] = ftm
    matchup['FTA'] = fta
    matchup = matchup.drop(axis=1, labels=['FGM/A*','FTM/A*'])
    matchup.columns = matchup.columns.str.replace('%','_perc')
    matchup = matchup[:].apply(pd.to_numeric, errors='ignore')
    matchup['Team'] = ['1',team2]
    matchup1 = matchup.copy()

    # Do the same for team 2.
    temp = "https://basketball.fantasysports.yahoo.com/" \
           "nba/{l}/matchup?date=totals&week={w}&mid1={t1}&mid2={t2}"
    url = temp.format(w=str(week), t1=team2, t2=team1, l=league)
    html = urlopen(url)
    soup = bs(html, 'html.parser')
    headers = [th.getText() for th in soup.findAll('tr')[1].findAll('th')][:-1]
    data_rows = soup.findAll('tr')[2:4]
    past = [[td.getText() for td in data_rows[i].findAll('td')[:-1]]
            for i in range(len(data_rows))]
    matchup = pd.DataFrame(past, columns=headers)
    fgm = []
    ftm = []
    fga = []
    fta = []
    for i, row in matchup.iterrows():
        gm, hold, ga = row['FGM/A*'].partition('/')
        tm, hold, ta = row['FTM/A*'].partition('/')
        fgm.append(gm)
        ftm.append(tm)
        fga.append(ga)
        fta.append(ta)
    matchup['FGM'] = fgm
    matchup['FGA'] = fga
    matchup['FTM'] = ftm
    matchup['FTA'] = fta
    matchup = matchup.drop(axis=1, labels=['FGM/A*','FTM/A*'])
    matchup.columns = matchup.columns.str.replace('%','_perc')
    matchup = matchup[:].apply(pd.to_numeric, errors='ignore')
    matchup['Team'] = ['1',team1]
    matchup2 = matchup.copy()

    # Combine data into a single dataframe, which provides
    # the total for each stat for each team
    # (10 categories x 2 teams).
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

def get_fas(sort
            , proj
            , player
            , league='46134'
            , date=None
            , watchlist=False
            , trade=False):
    """Search list of top 125 FAs by a user-provided sort-criteria,
    and determine per game stats (i.e, the rest-of-season 
    projections / projected games played) for provided player. This
    does not take matchup/recent performance into account.

    Only return value is player has an oppnent on provided date. 

    Watchlist is a shortcut which searches the users watchlist
    instead of all FA. Has added bonus of providing daily
    projections for player's specific matchup.

    Trade: In case of a 2-for-1 or 3-for-2 trade, a FA
    must be included in order to accurately reflect results. 
    For example, a 2-for-1 will be better if the best FA is Hunter 
    instead of Brad Wanamaker.
    """

    # Add ability to search watchlist instead
    # Need to log in! Installed geckodriver for selenium, but need to
    # log in still. This will also be necessary for private leagues. 
    
    if watchlist==True:
        urltemp = "https://basketball.fantasysports.yahoo.com/nba/" \
        "{l}/13/playerswatch?&date={d}&stat1=P&stat2=P&jsenabled=1"
        url = urltemp.format(l=league, d=date)
        html = urlopen(url)
        soup = bs(html, 'html.parser')
        headers = [th.getText() for th in soup.findAll('tr')[1].findAll('th')]
        headers = headers[:-1]
        data_rows = soup.findAll('tr')[1:]
        player_data = [[td.getText() for td in data_rows[i].findAll('td')[:-1]]
                       for i in range(len(data_rows))]
        player_data = [p for p in player_data if len(p)==len(headers)]
        pdd = np.asarray(player_data)
        pdd[:, 1] = [name.split('\n')[3].rpartition('-')[0].strip()[:-3].strip()
                     for name in pdd[:,1]]
        one = pd.DataFrame(pdd, columns=headers)
        df = df.append(one, ignore_index=True)
        breakpoint()
    else:
        urltemp = "https://basketball.fantasysports.yahoo.com" \
                  "/nba/{l}/players?&sort={sort}" \
                  "&status=A&pos=P&stat1={proj}&jsenabled=1&count={count}"

    # Set dictionary which converts sort criteria from
    # english to URL extension. This includes percent owned,
    # current total rank, preseason rank, and 7 counting stats.
    # This dictionary also provides conversion for each stat prediction
    # of interest, including season averages, 30 day averages,
    # projected rest of season stats, and projected rank over
    # the next 7 games Game-check indicated by 'opp' for 'opponent'.
    
    key = {'current':'AR&sdir=1', 'pre':'OR&sdir=1'
           , 'owned':'R_PO&sdir=1','3pm':'10&sdir=1'
           , 'pts':'11&sdir=1', 'reb': '12&sdir=1'
           , 'ast':'13&sdir=1', 'st':'14&sdir=1'
           , 'blk':'15&sdir=1', 'TO':'16&sdir=0'
           , 'proj':'S_PSR', 'next7':'S_PS7', 'avg':'S_AS_2021'
           , 'opp':'O_O', 'avg30' : 'S_AL30'}

    # Yahoo provides 25 players per page. For each page, determine stats
    # for each player, continuing until the player of interest is found.
    
    df = pd.DataFrame()
    c = 0

    while True:
        url = urltemp.format(sort=key[sort], proj=key[proj], count=c, l=league)
        html = urlopen(url)
        soup = bs(html, 'html.parser')
        headers = [th.getText() for th in soup.findAll('tr')[1].findAll('th')]
        headers = headers[:-1]
        data_rows = soup.findAll('tr')[1:]
        player_data = [[td.getText() for td in data_rows[i].findAll('td')[:-1]]
                       for i in range(len(data_rows))]
        player_data = [p for p in player_data if len(p)==len(headers)]
        pdd = np.asarray(player_data)
        pdd[:, 1] = [name.split('\n')[3].rpartition('-')[0].strip()[:-3].strip()
                     for name in pdd[:,1]]
        one = pd.DataFrame(pdd, columns=headers)
        df = df.append(one, ignore_index=True)
        if player in df['Players'].values:
            break
        c+=25
        if c>200:
            raise ValueError('Is FA still a FA and spelled correctly?')

    df.columns = df.columns.str.replace('%', '_perc')
    df.columns = df.columns.str.replace('*', '')
    # Note: sometimes a hyphenated name can be difficult to handle. This code
    # addresses that. 
    # df['Players']=[name.split('\n')[3].rpartition('-')[0].strip()[:-3].strip()
    #                for name in df['Players'].values]

    if player not in df['Players'].values:
        sys.exit('Player not in FA list. Check spelling and use \'I. LastName\' format')
    
    # Determine if player has a game on date of interest.
    if proj=='opp':
        inp = date[5:]
        m, d = inp.split('-')
        day = str(int(m)) + '/' + str(int(d))
        df['Today'] = df[day]!=''
        df = pd.concat([df['Players'], df['Today']], axis=1)
        return  df[df['Players']==player].iloc[0, 1:]
    else:
        fgm = []
        ftm = []
        fga = []
        fta = []
        for i, row in df.iterrows():
            gm, hold, ga = row['FGM/A'].partition('/')
            tm, hold, ta = row['FTM/A'].partition('/')
            fgm.append(gm)
            ftm.append(tm)
            fga.append(ga)
            fta.append(ta)
        df['FGM'] = fgm
        df['FGA'] = fga
        df['FTM'] = ftm
        df['FTA'] = fta
        df.replace('-', value=0.0, inplace=True)

        # Drop columns to match format of team stats. Any
        # columns that are not in the list of titles below
        # should be dropped. 

        titles = ['Players', '3PTM', 'PTS', 'REB'
                  , 'AST', 'ST', 'BLK', 'TO', 'FGM'
                  , 'FGA', 'FTM', 'FTA', 'GP']
        ix = []
        
        # Sort the columns for consistency. Get index
        # of columns to be dropped.
        
        cols = df.columns.sort_values(ascending=False)
        for i, item in enumerate(cols):
            if item not in titles:
                ix.append(i)
        df = df.drop(axis=1, labels=[cols[i] for i in ix])
        
        # Convert players stats to float type.
        df = df[:].apply(pd.to_numeric, errors='ignore')
        # For rest-of-season projections, divide projections by expected
        # games played to get estimate of projected stats for single game.
        # This does not take daily circumstance into account, and will
        # underestimate bench players who will play more due to a starter's
        # injury.
        if proj=='proj':
            df.loc[:, '3PTM':] = df.loc[:, '3PTM':].div(df['GP'], axis=0).round(1)
            df = df.dropna()
        # If considering the impact of a FA on a trade, keep the GP column.
        if trade == False:
            df = df.drop(labels=['GP'], axis=1)

        return df[df['Players']==player].iloc[0, 1:]


def get_team(team
             , base
             , league='46134'
             , date=None
             , drops=None
             , played=None
             , include_bench=False
             , injured=True
             , hash=None
             , return_players=False
             , trade=[]):

    """ Function to read in the total predicted stats
    for a team for a given day. 
    team = number of team (string)
    base = type of stat to use: projected (proj),  average (avg)
    , or average over last 30 days (avg_30).
    date = date of projected stats (MM/DD/YYYY)
    drops = list of players who will be dropped on given date.
    played: list of players to ignore since they have already 
    played that day (for midday simulations).
    include_bench: whether to include players on the bench
    injured: whether to account for injuries when using average stats
    trade: list of players who would be traded away
    """

    # Set up the basic URL
    url_temp = "https://basketball.fantasysports.yahoo.com" \
               "/nba/{id}/{team}{base}"

    # Define dictionary which converts english to URL
    # addendum. For example, 'proj' (projected) corresponds
    # to the sequence 'stat1=P&stat2=P' being added to the
    # basic URL. 
    key1 = {'r':'stat1=P&stat2=PSR'
            ,'proj': 'stat1=P&stat2=P'
            , 'o':'stat1=O'
            , 'avg':'stat1=AS&stat2=AS_2021'
            , 'avg_30': 'stat1=AS&stat2=AL30'}

    # Account for the date, if necessary.
    day = '/team?&date={day}&'
    if date!=None:
        day = day.format(day=date)
        link = day + key1[base]
    else:
        link = '?'+ key1[base]

    # Define the URL which contains the data we want
    # based on the user inputs.
    url = url_temp.format(id=league, team=team, base=link)
    # Retrieve the data using BeautifuSoup to scrape the HTML.
    html = urlopen(url)
    soup = bs(html, 'html.parser')
    headers = [th.getText() for th in soup.findAll('tr')[1].findAll('th')]
    headers = headers[:-1]
    data_rows = soup.findAll('tr')[1:]
    player_data = [[td.getText() for td in data_rows[i].findAll('td')[:-1]]
                   for i in range(len(data_rows))]
    for player in player_data:
        if len(player)>4:
            del player[4]
    player_data = [player for player in player_data if len(player)==len(headers)]

    # Clean up data
    df = pd.DataFrame(player_data, columns=headers)
    try:
        df = df.drop(axis=1, labels=['Action', 'Forecast', 'Opp', 'Status'])
    except KeyError:
        df = df.drop(axis=1, labels=['Action', 'Opp', 'Status'])
    stats = df.drop(axis=1, labels=['Pre-Season', 'Current', '% Started'])
    stats.columns = stats.columns.str.replace('%','_perc')
    names = []
    inj = []

    for name in stats['Players'].values:
        names.append(name.split('\n')[2].rpartition('-')[0][:-4].strip())
        inj.append(name.split('\n')[5]=='INJ')
    stats['Players'] = names
    stats['Inj'] = inj

    # stats['Players']=[name.split('\n')[2].split('-')[0][:-4].strip()
    #              for name in stats['Players'].values]

    fgm = []
    ftm = []
    fga = []
    fta = []
    for i, row in stats.iterrows():
        gm, hold, ga = row['FGM/A*'].partition('/')
        tm, hold, ta = row['FTM/A*'].partition('/')
        fgm.append(gm)
        ftm.append(tm)
        fga.append(ga)
        fta.append(ta)
    stats['FGM'] = fgm
    stats['FGA'] = fga
    stats['FTM'] = ftm
    stats['FTA'] = fta
    stats.replace('-', value=0.0, inplace=True)
    stats = stats.drop(axis=1, labels=['FGM/A*','FTM/A*'])
    stats = stats.set_index('Pos')
    stats = stats[:].apply(pd.to_numeric, errors='ignore')

    # For avg stats projections, need to check if a game is played that day
    if base in ['avg', 'avg_30']:
        # First drop extra axes
        stats = stats.drop(axis=1, labels=['MPG', 'GP*'])
        # breakpoint()
        if date!=None:
            url = url_temp.format(id=league, team=team, base=day+key1['o'])
            html = urlopen(url)
            soup = bs(html,'html.parser')
            headers = [th.getText() for th in soup.findAll('tr')[1].findAll('th')]
            headers = headers[:-1]
            data_rows = soup.findAll('tr')[1:]
            player_data = [[td.getText() for td in data_rows[i].findAll('td')[:-1]]
                           for i in range(len(data_rows))]

            for player in player_data:
                if len(player)>4:
                    del player[4]
            player_data = [player for player in player_data if len(player)==len(headers)]

            # Clean up data
            opps = pd.DataFrame(player_data, columns=headers)
            opps['Players'] = [name.split('\n')[2].rpartition('-')[0].strip()[:-3].strip()
                               for name in opps['Players'].values]
            inp = date[5:]
            m, d = inp.split('-')
            day = str(int(m)) + '/' + str(int(d))
            opps['Today'] = opps[day]!=''
            opps = pd.concat([opps['Players'], opps['Today']], axis=1).set_index('Players')
            stats = stats.join(opps, on='Players')
            stats = stats[stats['Today']==True]
            stats = stats.drop(axis=1, labels=['Today'])

    # Why team 2 and 9 special? Maybe season long relic to include
    # injured players that would be back soon, like Zion this year?
    if date!=None:
        if include_bench==False:
            # stats = stats.loc[:'Util', :]
            stats = stats[(stats.index!='IL+') & (stats.index!='BN')]
        # else:
        # Always ignore IL players
        # stats = stats.loc[:'BN', :]
        # stats = stats[stats.index!='IL+']
        # previously this had " if team!='2' and team!='9':"

    # if team!='2':
    # stats = stats.loc[:'BN', :]
    stats = stats[stats.index!='IL+']

    try:
        if drops!=None:
            stats = stats[stats['Players']!=drops]
    except ValueError:
        for drop in drops:
            stats = stats[stats['Players']!=drop]

    # played = ['Jalen Smith', 'Josh Hart', 'Dillon Brooks', 'Jaren Jackson Jr.']
    # for player in played:
    #     stats=stats[stats['Players'] != player]
    #breakpoint()
    # played=['Reggie Jackson', 'RJ Barrett']
    if played!=None:
        for player in played:
            stats=stats[stats['Players'] != player]
    if len(trade)!=0:
        person = pd.DataFrame()
        for tp in trade:
            person = pd.concat([person, stats[stats.loc[:,'Players']==tp]])
            stats = stats[stats.loc[:,'Players']!=tp]

    # breakpoint()
    if base in ['avg', 'avg_30']:
        # Ignore injured players?
        if injured==True:
            stats = stats[stats['Inj']==False]
            stats = stats.drop('Inj', axis=1)
        # Else, don't ignore them.
        else:
            stats = stats.drop('Inj', axis=1)
    else:
        stats = stats.drop('Inj', axis=1)

    # Before summing team, allow stats to be replaced with hashtag stats!
    # Note that it's unnecessary to get Yahoo's stats (and not just player names)
    # but it's simpler than reworking program at this stage.
    if hash!=None:
        player_projections = convert_to_hashtag(stats)
        # Join yahoo stats on hashtag stats
        # If doing by player name is difficult, try indexing by initials+3 letter team
        # name.
        

    team = stats.iloc[:, 1:].sum().astype(float)
    try:
        team['FG_perc'] = team['FGM'] / team['FGA']
        team['FT_perc'] = team['FTM'] / team['FTA']
    except RuntimeWarning:
        sys.exit('Runtime error')

    if len(trade)!=0:
        if return_players==True:
            return [team, person, stats]
        else:
            return [team, person]
    else:
        if return_players==True:
            return [team, stats]
        else:
            return team
    # Now we have, in a good format, all the projected stats for each team.


def matchup(team1
            , team2
            , week
            , start=0
            , end=7
            , base='proj'
            , league='81947'
            , fas=None
            , drops=None
            , played=None
            , include_bench=True
            , inj=True
            , sim=False):
    """ Simulate the results of a matchup between any
    two teams, for any amount of days (up to 14). Note:
    team numbers can be found in URL of a teams page 
    (https://basketball.fantasysports.yahoo.com/nba/league_id/team_id)
    Team1: Number of first team in the matchup (string)
    Team2: Number of opponent
    start: Day to start matchup (0=today, 1=tomorrow, etc)
    end: last day of matchup (7 for full week).
    base: Base system to use for stats (projected, average, etc)
    league: league ID (from URL)
    fas: list of free agent/free agents to be picked up by team1 each day,
    must be the same length as end-start. Use F. Lastname format. Can do 
    multiple players (in list form), e.g, ['L. James', ['L. James', 'S. Curry'], 'L. James']
    drops: list of players to be dropped each day. Follows same rules as fas, except
    uses First LastName. 
    include_bench: include players on the bench in projections? Necessary if 
    opponent has not set their lineup. 
    sim: Uses program for season-long simulation? """

    days = [str(date.today() + datetime.timedelta(days=x))
            for x in range(start, end)]
    if drops==None:
        drops = [None] * len(days)
    if fas==None:
        fas = [None] * len(days)
    if played==None:
        played = [None] * len(days)

    drops = dict(list(zip(days, drops)))
    fas = dict(list(zip(days, fas)))
    played = dict(list(zip(days, played)))

    t1 = pd.Series(dtype='float64')
    t2 = pd.Series(dtype='float64')
    for i, dates in enumerate(days):
        print(dates)
        t1=t1.add(get_team(team1, base, league=league, date=dates
                           , drops=drops[dates], include_bench=include_bench
                           , injured=inj), fill_value=0)
        if fas[dates]!=None:
            game_check=int(get_fas('owned','opp', fas[dates], date=dates,
                                   league=league)['Today'])
            
            free=get_fas('owned', base, fas[dates], league=league)*game_check
            free = free*2
            t1=t1.add(free, fill_value=0)
            #breakpoint()
        #else:
        #    t1=t1.add(get_team(team1, type, date=dates,
        #                       league=league,
        #                       include_bench=include_bench), fill_value=0)
        t2=t2.add(get_team(team2, base, date=dates
                           , league=league,include_bench=include_bench
                           , injured=inj), fill_value=0)

    #dd=[1,1,.7,7.8,6.8,2.1,.5,.9,1.9,2.7,5.6,1.7,2.0] # collins
    dd=np.array([1,1,2,9.7,3.4,1.3,.4,.2,.8,3.5,8.0,.7,.8]) #lyles
    # # dd=np.array([1,1,.2,8.2,10.1,1.4,1.3,.7,1.,3.4,6.0,1.3,1.9]) #vandy
    # kein = [1,1,.8,9.5,4.,2.9,1.,.5,1.2,3.6,8.2,1.6,2.1] # tht
    # #kein = [1,1,.7,9.2,2.6,3.7,.8,.1,1.4,3.5,7.6,1.5,2.] # neto
    # # kein = [1,1,1.6,12.5,3.6,2.3,1.1,.1,1.6,4.6,11.2,1.6,2.0] # tre
    # #kein = [1,1,1.5,11.7,4.3,1.2,.7,.2,1.,4.4,8.7,1.5,2.] # rui
    # #kein = [1,1,1.,10.8,4.9,2.1,.9,.4,1.3,3.8,8.0,2.2,2.8] # donte
    kein = [1,1,1.9,13,6.2,1.8,.6,.3,.8,4.3,10.1,2.5,2.8] # bones
    # #x,x,3, pts, reb, ast, st, blk, to, fgm, fga, ftm, fta

    # #kein=dj
    # #kein=dd
    kk2=pd.Series(dd)*0
    kk=pd.Series(kein)*0
    kk.index=t1.index
    kk2.index=t1.index
    t1=t1.add(kk).add(kk2)
    #breakpoint()
    
    t1['FG_perc'] = t1['FGM'] / t1['FGA']
    t1['FT_perc'] = t1['FTM'] / t1['FTA']
    t2['FG_perc'] = t2['FGM'] / t2['FGA']
    t2['FT_perc'] = t2['FTM'] / t2['FTA']
    if t1['FGA']==0:
        t1[:] = 0
    if t2['FGA']==0:
        t2[:] = 0
    t1['Team'] = team1
    t2['Team'] = team2
    matchup = pd.concat([t1, t2], axis=1).T.set_index('Team')
    current = get_matchup(team1, team2, week, league=league)
    current = current.replace('-', 0)
    current = current.replace('\*', '', regex=True).astype(float)
    
    total = matchup.add(current, fill_value=0)
    breakpoint()
    total['FG_perc'] = total['FGM'] / total['FGA']
    total['FT_perc'] = total['FTM'] / total['FTA']
    total = total.drop(axis=1, labels=['FGM','FGA','FTM','FTA'])
    temp = total.T
    temp['Margin'] = (temp[team1]-temp[team2]).astype(float)
    temp.iloc[:2, 2] =temp.iloc[:2, 2].round(4)
    temp.iloc[:2, 2] =temp.iloc[:2, 2].round(4)
    temp.iloc[2:, 2] =temp.iloc[2:, 2].round(1)
    temp.iloc[2:, 2] =temp.iloc[2:, 2].round(1)
    total = temp.T
    to = np.ones(total.shape[1]).astype(bool)

    to[-1] = False
    total['Score'] = 'NaN'
    total.loc[team1, 'Score'] = ((total.loc[team1, :'TO']>total.loc[team2, :'TO'])==to).sum()
    total.loc[team2, 'Score'] = ((total.loc[team2, :'TO']>total.loc[team1, :'TO'])==to).sum()

    #fas=get_fas('st','remaining')

    matchup['2PM'] = matchup['FGM'] - matchup['3PTM']
    matchup['FTO'] = matchup['FTA'] - matchup['FTM']
    matchup['FGO'] = matchup['FGA'] - matchup['FGM']

    t1 = matchup.loc[team1, :].astype(float)
    t2 = matchup.loc[team2, :].astype(float)
    n = 100000
    #breakpoint()
    d1 = np.random.poisson(t1.values, size=(n, t1.shape[0]))
    d2 = np.random.poisson(t2.values, size=(n, t2.shape[0]))
    df1 = pd.DataFrame(d1, columns=t1.index)
    df2 = pd.DataFrame(d2, columns=t2.index)
    df1['FGM'] = df1['2PM'] + df1['3PTM']
    df1['FGA'] = df1['FGO'] + df1['FGM']
    df1['FTA'] = df1['FTO'] + df1['FTM']
    df1['PTS'] = 3*df1['3PTM'] + 2*df1['2PM'] + df1['FTM']
    df1 = df1.drop(axis=1, labels=['2PM', 'FTO','FGO'])
    df2['FGM'] = df2['2PM'] + df2['3PTM']
    df2['FGA'] = df2['FGO'] + df2['FGM']
    df2['FTA'] = df2['FTO'] + df2['FTM']
    df2['PTS'] = 3*df2['3PTM'] + 2*df2['2PM'] + df2['FTM']
    df2 = df2.drop(axis=1, labels=['2PM', 'FTO','FGO'])

    df1 = df1.add(current.loc[team1, :])
    df2 = df2.add(current.loc[team2, :])
    df1['FG_perc'] = df1['FGM'] / df1['FGA']
    df1['FT_perc'] = df1['FTM'] / df1['FTA']
    df2['FG_perc'] = df2['FGM'] / df2['FGA']
    df2['FT_perc'] = df2['FTM'] / df2['FTA']
    df1 = df1.drop(['FGM','FTM','FGA', 'FTA'], axis=1)
    df2 = df2.drop(['FGM','FTM','FGA', 'FTA'], axis=1)
    err1 = df1.std(axis=0)
    err2 = df2.std(axis=0)
    err = np.sqrt(err1**2 + err2**2).round(2)
    err.name = 'Margin Error'
    # err[:2]=err[:2].round(4)
    # err[2:]=err[2:].round(2)
    total = total.append(err)
    total.loc[:, 'FG_perc':'FT_perc'] = (total.loc[:, 'FG_perc':'FT_perc']*100).astype(float).round(2)

    win = (df1>df2).astype(int)
    win['TO'] = (df1['TO']<df2['TO']).astype(int)
    tie = (df1==df2).astype(int)
    result = win + 0.5*tie
    wins = result.sum(axis=1)

    weights = np.ones_like(wins) / float(len(wins))
    hold = plt.hist(wins, bins=np.arange(0,20)/2.-.25, weights=weights)
    freq = hold[0] * 100
    num = hold[1][:-1] + 0.25
    outcome = pd.Series(freq, index=num).round(2)
    perc_win = (win.sum(axis=0)/n*100.).round(2)
    perc_win.name = 'Win'
    perc_tie = (tie.sum(axis=0)/n*100.).round(2)
    perc_tie.name = 'Tie'
    perc = pd.concat([perc_win, perc_tie], axis=1)
    ev = np.round(np.sum(outcome/100.*np.arange(19)/2.), 3)

    print('Odds of finishing with each point amount:')
    print(outcome)
    print()
    print('Odds of winning each category:')
    print(perc)
    print()
    print('Projected Results (averages):')
    print(total)
    print()
    print(('Expected Points: %.2f ' % ev))
    print('Win: %.2f%%' %  outcome[outcome.index>=5].sum())
    print('Lose: %.2f%%' %  outcome[outcome.index<4.5].sum())
    print('Tie: %.2f%%' %  outcome[4.5])
    print()
    if sim == True:
        return wins
    else:
        return [outcome, perc]


def get_all(week=18
            , base='r'
            , league='81947'
            , nTeams=14
            , hash=None
            , inj=False):
    # TRADES: Can only do 1 for 1 trades, but can do multiple teams.
    # Set the players coming from each team, and note the team they will
    # go to.

    ## Later: can add actual schedule to go with averages, can go through every actual matchup
    ## , can account for injured guys, use hashtag instead of yahoo
    teams = np.arange(1, nTeams+1)
    weeks_left = 26 - week
    avg = pd.DataFrame()
    proj = pd.DataFrame()
    avg_30 = pd.DataFrame()
    hashtag = pd.DataFrame()

    # issue where 2 for 1 trades with fa are weirdly high
    avg_trades = pd.DataFrame()
    proj_trades = pd.DataFrame()
    avg_30_trades = pd.DataFrame()
    hashtag_trades = pd.DataFrame()

    # Allow for up to 5 players to be traded from any team.
    trades = np.zeros((nTeams, 5)).astype(int).astype(str)
    # trades[12, 0] = 'Marcus Smart'
    # trades[12, 1] = 'Marcus Morris Sr.'
    # trades[10, 0] = 'Tobias Harris'
    #trades[6, 0] = 'Ricky Rubio'

    # Specify which team each a trade is to.
    trade_teams = np.zeros(nTeams).astype(str)
    # trade_teams[12] = '11'
    # trade_teams[10] = '13'

    avg_fas = pd.DataFrame()
    proj_fas = pd.DataFrame()
    avg_30_fas = pd.DataFrame()
    proj_fas = pd.DataFrame()
    hashtag_fas = pd.DataFrame()
    # FA which will be added after a 2-for-1 trade. Add a multiplier to
    # account for extra games due to streaming?
    fas_teams = np.zeros(nTeams).astype(int).astype(str)
    # Player that will be dropped in a 1-for-2 trade.
    drops = np.zeros((nTeams, 5)).astype(int).astype(str)

    # fas_teams[12] = 'C. Johnson'
    # drops[10, 0] = 'Grant Williams'
    #drops[1, 1] = ''

    # Go through each team, getting the projected stats based on
    # each of the following: season long projections, season averages,
    # and averages over the last 30 days.

    #get_hashtag once, here. Save to csv file, or dataframe

    for num, i in enumerate(teams):
        print(i)
        if drops[num, 0]=='0':
            drop = None
        else:
            drop = drops[num]

        trade_list = trades[num, trades[num,:] != '0']
        if len(trade_list) != 0:
            # Instead of an extra scrape, use the roster
            # scraped via projections to provide
            # the list of player names for hashtag stats.
            # Note that this ignores the IL+ player.
            proj_series, proj_players, roster = get_team(str(i)
                                                         , 'r'
                                                         , league=league
                                                         , include_bench=True
                                                         , injured=inj
                                                         , trade=trade_list
                                                         , drops=drop
                                                         , return_players=True)
            breakpoint()
            avg_series, avg_players = get_team(str(i)
                                               , 'avg'
                                               , league=league
                                               , include_bench=True
                                               , injured=inj
                                               , trade=trade_list
                                               , drops=drop)
            avg_30_series, avg_30_players = get_team(str(i)
                                                     , 'avg_30'
                                                     , league=league
                                                     , include_bench=True
                                                     , injured=inj
                                                     , trade=trade_list
                                                     , drops=drop)
            # hashtag_series, hashtag_players = get_team(str(i), 'r'
            #                                            , league=league
            #                                            , include_bench=True
            #                                            , injured=inj
            #                                            , trade=trade_list
            #                                            , drops=drop
            #                                            , hash=hash)

            # hashtag_series = convert_to_hashtag(roster)
            # hashtag_players = convert_to_hashtag(proj_players)

            proj_players['Team'] = trade_teams[num]
            proj_trades = proj_trades.append(proj_players,
                                             ignore_index=True)
            avg_players['Team'] = trade_teams[num]
            avg_trades = avg_trades.append(avg_players,
                                           ignore_index=True)
            avg_30_players['Team'] = trade_teams[num]
            avg_30_trades = avg_30_trades.append(avg_30_players,
                                                 ignore_index=True)
            # hashtag_players['Team'] = trade_teams[num]
            # hashtag_trades = hashtag_trades.append(hashtag_players
            #                                       , ignore_index=True)
        else:
            proj_series, roster = get_team(str(i)
                                           , 'r'
                                           , league=league
                                           , include_bench=True
                                           , injured=inj
                                           , drops=drop
                                           , return_players=True)
            avg_series = get_team(str(i)
                                  , 'avg'
                                  , league=league
                                  , include_bench=True
                                  , injured=inj
                                  , drops=drop)
            avg_30_series = get_team(str(i)
                                     , 'avg_30'
                                     , league=league
                                     , include_bench=True
                                     , injured=inj
                                     , drops=drop)
            # hashtag_series = convert_to_hashtag(roster)

        if fas_teams[num] != '0':
            af = get_fas('owned', 'avg', fas_teams[num], trade=True)
            a30f = get_fas('owned', 'avg30', fas_teams[num], trade=True)
            pf = get_fas('owned', 'proj', fas_teams[num], trade=True)
            # Need to make next line functional
            hf = convert_to_hashtag(pf)
            # hf = get_fas('owned', 'proj', fas_teams[num], trade=True, hashtag=hashtag)
            pf = pf * pf['GP']
            pf = pf.drop('GP')

            pf['Team'] = str(i)
            proj_fas= proj_fas.append(pf, ignore_index=True)
            af['Team'] = str(i)
            avg_fas = avg_fas.append(af, ignore_index=True)
            a30f['Team'] = str(i)
            avg_30_fas = avg_30_fas.append(a30f, ignore_index=True)
            # hf['Team'] = str(i)
            # hashtag_fas= hashtag_fas.append(hf, ignore_index=True)


        #if drops[num] != '0':
        #     stats = stats[stats.loc[:,'Players'] != tp]
        #    avg_series
        #    avg_30_series

        proj_series['Team'] = str(i)
        proj = proj.append(proj_series, ignore_index=True)
        avg_series['Team'] = str(i)
        avg = avg.append(avg_series, ignore_index=True)
        avg_30_series['Team'] = str(i)
        avg_30 = avg_30.append(avg_30_series, ignore_index=True)
        # hashtag_series['Team'] = str(i)
        # hashtag = hashtag_series.append(hashtag_series, ignore_index=True)


    proj = proj.set_index('Team')
    avg = avg.set_index('Team')
    avg_30 = avg_30.set_index('Team')
    # hashtag = hashtag.set_index('Team')
    # Group avg trades by team first and sum them

    # This will likely take work for hashtag.
    if np.any(trades != '0'):
        proj_trades = proj_trades.set_index('Team').drop(['Inj', 'Players'], axis=1).groupby('Team').sum()
        avg_trades = avg_trades.set_index('Team').drop(['Inj', 'Players'], axis=1).groupby('Team').sum()
        avg_30_trades = avg_30_trades.set_index('Team').drop(['Inj', 'Players'], axis=1).groupby('Team').sum()
        # hashtag_trades = hashtag_trades.set_index('Team').drop(['Inj', 'Players']
        #                                                        , axis=1).groupby('Team').sum()
        print(proj_trades)
    if np.any(fas_teams != '0'):
        proj_fas = proj_fas.set_index('Team')
        avg_fas = avg_fas.set_index('Team')
        avg_30_fas = avg_30_fas.set_index('Team')
        # hashtag_fas = hashtag_fas.set_index('Team')

    print(avg_30_fas)
    print(avg_fas)
    print(proj_fas)
    # print(hashtag_fas)

    print(proj_trades)
    print(avg_trades)
    print(avg_30_trades)
    # print(hashtag_trades)

    # Account for adjustments from trades or free agents.
    # First, trades.
    avg = avg.add(avg_trades, fill_value=0)
    avg_30 = avg_30.add(avg_30_trades, fill_value=0)
    proj = proj.add(proj_trades, fill_value=0)
    # hashtag = hashtag.add(hashtag_trades, fill_value=0)
    # Next, free agents (remember, drops already accounted for).
    avg = avg.add(avg_fas, fill_value=0)
    avg_30 = avg_30.add(avg_30_fas, fill_value=0)
    proj = proj.add(proj_fas, fill_value=0)
    # hashtag = hashtag.add(hashtag_fas, fill_value=0)
    # To get a weekly estimate, divide ROS projection by remaining weeks.
    # proj = proj / weeks_left
    proj = proj / 24
    # Alternatively, a weekly estimate for averages will be the average * the
    # average number of games in a week.
    nGames = 3.17
    avg = avg * nGames
    avg_30 = avg_30 * nGames
    # hashtag = hashtag * nGames

    # Finally, combine projections into a weight average.
    # Weighted average helps balance future projections (which
    # have games expected to play weighed in), actual performance
    # (since projections can be wild, and are not adjusted from pre-season
    # expectations until well into the season), and actual performance.
    paa = 0.15*proj + 0.3*avg + 0.55*avg_30 # + 0.0*hashtag

    paa['FG_perc'] = paa['FGM'] / paa['FGA']
    paa['FT_perc'] = paa['FTM'] / paa['FTA']
    weekly = paa.drop(axis=1, labels=['FGA','FTM', 'FGM', 'FTA' ])
    weekly = weekly.drop(axis=1, labels=[])
    # weekly.loc[:,'FG_perc':'FT_perc']*=weeks_left

    # Subjectively remove teams who don't appear to be contenders.
    # This will show the quality of a team versus the other playoff teams.
    # This is useful to distinguish. If your build is great against the
    # bottom teams but struggles against the top, then your team will
    # not be good in the playoffs. 
    # contenders = weekly.drop(['2', '3', '5', '14'])
    contenders = weekly
    print(contenders)

    # contenders=all.drop(axis=1, labels=['FGA','FTM', 'FGM', 'FTA', 'FG_perc', 'FT_perc'])
    # contenders = contenders.drop(['4','5','7','10'])

    
    # Here I attempt to estimate the strength of each team by calculating the
    # zscore for each category, similar to player rankings. We can compare this
    # to actual projections to determine accuracy. 
    zscores = (contenders - contenders.mean(axis=0)) / contenders.std(axis=0)
    #zscores=(contenders-contenders.mean(axis=0))/np.sqrt(contenders)
    # Flesh the above out: diff divided by uncertainty and not std...

    # Cap the zscores at +-3, since the benefit of being at 4 vs 3 has
    # very small impact on winning  percentage (both win all the time). Same
    # for -4 and -3 and losing (e.g, averaging 15 3s a week and 5 a week
    # makes practically no difference, losing 99.9% either way). 
    zscores['TO'] *= -1
    zscores[zscores > 3] = 3
    zscores[zscores < -3] = -3
    zscores['Total'] =  zscores.sum(axis=1)
    ranks = contenders.rank(axis=0, ascending=False)
    ranks.loc[:, 'TO'] = 15 - ranks.loc[:,'TO']
    print(ranks)
    print(zscores.sort_values('Total', ascending=False))

    breakpoint()

    # Now, I simulate the season using weekly averages. Note that obviously
    # week-to-week there will be large variations: schedules change, players
    # get injured. A base assumption is that this tends to even out
    # over the course of the season. Further, I don't have an algorithmic
    # way to handle the IL+ spot yet: e.g, this year Bam Adebayo is out 4-6 weeks.
    # While in the IL+ spot, he is ignored, so his team ('1') will look worse
    # than it is. Could be addressed by reading in injury lengthsm adding that
    # to dataframes, and dropping "worst" player based on some ranking.

    # Also I don't account for streaming/player activity, but this is simpler. For
    # example, team '4' tends to swap out 3 worst players for 3 new players which
    # have 4 game weeks. I could estimate this by multiplying the 3 worst players
    # on their roster by 4 instead of 3.17. I could add a similar effect from 3.17
    # to 5 on the worst spot for more conventional streamers, who trade out their
    # worst player to maximize games in that slot for a week.

    # That all said, this is a reasonable estimate/starting place.
    team_nums = np.arange(1, nTeams+1).astype(str)

    paa['2PM'] = paa['FGM'] - paa['3PTM']
    paa['FTO'] = paa['FTA'] - paa['FTM']
    paa['FGO'] = paa['FGA'] - paa['FGM']

    paa.index = paa.index.astype(int)
    paa = paa.sort_values('Team')
    paa.index = paa.index.astype(str)

    #t1=all.loc[team1,:].astype(int)
    #t2=matchup.loc[team2,:].astype(int)
    n = 1000
    d1 = np.random.poisson(paa.values, size=(n,paa.shape[0], paa.shape[1]))
    df = pd.DataFrame(columns=paa.columns)
    for i in range(d1.shape[1]):
        df_team = pd.DataFrame(d1[:,i,:], columns=paa.columns, index=[team_nums[i]]*n)
        df = pd.concat([df, df_team], axis=0)
        print((team_nums[i]))

    #d2=np.random.poisson(t2.values, size=(n,t2.shape[0]))
    #df1=pd.DataFrame(d1, columns=all.columns)
    #df2=pd.DataFrame(d2, columns=t2.index)
    df['FGM'] = df['2PM'] + df['3PTM']
    df['FGA'] = df['FGO'] + df['FGM']
    df['FTA'] = df['FTO'] + df['FTM']
    df['PTS'] = 3*df['3PTM'] + 2*df['2PM'] + df['FTM']
    df = df.drop(axis=1, labels=['2PM', 'FTO','FGO'])

    df['FG_perc'] = df['FGM'] / df['FGA']
    df['FT_perc'] = df['FTM'] / df['FTA']
    df = df.drop(['FGM','FTM','FGA', 'FTA'], axis=1)


    # HERE is where real schedule is useful
    # gen = itertools.combinations(team_nums, r=2)
    evs = pd.DataFrame(index=team_nums, columns=team_nums)
    win_perc = pd.DataFrame(index=team_nums, columns=team_nums)

    wins_dist = pd.DataFrame(index=np.repeat(team_nums, n), columns=team_nums)
    combos = set_schedule(week=week-1, tuples=True)
    for i, combo in enumerate(combos):
        team1 = combo[0]
        team2 = combo[1]
        # For when there are <=  2 weeks left, we can simulate
        # results for entire league using specific schedule.  
        if i<6:
            wins = matchup(team1, team2, 19, end=4, sim=True)
        else:
            wins = matchup(team1, team2, 20, start=4, end=11, sim=True)

        wins2 = 9 - wins
        wins.index = [team1] * n
        wins2.index = [team2] * n
        wins_dist.loc[team1, team2] = wins
        wins_dist.loc[team2, team1] = wins2
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


    current = get_standings()
    # Will adding these out of order still work due to the shared index?
    score_dist = score_dist + current

    score_means = score_dist.mean().sort_values(ascending=False)
    print(score_means)
    print((score_dist.std().sort_values(ascending=False)))
    season_rank = score_dist.rank(axis=1, ascending=False, method='first')

    reg_win = ((season_rank==1.).sum()/n*100.).round(2).sort_values(ascending=False)
    reg_tie =  ((season_rank==1.5).sum()/n*100.).round(2).sort_values(ascending=False)
    playoff = ((season_rank<nQual+1.).sum()/n*100.).round(2).sort_values(ascending=False)
    bye = ((season_rank<2.5).sum()/n*100.).round(2).sort_values(ascending=False)
    reg_cash = reg_win + reg_tie*.5
    #print "Reg EV:",  reg_cash
    #print "Playoff percent:",  playoff
    #score_dist.hist(bins=12, density=True)
    #plt.show()
    #score_dist.rank(axis=1, ascending=False).hist(bins=12, density=True)
    #plt.show()

    playoff_ev = playoff.copy() - playoff.copy()
    print("now do playoff teams only")

    bad_combos=[]
    for i, seed in season_rank.iterrows():
        seeds = seed[seed < nQual+1].astype(int)
        remainder = seed[seed>=nQual+1].index.values.astype(str)
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
        mapper = dict(list(zip(seeds.index.values, seeds.values)))
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
        invert_mapper = {v: k for k, v in list(mapper.items())}
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
    print(("Playoff percent:",  playoff))
    print(("Regular Season EV", reg_cash))
    print(("Total EV", gross))
    print(("Net EV", profit))
    # print "Bye odds", bye
    # score_dist.hist(bins=12, density=True)
    # plt.show()
    #score_dist.rank(axis=1, ascending=False).hist(bins=12, density=True)
    #plt.show()
    breakpoint()
    return paa

# def corr()
#    """Read in like 10 players stats for every game, scatter plots (corner?)
#    between every pair of stats to find correlations"""

#def brier():
    #update brier score for this program based on wins and losses

def get_predictions(week, team1s, team2s,
                    league='81947', mock=False, bench=True,
                    base='proj', save=False):
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
                                league=league, include_bench=bench, base=base)
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

    print('What is the variable hold?')
    breakpoint()
    #saving = int(raw_input('Did you set up correct matchups ' \
    #                       'and days for the week? '))
    if save == True:
        try:
            if mock == False:
                if base == 'proj':
                    preds = pd.read_csv('fantasy_predictions.csv', index_col=[0, 1])
                    preds = preds.append(hold)
                    preds.to_csv('fantasy_predictions.csv')
                elif base == 'avg':
                    preds = pd.read_csv('fantasy_predictions_avg.csv', index_col=[0, 1])
                    preds = preds.append(hold)
                    preds.to_csv('fantasy_predictions_avg.csv')
                else:
                    preds = pd.read_csv('fantasy_predictions_avg_30.csv', index_col=[0, 1])
                    preds = preds.append(hold)
                    preds.to_csv('fantasy_predictions_avg_30.csv')
            else:
                if base == 'proj':
                    preds = pd.read_csv('mock_fantasy_predictions.csv', index_col=[0, 1])
                    preds = preds.append(hold)
                    preds.to_csv('mock_fantasy_predictions.csv')
                elif base == 'avg':
                    preds = pd.read_csv('mock_fantasy_predictions_avg.csv', index_col=[0, 1])
                    preds = preds.append(hold)
                    preds.to_csv('mock_fantasy_predictions_avg.csv')
                else:
                    preds = pd.read_csv('mock_fantasy_predictions_avg_30.csv', index_col=[0, 1])
                    preds = preds.append(hold)
                    preds.to_csv('mock_fantasy_predictions_avg_30.csv')
        except IOError:
            if mock == False:
                if base == 'proj':
                    hold.to_csv('fantasy_predictions.csv')
                elif base == 'avg':
                    hold.to_csv('fantasy_predictions_avg.csv')
                else:
                    hold.to_csv('fantasy_predictions_avg_30.csv')
            else:
                if base == 'proj':
                    hold.to_csv('mock_fantasy_predictions.csv')
                elif base == 'avg':
                    hold.to_csv('mock_fantasy_predictions_avg.csv')
                else:
                    hold.to_csv('mock_fantasy_predictions_avg_30.csv')
    return 1

def record_results(week, team1s, team2s, league='46134', mock=False):
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
                if isinstance(match.iloc[j, k], str):
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

def set_schedule(week=0, tuples=False):
    """ Function to define schedule for entire season
    and return it in dictionary form.
    Output: 1-d array of dictionaries. Each dictionary is the 
    schedule for a given week. Team is the key, and that team's
    opponent is the value for that key. Can be converted to 
    list of tuples via dict.items."""
    nWeeks = 20
    nTeams = 14
    teams1 = np.zeros((nWeeks, nTeams)).astype(int)
    teams2 = np.zeros((nWeeks, nTeams)).astype(int)
    teams1[:] = np.arange(1, nTeams+1)
    teams2[:] = [3, 10, 1, 8, 13, 14, 12, 4, 11, 2, 9, 7, 5, 6]
    # Increase by one each week to 13
    # 14 is when index = team number
    inc = np.tile(np.arange(nWeeks), (nTeams, 1)).T
    teams2 += inc
    teams2[teams2 > nTeams] -= (nTeams-1)
    #teams2[teams2 > nTeams-1] -= (nTeams-1)
    # Team 14
    teams2[:, nTeams-1] = [6, 9, 4, 7, 2, 5, 13
                           , 10, 12, 8, 11, 3, 1
                           , 6, 9, 4, 7, 2, 5, 13]

    # Replace self with 14:
    teams2[teams2==teams1] = nTeams
    teams1 = teams1.astype(str).tolist()
    teams2 = teams2.astype(str).tolist()

    matches = [dict(list(zip(teams1[i], teams2[i]))) for i in range(nWeeks)]

    if tuples==False:
        current = matches[week]
        current = [tuple(sorted(t))
                   for t in list(current.items())]
        current = sorted(list(set(current)))
        team1s = np.array([tup[0] for tup in current])
        team2s = np.array([tup[1] for tup in current])
        #breakpoint()
        return team1s, team2s
    else:
        remaining_matches = matches[week:]
        match_tuples = []
        for dic in remaining_matches:
            st = [tuple(sorted(t)) for t in list(dic.items())]
            match_tuples += list(set(st))
        return match_tuples
        
if __name__ == '__main__':
    config = configparser.ConfigParser()
    config.read('config.py')
    #planet = config.get('DATA', 'planet')
    #transit = config.getboolean('DATA', 'transit')

    week = config.getint('VALUES', 'week')
    league = config.get('VALUES', 'league')
    mock_league = config.get('VALUES', 'mock_league')
    mock = config.getboolean('EXTRAS', 'mock_league')
    save_results = config.getboolean('EXTRAS', 'record_results')
    save_predict = config.getboolean('EXTRAS', 'record_predictions')
    predict = config.getboolean('EXTRAS', 'predict')
    projected = config.getboolean('BASE', 'projected')
    average = config.getboolean('BASE', 'average')
    average_30 = config.getboolean('BASE', 'average_last_30')
  
    pre_week = week - 1

    teams1, teams2 = set_schedule(week)

    if save_results==True:
        if mock==False:
            record_results(pre_week, teams1, teams2, league=league, mock=mock)
            print("Results recorded for league %s" % league)
        else:
            record_results(pre_week, teams1, teams2, league=league, mock=mock)
            print("Results recorded for league %s" % league)

    if predict==True:
        if mock==False:
            if projected==True:
                get_predictions(week, teams1, teams2
                                , league=league, mock=False
                                , save=save_predict)
                print("Predictions recorded for league %s" % league)
                print()
                print()
            if average==True:
                get_predictions(week, teams1, teams2
                                , league=league, mock=False, base='avg'
                                , save=save_predict)
                print("Average predictions recorded for league %s" % league)
                print()
                print()
            if average_30==True:
                get_predictions(week, teams1, teams2,
                                league=league, mock=False, base='avg_30'
                                , save=save_predict)
                print("30-day average predictions recorded for league %s"
                      % league)
                print()
                print()
    breakpoint()
    # league = mock_league
    # teams1 = np.array([1, 3]).astype(str)
    # teams2 = np.array([2, 4]).astype(str)
    # mock=True
    # record_predictions(week, teams1, teams2, league=league, mock=mock, bench=False)
    # print(("Predictions recorded for league %s" % league))
    # print()
    # print()
    # record_predictions(week, teams1, teams2, league=league, mock=mock, base='avg')
    # print(("Average predictions recorded for league %s" % league))
    # print()
    # print()
    # record_predictions(week, teams1, teams2,
    #                    league=league, mock=mock, base='avg_30')
    # print(("30-day average predictions recorded for league %s" % league))
    # print()
    # print()
