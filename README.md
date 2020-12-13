# ws - Weather Station
![0](https://github.com/boanjo/boanjo.github.io/blob/master/ws_screen.jpg?raw=true "Pic 0")

WS is a graphical frontend to be used on top of existing homeautomation (or it can be used standalone) like Domoticz or HomeAssistant and your own sensor network with MySensors. It is NOT a homeautomation controller but simply a listener on weather related sensors. To enable this listener pattern you need to have your MySensors hooked up via MQTT which is a popular way of disconnecting sensor networks and controller. It has a hardcoded web interface (even if it is of course possible for you to change) and the reason for this is that it has been satisfactory for a number of deployments over a number of years. What is a nice looking GUI is of course in the eyes of the beholder but for some reason i still think this is the best GUI for me with clear information without distracting details. It is also possile to read from a larger distance which i also consider important. The ws page runs on any server locally (including raspberry pi) or remote and to be displayed continously on a 10" tablet. I have a number of these systems that have been up for more than 5 years. You can use an app like the "Fully Kiosk Browser" on android. I have made my own simple app that switches webviews after fully loaded periodically every 30 sec which makes a seemless and very smooth UI experience. It also handles loss of wifi and other quirks that might happen. If there is an interest in the APP let me know and i can fix that!  

<p align="center">
  <img src="https://github.com/boanjo/boanjo.github.io/blob/master/ws_tablet.jpg?raw=true">
</p>

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

MySensors setup:
I have connected a modified RainWise raingauge to this node with my own 3D printed Stevenson Screen for outdoor temperature. https://github.com/boanjo/myhome/blob/master/weather_station_dc/. On my roof i have the Davis instruments anemometer (i only use the HW and own MySensors radio) https://github.com/boanjo/myhome/tree/master/anemometer


![3](https://github.com/boanjo/boanjo.github.io/blob/master/ws_mysensor.jpg?raw=true "Pic 3")


This is how i can look a few days before Christmas :)!

![4](https://github.com/boanjo/boanjo.github.io/blob/master/ws_screen.jpg?raw=true "Pic 4")

