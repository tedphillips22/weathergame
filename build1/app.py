from flask import Flask, flash, redirect, render_template, request, session 
import requests, json
from flask_session import Session
from cs50 import SQL
from werkzeug.security import check_password_hash, generate_password_hash
from functools import wraps


app = Flask(__name__)

db = SQL("sqlite:///weather.db")

app.config["TEMPLATES_AUTO_RELOAD"] = True

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

##### HELPER FUNCTIONS ######

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

def message(message):
    """Render message to user."""

    return render_template("message.html", message=message)

def namecheck(city):
    namecheck = db.execute("SELECT count(*) FROM cities WHERE city_state = ?", city)[0]['count(*)']
    return(namecheck)

def citycheck(city):    
    cityid = db.execute("SELECT id FROM cities WHERE city_state = ?", city)[0]['id']
    return(cityid)


####### PAGE FUNCTIONS #######

@app.route("/")
@login_required
def index():
    return render_template("index.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return message("must provide username")

        # Ensure password was submitted
        elif not request.form.get("password"):
            return message("must provide password")

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return message("invalid username and/or password")

        # Remember which user has logged in
        session["userid"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

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
        if len(db.execute("SELECT username FROM users WHERE username = ?", username)) != 0:
            return message("Username already exists")

        password = request.form.get("password")
        confirmation = request.form.get("confirmation")
        if password != confirmation:
            return message("Passwords don't match")

        else:
            hash = generate_password_hash(password)
            db.execute("INSERT INTO users (username, hash) VALUES(?, ?)", username, hash)
            return redirect("/")

    else:

        return render_template("register.html")

@app.route("/maketeam", methods = ["POST", "GET"])
@login_required
def maketeam():
    if request.method == "POST":
        
        teamname = request.form.get("teamname")
        #Check for team name dupes
        
        userid = session["userid"]
        
        city1 = request.form.get("city1")
        if namecheck(city1) == 0:
            return message("Some cities not found. Please use autocomplete and fill in all the blanks.")
        city1id = citycheck(city1)

        city2 = request.form.get("city2")
        if namecheck(city2) == 0:
            return message("Some cities not found. Please use autocomplete and fill in all the blanks.")
        city2id = citycheck(city2)

        city3 = request.form.get("city3")
        if namecheck(city3) == 0:
            return message("Some cities not found. Please use autocomplete and fill in all the blanks.")
        city3id = citycheck(city3)

        db.execute("INSERT INTO teams (userid, teamname) VALUES (?, ?)", userid, teamname)
        teamid = db.execute("SELECT id FROM teams WHERE teamname = ? AND userid = ?", teamname, userid)[0]['id']
        db.execute("INSERT INTO teamcities (teamid, cityid) VALUES (?, ?)", teamid, city1id)
        db.execute("INSERT INTO teamcities (teamid, cityid) VALUES (?, ?)", teamid, city2id)
        db.execute("INSERT INTO teamcities (teamid, cityid) VALUES (?, ?)", teamid, city3id)

        return message("Team named {0} created".format(teamname))

    else:
        cities = db.execute("SELECT city_state FROM cities")
        return render_template("maketeam.html", cities = cities)
        
@app.route("/myteams")
@login_required
def myteams():
    userid = session["userid"]

    teamidsdict = db.execute("SELECT id FROM teams WHERE userid = ?", userid)
    teamids = []

    #generate list of users teamids
    counter = 0
    for row in teamidsdict:
        temp = teamidsdict[counter]
        teamidtemp = temp["id"]
        teamids.append(teamidtemp)
        counter += 1

    teamsdict = []

    #generate list of all cities from all teams [{'teamid': x, 'cityid': x}, ...]
    counter = 0
    for id in teamids:
        cityiddicttemp = db.execute("SELECT teamid, cityid FROM teamcities WHERE teamid = ?", teamids[counter])
        teamsdict.append(cityiddicttemp)
        counter += 1

    
    #convert dict of ids to names
    citydict = []
    teamslist = []
    counter = 0
    for row in teamsdict:
        counter = 0
        teamidtemp = row[counter]['teamid']
        teamnametemp = db.execute("SELECT teamname FROM teams WHERE id = ?", teamidtemp)[0]['teamname']
        teamslist.append({'teamname' : teamnametemp})
        for item in row:
            cityidtemp = row[counter]['cityid']
            counter += 1                
            citynametemp = db.execute("SELECT city FROM cities WHERE id = ?", cityidtemp)[0]['city']
            #query weather api for data and select what we need from it
            
            weathertemp = get_current_weather(cityidtemp)
            
            temperature = weathertemp['hourly']['temperature_2m'][0]
            feelslike = weathertemp['hourly']['apparent_temperature'][0]
            weathercode = weathertemp['hourly']['weathercode'][0]

            weatherdesc = db.execute("SELECT description FROM weathercodes WHERE code = ?", weathercode)[0]['description']




            citydict.append({'teamname' : teamnametemp, 'cityname' : citynametemp, 'temperature' : temperature, 'feelslike' : feelslike, 'weatherdesc' : weatherdesc})
            
    


    return render_template("teampage.html", citydict = citydict, teamslist = teamslist)
