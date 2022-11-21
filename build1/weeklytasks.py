import gamefunctions as gf
import getweatherdata as gwd
from cs50 import SQL

db = SQL("sqlite:///weather.db")

def getrosteredpredictions():
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


# def runleaguematchups(cat1, cat2, cat3, cat4, cat5):
#     leagueids = db.execute("SELECT id FROM leagues")

#     for x in leagueids:
#         leagueid = x['id']
#         members = db.execute("SELECT teamid FROM leaguemembers WHERE leagueid = ?", leagueid)


#     return()


