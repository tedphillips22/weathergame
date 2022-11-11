import requests
from cs50 import SQL
from datetime import date, timedelta

db = SQL("sqlite:///weather.db")

def getprediction(cityid, pcode): #fetches daily predictions for given city/pcode combination. creates 7 entries in predictions table
    lat = db.execute("SELECT lat FROM cities WHERE id = ?", cityid)[0]['lat']
    lon = db.execute("SELECT lon FROM cities WHERE id = ?", cityid)[0]['lon']

    url = "https://api.open-meteo.com/v1/forecast?latitude="+str(lat)+"&longitude="+str(lon)+"&hourly=cloudcover&daily=temperature_2m_max,temperature_2m_min,apparent_temperature_max,apparent_temperature_min,precipitation_sum,rain_sum,showers_sum,snowfall_sum,precipitation_hours,windgusts_10m_max&temperature_unit=fahrenheit&windspeed_unit=mph&precipitation_unit=inch&timezone=America%2FNew_York"
    response = requests.get(url)
    weatherdict = response.json()

    pname = db.execute("SELECT pname FROM param_codes WHERE pcode = ?", pcode)[0]['pname']
    

    #special version for cloudcover (only available as hourly data)
    if pcode == 10:
        for x in range(0,7):
            day = date.today() + timedelta(days=x)
            ccsum = 0
            for y in range((24*x),(24*(x+1))):
                cc = weatherdict['hourly']['cloudcover'][y]
                ccsum += cc
            ccday = ccsum / 24
            db.execute("INSERT INTO predictions (parameterid, parametervalue, cityid, date) VALUES(?,?,?,?)", pcode, ccday, cityid, day)
    
    elif pcode == 6: #special version for snow (comes in cm for some reason)
        for x in range(0,7):
            day = date.today() + timedelta(days=x)
            val = weatherdict['daily']['snowfall_sum'][x] / 2.54 #cm to inch conversion
            db.execute("INSERT INTO predictions (parameterid, parametervalue, cityid, date) VALUES(?,?,?,?)", pcode, val, cityid, day)
   
    else:
        for x in range(0,7):
            day = date.today() + timedelta(days=x)
            val = weatherdict['daily'][pname][x]
            db.execute("INSERT INTO predictions (parameterid, parametervalue, cityid, date) VALUES(?,?,?,?)", pcode, val, cityid, day)

    return()

def getmeasurement(cityid, pcode):
    lat = db.execute("SELECT lat FROM cities WHERE id = ?", cityid)[0]['lat']
    lon = db.execute("SELECT lon FROM cities WHERE id = ?", cityid)[0]['lon']

    url = "https://api.open-meteo.com/v1/forecast?latitude="+str(lat)+"&longitude="+str(lon)+"&hourly=cloudcover&daily=temperature_2m_max,temperature_2m_min,apparent_temperature_max,apparent_temperature_min,precipitation_sum,rain_sum,showers_sum,snowfall_sum,precipitation_hours,windgusts_10m_max&temperature_unit=fahrenheit&windspeed_unit=mph&precipitation_unit=inch&timezone=America%2FNew_York&past_days=7"
    response = requests.get(url)
    weatherdict = response.json()

    pname = db.execute("SELECT pname FROM param_codes WHERE pcode = ?", pcode)[0]['pname']

    #special version for cloudcover (only available as hourly data)
    if pcode == 10:
        for x in range(0,7):
            day = date.today() + timedelta(days= x - 7)
            ccsum = 0
            for y in range((24*x),(24*(x+1))):
                cc = weatherdict['hourly']['cloudcover'][y]
                ccsum += cc
            ccday = ccsum / 24
            db.execute("INSERT INTO measurements (parameterid, parametervalue, cityid, date) VALUES(?,?,?,?)", pcode, ccday, cityid, day)
    
    elif pcode == 6: #special version for snow (comes in cm for some reason)
        for x in range(0,7):
            day = date.today() + timedelta(days= x - 7)
            val = weatherdict['daily']['snowfall_sum'][x] / 2.54 #cm to inch conversion
            db.execute("INSERT INTO measurements (parameterid, parametervalue, cityid, date) VALUES(?,?,?,?)", pcode, val, cityid, day)
   
    else:
        for x in range(0,7):
            day = date.today() + timedelta(days= x - 7)
            val = weatherdict['daily'][pname][x]
            db.execute("INSERT INTO measurements (parameterid, parametervalue, cityid, date) VALUES(?,?,?,?)", pcode, val, cityid, day)

    return()

def getaverage(cityid, pcode):
    lat = db.execute("SELECT lat FROM cities WHERE id = ?", cityid)[0]['lat']
    lon = db.execute("SELECT lon FROM cities WHERE id = ?", cityid)[0]['lon']

    today = date.today()
    weekago = date.today() + timedelta(days = -7)

    valsum = 0

    pname = db.execute("SELECT pname FROM param_codes WHERE pcode = ?", pcode)[0]['pname']    

    for x in range(1,20):
        startdate = weekago + timedelta(days = -365.25*x)
        enddate = today + timedelta(days = -365.25*x)
        url = "https://archive-api.open-meteo.com/v1/era5?latitude="+str(lat)+"&longitude="+str(lon)+"&start_date="+str(startdate)+"&end_date="+str(enddate)+"&hourly=cloudcover&daily=temperature_2m_max,temperature_2m_min,apparent_temperature_max,apparent_temperature_min,precipitation_sum,rain_sum,snowfall_sum,precipitation_hours,windgusts_10m_max&timezone=America%2FNew_York&temperature_unit=fahrenheit&windspeed_unit=mph&precipitation_unit=inch"
        response = requests.get(url)
        weatherdict = response.json()
        val = 0
        if pcode == 10: #cloudcover only available hourly
            for x in range(0,7):
                day = startdate + timedelta(days = x)
                ccsum = 0
                for y in range((24*x),(24*(x+1))):
                    cc = weatherdict['hourly']['cloudcover'][y]
                    ccsum += cc
            val = ccsum / 24
        
        elif pcode == 6: #snowfall in cm
            for x in range(0,7):
                day = startdate + timedelta(days= x)
                val = weatherdict['daily']['snowfall_sum'][x] / 2.54 #cm to inch conversion
                
        else:
            for x in range(0,7):
                day = startdate + timedelta(days= x)
                val = weatherdict['daily'][pname][x]  
        
        valsum = valsum + val
            
    avgval = valsum / 20

    db.execute("INSERT INTO averages (parameterid, parametervalue, cityid, date) VALUES(?,?,?,?)", pcode, avgval, cityid, today)

        
    return()