import numpy as np
from numpy import random
from selenium import webdriver
from selenium.webdriver.support.ui import Select
from bs4 import BeautifulSoup as bs
import time
import pandas as pd
import datetime


def ev(mean, var):
    mean = mean*3
    return (random.normal(mean, np.sqrt(var), size=100000)>0).sum()/100000

def get_hashtag(base='ros'):
    """ Program that scrapes projections for 
    every player ROS from hashtag basketball.

    Instead of "total" vs "average", which is flawed since
    hashtag does not update games played projections and 
    so current injuries are very wonky, I use 'proj', which
    is simply the average projections from the website, and 
    'ros', which is the true ROS projection averages. This is
    the projection total - (actual averages * actual GP) / 
    (projected GP - actual GP). This is interpreted as the projected
    average performance over the remaining games. I allow this to vary
    since I don't have the hashtag algorithm and don't know 
    for sure how they calculate this. 

    Example: Lillard is projected at 25.6 ppg, which is 28ppg combined
    with his actual 23 ppg. So you can view it as a loose and strict
    prior.
    """
    # First, I need to do the very important step
    # of loading the table including data for all players.
    # The data itself is not included in the default HTML,
    # and no json is obviously present, so I must use selenium.

    # First I load the page.
    link = 'https://hashtagbasketball.com/fantasy-basketball-rankings'
    browser = webdriver.Firefox()
    browser.get(link)
    # Then, I need to select "All" from the drop down menu.
    # A similar method can be used to pick any customizations
    # I want for ROS rankings.
    
    name = "ctl00$ContentPlaceHolder1$DDSHOW"
    select = Select(browser.find_element_by_name(name))
    select.select_by_visible_text('All')
    # Wait 3 seconds for table to reload.
    time.sleep(3)

    html = browser.page_source
    soup = bs(html, 'html.parser')
    headers = [th.getText() for th in soup.findAll('tr')[4].findAll('th')]
    data_rows = soup.findAll('tr')[5:]
    data = [[td.getText().strip('\n')
             for td in data_rows[i].findAll('td')]
            for i in range(len(data_rows))]
    stats = pd.DataFrame(data, columns=headers)
    fga = [item.split('\n')[-1].strip('()').split('/')[-1]
           for item in stats.loc[:,'FG%'].values]
    fgm = [item.split('\n')[-1].strip('()').split('/')[0]
           for item in stats.loc[:,'FG%'].values]
    fta = [item.split('\n')[-1].strip('()').split('/')[-1]
           for item in stats.loc[:,'FT%'].values]
    ftm = [item.split('\n')[-1].strip('()').split('/')[0]
           for item in stats.loc[:,'FT%'].values]
    players = [item.rstrip(' ')
            for item in stats.loc[:,'PLAYER'].values]
    # Correct the inconsistent player names:
    for i, play in enumerate(players):
        if 'Aleksej' in play:
            players[i] = 'Aleksej Pokusevski'
        if 'Robert Williams' in play:
            players[i] = 'Robert Williams'
        if 'P.J. Washington' in play:
            players[i] = 'PJ Washington'
        if 'Hyland' in play:
            players[i] = 'Bones Hyland'
        if 'Trey Murphy' in play:
            players[i] = 'Trey Murphy III'
        if 'Kenyon Martin Jr.' in play:
            players[i] = 'KJ Martin Jr.'
        if 'Maurice Harkless' in play:
            players[i] = 'Moe Harkless'
        if 'Kira Lewis' in play:
            players[i] = 'Kira Lewis Jr'
        if 'Satoransky' in play:
            players[i] = 'Tomas Satoransky'
        if 'Garza' in play:
             players[i] = 'Luka Garza'
    stats['FGM'] = fgm
    stats['FGA'] = fga
    stats['FTM'] = ftm
    stats['FTA'] = fta
    stats['PLAYER'] = players
    
    # Now drop the useless columns
    stats = stats.drop(labels=['R#'
                               , 'POS'
                               , 'TEAM'
                               , 'MPG'
                               , 'TOTAL'
                               , 'FG%'
                               , 'FT%'], axis=1)
    stats =  stats.set_index('PLAYER')
    # Coerce will force the non-data rows (aka the header
    # rows interspersed with the data) to be NaN, allowing
    # for easy removal. 
    stats = stats[:].apply(pd.to_numeric, errors='coerce')
    stats = stats.dropna()
    stats_total = stats.mul(stats['GP'], axis=0).drop('GP', axis=1)
    stats_total['GP'] = stats['GP']

    # Now the page contains all the data I need in the HTML,
    # so I can scrape it using beautiful soup.

    name1 = "ctl00$ContentPlaceHolder1$DDDURATION"
    select = Select(browser.find_element_by_name(name1))
    select.select_by_index(0)
    time.sleep(3)
    html = browser.page_source
    soup = bs(html, 'html.parser')
    headers = [th.getText() for th in soup.findAll('tr')[4].findAll('th')]
    data_rows = soup.findAll('tr')[5:]
    data = [[td.getText().strip('\n')
             for td in data_rows[i].findAll('td')]
            for i in range(len(data_rows))]
    proj = pd.DataFrame(data, columns=headers)
    browser.close()

    # Need to separate the FG% and FT% into the made and attempted
    # components.

    fga = [item.split('\n')[-1].strip('()').split('/')[-1]
           for item in proj.loc[:,'FG%'].values]
    fgm = [item.split('\n')[-1].strip('()').split('/')[0]
           for item in proj.loc[:,'FG%'].values]
    fta = [item.split('\n')[-1].strip('()').split('/')[-1]
           for item in proj.loc[:,'FT%'].values]
    ftm = [item.split('\n')[-1].strip('()').split('/')[0]
           for item in proj.loc[:,'FT%'].values]
    players = [item.rstrip(' ')
               for item in proj.loc[:,'PLAYER'].values]
    proj['FGM'] = fgm
    proj['FGA'] = fga
    proj['FTM'] = ftm
    proj['FTA'] = fta
    proj['PLAYER'] = players
    # Now drop the useless columns
    proj = proj.drop(labels=['R#'
                             , 'POS'
                             , 'TEAM'
                             , 'MPG'
                             , 'TOTAL'
                             , 'FG%'
                             , 'FT%'], axis=1)
    proj =  proj.set_index('PLAYER')
    proj = proj[:].apply(pd.to_numeric, errors='coerce')
    proj = proj.dropna()
    proj_total = proj.mul(proj['GP'], axis=0).drop('GP', axis=1)
    proj_total['GP'] = proj['GP']

    # Get ROS averages, which disentangles current
    # performance from future projections. 
    ros_total = proj_total.subtract(stats_total, fill_value=0)
    ros = ros_total.div(ros_total['GP'], axis=0)

    # Edit headers to match yahoo 
    rename_dic = {'3PM': '3PTM', 'TREB': 'REB', 'STL': 'ST'}
    ros.rename(rename_dic, axis=1, inplace=True)
    proj.rename(rename_dic, axis=1, inplace=True)

    today = str(datetime.date.today())
    ros['Date'] = today
    proj['Date'] = today
    
    # Save to csv instead of returning
    ros.to_csv('./stats/hashtag_ros.csv')
    proj.to_csv('./stats/hashtag_proj.csv')


    if base=='ros':
        return ros
    if base=='proj':
        return proj



def convert_to_hashtag(player_list, get=False):
    """ Read in a list of players with yahoo stats. Read in hashtag stats,
    or, if outdated, get re-get stats. Compare the two by player name
    to assign hashtag projections to each player, and return this new
    dataframe. 

    This allows for week- or season-long projections based on hashtag
    projections (as opposed to yahoo alone). 
    """

    # If get_hashtag is true, get new stats.
    if get==True:
        hashtag = get_hashtag()
        
    # If not, search for hashtag stats
    else:
        try:
            hashtag = pd.read_csv('./stats/hashtag_proj.csv', index_col=0)
            # If found, check if date is within a week. If so, use csv.
            date = hashtag['Date'].values[0]
            get_date = datetime.datetime.strptime(date,'%Y-%m-%d').date()
            delta = datetime.date.today() - get_date
            days = delta.days
            # If data is more than a week old, then get new stats.
            if days>7:
                hashtag = get_hashtag()
        except IOError:
            # if not found, generate them with get_hashtag
            hashtag = get_hashtag()
        

    # Now, hashtag contains current hashtag projections for all nba players.

    # good to hear
    breakpoint()
    # Join hashtag projections on player_list to isolate projections
    # for players on team. Be cognizant of player name differences
    # between yahoo and hashtag.

    team = player_list.join(hashtag, type='inner')

    return team

   



    
