from datetime import date, timedelta
from re import findall
from cs50 import SQL
from getweatherdata import getaverage, getmeasurement
import random
import config

db = config.db

def runmatchup(catcode, team1id, team2id):

    getmatchupdata(catcode, team1id, team2id)
    if "T" in catcode:
        packageTdata(catcode, team1id, team2id)
        scoreTmatchup(catcode, team1id, team2id)
    if "C" in catcode:
        packageCdata(catcode, team1id, team2id)
        scoreCmatchup(catcode, team1id, team2id)

def getmatchupdata(catcode, team1id, team2id): #accepts a category code and two team IDs and fetches/stores appropriate data 
    #make list of cityids
    team1cities = db.execute("SELECT cityid FROM teamcities WHERE teamid = ?", team1id)
    team2cities = db.execute("SELECT cityid FROM teamcities WHERE teamid = ?", team2id)

    #find weather parameter in catcode
    pcode = findall("\d+", catcode) #pulls out numeric characters

    today = date.today()
    

    #get relevent weather data based on cat code and store in appropriate table

    if "A" in catcode:
        
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
    if "R" or "P" in catcode: 
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
    
    return()


def packageTdata(catcode, team1id, team2id): #returns measurement data and relevant comparison data based on catcode and two team IDs (requires running getmatchupdata first)
    today = date.today()
    weekago = today + timedelta(days=-7)

    #make list of cityids
    team1cities = db.execute("SELECT cityid FROM teamcities WHERE teamid = ?", team1id)
    team2cities = db.execute("SELECT cityid FROM teamcities WHERE teamid = ?", team2id)

    #find weather parameter in catcode
    pcode = findall("\d+", catcode) #pulls out numeric characters 

    team1rawsum = 0
    team2rawsum = 0
    team1compsum = 0 #comparison sum
    team2compsum = 0

    for y in range(0,7):
        xdate = today - timedelta(days = y + 1)
        for x in team1cities:
            cityid = x['cityid']
            cityval = db.execute("SELECT paramtervalue FROM measurements WHERE parameterid = ? AND cityid = ? AND date = ?", pcode, cityid, xdate)
            team1rawsum += cityval
        for x in team2cities:
            cityid = x['cityid']
            cityval = db.execute("SELECT paramtervalue FROM measurements WHERE parameterid = ? AND cityid = ? AND date = ?", pcode, cityid, xdate)
            team2rawsum += cityval
        if "P" in catcode:
            for x in team1cities:
                cityid = x['cityid']
                cityval = db.execute("SELECT paramtervalue FROM predictions WHERE parameterid = ? AND cityid = ? AND date = ?", pcode, cityid, xdate)
                team1compsum += cityval
            for x in team2cities:
                cityid = x['cityid']
                cityval = db.execute("SELECT paramtervalue FROM predictions WHERE parameterid = ? AND cityid = ? AND date = ?", pcode, cityid, xdate)
                team2compsum += cityval
    if "A" in catcode:
        for x in team1cities:
            cityid = x['cityid']
            cityval = db.execute("SELECT paramtervalue FROM averages WHERE parameterid = ? AND cityid = ? AND date = ?", pcode, cityid, today)
            team1rawsum += 7 * cityval #only 1 average value per week per city, so multiply by 7 to normalize
        for x in team2cities:
            cityid = x['cityid']
            cityval = db.execute("SELECT paramtervalue FROM averages WHERE parameterid = ? AND cityid = ? AND date = ?", pcode, cityid, today)
            team2rawsum += 7 * cityval 

    return(team1rawsum, team1compsum, team2rawsum, team2compsum)


def packageCdata(catcode, team1id, team2id):
    today = date.today()
    weekago = today + timedelta(days=-7)

    #make list of cityids
    team1cities = db.execute("SELECT cityid FROM teamcities WHERE teamid = ?", team1id)
    team2cities = db.execute("SELECT cityid FROM teamcities WHERE teamid = ?", team2id)

    #find weather parameter in catcode
    pcode = findall("\d+", catcode) #pulls out numeric characters 

    team1rawsums = []
    team2rawsums = []
    team1compsums = []
    team2compsums = []

    for y in range(0,7):
        xdate = today - timedelta(days = y + 1)
        for x in team1cities:
            cityid = x['cityid']
            cityval = db.execute("SELECT paramtervalue FROM measurements WHERE parameterid = ? AND cityid = ? AND date = ?", pcode, cityid, xdate)
            team1rawsums.append({'cityid': cityid, 'val':cityval})
        for x in team2cities:
            cityid = x['cityid']
            cityval = db.execute("SELECT paramtervalue FROM measurements WHERE parameterid = ? AND cityid = ? AND date = ?", pcode, cityid, xdate)
            team2rawsums.append({'cityid': cityid, 'val':cityval})
        if "P" in catcode:
            for x in team1cities:
                cityid = x['cityid']
                cityval = db.execute("SELECT paramtervalue FROM predictions WHERE parameterid = ? AND cityid = ? AND date = ?", pcode, cityid, xdate)
                team1compsums.append({'cityid': cityid, 'val':cityval})
            for x in team2cities:
                cityid = x['cityid']
                cityval = db.execute("SELECT paramtervalue FROM predictions WHERE parameterid = ? AND cityid = ? AND date = ?", pcode, cityid, xdate)
                team2compsums.append({'cityid': cityid, 'val':cityval})
    if "A" in catcode:
        for x in team1cities:
            cityid = x['cityid']
            cityval = db.execute("SELECT paramtervalue FROM averages WHERE parameterid = ? AND cityid = ? AND date = ?", pcode, cityid, today)
            team1rawsums.append({'cityid': cityid, 'val':(cityval * 7)}) #only 1 average value per week per city, so multiply by 7 to normalize
        for x in team2cities:
            cityid = x['cityid']
            cityval = db.execute("SELECT paramtervalue FROM averages WHERE parameterid = ? AND cityid = ? AND date = ?", pcode, cityid, today)
            team2rawsums.append({'cityid': cityid, 'val':(cityval * 7)}) 

    return(team1rawsums, team1compsums, team2rawsums, team2compsums)

def scoreTmatchup (catcode, team1id, team2id, team1rawsum, team1compsum, team2rawsum, team2compsum):
    #check for bye week
    if team1id == 0:
        return(team2id)
    elif team2id == 0:
        return(team1id)
        
    team1diff = abs(team1compsum - team1rawsum)
    team2diff = abs(team2compsum - team2rawsum)

    if "R" in catcode:
        rawdiff = team1rawsum - team2rawsum
        if "L" in catcode:
            rawdiff = -rawdiff
        if rawdiff > 0:
            return(team1id)
        elif rawdiff < 0:
            return(team2id)
        else: 
            return("tie")
    else:
        diffdiff = team1diff - team2diff
        if "L" in catcode:
            diffdiff = -diffdiff
        if diffdiff > 0:
            return(team1id)
        elif diffdiff < 0:
            return(team2id)
        else: 
            return("tie")

def scoreCmatchup(catcode, team1id, team2id, team1rawsums, team1compsums, team2rawsums, team2compsums):
    #check for bye week
    if team1id == 0:
        return(team2id)
    elif team2id == 0:
        return(team1id)

    #make list of cityids
    team1cities = db.execute("SELECT cityid FROM teamcities WHERE teamid = ?", team1id)
    team2cities = db.execute("SELECT cityid FROM teamcities WHERE teamid = ?", team2id)

    cityvals = []
    cityvals = []

    for x in range (0,3):
        xraw = team1rawsums[x]['val']
        xcomp = team1compsums[x]['val']
        xid = team1rawsums[x]['cityid']
        xdiff = abs(xraw - xcomp)
        cityvals.append({'cityid':xid, 'diff':xdiff})

        xraw = team2rawsums[x]['val']
        xcomp = team2compsums[x]['val']
        xid = team2rawsums[x]['cityid']
        xdiff = abs(xraw - xcomp)
        cityvals.append({'cityid':xid, 'diff':xdiff})

    tempwinv = -10000000
    tempwinid = 0

    for x in cityvals:
        v = x['diff']
        if "L" in catcode:
            v = -v
        if v > tempwinv:
            tempwinv = v
            tempwinid = x['cityid']
    
    if {'cityid':tempwinid} in team1cities:
        return(team1id)
    elif {'cityid':tempwinid} in team2cities:
        return(team2id)
    else:
        return("ERROR in scoreCmatchup")





    
        

