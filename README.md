# ws - Weather Station
<p align="center">
  <img src="https://github.com/boanjo/boanjo.github.io/blob/master/ws_screen.jpg?raw=true">
</p>

WS is a graphical frontend to be used on top of existing homeautomation (or it can be used standalone) like Domoticz or HomeAssistant and your own sensor network with MySensors. It is NOT a homeautomation controller but simply a listener on weather related sensors. To enable this listener pattern you need to have your MySensors hooked up via MQTT which is a popular way of disconnecting sensor networks and controller. It has a hardcoded web interface (even if it is of course possible for you to change) and the reason for this is that it has been satisfactory for a number of deployments over a number of years. What is a nice looking GUI is of course in the eyes of the beholder but for some reason i still think this is the best GUI for me with clear information without distracting details. It is also possile to read from a larger distance which i also consider important. The ws page runs on any server locally (including raspberry pi) or remote and to be displayed continously on a 10" tablet. I have a number of these systems that have been up for more than 5 years. You can use an app like the "Fully Kiosk Browser" on android. I have made my own simple app that switches webviews after fully loaded periodically every 30 sec which makes a seemless and very smooth UI experience. It also handles loss of wifi and other quirks that might happen. If there is an interest in the APP let me know and i can fix that!  

Here is a YouTube video where i'm going through the setup: https://youtu.be/JygoxuusSYA


I have made a few architectural desicions: 
- I only support MQTT gateway (for example how to build one https://github.com/boanjo/myhome/tree/master/gateway_mqtt) and that is to be able to listen on the gateway and controller and only act as an addon for both new and existing systems. I also have a few systems that run over mobile internet without possibility to do port forwarding (which from security perspective should be avoided too if possible) hence keeping the web interface off site makes life easier for me to manage the systems.
- I am using both polling the database and listen to websockets MQTT messages. This might seem a tad overcomplicated, but i want as fast feedback on the sensors as possible (especially wind gust and rain). In one prototype i used database only but with frequent polling. This didn't scale very well and caused quite high load on the mysqld and to my surprise also influxdbd even if only polling every 1-3 seconds or so. And vice versa it's not possible to only use mqtt as it doesn't store state. I.e. you need to be able to fetch the previous values anyway.
- Keeping the webserver on a web host provider scales better if you have many listeners (like your whole neighbourhood ;-)) of the weather information
- Quite many parameters are configurable in cfg directory. Change the names to suite your needs and let it be reflected in your docker-compose.yml file. I this example i have added two of my systems as inspiration. In many cases it's easier to do changes or extensions in the mqtt app (ws.py) or web app/template (app.py or weather.html)

The MySensors network produces data continously (especially the wind (anemometer) which reports every 5 seconds (in case of change) for both speed and direction. 
1. This is reported from the gataway to the mosquitto MQTT server.
2. The data is picked up by your controller (Domoticz, HA..) if you subscribe to the topic and the same infromation is then also picked up by the WS MQTT app. This is a python client using paho library to listen and send MQTT messages. 
3. The MQTT app translates the data into a more readable format and republishes it under a new topic (that you decide in your config.json) 
4. The MQTT app also stores the data in a MySql database (could just as well been an influxdb) with the exception of wind that is stored less frequent like wind speed peak every 30 sec and median direction every 15 min. 
5. The Web client continously listens for changes one the WS topic (sent in 4) via MQTT over websockets. This allows to have "realtime" changes to the data. So when you hear the wind gust you will see the speed on your display within max 5 seconds (i.e. the max time between wind speed samples).
6. On every page load the values are fetched from the database. Outdoor Temp, Indoor Temp, Rain (by fetching min max to diff) plus wind speed and direction. Also the last weeks min max values for temp outdoor and rain is fetched to be shown in the chart. As mentioned in 5 changes appear instantly and in case of rain it will also trigger a new fetch from the database. The Flask web app renders the web UI that is displayed on the tablet, phone or browser. As i mentioned above i use my own android app for full control but a app like the Full Kiosk Browser should do the trick too.
![2](https://github.com/boanjo/boanjo.github.io/blob/master/ws_overview.jpg?raw=true "Pic 2")

## Example setup #1 (my personal setup):
I have connected a modified RainWise raingauge to this node with my own 3D printed Stevenson Screen for outdoor temperature. https://github.com/boanjo/myhome/blob/master/weather_station_dc/. The biggest reason i have the sensor dc powered is the outdoor temperature which also has a small DC fan connected to it to ensure ventilation of the Stevenson Cage also on really sunny days (it's extra precausion but it dont' really know if it is needed)

Rain - If you want to pole mount the RainWise raingauge see here for a model you can print (or if you want to have it as a separate sensor node) https://github.com/boanjo/myhome/tree/master/rain_gauge
Out Temp - Here is the printable https://www.thingiverse.com/thing:4645989 and also a YouTube video of the making. 

Here is a fusion 360 rendering of the setup (no it's not my garden view ;)
![3](https://github.com/boanjo/boanjo.github.io/blob/master/ws_assembly.png?raw=true "Pic 3")


Wind - On my roof i have the Davis instruments anemometer (i only use the HW and own MySensors radio) https://github.com/boanjo/myhome/tree/master/anemometer. It's solar powered and i'd say it's a must for an anemometer.

Indoor temperature - https://github.com/boanjo/myhome/tree/master/temp_indoor_dc (or the battery powered version https://github.com/boanjo/myhome/tree/master/temp_indoor) which is my favorite case for indoor sensors. Previously i've always found it difficult to make beautiful 433MHz sensors due to the antennas - but this i like :)

## Example setup #2:
All Sensors (Rain, Wind, Temperature) hooked up to the same weather_stataion:
https://github.com/boanjo/myhome/blob/master/weather_station_dc/

## Example setup #3:
All sensors are their own nodes - see myhome for all sensors (with separate README.md descriptions) https://github.com/boanjo/myhome

## Parts and rough BOM for this WS project
- RainWise RainGauge ~100 USD here in Europe (cheaper in the US) (https://github.com/boanjo/myhome/blob/master/rain_gauge/)
- RainWise Mounting ~15USD PLA/PETG and metal rods (https://www.thingiverse.com/thing:4641372)
- Davis Anemometer ~150 USD here in Europe (cheaper in the US) (https://github.com/boanjo/myhome/blob/master/anemometer/)
- Stevenson Screen ~15 USD of PETG plastic, rods and electronics (https://www.thingiverse.com/thing:4645989) 
- Weather Station box ~10 USD PETG and electronics (https://github.com/boanjo/myhome/blob/master/weather_station_dc/)
- Indoor Temperature ~15 USD PLA and electronics (Si7021 temp + hum is ~7USD) (https://github.com/boanjo/myhome/tree/master/temp_indoor_dc)
- MQTT GW ~10 USD PLA and electronics (https://github.com/boanjo/myhome/blob/master/gateway_mqtt/)

A total of around 320 USD and you will have a really reliable and nice weatherstation setup. I like being able to build things from "scratch" but I have chosen to use the Davis and RainWise for wind and rain as they are proven reliable and is well worth the investment. I've have tried numerous other solutions over the years and this is the best quality vs cost (including continous troubleshooting of other poor HW) combo i have experienced. 


![4](https://github.com/boanjo/boanjo.github.io/blob/master/ws_mysensor.jpg?raw=true "Pic 4")

Then of course you need a RPI or other server HW for the actual WS applications and also a cheap tablet (But nice and clear display) for showing the results in realtime.

This is how i can look a few days before Christmas :) in the south of Sweden - a few degrees and rain!

![5](https://github.com/boanjo/boanjo.github.io/blob/master/ws_tablet.jpg?raw=true "Pic 5")

