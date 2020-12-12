#!/usr/bin/python
# -*- coding: utf-8 -*-

import paho.mqtt.client as mqtt
import paho.mqtt.publish as publish
from datetime import datetime
import sys
import json
import time
import socket
from select import select
import mysql.connector
from mysql.connector import Error
import sys
import os

class WeatherMqtt:

    def __init__(self, config):

        self.config = config
        self.last_wind_dir_upload_time = datetime.now()
        self.wind_dir = []
        self.last_wind_speed_upload_time = datetime.now()
        self.wind_speed_max = 0.0
    
    def upload_to_db(self, d_str, t_str, sensor, value):      
        
        try:
            connection = mysql.connector.connect(host=str(config['mysql']['host']),
                                                 user=str(config['mysql']['user']),
                                                 passwd=str(config['mysql']['password']),
                                                 db=str(config['mysql']['database']),
                                                 port=int(config['mysql']['port']))
            
            cursor = connection.cursor()
            
            cursor.execute('INSERT INTO %s (date, time, sensor, value) VALUES ("%s", "%s", "%s", %s)' % (str(config['mysql']['table']), d_str, t_str, sensor, float(value)))
            # must commit before close
            connection.commit()
            cursor.close()
            
        except Error as e :
            print ("Error while connecting to MySQL", e)
        finally:
            #closing database connection.
            if(connection.is_connected()):
                connection.close()
        return         

    def on_connect(self, mqttc, obj, flags, rc):
        print("rc: " + str(rc))


        #    S_DOOR 0 Door and window sensors V_TRIPPED, V_ARMED
        #    S_MOTION 1 Motion sensorsV_TRIPPED, V_ARMED
        #    S_SMOKE 2 Smoke sensorV_TRIPPED, V_ARMED
        #    S_BINARY 3 Binary device (on/off)V_STATUS, V_WATT
        #    S_DIMMER 4 Dimmable device of some kindV_STATUS (on/off), V_PERCENTAGE (dimmer level 0-100), V_WATT
        #    S_COVER 5 Window covers or shadesV_UP, V_DOWN, V_STOP, V_PERCENTAGE
        #    S_TEMP 6 Temperature sensorV_TEMP, V_ID
        #    S_HUM 7 Humidity sensorV_HUM
        #    S_BARO 8 Barometer sensor (Pressure)V_PRESSURE, V_FORECAST
        #    S_WIND 9 Wind sensorV_WIND, V_GUST, V_DIRECTION
        #    S_RAIN 10 Rain sensorV_RAIN, V_RAINRATE

    def is_for_me(self, msg_type, node_id, child_id):
        if(int(self.config[msg_type]['node_id']) == node_id and int(self.config[msg_type]['child_id']) == child_id):
            return True
        return False
    
    def on_message(self, mqttc, obj, msg):
        
        now = datetime.now()
        d_str = now.strftime("%Y-%m-%d")
        t_str = now.strftime("%H:%M:%S")

        print(d_str + " " + t_str + " " + msg.topic + " " + str(msg.payload))

        manip = msg.topic
        # trim off any topic part
        for topic in self.config['mqtt']['mys_topics']:
            manip = manip.replace(topic + "/", '')
        
        arr = manip.split('/')

        if len(arr) != 5:
            print("Unknown message, skipping %s" % (len(arr)))
            for x in arr:
                print(x)
            sys.stdout.flush()
            return
        
        node_id = int(arr[0])
        child_id = int(arr[1])
        msg_id = int(arr[4])
        
        # 10 = V_DIRECTION 
        if(msg_id == 10 and self.is_for_me('wind', node_id, child_id)):
            self.wind_dir.append(float(msg.payload))

            # So we only upload once every 15 min (900 sec)
            if ((now - self.last_wind_dir_upload_time).total_seconds() > 900):
                if len(self.wind_dir) > 0:
                    most_common_dir =  max(set(self.wind_dir), key=self.wind_dir.count)
                    self.upload_to_db(d_str, t_str, "wind_dir", most_common_dir)
                    self.wind_dir = []
                    self.last_wind_dir_upload_time = now;
            mqttc.publish(self.config['mqtt']['ws_topic'] + "/wind_dir", payload=msg.payload)
            
                
        # 8 = V_WIND
        elif(msg_id == 8 and self.is_for_me('wind', node_id, child_id)):
            if(float(msg.payload) > self.wind_speed_max):
                self.wind_speed_max = float(msg.payload)
            
            # So we only upload once every 30 sec
            if ((now - self.last_wind_speed_upload_time).total_seconds() > 30):
                self.upload_to_db(d_str, t_str, "wind_speed", self.wind_speed_max)
                self.wind_speed_max = 0.0
                self.last_wind_speed_upload_time = now
            mqttc.publish(self.config['mqtt']['ws_topic'] + "/wind_speed", payload=msg.payload)
                    
        # 0 = V_TEMPERATURE
        elif(msg_id == 0):
            if(self.is_for_me('temp_in', node_id, child_id)):
                self.upload_to_db(d_str, t_str, "temp_in", msg.payload)
                mqttc.publish(self.config['mqtt']['ws_topic'] + "/temp_in", payload=msg.payload)
            elif(self.is_for_me('temp_out', node_id, child_id)):
                self.upload_to_db(d_str, t_str, "temp_out", msg.payload)
                mqttc.publish(self.config['mqtt']['ws_topic'] + "/temp_out", payload=msg.payload)
                
        # 1 = V_HUMIDITY
        elif(msg_id == 1):        
            if(self.is_for_me('temp_in', node_id, child_id)):
                self.upload_to_db(d_str, t_str, "hum_in", msg.payload)
                mqttc.publish(self.config['mqtt']['ws_topic'] + "/hum_in", payload=msg.payload)
            elif(self.is_for_me('temp_out', node_id, child_id)):
                self.upload_to_db(d_str, t_str, "hum_out", msg.payload)
                mqttc.publish(self.config['mqtt']['ws_topic'] + "/hum_out", payload=msg.payload)
                
        # 6 = V_RAIN
        elif(msg_id == 6 and self.is_for_me('rain', node_id, child_id)):        
            self.upload_to_db(d_str, t_str, "rain", msg.payload)
            # We just use the rain as trigger. The max min diff will be made in the
            # client is anyone is listening
            mqttc.publish(self.config['mqtt']['ws_topic'] + "/rain", payload=msg.payload)
            
        sys.stdout.flush()
                    

    def on_publish(self, mqttc, obj, mid):
        mid


    def on_disconnect(self, client, userdata, rc):
        self.disconnected = True, rc

    def on_subscribe(self, mqttc, obj, mid, granted_qos):
        print("Subscribed: " + str(mid) + " " + str(granted_qos))

    def on_log(self, mqttc, obj, level, string):
        print(string)

    def do_select(self):
        sock = self.client.socket()
        if not sock:
            raise Exception("Socket is gone")

        #print("Selecting for reading" + (" and writing" if self.client.want_write() else ""))
        r, w, e = select(
            [sock],
            [sock] if self.client.want_write() else [],
            [],
            1
        )

        if sock in r:
            #print("Socket is readable, calling loop_read")
            self.client.loop_read()

        if sock in w:
            #print("Socket is writable, calling loop_write")
            self.client.loop_write()

        self.client.loop_misc()


        
    def main(self):
        self.disconnected = (False, None)
        self.client = mqtt.Client()
        self.client.on_message = self.on_message
        self.client.on_connect = self.on_connect
        #self.client.on_publish = self.on_publish
        self.client.on_subscribe = self.on_subscribe
        # Uncomment to enable debug messages
        #self.client.on_log = self.on_log

        
        self.client.connect(self.config['mqtt']['url'], self.config['mqtt']['port'], 60)
        for topic in self.config['mqtt']['mys_topics']:
            print("subscribed to %s" % topic)
            self.client.subscribe("%s/#" % topic, 0)

        print("v1.01")
        print("Socket opened")
        self.client.socket().setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 2048)

        prev_time = ""
        
        while not self.disconnected[0]:
            self.do_select()

            now = datetime.now()
            dt_str = now.strftime("%H:%M")

            if(dt_str != prev_time):
                prev_time = dt_str


            

            #time.sleep(5)
            #print("woken up")
            ret = 1


print("Starting")

with open("/cfg/config.json") as json_file:
    config = json.load(json_file)
    ws = WeatherMqtt(config)
    ws.main()
print("Finished")
