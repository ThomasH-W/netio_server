#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Read openweather JSON file
# 2013-06-29 V0.3 by Thomas Hoeser
#
import urllib2, json, sys, pprint, argparse

from time import strftime
from datetime import datetime

verbose_level = 0
debug_level   = 0
#---------------------------------------------------------------------------------------------
ow_dict_example = {
	u'base': u'global stations',
    u'clouds': {   u'all': 75},    # Cloudiness in %
    u'cod': 200,
    u'coord': {   u'lat': 50.950001, u'lon': 7.53333}, # City location
    u'dt': 1371876600,                 # Time of data receiving in unixtime GMT
    u'id': 2809517,
    u'main': {   u'humidity': 77,      # Humidity in %
                 u'pressure': 1016,    # Atmospheric pressure in hPa
                 u'temp': 287.69,      # Temperature in Kelvin. Subtracted 273.15 from this figure to convert to Celsius.
                 u'temp_max': 289.15,  # Minimum and maximum temperature
                 u'temp_min': 287.04},
    u'name': u'Wiehl',                 # City name
    u'rain': {   u'3h': 0.5},          # Precipitation volume mm per 3 hours
    u'sys': {   u'country': u'DE', u'sunrise': 1371870953, u'sunset': 1371930488},
	# see http://bugs.openweathermap.org/projects/api/wiki/Weather_Condition_Codes
    u'weather': [   {   u'description': u'broken clouds',
                        u'icon': u'04d',  # icon no - e.g. : 04d.png = broken clouds
                        u'id': 803,    # Weather Condition Codes - e.g. 803 = broken clouds
                        u'main': u'Clouds'}],
    u'wind': {  u'deg': 170,  			# Wind direction in degrees (meteorological)
				u'speed': 3.6}          # Wind speed in mps
				}

#---------------------------------------------------------------------------------------------
def temp_k2c(temp_k):
	temp_c = round(temp_k - 273.15,1)
	return(temp_c)

#---------------------------------------------------------------------------------------------
def speed_mps2ms(speed_mps):
	speed_ms = round(speed_mps * 0.44704,1)
	return(speed_ms)

#---------------------------------------------------------------------------------------------
def wind_deg2txt(deg):
    #                 0   1    2   3    4   5    6   7    8
    wind_dir_name = ['N','NO','O','SO','S','SW','W','NW','N']

    wind_sections = 360 / 8
    offset = wind_sections / 2 
    # range(start, stop[, step])
    y = int( (deg + offset) / wind_sections )
    if verbose_level > 3 :print deg, y, offset, wind_sections,
    wind_dir_txt = wind_dir_name[y]
    if verbose_level > 3 :print " -> " + wind_dir_txt
    
    return(wind_dir_txt)
    
#---------------------------------------------------------------------------------------------
if __name__ == "__main__":

   pp = pprint.PrettyPrinter(indent=4)

   parser = argparse.ArgumentParser(description='open weather client by Thomas Hoeser / 2013')
   parser.add_argument("-v", "--verbose", default=False,
                          dest='verbose', help="increase output verbosity", type=int)
   parser.add_argument("-d", "--debug", action='store_const', dest='debug',
                    const='value-to-store', help="debug mode - will prevent executing send command or reading 1-wire sensor")
   parser.add_argument('--version', action='version', version='%(prog)s 0.2')

   parser.add_argument("city")
   args = parser.parse_args()

   if args.verbose	:  verbose_level = args.verbose
   if args.debug	:  debug_level = 1

   ow_city =   args.city     # set your city from command line
   ow_city = ow_city.lower()
   ow_file_cur = "/home/pi/ow_" + ow_city + "_cur.json"
   ow_file_for = "/home/pi/ow_" + ow_city + "_for.json"
   ow_file_for7= "/home/pi/ow_" + ow_city + "_for7.json"

   # ----------------------------------------------------------------------------------------
   print "------------------------- Aktuell"
   if verbose_level > 0 :
   	print "open JSON file: ", ow_file_cur

   try:
	   with open(ow_file_cur, 'r') as json_file:
	   	json_out_cur = json.load(json_file)
   except:
   		print "PANIC: cannot open file: "  + ow_file_cur
		sys.exit(1)

   if verbose_level > 1 :
	   pp.pprint(json_out_cur)

   print "Stadt       : " + str(json_out_cur['name'])
   print "ID          : " + str(json_out_cur['id'])
   status = datetime.fromtimestamp(json_out_cur['dt']).strftime('%Y-%m-%d %H:%M')
   print "Stand       : " + status
   print "Windrichtung: " + str(json_out_cur['wind']['deg']) + " Grad"
   wind_speed = json_out_cur['wind']['speed']
   wind_speed = speed_mps2ms(wind_speed)
   print "Windgeschw. : " + str(wind_speed) + " m/s"
   print "Wolken      : " + str(json_out_cur['clouds']['all']) + "%"
   print "Himmel      : " + str(json_out_cur['weather'][0]['description']) + ""
   print "owIcon      : " + str(json_out_cur['weather'][0]['icon']) + ""
   print "owID        : " + str(json_out_cur['weather'][0]['id']) + ""
   print "Feuchte     : " + str(json_out_cur['main']['humidity']) + "%"
   print "Druck       : " + str(json_out_cur['main']['pressure']) + " hPa"
   # print "Regen       : " + str(json_out_cur['rain']['3h']) + " mm / 3 Stunden"
   aufgang = datetime.fromtimestamp(json_out_cur['sys']['sunrise']).strftime('%H:%M')
   print "S.Aufgang   : " + aufgang
   aufgang = datetime.fromtimestamp(json_out_cur['sys']['sunset']).strftime('%H:%M')
   print "S.Untergang : " + aufgang

   # temperature is measured in degree Kelvin unit
   # get current temperature
   temp_cur_c = temp_k2c ( json_out_cur['main']['temp'] )
   print "Temp.       : " + str(temp_cur_c) + " Grad"
   temp_min_c = temp_k2c ( json_out_cur['main']['temp_min'] )
   print "Temp.min    : " + str(temp_min_c) + " Grad"
   temp_max_c = temp_k2c ( json_out_cur['main']['temp_max'] )
   print "Temp.max    : " + str(temp_max_c) + " Grad"

   # ----------------------------------------------------------------------------------------
   print "\n------------------------- Vorhersage - 3 Tage / 3h"

   if verbose_level > 0 :
   	print "open JSON file: ", ow_file_for

   try:
	   with open(ow_file_for, 'r') as json_file:
	   	json_out_for = json.load(json_file)
   except:
   		print "PANIC: cannot open file: "  + ow_file_for
		sys.exit(1)

   if verbose_level > 1 :
	   pp.pprint(json_out_for)

   print "Stadt       : " + str(json_out_for['city']['name'])
   print "Einträge    : " + str(json_out_for['cnt'])
   count =  json_out_for['cnt']
   #      2013-06-28 18:00:00  12.6 Grad  11.6 Grad  12.6 Grad
   print "Zeit                 Temp       Temp.min   Temp.max"
   cur_date = "cur"
   old_date = "old"
   temp_d_min = 0
   temp_d_max = 0
   for x in range(1,count):
       cur_stamp = json_out_for['list'][x]['dt_txt']
       cur_date = cur_stamp[0:10]
       cur_hour = cur_stamp[11:13]
       if x > 0:
          if cur_date != old_date:
             print temp_d_min, temp_d_max
             temp_d_min = 100
             temp_d_max = -100
             
          old_date = cur_date
       #print cur_date, cur_hour
       print "" + str(json_out_for['list'][x]['dt_txt']) + "",
   
       temp_cur_c = temp_k2c ( json_out_for['list'][x]['main']['temp'] )
       print " " + str(temp_cur_c) + " Grad",
 
       temp_min_c = temp_k2c ( json_out_for['list'][x]['main']['temp_min'] )
       if temp_min_c < temp_d_min:
          temp_d_min = temp_min_c
       print " " + str(temp_min_c) + " Grad",
 
       temp_max_c = temp_k2c ( json_out_for['list'][x]['main']['temp_max'] )
       if temp_max_c > temp_d_max:
          temp_d_max = temp_max_c
       print " " + str(temp_max_c) + " Grad",
   
       print " " + str(json_out_for['list'][x]['main']['humidity']) + "%",
       print " " + str(int(json_out_for['list'][x]['main']['pressure'])) + " hPa",
       print " " + str(int(json_out_for['list'][x]['main']['deg'])) + " Grad",
       wind_speed = json_out_for['list'][x]['wind']['speed']
       wind_speed = speed_mps2ms(wind_speed)
       print " " + str(wind_speed) + " m/s",
       print " " + str(json_out_for['list'][x]['clouds']['all']) + " %",
       print " " + str(json_out_for['list'][x]['weather'][0]['icon']) + "",
       print " " + str(json_out_for['list'][x]['weather'][0]['id']) + "",
       print " " + str(json_out_for['list'][x]['weather'][0]['main']) + "",
       print " " + str(json_out_for['list'][x]['weather'][0]['description']) + "",
       print

   # ----------------------------------------------------------------------------------------
   print "\n------------------------- Vorhersage - 7 Tage"

   if verbose_level > 0 :
   	print "open JSON file: ", ow_file_for7

   try:
	   with open(ow_file_for7, 'r') as json_file:
	   	json_out_for = json.load(json_file)
   except:
   		print "PANIC: cannot open file: "  + ow_file_for7
		sys.exit(1)

   if verbose_level > 1 :
	   pp.pprint(json_out_for)

   print "Stadt       : " + str(json_out_for['city']['name'])
   status = datetime.fromtimestamp(json_out_cur['dt']).strftime('%Y-%m-%d %H:%M')
   print "Stand       : " + status
   print "Einträge    : " + str(json_out_for['cnt'])
   count =  json_out_for['cnt']
   #      2013-06-28 18:00:00  12.6 Grad  11.6 Grad  12.6 Grad
   print "Zeit                 Temp       Temp.min   Temp.max"
   for x in range(1,count):
       print "Tag-" + str(x),
       print " " + str(json_out_for['list'][x]['humidity']) + "%",
       print " " + str(int(json_out_for['list'][x]['pressure'])) + " hPa",
       print " " + str(int(json_out_for['list'][x]['deg'])) + " Grad",
       wind_richtung =  wind_deg2txt(json_out_for['list'][x]['deg'])
       print " " + wind_richtung + "",
       wind_speed = json_out_for['list'][x]['speed']
       wind_speed = speed_mps2ms(wind_speed)
       print " " + str(wind_speed) + " m/s",
       print " " + str(json_out_for['list'][x]['clouds']) + " %",
       print " " + str(json_out_for['list'][x]['weather'][0]['icon']) + "",
       print " " + str(json_out_for['list'][x]['weather'][0]['id']) + "",
       print " " + str(json_out_for['list'][x]['weather'][0]['main']) + "",
       print " " + str(json_out_for['list'][x]['weather'][0]['description']) + "",
       print
