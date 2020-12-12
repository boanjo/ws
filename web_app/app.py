from typing import List, Dict
from flask import Flask
from flask import render_template
from flask import request
import mysql.connector
from mysql.connector import Error
import time
import calendar
import json
import re
import os
import datetime
from datetime import date, timedelta

config = {}
app = Flask(__name__, static_url_path='/static')
            
def get_last_week_sensor(sensor):      
    series_list = []

    try:
        connection = mysql.connector.connect(host=str(config['mysql']['host']),
                                             user=str(config['mysql']['user']),
                                             passwd=str(config['mysql']['password']),
                                             db=str(config['mysql']['database']),
                                             port=int(config['mysql']['port']))

        cursor = connection.cursor()
        cursor.execute('SELECT date, MAX(value), MIN(value) FROM %s where sensor="%s" AND date BETWEEN DATE_SUB(NOW(), INTERVAL 7 DAY) AND NOW() GROUP BY DATE(date)' % (str(config['mysql']['table']), sensor))

        
        for [d_str,max_val,min_val] in cursor:
            series_list.append([str(d_str), max_val, min_val])
                        
        cursor.close()
    except Error as e :
        print ("Error while connecting to MySQL", e)
    finally:
        #closing database connection.
        if(connection.is_connected()):
            connection.close()


    return series_list

def get_current_sensor_values():      
    key_val = dict()

    try:
        connection = mysql.connector.connect(host=str(config['mysql']['host']),
                                             user=str(config['mysql']['user']),
                                             passwd=str(config['mysql']['password']),
                                             db=str(config['mysql']['database']),
                                             port=int(config['mysql']['port']))

        cursor = connection.cursor()
        cursor.execute('SELECT id, sensor, date, time, value FROM %s where id in (SELECT MAX(id) FROM %s GROUP BY sensor)' % (str(config['mysql']['table']), str(config['mysql']['table'])))

        for [id_num,sensor,d_str,t_str,value] in cursor:
            data = dict()
            data['value'] = value
            data['date'] = str(d_str)
            data['time'] = str(t_str)
            key_val[sensor] = data
                        
        cursor.close()
    except Error as e :
        print ("Error while connecting to MySQL", e)
    finally:
        #closing database connection.
        if(connection.is_connected()):
            connection.close()

    return key_val


def map_direction(wind_dir):
    ret = "UNF"
    if(wind_dir == "0.0"):
        ret = "N"
    elif(wind_dir == "22.5"):
        ret = "NNE"
    elif(wind_dir == "45.0"):
        ret = "NE"
    elif(wind_dir == "67.5"):
        ret = "ENE"
    elif(wind_dir == "90.0"):
        ret = "E"
    elif(wind_dir == "112.5"):
        ret = "ESE"
    elif(wind_dir == "135.0"):
        ret = "SE"
    elif(wind_dir == "157.5"):
        ret = "SSE"
    elif(wind_dir == "180.0"):
        ret = "S"
    elif(wind_dir == "202.5"):
        ret = "SSW"
    elif(wind_dir == "225.0"):
        ret = "SW"
    elif(wind_dir == "247.5"):
        ret = "WSW"
    elif(wind_dir == "270.0"):
        ret = "W"
    elif(wind_dir == "292.5"):
        ret = "WNW"
    elif(wind_dir == "315.0"):
        ret = "NW"
    elif(wind_dir == "337.5"):
        ret = "NNW"
    return ret

def get_rain_for_date(d, rain_list):
    for [d2,max_val,min_val] in rain_list:
        if d == d2:
            return float("{0:0.1f}".format(float(max_val) - float(min_val)))
    return 0.0

def get_temp_max_for_date(d, list):
    for [d2,max_val,min_val] in list:
        if d == d2:
            return float(max_val)
    return -255.0

def get_temp_min_for_date(d, list):
    for [d2,max_val,min_val] in list:
        if d == d2:
            return float(min_val)
    return -255.0

def format_date(dt):
    m = dt.month
    if(m < 10):
        m = '0' + str(m)
    d = dt.day
    if(d < 10):
        d = '0' + str(d)
    return str(dt.year) + "-" + str(m) + "-" + str(d)

def format_time(dt):
    h = dt.hour
    if(h < 10):
        h = '0' + str(h)
    m = dt.minute
    if(m < 10):
        m = '0' + str(m)
    s = dt.second
    if(s < 10):
        s = '0' + str(s)
    return str(h) + ":" + str(m) + ":" + str(s)

@app.route('/api_get_current_sensor_values')
def api_get_current_sensor_values():      
    
    return json.dumps(get_current_sensor_values())



@app.route('/api_get_last_week')
def api_get_last_week():


    rain_list = get_last_week_sensor('rain')
    out_list = get_last_week_sensor('temp_out')
    
    ret_list = []
    for i in range(7):
        dt = date.today() - timedelta(6-i)

        # 2020-07-01 -> 1/7
        short_dt = str(dt.day) + "/" + str(dt.month)

        d = format_date(dt)
        series = dict()
        series['date'] = str(short_dt)
        series['rain'] = get_rain_for_date(str(d), rain_list)
        series['temp_max'] = get_temp_max_for_date(str(d), out_list)
        series['temp_min'] = get_temp_min_for_date(str(d), out_list)
        
        ret_list.append(series)
                
    return json.dumps(ret_list)

@app.route('/weather')
def weather():

    sensors = get_current_sensor_values()

    temp_out = '-.-'
    if('temp_out' in sensors):
        temp_out = sensors['temp_out']['value']
    temp_in = '-.-'
    if('temp_in' in sensors):
        temp_in = sensors['temp_in']['value']
    wind_speed = '-.-'
    if('wind_speed' in sensors):
        wind_speed = sensors['wind_speed']['value']
    wind_dir = "UNDEF"
    if('wind_dir' in sensors):
        wind_dir = map_direction(str(sensors['wind_dir']['value']))
    
    
    dt = date.today()

    return render_template('weather.html',
                           title=str(config['general']['title']),
                           temp_out=temp_out,
                           temp_in=temp_in,
                           wind_speed=wind_speed,
                           wind_dir=wind_dir,
                           forecast_url=str(config['general']['forecast_url']),
                           mqtt_topic=config['mqtt']['ws_topic'],
                           mqtt_url=config['mqtt']['url'],
                           mqtt_port=config['mqtt']['websockets_port'],
                           footer='&copy; %s - Anders Johansson' % (dt.year)
    )

if __name__ == '__main__':
    with open("/cfg/config.json") as json_file:
         config = json.load(json_file)
         
         app.run(host='0.0.0.0')


