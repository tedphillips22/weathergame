import gamefunctions as gf
import getweatherdata as gwd
from cs50 import SQL
from datetime import datetime

db = SQL("sqlite:///weather.db")

def getrosteredpredictions():
    now = datetime.now()
    
    if now.weekday() != 6:
        return()

    rosteredcityids = []

    rawrosteredcities = db.execute("SELECT cityid FROM teamcities")
    for x in rawrosteredcities:
        cid = x['cityid']
        if cid in rosteredcityids:
            continue
        else:
            rosteredcityids.append(cid)

    allpcodes = db.execute("SELECT pcode FROM param_codes")

    for cityid in rosteredcityids:
        weatherdict = gwd.getpredictiondict(cityid)
        for p in allpcodes:
            pcode = p['pcode']
            print("Getting prediction:", cityid, pcode)
            gwd.readpredictiondict(cityid, pcode, weatherdict)
    
    return()


def getcatlist(weekid):
    catlist = []
    
    cat1 = db.execute("SELECT Cat1 FROM weeks WHERE weekid = ?", weekid)[0]['Cat1']
    catlist.append(cat1)

    cat2 = db.execute("SELECT Cat2 FROM weeks WHERE weekid = ?", weekid)[0]['Cat2']
    catlist.append(cat2)

    cat3 = db.execute("SELECT Cat3 FROM weeks WHERE weekid = ?", weekid)[0]['Cat3']
    catlist.append(cat3)

    cat4 = db.execute("SELECT Cat4 FROM weeks WHERE weekid = ?", weekid)[0]['Cat4']
    catlist.append(cat4)

    cat5 = db.execute("SELECT Cat5 FROM weeks WHERE weekid = ?", weekid)[0]['Cat5']
    catlist.append(cat5)


    print(catlist)

def runleaguematchups(week, catlist):
    #Fetch active league IDS
    leagueids = db.execute("SELECT id FROM leagues WHERE active = 1")

    #Fetch relevant matchups
    matchups = []
    for league in leagueids:
        leagueid = league['id']
        leaguematchups = db.execute("SELECT matchupid, hometeamid, awayteamid FROM schedules WHERE leagueid = ? AND week = ?", leagueid, week)
        for row in leaguematchups:
            matchups.append(row)

    for matchup in matchups:
        team1id = matchup['hometeamid']
        team2id = matchup['awayteamid']
        for catcode in catlist:
            winner = gf.runmatchup(catcode, team1id, team1id)
            db.execute("UPDATE schedules SET winner = ? WHERE week = ? AND hometeamid = ? AND awayteamid = ?", winner, week, team1id, team2id)

    
        
    
    #Run each matchup

    return()


