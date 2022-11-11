from datetime import date
from re import findall
from cs50 import SQL
from getweatherdata import getaverage, getmeasurement, getprediction


db = SQL("sqlite:///weather.db")

def runcat(catcode, team1id, team2id):
    #make list of cityids
    team1cities = db.execute("SELECT cityid FROM teamcities WHERE teamid = ?", team1id)
    team2cities = db.execute("SELECT cityid FROM teamcities WHERE teamid = ?", team2id)

    #parse catcode
    pcode = findall("\d+", catcode)

    today = date.today()
    

    #get relevent weather data based on cat code

    if "P" in catcode:
        for x in team1cities:
            cityid1 = x['cityid']     #check if data already fetched?
            if db.execute("SELECT count(*) FROM predictions WHERE cityid = ? AND date = ?", cityid1, today)[0]['count(*)'] != 0:
                continue
            getprediction(cityid1, pcode)
            if db.execute("SELECT count(*) FROM measurements WHERE cityid = ? AND date = ?", cityid1, today)[0]['count(*)'] != 0:
                continue            
            getmeasurement(cityid1, pcode)            
        for x in team2cities:
            cityid2 = x['cityid']
            if db.execute("SELECT count(*) FROM predictions WHERE cityid = ? AND date = ?", cityid2, today)[0]['count(*)'] != 0:
                continue
            getprediction(cityid2, pcode)
            if db.execute("SELECT count(*) FROM measurements WHERE cityid = ? AND date = ?", cityid2, today)[0]['count(*)'] != 0:
                continue
            getmeasurement(cityid2, pcode)
    if "A" in catcode:
        print('caught A')
        for x in team1cities:
            cityid1 = x['cityid']
            if db.execute("SELECT count(*) FROM averages WHERE cityid = ? AND date = ?", cityid1, today)[0]['count(*)'] != 0:
                continue               
            getaverage(cityid1, pcode)  
            if db.execute("SELECT count(*) FROM measurements WHERE cityid = ? AND date = ?", cityid1, today)[0]['count(*)'] != 0:
                continue          
            getmeasurement(cityid1, pcode)            
        for x in team2cities:
            cityid2 = x['cityid']
            if db.execute("SELECT count(*) FROM averages WHERE cityid = ? AND date = ?", cityid2, today)[0]['count(*)'] != 0:
                continue
            getaverage(cityid2, pcode)
            if db.execute("SELECT count(*) FROM measurements WHERE cityid = ? AND date = ?", cityid2, today)[0]['count(*)'] != 0:
                continue
            getmeasurement(cityid2, pcode)
    if "R" in catcode:
        for x in team1cities:
            cityid1 = x['cityid']
            if db.execute("SELECT count(*) FROM measurements WHERE cityid = ? AND date = ?", cityid1, today)[0]['count(*)'] != 0:
                continue                             
            getmeasurement(cityid1, pcode)            
        for x in team2cities:
            cityid2 = x['cityid']
            if db.execute("SELECT count(*) FROM measurements WHERE cityid = ? AND date = ?", cityid2, today)[0]['count(*)'] != 0:
                continue
            getmeasurement(cityid2, pcode)

    #make comparisons to determine winner
    #if "T" in catcode:


    
    return()

