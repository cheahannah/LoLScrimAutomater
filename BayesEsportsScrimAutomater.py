import os
import pandas as pd
import json
import numpy as np 
from datetime import datetime, timedelta

'''
This code is meant to convert 1 folder of 1 game data (usually around +7000 individual JSON files) 
from https://bayesesports.com/ into a .csv file to input on a spreadsheet as per this document (https://docs.google.com/document/d/1d0nR6oXwWNZ8yDAfGge38dVE6TDg-QWhCjIQrr_7E8Y/edit?usp=sharing).
It's really scrappy code since something was always different with the game data.
For any questions & concerns, feel free to hit me up on Discord xirimpi#3959.
'''

def json_to_df(json_dir):
    '''
    Input: 
        json_dir: a folder of individual JSON files for one game
    Output: 
        rawdata: a flattened pandas dataframe
    '''
    #Empty list to store json file info
    json_list = [] 

    for root, dirs, files in os.walk(json_dir):
        for name in files:
            if name.endswith((".json")):
                json_path = os.path.join(root, name)
                #Read json file info
                json_data = pd.read_json(json_path, lines=True)  
                #Append json file info to list
                json_list.append(json_data) 

    rawdata = pd.concat(json_list, ignore_index=True)

    # Reorder the data (even though the files in the folder were originally in order, they somehow became out of order)
    rawdatasorted = rawdata.sort_values(by='seqIdx', ascending=True).reset_index()

    #Flatten the 'payload' columns
    rawdata = pd.json_normalize(rawdatasorted['payload']) 
    rawdata = rawdata.rename(columns=lambda x: x.replace('payload.', '')).rename(columns=lambda x: x.replace('payload.payload.', ''))
    
    return rawdata

def get_team_data(rawdata): 
    '''
    Input: 
        rawdata: flattened pandas dataframe from 'json_to_df' function
    Outputs: 
        CLG: a cleaned pandas dataframe for whichever team is CLG
        team2: a cleaned pandas dataframe for opponent team

    '''
    #Selects certain columns from rawdata
    rawdata = rawdata[['type', 'subject', 'action', 'sourceUpdatedAt', 'gameTime', 'teamOne.players',
                    'teamTwo.players', 'winningTeam', 'victimTeamUrn', 'teamOne.dragonKills', 
                    'teamTwo.dragonKills', 'monsterType', 'killerTeamUrn',
                   'buildingType', 'buildingTeamUrn', 'lane', 'turretTier']]

    #intermediate dataframe
    data = rawdata.copy()
    data = rawdata[rawdata['teamOne.players'].notnull()]
    data['sourceUpdatedAt'] = pd.to_datetime(data['sourceUpdatedAt'])
    data['date'] = [d.date() for d in data['sourceUpdatedAt']]

    #Team 1 code starts here
    teamOne = pd.DataFrame()
    #Flatten nested JSON column for teamOne to expand each row to be a player 
    for each in data[data["teamOne.players"].notnull()]['teamOne.players']:
        teamOne = pd.concat([teamOne, pd.json_normalize(each)])

    teamOne[['teamName', 'summonerName']] = teamOne["summonerName"].str.split(' ', expand=True)
    #Get NA Global Contract Database from website
    nagcd = pd.read_html('https://lol.fandom.com/wiki/Archive:Global_Contract_Database/NA/Current')[2].rename(columns={"Official Summoner Name": 'summonerName'})
    #Summoner names were slightly different and had to be fixed
    nagcd['summonerName'] = nagcd['summonerName'].replace('Wildturtle','WildTurtle')
    #Merge nagcd & teamOne to get lane positions for each player
    teamOne = pd.merge(teamOne, nagcd, on=['summonerName'], how='left')

    #Flattening the column earlier made the dataframe 5x longer than before (since 5 players each team) and it created a new dataframe
    # so repeat each row of 'sourceUpdatedAt', 'gameTime', and 'sourceUpdatedAtDT' 5 times as well
    teamOne['sourceUpdatedAt'] = np.repeat(data['sourceUpdatedAt'], 5).reset_index(drop=True)
    teamOne['gameTime'] = np.repeat(data['gameTime'], 5).reset_index(drop=True)
    #'sourceUpdatedAtDT is 'sourcedUpdatedAt' but in datetime formate
    teamOne['sourceUpdatedAtDT'] = [each.strftime('%H:%M:%S') for each in teamOne['sourceUpdatedAt']]
    teamOne['date'] = np.repeat(data['date'], 5).reset_index(drop=True)

    #Select relevant columns to output
    teamOne = teamOne[['date', 'sourceUpdatedAt', 'sourceUpdatedAtDT', 'gameTime', 'teamID', 'Team', 'teamName', 'summonerName', 'summonerID', 'accountID', 'Position',
                            'championID', 'pickTurn', 'pickMode', 'level', 'experience', 'currentGold', 
                            'totalGold', 'goldPerSecond', 'stats.minionsKilled', 'stats.championsKilled']]
    teamOne = teamOne.rename(columns={"stats.minionsKilled": "minionsKilled", "stats.championsKilled": "champsKilled"})
    teamOne = teamOne.dropna().sort_values('sourceUpdatedAt').reset_index()

    #Team 2 code starts here
    teamTwo = pd.DataFrame()
    #Flatten nested JSON column for teamTwo
    for each in data[data["teamTwo.players"].notnull()]['teamTwo.players']:
        teamTwo = pd.concat([teamTwo, pd.json_normalize(each)])

    teamTwo[['teamName', 'summonerName']] = teamTwo["summonerName"].str.split(' ', expand=True)
    #Merge nagcd & teamTwo to get lane positions for each player
    teamTwo = pd.merge(teamTwo, nagcd, on=['summonerName'], how='left')

    #Flattening the column earlier made the dataframe 5x longer than before (since 5 players each team) and it created a new dataframe
    # so repeat each row of 'sourceUpdatedAt', 'gameTime', and 'sourceUpdatedAtDT' 5 times as well
    teamTwo['sourceUpdatedAt'] = np.repeat(data['sourceUpdatedAt'], 5).reset_index(drop=True)
    teamTwo['gameTime'] = np.repeat(data['gameTime'], 5).reset_index(drop=True)
    #'sourceUpdatedAtDT is 'sourcedUpdatedAt' but in datetime formate
    teamTwo['sourceUpdatedAtDT'] = [each.strftime('%H:%M:%S') for each in teamTwo['sourceUpdatedAt']]
    teamTwo['date'] = np.repeat(data['date'], 5).reset_index(drop=True)

    #Select relevant columns to output
    teamTwo = teamTwo[['date', 'sourceUpdatedAt', 'sourceUpdatedAtDT', 'gameTime', 'teamID', 'Team', 'teamName', 'summonerName', 'summonerID', 'accountID', 'Position',
                            'championID', 'pickTurn', 'pickMode', 'level', 'experience', 'currentGold', 
                            'totalGold', 'goldPerSecond', 'stats.minionsKilled', 'stats.championsKilled']]
    teamTwo = teamTwo.rename(columns={"stats.minionsKilled": "minionsKilled", "stats.championsKilled": "champsKilled"})
    teamTwo = teamTwo.dropna().sort_values('sourceUpdatedAt').reset_index()
    
    #get objectives for each team
    CLG, team2 = objectives(data, teamOne, teamTwo)
    
    return CLG, team2

def get_team_data_academy(rawdata):
    '''
    Had to create a different function for CLG Academy because the global database and roster was whack for Amateur teams
    Input: 
        rawdata: flattened pandas dataframe from 'json_to_df' function
    Outputs: 
        CLG: a cleaned pandas dataframe for whichever team is CLG Academy
        team2: a cleaned pandas dataframe for opponent team

    '''
    #Selects certain columns from rawdata
    rawdata = rawdata[['type', 'subject', 'action', 'sourceUpdatedAt', 'gameTime', 'teamOne.players',
                    'teamTwo.players', 'winningTeam', 'victimTeamUrn', 'teamOne.dragonKills', 
                    'teamTwo.dragonKills', 'monsterType', 'killerTeamUrn',
                   'buildingType', 'buildingTeamUrn', 'lane', 'turretTier']]

    #intermediate dataframe
    data = rawdata.copy()
    data = rawdata[rawdata['teamOne.players'].notnull()]
    data['sourceUpdatedAt'] = pd.to_datetime(data['sourceUpdatedAt'])
    data['date'] = [d.date() for d in data['sourceUpdatedAt']]

    #Team 1 code starts here
    teamOne = pd.DataFrame()
    #Flatten nested JSON column for teamOne to expand each row to be a player 
    for each in data[data["teamOne.players"].notnull()]['teamOne.players']:
        teamOne = pd.concat([teamOne, pd.json_normalize(each)])

    #Had a harder time selecting teamName and summonerName from dataframe because one or the other would be missing
    team_summoner = pd.DataFrame(teamOne["summonerName"].str.split(' ', 1).to_list(), columns=['teamName', 'summonerName'])
    mask = (team_summoner['teamName'] != team_summoner['teamName'].head(1).item())
    team_summoner.loc[mask, 'summonerName'] = team_summoner['teamName']
    team_summoner.loc[mask, 'teamName'] = team_summoner['teamName'].head(1).item()
    teamOne[['teamName', 'summonerName']] = team_summoner

    #Get NA Global Contract Database from website
    nagcd = pd.read_html('https://lol.fandom.com/wiki/Archive:Global_Contract_Database/NA/Current')[2].rename(columns={"Official Summoner Name": 'summonerName'}).drop_duplicates(subset='summonerName')
    #Summoner names were slightly different and had to be fixed
    nagcd['summonerName'] = nagcd['summonerName'].replace('Faisal','Faisall')
    #nagcd['summonerName'] = nagcd['summonerName'].replace('Fizzi','Zyko')
    nagcd['summonerName'] = nagcd['summonerName'].replace('Jojopyun','jojopyun')
    nagcd['summonerName'] = nagcd['summonerName'].replace('Wildturtle','WildTurtle')
    #Merge nagcd & teamOne to get lane positions for each player
    if teamOne['summonerName'].head(1).item() in nagcd['summonerName'].unique():
        teamOne = pd.merge(teamOne, nagcd, on=['summonerName'], how='left')
    #If an amateur team was not in the global database, I had to manually code them in
    elif teamOne['teamName'].head(1).item() == 'AOER':
        teamOne.loc[teamOne['summonerName']=='Chim', 'Position'] = 'Top'
        teamOne.loc[teamOne['summonerName']=='Jozy', 'Position'] = 'Jungle'
        teamOne.loc[teamOne['summonerName']=='LEO99', 'Position'] = 'Mid'
        teamOne.loc[teamOne['summonerName']=='Shorthop', 'Position'] = 'Bot'
        teamOne.loc[teamOne['summonerName']=='Fizzi', 'Position'] = 'Support'

    #change column name to make less confusing later
    if 'teamName' in teamOne.columns:
        teamOne.rename(columns={"teamName": "Team_name"}, inplace=True)

    #Flattening the column earlier made the dataframe 5x longer than before (since 5 players each team) and it created a new dataframe
    # so repeat each row of 'sourceUpdatedAt', 'gameTime', and 'sourceUpdatedAtDT' 5 times as well
    teamOne['sourceUpdatedAt'] = np.repeat(data['sourceUpdatedAt'], 5).reset_index(drop=True)
    teamOne['gameTime'] = np.repeat(data['gameTime'], 5).reset_index(drop=True)
    #'sourceUpdatedAtDT is 'sourcedUpdatedAt' but in datetime formate
    teamOne['sourceUpdatedAtDT'] = [each.strftime('%H:%M:%S') for each in teamOne['sourceUpdatedAt']]
    teamOne['date'] = np.repeat(data['date'], 5).reset_index(drop=True)

    #Select relevant columns to output
    teamOne = teamOne[['date', 'sourceUpdatedAt', 'sourceUpdatedAtDT', 'gameTime', 'teamID', 'Team_name', 'summonerName', 'summonerID', 'accountID', 'Position',
                            'championID', 'pickTurn', 'pickMode', 'level', 'experience', 'currentGold', 
                            'totalGold', 'goldPerSecond', 'stats.minionsKilled', 'stats.championsKilled']]
    teamOne = teamOne.rename(columns={"stats.minionsKilled": "minionsKilled", "stats.championsKilled": "champsKilled"})
    teamOne = teamOne.sort_values('sourceUpdatedAt').reset_index()

    #Team 2 code starts here
    teamTwo = pd.DataFrame()
    #Flatten nested JSON column for teamTwo
    for each in data[data["teamTwo.players"].notnull()]['teamTwo.players']:
        teamTwo = pd.concat([teamTwo, pd.json_normalize(each)])

    #Had a harder time selecting teamName and summonerName from dataframe because one or the other would be missing
    team_summoner = pd.DataFrame(teamTwo["summonerName"].str.split(' ', 1).to_list(), columns=['teamName', 'summonerName'])
    mask = (team_summoner['teamName'] != team_summoner['teamName'].head(1).item())
    team_summoner.loc[mask, 'summonerName'] = team_summoner['teamName']
    team_summoner.loc[mask, 'teamName'] = team_summoner['teamName'].head(1).item()
    teamTwo[['teamName', 'summonerName']] = team_summoner
    #Merge nagcd & teamTwo to get lane positions for each player
    if teamTwo['summonerName'].head(1).item() in nagcd['summonerName'].unique():
        teamTwo = pd.merge(teamTwo, nagcd, on=['summonerName'], how='left')
    #If an amateur team was not in the global database, I had to manually code them in
    elif teamTwo['teamName'].head(1).item() == 'AOER':
        teamTwo.loc[teamOne['summonerName']=='Chim', 'Position'] = 'Top'
        teamTwo.loc[teamOne['summonerName']=='Jozy', 'Position'] = 'Jungle'
        teamTwo.loc[teamOne['summonerName']=='LEO99', 'Position'] = 'Mid'
        teamTwo.loc[teamOne['summonerName']=='Shorthop', 'Position'] = 'Bot'
        teamTwo.loc[teamOne['summonerName']=='Fizzi', 'Position'] = 'Support'
    
    #change column name to make less confusing later
    if 'teamName' in teamTwo.columns:
        teamTwo.rename(columns={"teamName": "Team_name"}, inplace=True)

    #Flattening the column earlier made the dataframe 5x longer than before (since 5 players each team) and it created a new dataframe
    # so repeat each row of 'sourceUpdatedAt', 'gameTime', and 'sourceUpdatedAtDT' 5 times as well
    teamTwo['sourceUpdatedAt'] = np.repeat(data['sourceUpdatedAt'], 5).reset_index(drop=True)
    teamTwo['gameTime'] = np.repeat(data['gameTime'], 5).reset_index(drop=True)
    #'sourceUpdatedAtDT is 'sourcedUpdatedAt' but in datetime formate
    teamTwo['sourceUpdatedAtDT'] = [each.strftime('%H:%M:%S') for each in teamTwo['sourceUpdatedAt']]
    teamTwo['date'] = np.repeat(data['date'], 5).reset_index(drop=True)

    #Select relevant columns to output
    teamTwo = teamTwo[['date', 'sourceUpdatedAt', 'sourceUpdatedAtDT', 'gameTime', 'teamID', 'Team_name', 'summonerName', 'summonerID', 'accountID', 'Position',
                            'championID', 'pickTurn', 'pickMode', 'level', 'experience', 'currentGold', 
                            'totalGold', 'goldPerSecond', 'stats.minionsKilled', 'stats.championsKilled']]
    teamTwo = teamTwo.rename(columns={"stats.minionsKilled": "minionsKilled", "stats.championsKilled": "champsKilled"})
    teamTwo = teamTwo.sort_values('sourceUpdatedAt').reset_index()
    
    #get objectives for each team
    CLG, team2 = objectives_academy(data, teamOne, teamTwo)
    
    return CLG, team2

def get_cs(team, time, position):
    '''
    Gets creep score for a position from a team at a certain time
    '''
    if position in team['Position'].unique():
        return team.loc[(team['sourceUpdatedAtDT']==time) & (team['Position']==position)].head(1)['minionsKilled'].item()
    else:
        return np.nan
    
def get_team_cs(team, time):
    '''
    Calculates creep score for all positions on a team at a certain time
    '''
    return get_cs(team, time, 'Top') + get_cs(team, time, 'Jungle') + get_cs(team, time, 'Mid') + get_cs(team, time, 'Bot') + get_cs(team, time, 'Support')

def get_g(team, time, position):
    '''
    Gets gold for a position from a team at a certain time
    '''
    if position in team['Position'].unique():
        return team.loc[(team['sourceUpdatedAtDT']==time) & (team['Position']==position)].head(1)['totalGold'].item()
    else:
        return np.nan

def get_team_g(team, time):
    '''
    Calculates gold for all positions on a team at a certain time
    '''
    return get_g(team, time, 'Top') + get_g(team, time, 'Jungle') + get_g(team, time, 'Mid') + get_g(team, time, 'Bot') + get_g(team, time, 'Support')

def get_xp(team, time, position):
    '''
    Gets experience for a position from a team at a certain time
    '''
    if position in team['Position'].unique():
        return team.loc[(team['sourceUpdatedAtDT']==time) & (team['Position']==position)].head(1)['experience'].item()
    else:
        return np.nan
    
def get_team_xp(team, time):
    '''
    Calculates experience for all positions on a team at a certain time
    '''
    return get_xp(team, time, 'Top') + get_xp(team, time, 'Jungle') + get_xp(team, time, 'Mid') + get_xp(team, time, 'Bot') + get_xp(team, time, 'Support')                       

def check_time(team, time):
    '''
    Returns datetime format of specified time if it exists in team's time stamps, else returns next closest datetime format of time stamp
    '''
    updatedTime = team.loc[0]['sourceUpdatedAt'] + pd.Timedelta(minutes = time)
    DT = updatedTime.strftime('%H:%M:%S')
    if DT in team['sourceUpdatedAtDT'].unique():
        return DT
    else:
        closest = min(team['sourceUpdatedAt'], key=lambda x: abs(x - updatedTime))
        return closest.strftime('%H:%M:%S')        

def objectives(data, teamOne, teamTwo):
    '''
    Input:
        data: rawdata dataframe from json_to_df function
        teamOne: teamOne dataframe from get_team_data function
        teamTwo: teamTwo dataframe from get_team_data function
    Output: 
        CLG: cleaned dataframe for whichever team is CLG
        team2: cleaned dataframe for opponent team
    '''
    #getting winning team ('100' is teamOne, '200' is teamTwo)
    if data[data['winningTeam'] != 0]['winningTeam'].dropna().empty:
        teamOne['winningTeam'] = False
        teamTwo['winningTeam'] = False
    else:
        winningTeam = data[data['winningTeam'] != 0]['winningTeam'].dropna().item()
        teamOne['winningTeam'] = (winningTeam == teamOne['teamID']).head(1).item()
        teamTwo['winningTeam'] = (winningTeam == teamTwo['teamID']).head(1).item()
    
    #which team got first blood
    firstblood= data['victimTeamUrn'].dropna()
    if firstblood.empty:
        teamOne['firstBlood'] = 0
        teamTwo['firstBlood'] = 0
    elif firstblood.head(1).item() == 'live:lol:riot:team:one':
        teamOne['firstBlood'] = 0
        teamTwo['firstBlood'] = 1
    else:
        teamOne['firstBlood'] = 1
        teamTwo['firstBlood'] = 0

    #which team got first dragon
    firstdrag = data[(data['teamOne.dragonKills']==1) | (data['teamTwo.dragonKills']==1)]
    if firstdrag.empty:
        teamOne['firstDrag'] = 0
        teamTwo['firstDrag'] = 0
    elif firstdrag['teamOne.dragonKills'].head(1).item() == 0:
        teamOne['firstDrag'] = 0
        teamTwo['firstDrag'] = 1
    else:
        teamOne['firstDrag'] = 1
        teamTwo['firstDrag'] = 0

    #which team got first herald
    firsther = data[data['monsterType']=='riftHerald']['killerTeamUrn']
    if firsther.empty:
        teamOne['firstHerald'] = 0
        teamTwo['firstHerald'] = 0
    elif firsther.head(1).item()  == 'live:lol:riot:team:one':
        teamOne['firstHerald'] = 1
        teamTwo['firstHerald'] = 0
    else:
        teamOne['firstHerald'] = 0
        teamTwo['firstHerald'] = 1

    #which team got first tower
    firsttower = data[(data['buildingType']=='turret')]['buildingTeamUrn']
    if firsttower.empty:
        teamOne['firstTower'] = 0
        teamTwo['firstTower'] = 0
    elif firsttower.head(1).item() == 'live:lol:riot:team:one':
        teamOne['firstTower'] = 0
        teamTwo['firstTower'] = 1
    else:
        teamOne['firstTower'] = 1
        teamTwo['firstTower'] = 0

    #which team got first mid tower (doesn't matter if the actual first tower was the mid tower)
    firstmid = data[(data['buildingType']=='turret') & (data['lane']=='mid') & (data['turretTier']=='outer')]['buildingTeamUrn']
    if firstmid.empty:
        teamOne['firstMid'] = 0
        teamTwo['firstMid'] = 0
    elif firstmid.head(1).item() == 'lie:lol:riot:team:one':
        teamOne['firstMid'] = 0
        teamTwo['firstMid'] = 1
    else:
        teamOne['firstMid'] = 1
        teamTwo['firstMid'] = 0
        
    #clarifying which team is CLG
    #I couldn't find another way to identity which team was which when both team name were 'CLG' (like CLG Academy vs CLG) so I checked the players in each team
    #Finn was our Top laner in Academy at the time, please change this to another player
    if any("Finn" in x for x in teamOne['summonerName'].head(5)):
        CLG = teamOne.copy()
        team2 = teamTwo.copy()
    else:
        CLG = teamTwo.copy()
        team2 = teamOne.copy()
        
    return CLG, team2

def objectives_academy(data, teamOne, teamTwo):
    '''
    Had to create a different function for CLG Academy because the global database and roster was whack for Amateur teams
    Input:
        data: rawdata dataframe from json_to_df function
        teamOne: teamOne dataframe from get_team_data function
        teamTwo: teamTwo dataframe from get_team_data function
    Output: 
        CLG: cleaned dataframe for whichever team is CLG
        team2: cleaned dataframe for opponent team
    '''
     #which team got first blood
    firstblood= data['victimTeamUrn'].dropna()
    if firstblood.empty:
        teamOne['firstBlood'] = 0
        teamTwo['firstBlood'] = 0
    elif firstblood.head(1).item() == 'live:lol:riot:team:one':
        teamOne['firstBlood'] = 0
        teamTwo['firstBlood'] = 1
    else:
        teamOne['firstBlood'] = 1
        teamTwo['firstBlood'] = 0

    #which team got first dragon
    firstdrag = data[(data['teamOne.dragonKills']==1) | (data['teamTwo.dragonKills']==1)]
    if firstdrag.empty:
        teamOne['firstDrag'] = 0
        teamTwo['firstDrag'] = 0
    elif firstdrag['teamOne.dragonKills'].head(1).item() == 0:
        teamOne['firstDrag'] = 0
        teamTwo['firstDrag'] = 1
    else:
        teamOne['firstDrag'] = 1
        teamTwo['firstDrag'] = 0

    #which team got first herald
    firsther = data[data['monsterType']=='riftHerald']['killerTeamUrn']
    if firsther.empty:
        teamOne['firstHerald'] = 0
        teamTwo['firstHerald'] = 0
    elif firsther.head(1).item()  == 'live:lol:riot:team:one':
        teamOne['firstHerald'] = 1
        teamTwo['firstHerald'] = 0
    else:
        teamOne['firstHerald'] = 0
        teamTwo['firstHerald'] = 1

    #which team got first tower
    firsttower = data[(data['buildingType']=='turret')]['buildingTeamUrn']
    if firsttower.empty:
        teamOne['firstTower'] = 0
        teamTwo['firstTower'] = 0
    elif firsttower.head(1).item() == 'live:lol:riot:team:one':
        teamOne['firstTower'] = 0
        teamTwo['firstTower'] = 1
    else:
        teamOne['firstTower'] = 1
        teamTwo['firstTower'] = 0

    #which team got first mid tower (doesn't matter if the actual first tower was the mid tower)
    firstmid = data[(data['buildingType']=='turret') & (data['lane']=='mid') & (data['turretTier']=='outer')]['buildingTeamUrn']
    if firstmid.empty:
        teamOne['firstMid'] = 0
        teamTwo['firstMid'] = 0
    elif firstmid.head(1).item() == 'lie:lol:riot:team:one':
        teamOne['firstMid'] = 0
        teamTwo['firstMid'] = 1
    else:
        teamOne['firstMid'] = 1
        teamTwo['firstMid'] = 0

    #clarifying which team is CLG
    #I couldn't find another way to identity which team was which when both team name were 'CLG' (like CLG Academy vs CLG) so I checked the players in each team
    #Thien was our Top laner in Academy at the time, please change this to another player
    if any("Thien" in x for x in teamOne['summonerName'].head(5)):
        CLG = teamOne.copy()
        team2 = teamTwo.copy()
    else:
        CLG = teamTwo.copy()
        team2 = teamOne.copy()

    return CLG, team2

def final_output(teamOne, teamTwo):
    '''
    Input: 
        teamOne: CLG dataframe from objectives function
        teamTwo: team2 dataframe from objectives function
    Output:
        final_df: cleaned dataframe with all stats needed
    '''
    #Get timestamp for 10 minutes
    ten = check_time(teamOne, 10)
    #Get CSD stats for each lane at 10 minutes
    csd10top = get_cs(teamOne, ten, 'Top') - get_cs(teamTwo, ten, 'Top')
    csd10jg =  get_cs(teamOne, ten, 'Jungle') - get_cs(teamTwo, ten, 'Jungle')
    csd10mid = get_cs(teamOne, ten, 'Mid') - get_cs(teamTwo, ten, 'Mid')
    csd10bot = get_cs(teamOne, ten, 'Bot') - get_cs(teamTwo, ten, 'Bot')
    csd10sup = get_cs(teamOne, ten, 'Support') - get_cs(teamTwo, ten, 'Support')
    #Get GD stats for each lane at 10 minutes
    gd10top = get_g(teamOne, ten, 'Top') - get_g(teamTwo, ten, 'Top')
    gd10jg =  get_g(teamOne, ten, 'Jungle') - get_g(teamTwo, ten, 'Jungle')
    gd10mid = get_g(teamOne, ten, 'Mid') - get_g(teamTwo, ten, 'Mid')
    gd10bot = get_g(teamOne, ten, 'Bot') - get_g(teamTwo, ten, 'Bot')
    gd10sup = get_g(teamOne, ten, 'Support') - get_g(teamTwo, ten, 'Support')
    #Get XPD stats for each lane at 10 minutes
    xpd10top = get_xp(teamOne, ten, 'Top') - get_xp(teamTwo, ten, 'Top')
    xpd10jg =  get_xp(teamOne, ten, 'Jungle') - get_xp(teamTwo, ten, 'Jungle')
    xpd10mid = get_xp(teamOne, ten, 'Mid') - get_xp(teamTwo, ten, 'Mid')
    xpd10bot = get_xp(teamOne, ten, 'Bot') - get_xp(teamTwo, ten, 'Bot')
    xpd10sup = get_xp(teamOne, ten, 'Support') - get_xp(teamTwo, ten, 'Support')
    
    #Get timestamp for 15 minutes
    fifteen = check_time(teamOne, 15)
    #Get CSD stats for each lane at 15 minutes
    csd15top = get_cs(teamOne, fifteen, 'Top') - get_cs(teamTwo, fifteen, 'Top')
    csd15jg =  get_cs(teamOne, fifteen, 'Jungle') - get_cs(teamTwo, fifteen, 'Jungle')
    csd15mid = get_cs(teamOne, fifteen, 'Mid') - get_cs(teamTwo, fifteen, 'Mid')
    csd15bot = get_cs(teamOne, fifteen, 'Bot') - get_cs(teamTwo, fifteen, 'Bot')
    csd15sup = get_cs(teamOne, fifteen, 'Support') - get_cs(teamTwo, fifteen, 'Support')
    #Get GD stats for team at 15 minutes
    gd15 = get_team_g(teamOne,fifteen) - get_team_g(teamTwo,fifteen)
    #Get XPD stats for each lane at 15 minutes
    xpd15top = get_xp(teamOne, fifteen, 'Top') - get_xp(teamTwo, fifteen, 'Top')
    xpd15jg =  get_xp(teamOne, fifteen, 'Jungle') - get_xp(teamTwo, fifteen, 'Jungle')
    xpd15mid = get_xp(teamOne, fifteen, 'Mid') - get_xp(teamTwo, fifteen, 'Mid')
    xpd15bot = get_xp(teamOne, fifteen, 'Bot') - get_xp(teamTwo, fifteen, 'Bot')
    xpd15sup = get_xp(teamOne, fifteen, 'Support') - get_xp(teamTwo, fifteen, 'Support')
    
    #Get timestamp for 20 minutes
    twenty = check_time(teamOne, 20)
    #Get GD stats for team at 20 minutes
    gd20 = get_team_g(teamOne, twenty) - get_team_g(teamTwo, twenty)
    
    #create final output dataframe
    final_df = pd.DataFrame({
        'Date': teamOne['date'].head(1).item(),
        'Win': teamOne['winningTeam'].head(1).item(),
        'Team': teamTwo['Team'].head(1).item(),
        'First Blood': teamOne['firstBlood'].head(1).item(),
        'First Drag': teamOne['firstDrag'].head(1).item(),
        'First Herald': teamOne['firstHerald'].head(1).item(),
        'First Tower': teamOne['firstTower'].head(1).item(),
        'Mid Tower': teamOne['firstMid'].head(1).item(),
        
        'CSD@10 Top': [csd10top],
        'CSD@10 Jg': [csd10jg],
        'CSD@10 Mid': [csd10mid],
        'CSD@10 AD': [csd10bot],
        'CSD@10 Sup': [csd10sup],
        'GD@10 Top': [gd10top],
        'GD@10 Jg': [gd10jg],
        'GD@10 Mid': [gd10mid],
        'GD@10 AD': [gd10bot],
        'GD@10 Sup': [gd10sup],
        'XPD@10 Top': [xpd10top],
        'XPD@10 Jg': [xpd10jg],
        'XPD@10 Mid': [xpd10mid],
        'XPD@10 AD': [xpd10bot],
        'XPD@10 Sup': [xpd10sup],
        
        'CSD@15 Top': [csd15top],
        'CSD@15 Jg': [csd15jg],
        'CSD@15 Mid': [csd15mid],
        'CSD@15 AD': [csd15bot],
        'CSD@15 Sup': [csd15sup],
        
        'XPD@15 Top': [xpd15top],
        'XPD@15 Jg': [xpd15jg],
        'XPD@15 Mid': [xpd15mid],
        'XPD@15 AD': [xpd15bot],
        'XPD@15 Sup': [xpd15sup],

        'GD@15 Team': [gd15],
        'GD@20 Team': [gd20]
        })
    
    return final_df                                     

def final_output_academy(teamOne, teamTwo):
    '''
    Had to create a different function for Academy because they wanted different stats
    Input: 
        teamOne: CLG dataframe from objectives function
        teamTwo: team2 dataframe from objectives function
    Output:
        final_df: cleaned dataframe with all stats needed
    '''
        
    #Get timestamp for 10 minute
    ten = check_time(teamOne, 10)
    #Get CSD stats for each lane at 10 minutes
    csd10top = get_cs(teamOne, ten, 'Top') - get_cs(teamTwo, ten, 'Top')
    csd10jg =  get_cs(teamOne, ten, 'Jungle') - get_cs(teamTwo, ten, 'Jungle')
    csd10mid = get_cs(teamOne, ten, 'Mid') - get_cs(teamTwo, ten, 'Mid')
    csd10bot = get_cs(teamOne, ten, 'Bot') - get_cs(teamTwo, ten, 'Bot')
    csd10sup = get_cs(teamOne, ten, 'Support') - get_cs(teamTwo, ten, 'Support')
    #Get GD stats for each lane at 10 minutes
    gd10top = get_g(teamOne, ten, 'Top') - get_g(teamTwo, ten, 'Top')
    gd10jg =  get_g(teamOne, ten, 'Jungle') - get_g(teamTwo, ten, 'Jungle')
    gd10mid = get_g(teamOne, ten, 'Mid') - get_g(teamTwo, ten, 'Mid')
    gd10bot = get_g(teamOne, ten, 'Bot') - get_g(teamTwo, ten, 'Bot')
    gd10sup = get_g(teamOne, ten, 'Support') - get_g(teamTwo, ten, 'Support')
    #Get XPD stats for each lane at 10 minutes
    xpd10top = get_xp(teamOne, ten, 'Top') - get_xp(teamTwo, ten, 'Top')
    xpd10jg =  get_xp(teamOne, ten, 'Jungle') - get_xp(teamTwo, ten, 'Jungle')
    xpd10mid = get_xp(teamOne, ten, 'Mid') - get_xp(teamTwo, ten, 'Mid')
    xpd10bot = get_xp(teamOne, ten, 'Bot') - get_xp(teamTwo, ten, 'Bot')
    xpd10sup = get_xp(teamOne, ten, 'Support') - get_xp(teamTwo, ten, 'Support')\
    
    #Get timestamp for 15 minutes
    fifteen = check_time(teamOne, 15)
    #Get CSD stats for each lane at 15 minutes
    csd15top = get_cs(teamOne, fifteen, 'Top') - get_cs(teamTwo, fifteen, 'Top')
    csd15jg =  get_cs(teamOne, fifteen, 'Jungle') - get_cs(teamTwo, fifteen, 'Jungle')
    csd15mid = get_cs(teamOne, fifteen, 'Mid') - get_cs(teamTwo, fifteen, 'Mid')
    csd15bot = get_cs(teamOne, fifteen, 'Bot') - get_cs(teamTwo, fifteen, 'Bot')
    csd15sup = get_cs(teamOne, fifteen, 'Support') - get_cs(teamTwo, fifteen, 'Support')\
    #Get GD stats for each lane at 15 minutes
    gd15top = get_g(teamOne, fifteen, 'Top') - get_g(teamTwo, fifteen, 'Top')
    gd15jg =  get_g(teamOne, fifteen, 'Jungle') - get_g(teamTwo, fifteen, 'Jungle')
    gd15mid = get_g(teamOne, fifteen, 'Mid') - get_g(teamTwo, fifteen, 'Mid')
    gd15bot = get_g(teamOne, fifteen, 'Bot') - get_g(teamTwo, fifteen, 'Bot')
    gd15sup = get_g(teamOne, fifteen, 'Support') - get_g(teamTwo, fifteen, 'Support')
    #Get XPD stats for each lane at 15 minutes
    xpd15top = get_xp(teamOne, fifteen, 'Top') - get_xp(teamTwo, fifteen, 'Top')
    xpd15jg =  get_xp(teamOne, fifteen, 'Jungle') - get_xp(teamTwo, fifteen, 'Jungle')
    xpd15mid = get_xp(teamOne, fifteen, 'Mid') - get_xp(teamTwo, fifteen, 'Mid')
    xpd15bot = get_xp(teamOne, fifteen, 'Bot') - get_xp(teamTwo, fifteen, 'Bot')
    xpd15sup = get_xp(teamOne, fifteen, 'Support') - get_xp(teamTwo, fifteen, 'Support')
    
    #Create final dataframe to output
    final_df = pd.DataFrame({
        'Date': teamOne['date'].head(1).item(),
        'Team': teamTwo['Team_name'].head(1).item(),
        'First Blood': teamOne['firstBlood'].head(1).item(),
        'First Drag': teamOne['firstDrag'].head(1).item(),
        'First Herald': teamOne['firstHerald'].head(1).item(),
        'First Tower': teamOne['firstTower'].head(1).item(),
        'Mid Tower': teamOne['firstMid'].head(1).item(),
        
        'CSD@10 Top': [csd10top],
        'CSD@10 Jg': [csd10jg],
        'CSD@10 Mid': [csd10mid],
        'CSD@10 AD': [csd10bot],
        'CSD@10 Sup': [csd10sup],
        'GD@10 Top': [gd10top],
        'GD@10 Jg': [gd10jg],
        'GD@10 Mid': [gd10mid],
        'GD@10 AD': [gd10bot],
        'GD@10 Sup': [gd10sup],
        'XPD@10 Top': [xpd10top],
        'XPD@10 Jg': [xpd10jg],
        'XPD@10 Mid': [xpd10mid],
        'XPD@10 AD': [xpd10bot],
        'XPD@10 Sup': [xpd10sup],
        
        'CSD@15 Top': [csd15top],
        'CSD@15 Jg': [csd15jg],
        'CSD@15 Mid': [csd15mid],
        'CSD@15 AD': [csd15bot],
        'CSD@15 Sup': [csd15sup],
        'GD@15 Top': [gd15top],
        'GD@15 Jg': [gd15jg],
        'GD@15 Mid': [gd15mid],
        'GD@15 AD': [gd15bot],
        'GD@15 Sup': [gd15sup],
        'XPD@15 Top': [xpd15top],
        'XPD@15 Jg': [xpd15jg],
        'XPD@15 Mid': [xpd15mid],
        'XPD@15 AD': [xpd15bot],
        'XPD@15 Sup': [xpd15sup]
        })
    
    return final_df

def scrim_automater(json_dir):
    '''
    Runs all functions
    '''
    rawdata = json_to_df(json_dir)
    teamOne, teamTwo = get_team_data(rawdata)
    final = final_output(teamOne, teamTwo)
    return final

def scrim_automater_academy(json_dir):
    '''
    Runs all functions. Had to create a separate function for academy
    '''
    rawdata = json_to_df(json_dir)
    CLG, team2 = get_team_data_academy(rawdata)
    final = final_output_academy(CLG, team2)
    return final

#Change directory to match what game file you want to convert
#output = scrim_automater('\\Users\\...')
output = scrim_automater_academy('\\Users\\cheah\\Documents\\CLG\\8-8_CLGavsDig_1')

#Save output to a .csv file to put into spreadsheet
output.to_csv('8-8_CLGavsDig_1.csv')