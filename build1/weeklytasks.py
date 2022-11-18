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

    for city in rosteredcityids:
        cityid = city['cityid']
        for p in allpcodes:
            pcode = p['pcode']
            gwd.getprediction(cityid, pcode)