from flask import Flask, flash, redirect, render_template, request, session 
import requests
from cs50 import SQL
from functools import wraps
import config
from re import findall

db = config.db

def login_required(f):
    """
    Decorate routes to require login.

    https://flask.palletsprojects.com/en/1.1.x/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("userid") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function

def get_current_weather(cityid):

    lat = db.execute("SELECT lat FROM cities WHERE id = ?", cityid)[0]['lat']
    lon = db.execute("SELECT lon FROM cities WHERE id = ?", cityid)[0]['lon']

    #"exclude" can change data called on api, see openweathermap documentation
    url = "https://api.open-meteo.com/v1/forecast?latitude="+str(lat)+"&longitude="+str(lon)+"&hourly=temperature_2m,apparent_temperature,precipitation,weathercode&temperature_unit=fahrenheit&windspeed_unit=mph&precipitation_unit=inch&timezone=America%2FNew_York&past_days=0"

    response = requests.get(url)
    weatherdict = response.json()

    return(weatherdict)

def message(message, errorval):
    """Render message to user."""
    # errorval = 1 includes back button 
    # 0 for no button
    return render_template("message.html", message=message, errorval = errorval)

def namecheck(city): #verifies city name is in database
    namecheck = db.execute("SELECT count(*) FROM cities WHERE city_state = ?", city)[0]['count(*)']
    return(namecheck)

def citycheck(city): #converts city name to cityID
    cityid = db.execute("SELECT id FROM cities WHERE city_state = ?", city)[0]['id']
    return(cityid)

def getusersleaguenames(userid): #outputs dict of leaguenames for given userID
    leagueids = db.execute ("SELECT leagueid FROM leaguemembers WHERE userid = ?", userid)

    #convert league IDS to league names
    counter = 0
    leaguenames = []
    for row in leagueids:
        leagueid = leagueids[counter]['leagueid']
        leaguename = db.execute("SELECT leaguename FROM leagues WHERE id = ?", leagueid)[0]['leaguename']
        leaguenames.append({'leaguename' : leaguename})
        counter += 1

    return(leaguenames)

def getusersteamnames(userid): #outputs dict of teamnames for given userID
    teamnames = db.execute("SELECT teamname FROM teams WHERE userid = ?", userid)
    return(teamnames)

def getusersleagueteamdicts(userid): #outputs dict of leaguename/leagueID/teamname for given userID
    leagueidsdict = db.execute('SELECT leagueid FROM leaguemembers WHERE userid = (?)', userid)
    leagueids = []

    #generate list of leagueids for user:
    counter = 0
    for row in leagueidsdict:
        temp = leagueidsdict[counter]
        leagueidtemp = temp["leagueid"]
        leagueids.append(leagueidtemp)
        counter += 1
    
    #convert ids to leaguenames:
    usersleagueteamdict = []
    counter = 0
    for id in leagueids:
        leaguename = db.execute("SELECT leaguename FROM leagues WHERE id = (?)", leagueids[counter])[0]["leaguename"]
        teamid = db.execute("SELECT teamid FROM leaguemembers WHERE userid = (?) AND leagueid = (?)", userid, leagueids[counter])[0]['teamid']
        teamname = db.execute("SELECT teamname FROM teams WHERE id = (?)", teamid)[0]['teamname']
        usersleagueteamdict.append({'leaguename' : leaguename, 'leagueid' : leagueids[counter], 'teamname': teamname})
        counter += 1
    
    return(usersleagueteamdict)

def getleagueinfo(leagueid): #outputs dict with teamname/username pairs for given leagueID
    teamsdict = db.execute("SELECT teamid FROM leaguemembers WHERE leagueid = (?)", leagueid)
    
   
    #loop through dict of team IDS and generate list of teams & owners
    counter = 0
    leaguelist = []
    for row in teamsdict:
        teamname = (db.execute("SELECT teamname FROM teams WHERE id = (?)", teamsdict[counter]["teamid"])[0]['teamname'])
        useridtemp = db.execute("SELECT userid FROM teams WHERE id = (?)", teamsdict[counter]["teamid"])[0]['userid']
        username = db.execute("SELECT username FROM users WHERE id = (?)", useridtemp)[0]['username']
        counter += 1
        leaguelist.append({'teamname' : teamname, 'username' : username})

   
    return(leaguelist)

def getteamcitiesweather(teamid): #outputs dict with city_state names and current weather info for those cities
    citiesdict = db.execute("SELECT cityid FROM teamcities WHERE teamid = (?)", teamid)

    #loop through dict of city IDS and generate list of cities
    counter = 0
    citylist = []
    for row in citiesdict:
        cityid = citiesdict[counter]['cityid']
        cityname = db.execute("SELECT city_state FROM cities WHERE id = (?)", cityid)[0]['city_state']
        
        # query API for weather info and add to citylist
        weathertemp = get_current_weather(cityid)

        temperature = weathertemp['hourly']['temperature_2m'][0]
        feelslike = weathertemp['hourly']['apparent_temperature'][0]
        weathercode = weathertemp['hourly']['weathercode'][0]
        weatherdesc = db.execute("SELECT description FROM weathercodes WHERE code = ?", weathercode)[0]['description']

        citylist.append({'cityname' : cityname, 'temperature' : temperature, 'feelslike' : feelslike, 'weatherdesc' : weatherdesc})
        counter += 1
    
    return(citylist)

def getteamsleagueinfo(teamid): #outputs dict of leaguenames for a given teamid
    leagueids = db.execute("SELECT leagueid FROM leaguemembers WHERE teamid = ?", teamid)
    print(leagueids)
    counter = 0
    leaguenames = []
    for row in leagueids:
        leaguename = db.execute("SELECT leaguename FROM leagues WHERE id = ?", leagueids[counter]['leagueid'])[0]['leaguename']
        leaguenames.append({'leaguename' : leaguename})
        counter += 1
    
    print(leaguenames)
    
    return(leaguenames)

def decodecatcode(catcode):
    pcode = findall("\d+", catcode)

    pname = db.execute("SELECT description FROM param_codes WHERE pcode = ?", pcode)[0]['description']

    type = 'type'
    MorL = 'MorL'
    TorC = 'TorC'

    catname = 'catname'

    if "T" in catcode:
        TorC = " as a team"
    elif "C" in catcode:
        TorC = " for a single city"

    

    if "R" in catcode:
        if "M" in catcode:
            catname = "Highest " + pname + TorC
        elif "L" in catcode:
            catname = "Lowest " + pname + TorC
    
    if "P" in catcode:
        if "M" in catcode:
            catname = "Furthest " + pname + " from prediction" + TorC
        elif "L" in catcode:
            catname = "Closest " + pname + " to prediction" + TorC
    
    if "A" in catcode:
        if "M" in catcode:
            catname = "Furthest " + pname + " from 20 year average" + TorC
        elif "L" in catcode:
            catname = "Closest " + pname + " to 20 year average" + TorC

    return(catname) 

 