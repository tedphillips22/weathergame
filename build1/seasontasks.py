import gamefunctions as gf
import random
from cs50 import SQL
from datetime import date
import config
import math

db = config.db

#Clear out schedule table

#Clear out weather data

#Define weekly categories
    #Currently, manually create weeks category in google sheets and upload to db via csv

#Set week0 manually
week0 = date(2022, 12, 11) 

def main():
    setallmatchups()
    return()

def getweeknum():
    today = date.today()
    weeknum = math.floor((today - week0).days / 7)
    return(weeknum)


#Make the matchup schedule


def makeschedule(leagueid):
    teamsdict = db.execute("SELECT teamid FROM leaguemembers WHERE leagueid = ?", leagueid)
    
    teams = []
    

    for row in teamsdict:
        team = row['teamid']
        teams.append(team)
    
    if (len(teams) % 2) != 0:
        teams.append('None')

    pairs = [(i, j) for i in teams for j in teams if i != j]
    random.shuffle(pairs)

    numWeeks = len(teams) - 1
    numPairs = len(teams)//2
    matchUps = {}
    for week in range(numWeeks):
        matchUps[f'Week {week}'] = []
        for _ in range(numPairs):
            for pair in pairs:
                if pair[0] not in [team for match in matchUps[f'Week {week}'] for team in match]:
                    if pair[1] not in [team for match in matchUps[f'Week {week}'] for team in match]:
                        if pair not in [match for w in range(week) for match in matchUps[f'Week {w}']] and (pair[1], pair[0]) not in [match for w in range(week) for match in matchUps[f'Week {w}']]:
                            break
            matchUps[f'Week {week}'].append(pair)

    

    for wweek in matchUps:
        week = [int(s) for s in wweek.split() if s.isdigit()][0]
        for matchup in matchUps[f'Week {week}']:
            hometeamid = matchup[0]
            if hometeamid == 'None':
                hometeamid = 0
            awayteamid = matchup[1]
            if awayteamid == 'None':
                awayteamid = 0
            
            db.execute("INSERT INTO matchups (leagueid, week, hometeamid, awayteamid) VALUES (?,?,?,?)", leagueid, week, hometeamid, awayteamid)
    
    return()

def setallmatchups():
    #Fetch active league IDS
    leagueids = db.execute("SELECT id FROM leagues WHERE active = 1")

    for league in leagueids:
        leagueid = league['id']
        makeschedule(leagueid)
    return()

main()