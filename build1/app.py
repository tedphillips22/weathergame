from flask import Flask, flash, redirect, render_template, request, session 
import urllib.request, json, datetime
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

APIkey = "fc554137bf63e3cc6f44bae5376883b3"

def get_weather(city):

    lat = db.execute("SELECT lat FROM cities WHERE city = ?", city)
    lon = db.execute("SELECT lon FROM cities WHERE city = ?", city)

    #"exclude" can change data called on api, see openweathermap documentation
    url = "https://api.openweathermap.org/data/3.0/onecall?lat={"+str(lon)+"}={"+str(lat)+"}&exclude={minutely,hourly,alerts}&appid={"+APIkey+"}"

    response = urllib.request.urlopen(url)
    weatherdata = response.read()
    weatherdict = json.loads(weatherdata)

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

    counter = 0
    for row in teamidsdict:
        temp = teamidsdict[counter]
        print(temp)
        teamidtemp = temp["id"]
        print(teamidtemp)
        teamids.append(teamidtemp)
        print(teamids)
        counter += 1

    cityids = []
    for id in teamids:
        cityiddict = db.execute("SELECT cityid FROM teamcities WHERE teamid = ?", teamids[id])
        cityids.append(cityiddict["cityid"])


 
    print(cityids)

    return render_template("teampage.html")
