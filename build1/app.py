import json
from functools import wraps
import operator

import requests
from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from werkzeug.security import check_password_hash, generate_password_hash
from flask_session import Session
from urllib.parse import unquote
import regex as re

import gamefunctions as g
from helpers import (citycheck, get_current_weather, getleagueinfo,
                     getteamcitiesweather, getteamsleagueinfo,
                     getusersleaguenames, getusersleagueteamdicts,
                     getusersteamnames, login_required, message, namecheck,
                     decodecatcode)
from seasontasks import getweeknum
import config

app = Flask(__name__)

db = config.db

app.config["TEMPLATES_AUTO_RELOAD"] = True

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


########################################################################################
####### PAGE FUNCTIONS #################################################################
########################################################################################


########## Website Functions -- Home page, Login, Logout, Register #################################

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/rainchecker")
@login_required
def rainchecker():
    userid = session["userid"]

    leaguedict = getusersleagueteamdicts(userid)

    teamnames = getusersteamnames(userid)

    return render_template("rainchecker.html", leaguedict = leaguedict, teamnames = teamnames)

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return message("must provide username", 1)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return message("must provide password", 1)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return message("invalid username and/or password", 1)

        # Remember which user has logged in
        session["userid"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/rainchecker")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")

@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")

@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "POST":

        username = request.form.get("username")
        if len(db.execute("SELECT username FROM users WHERE username LIKE ?", username)) != 0:
            return message("Username already exists", 1)

        password = request.form.get("password")
        confirmation = request.form.get("confirmation")
        if password != confirmation:
            return message("Passwords don't match", 1)

        else:
            hash = generate_password_hash(password)
            db.execute("INSERT INTO users (username, hash) VALUES(?, ?)", username, hash)
            return redirect("/")

    else:

        return render_template("register.html")

########## Team and league forms ###############################################################

@app.route("/maketeam", methods = ["POST", "GET"])
@login_required
def maketeam():
    if request.method == "POST":
        
        teamname = request.form.get("teamname")
        
        #Check for duplicate teamname
        if db.execute("SELECT count(*) FROM teams WHERE teamname LIKE ?", teamname)[0]['count(*)'] != 0:
            return message("Team name taken. Please try again.", 1)
        
        userid = session["userid"]
        
        city1 = request.form.get("city1")
        if namecheck(city1) == 0:
            return message("Some cities not found. Please use autocomplete and fill in all the blanks.", 1)
        city1id = citycheck(city1)

        city2 = request.form.get("city2")
        if namecheck(city2) == 0:
            return message("Some cities not found. Please use autocomplete and fill in all the blanks.", 1)
        city2id = citycheck(city2)

        city3 = request.form.get("city3")
        if namecheck(city3) == 0:
            return message("Some cities not found. Please use autocomplete and fill in all the blanks.", 1)
        city3id = citycheck(city3)

        db.execute("INSERT INTO teams (userid, teamname) VALUES (?, ?)", userid, teamname)
        teamid = db.execute("SELECT id FROM teams WHERE teamname = ? AND userid = ?", teamname, userid)[0]['id']
        db.execute("INSERT INTO teamcities (teamid, cityid) VALUES (?, ?)", teamid, city1id)
        db.execute("INSERT INTO teamcities (teamid, cityid) VALUES (?, ?)", teamid, city2id)
        db.execute("INSERT INTO teamcities (teamid, cityid) VALUES (?, ?)", teamid, city3id)

        return message('Team named "{0}" created'.format(teamname), 0)

    else:
        cities = db.execute("SELECT city_state FROM cities")
        return render_template("maketeam.html", cities = cities)
        

@app.route("/makeleague", methods = ["POST", "GET"])
@login_required
def makeleague():
    if request.method == "POST":
        leaguename = request.form.get("leaguename")

        #Check for duplicate league names (currently not working)
        leaguecheck = db.execute("SELECT count(*) FROM leagues WHERE leaguename LIKE (?)", leaguename)[0]['count(*)'] 
        if leaguecheck != 0:
            return message("League name taken. Please try another name.", 1)

        code = request.form.get("code")

        userid = session["userid"]

        db.execute("INSERT INTO leagues (leaguename, founderid, code, active) VALUES (?, ?, ?, ?)", leaguename, userid, code, 1)

        return message('League called "{0}" created'.format(leaguename), 0)


    else:
        return render_template("makeleague.html")

@app.route("/joinleague", methods = ["POST", "GET"])
@login_required
def joinleague():
    if request.method == "POST":
        userid = session["userid"]

        leaguegiven = request.form.get("leaguename")

        #check if leaguename provided by user exists
        leaguecheck = db.execute("SELECT count(*) FROM leagues WHERE leaguename LIKE (?)", leaguegiven)[0]['count(*)']
        
        if leaguecheck == 0:
            return message("League not found", 1)

        leagueid = db.execute("SELECT id FROM leagues WHERE leaguename LIKE (?)", leaguegiven)[0]["id"]

        membercheck = db.execute("SELECT count(*) FROM leaguemembers WHERE userid = (?) AND leagueid = (?)", userid, leagueid)[0]['count(*)']
        if membercheck != 0:
            return message("Can't join a league more than once.", 1)

        #check passcode
        codegiven = request.form.get("code")
        leaguecode = db.execute("SELECT code FROM leagues WHERE leaguename LIKE (?)", leaguegiven)[0]["code"]

        if leaguecode != codegiven:
            return message("Passcode incorrect", 1)

        
        teamname = request.form.get("teamname")
        
        teamiddict = db.execute("SELECT id FROM teams WHERE teamname = (?) AND userid = (?)", teamname, userid)

        

        teamid = teamiddict[0]['id']

        db.execute("INSERT INTO leaguemembers (userid, leagueid, teamid) VALUES (?, ?, ?)", userid, leagueid, teamid)

        return message('Successfully joined league called "{0}".'.format(leaguegiven), 0)
        


    else: 
        userid = session["userid"]
        userteams = db.execute("SELECT teamname FROM teams WHERE userid = (?)", userid)
        if len(userteams) == 0:
            return message("You must create at least one team before joining a league", 1)
        return render_template("joinleague.html", userteams = userteams)


########## Display user, team, and league info ################################################

@app.route("/myleagues")
@login_required
def myleagues():
    userid = session["userid"]

    leaguedict = getusersleagueteamdicts(userid)

    return render_template("myleagues.html", leaguedict = leaguedict)


@app.route("/league/<leaguename>")
@login_required
def leaguepage(leaguename):
    weeknum = getweeknum() 

    print(leaguename)
    leaguename = unquote(leaguename)
    print(leaguename)

    leagueid = db.execute("SELECT id FROM leagues WHERE leaguename LIKE (?)", leaguename)[0]['id']

    lleaguename = db.execute("SELECT leaguename FROM leagues WHERE id = (?)", leagueid)[0]['leaguename']

    leaguelist = getleagueinfo(leagueid)

    matchuplist = db.execute("SELECT hometeamid, awayteamid FROM matchups WHERE leagueid = ? and week = ?", leagueid, weeknum) ##wtf is happening here??? inventing tons of nonexistent matchups
    
    matchups = []

    for row in matchuplist:
        homeid = row['hometeamid']
        awayid = row['awayteamid']
        homename = db.execute("SELECT teamname FROM teams WHERE id = ?", homeid)[0]['teamname']
        awayname = db.execute("SELECT teamname FROM teams WHERE id = ?", awayid)[0]['teamname']
        matchups.append({'home': homename, 'away': awayname})

    

    userid = session["userid"]
    userhomegames = db.execute("SELECT week, awayteamid FROM matchups WHERE leagueid = ? and hometeamid = ?", leagueid, userid)
    userawaygames = db.execute("SELECT week, hometeamid FROM matchups WHERE leagueid = ? and awayteamid = ?", leagueid, userid)

    usermatchups = []

    for row in userhomegames:
        weekid = row['week']
        opponentid = row['awayteamid']
        opponentname = db.execute("SELECT teamname FROM teams WHERE id = ?", opponentid)[0]['teamname']
        usermatchups.append({'week':weekid, 'opponent':opponentname})

    for row in userawaygames:
        weekid = row['week']
        opponentid = row['hometeamid']
        opponentname = db.execute("SELECT teamname FROM teams WHERE id = ?", opponentid)[0]['teamname']
        usermatchups.append({'week':weekid, 'opponent':opponentname})

    usermatchups.sort(key=operator.itemgetter('week'))

    thisweekscats = []

    catstemp = db.execute("SELECT Cat1, Cat2, Cat3, Cat4, Cat5 FROM weeks WHERE weekid = ?", weeknum)[0]

    thisweekscats.append({'catname': decodecatcode(catstemp['Cat1'])})
    thisweekscats.append({'catname': decodecatcode(catstemp['Cat2'])})
    thisweekscats.append({'catname': decodecatcode(catstemp['Cat3'])})
    thisweekscats.append({'catname': decodecatcode(catstemp['Cat4'])})
    thisweekscats.append({'catname': decodecatcode(catstemp['Cat5'])})

    weekname = db.execute("SELECT weekName FROM weeks WHERE weekid = ?", weeknum)[0]['weekName']
    
    resultsraw = db.execute("SELECT hometeamid, awayteamid, winner FROM matchups WHERE leagueid = ? AND week = ?", leagueid, weeknum - 1)
    results = []
    
    if len(resultsraw) != 0:
        for row in resultsraw:
            hometeamname = db.execute("SELECT teamname FROM teams WHERE id = ?", row['hometeamid'])[0]['teamname']
            awayteamname = db.execute("SELECT teamname FROM teams WHERE id = ?", row['awayteamid'])[0]['teamname']
            winnername = db.execute("SELECT teamname FROM teams WHERE id = ?", row['winner'])[0]['teamname']
            results.append({'hometeamname':hometeamname, 'awayteamname':awayteamname, 'winnername':winnername})

    winslosses = []

    for team in leaguelist:
        teamname = team['teamname']
        owner = team['username']
        wincount = 0
        losscount = 0
        if len(results) != 0:
            for row in results:
                if row['hometeamname'] == teamname or row['awayteamname'] == teamname:
                    if row['winnername'] == teamname:
                        wincount += 1
                    else:
                        losscount += 1
                else:
                    continue
        winslosses.append({'teamname':teamname, 'owner':owner, 'wins': wincount, 'losses': losscount})

    return render_template("league.html", winslosses = winslosses, results = results, thisweekscats = thisweekscats, weekname = weekname, lleaguename = lleaguename, usermatchups = usermatchups, leaguelist = leaguelist, matchups = matchups)


@app.route("/team/<teamname>")
@login_required
def teampage(teamname):
    teamid = db.execute("SELECT id FROM teams WHERE teamname LIKE (?)", teamname)[0]['id']

    tteamname = db.execute("SELECT teamname FROM teams WHERE id = (?)", teamid)[0]['teamname']

    citylist = getteamcitiesweather(teamid)

    leaguenames = getteamsleagueinfo(teamid)

    return render_template("team.html", tteamname = tteamname, citylist = citylist, leaguenames = leaguenames)

@app.route("/user/<username>")
@login_required
def userpage(username):
    if username == "self":
        pageid = session["userid"]
    else:
        pageid = db.execute("SELECT id FROM users WHERE username LIKE (?)", username)[0]['id']

    uusername = db.execute("SELECT username FROM users WHERE id = ?", pageid)[0]['username']

    teamnames = getusersteamnames(pageid)

    leaguenames = getusersleaguenames(pageid)
    
    return render_template("user.html", uusername = uusername, teamnames = teamnames, leaguenames = leaguenames)

@app.route("/matchups/<matchupid>")
@login_required
def matchuppage(matchupid):
    userid = session["userid"]
    weeknum = getweeknum()

    matchupinfo = db.execute("SELECT * FROM matchups WHERE matchupid = ?", matchupid)

    team1id = matchupinfo[0]['hometeamid']
    team2id = matchupinfo[0]['awayteamid']
    winnerid = matchupinfo[0]['winner']

    team1name = db.execute("SELECT teamname FROM teams WHERE id = ?", team1id)[0]['teamname']
    team2name = db.execute("SELECT teamname FROM teams WHERE id = ?", team2id)[0]['teamname']
    if winnerid:
        winnername = db.execute("SELECT teamname FROM teams WHERE id = ?", winnerid)[0]['teamname']
    else:
        winnername = None

    return render_template("matchup.html", matchupinfo = matchupinfo, weeknum = weeknum, winnername = winnername, team1name = team1name, team2name = team2name)
