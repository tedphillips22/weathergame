from flask import Flask, flash, redirect, render_template, request, session 
import requests, json
from flask_session import Session
from cs50 import SQL
from werkzeug.security import check_password_hash, generate_password_hash
from functools import wraps
from helpers import login_required, get_current_weather, message, namecheck, citycheck, getleagueinfo, getteamcitiesweather, getteamsleagueinfo, getusersleaguenames, getusersleagueteamdicts, getusersteamnames

db = SQL("sqlite:///weather.db")

#days = ["Su", "Mo", "Tu", "We", "Th", "Fr", "Sa"]

