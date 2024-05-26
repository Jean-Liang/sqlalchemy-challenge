# Import the dependencies.
import os
import numpy as np
import pandas as pd
import datetime as dt


import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func
from sqlalchemy import desc

from flask import Flask, jsonify


#################################################
# Database Setup
#################################################

# Create engine using the `hawaii.sqlite` database file
engine = create_engine("sqlite:///Resources/hawaii.sqlite")

# Declare a Base using `automap_base()`
Base = automap_base()
# Use the Base class to reflect the database tables
Base.prepare(autoload_with=engine)

# Assign the measurement class to a variable called `Measurement` and
# the station class to a variable called `Station`
Measurement = Base.classes.measurement
Station = Base.classes.station

# Create a session
session = Session(engine)

#################################################
# Flask Setup
#################################################
app = Flask(__name__)


#################################################
# Flask Routes
#################################################

# 1. Start at the homepage and List all the available routes.
@app.route("/")
def welcome():
    """List all available api routes."""
    return (
        f"Welcome to the Honolulu Hawaii App API!<br/>"
        f"Available Routes:<br/>"
        f"/api/v1.0/precipitation<br/>"
        f"/api/v1.0/stations<br/>"
        f"/api/v1.0/tobs<br/>"
        f"/api/v1.0/<start><br/>"
        f"/api/v1.0/<start>/<end><br/>"
    )

# 2. Convert the query results to a dictionary using `date` as the key and `prcp` as the value
# Return the JSON representation of your dictionary.
@app.route("/api/v1.0/precipitation")
def precipitation():
    # Query all dates and precipitation values
    results = session.query(Measurement.date, Measurement.prcp).all()
    
    # Convert the query results to a dictionary
    precipitation_dictionary = {date: prcp for date, prcp in results}

    return jsonify(precipitation_dictionary)

# 3. Return a JSON list of stations from the dataset
@app.route("/api/v1.0/stations")
def stations():
    # Query all stations
    results = session.query(Station.station).all()
    
    stations_list = list(np.ravel(results))
    
    return jsonify(stations_list)

# 4. Query the dates and temperature observations of the most active station for the previous year of data
# Return a JSON list of temperature observations for the previous year.
@app.route("/api/v1.0/tobs")
def tobs():
    # Calculate the date one year from the last date in the dataset
    most_recent_date_str = session.query(func.max(Measurement.date)).scalar()   
    most_recent_date = dt.datetime.strptime(most_recent_date_str, '%Y-%m-%d')
    One_year_ago_date=most_recent_date- dt.timedelta(days=365)
    
    # Query the last 12 months of temperature observation data for this station
    temperature_observation_data = session.query(Measurement.date, Measurement.tobs)\
                     .filter(Measurement.station == 'USC00519281')\
                     .filter(Measurement.date >= One_year_ago_date)\
                     .all()
    
    # Convert list of tuples into a list of dictionaries
    tobs_list = [{"date": date, "tobs": tobs} for date, tobs in temperature_observation_data]
    
    return jsonify(tobs_list)

# 5. Return a JSON list of the minimum temperature, the average temperature, and the maximum temperature for a specified start or start-end range
# For a specified start, calculate TMIN, TAVG, and TMAX for all the dates greater than or equal to the start date.
# For a specified start date and end date, calculate TMIN, TAVG, and TMAX for the dates from the start date to the end date, inclusive.

@app.route("/api/v1.0/<start>")
@app.route("/api/v1.0/<start>/<end>")
def temp_range(start, end=None):
    # Convert start and end dates to datetime
    start_date = dt.datetime.strptime(start, '%Y-%m-%d')
    
    # If there is no end date, set it to the maximum date (latest) in the dataset
    # User cannot run the temperature data file date greater than the database file 
    max_date_str = session.query(func.max(Measurement.date)).scalar()
    max_date = dt.datetime.strptime(max_date_str, '%Y-%m-%d')

    if not end:
         end_date = max_date
    else:
        end_date = dt.datetime.strptime(end, '%Y-%m-%d')
        if end_date > max_date:
            return jsonify({"error": "End date cannot be greater than the maximum date '2017-08-23' in the dataset"}), 400

    
    # Query for the min, avg, and max temperatures
    temp_results = session.query(func.min(Measurement.tobs), func.avg(Measurement.tobs), func.max(Measurement.tobs))\
                     .filter(Measurement.date >= start_date)\
                     .filter(Measurement.date <= end_date)\
                     .all()
    
    # Convert the results into a dictionary
    temp_dict = {
        "start_date": start,
        "end_date": end,
        "min_temp": temp_results[0][0],
        "avg_temp": temp_results[0][1],
        "max_temp": temp_results[0][2]
    }
    
    return jsonify(temp_dict)

if __name__ == '__main__':
    app.run(debug=True)