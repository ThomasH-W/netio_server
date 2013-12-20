#!/usr/bin/python
# -*- coding: utf-8 -*-
# server for netio server
# 2013-12-20 V1.9b by Thomas Hoeser

# ChangeLog V1.9
# fixed error for gpio command - thanks to micmuec
# gpio added - provided by Bart / Tobi 
# http://www.forum-raspberrypi.de/Thread-netio-app-spielereien-gemeinschaftsprojekt



from netio_config import HOST, PORT, light_dict,sensor_dict, time_multi,debug_level,verbose_level,oscmd_Light, pickle_file,server_init_mode,oscmd_Light2,timer_mode,t,lan_dict,log_level,log_file, openweather_path
# -----------------------------------------------------------------------------------------------
# usually you do not need change the code below

# To do:
# read  from remote database avrio

import locale
# locale.setlocale(locale.LC_ALL, 'de_DE')

import SocketServer, socket
SocketServer.TCPServer.allow_reuse_address = True
# if the server is getting terminated with Ctrl-C the socket is not closed and you need to wait sometime
# allow_reuse_address will overcome this
import sys
import os
import subprocess
import random
import pickle
import time
import threading
import argparse # analyze command line arguments

import urllib2, json, pprint
from datetime import datetime, timedelta

# Name to be used in NetIO for on and off
LightCmdOn     = "an"
LightCmdOff    = "aus"
LightCmdStatus = "status"
LightCmdStop   = "stop"

LanCmdOn     = "an"
LanCmdOff    = "aus"
LanCmdStatus = "status"

# The following dict looks odd - but I started wiht a different concept.
server_dict = { "read"   : "read",
                "licht"  : oscmd_Light,
                "licht2" : oscmd_Light2,
				"wetter" : "wetter",
				"temp"   : "Temp",
				"system" : "system",
				"timer"  : "Timer",
				"linux"	 : "Linux",
				"lan"    : "Lan",
				"log"	 : "Log",
				"gpio" : "gpio",
				"dict"   : "dict"
				}

# dictionary with will be create during init phase of server
light_state	= {}
timer_state	= {}

# multiple timers - not yet implemented
timer		= [0,0,0,0,0]

LightMode   = 0
server_cmd  = ""
server_reply= ""
client_cmd  = ""
os_cmd      = ""
send433     = 0

# ring buffer for log entries
class RingBuffer:
    def __init__(self, size):
        self.data = [None for i in xrange(size)]
    def append(self, x):
        self.data.pop(0)
        self.data.append(x)
    def get(self):
        return self.data
		
max_log_entries = 100
log_buffer = RingBuffer(max_log_entries)
log_buffer.append("server definitions loaded")

id_dict_name = {
              '01d' : ['d_0_M','wolkenlos'],        # 'sky is clear'
              '01n' : ['n_0_M','wolkenlos'],        # 'sky is clear'
              '02d' : ['d_1_M','leicht_bewoelkt'],  # 'few clouds'
              '02n' : ['n_1_M','leicht_bewoelkt'],  # 'few clouds'
              '03d' : ['d_2_M','bewoelkt'],         # 'scattered clouds'
              '03n' : ['n_2_M','bewoelkt'],         # 'scattered clouds'
              '04d' : ['d_3_M','bedeckt'],          # 'broken clouds'
              '04n' : ['n_3_M','bedeckt'],          # 'broken clouds'
              '09d' : ['d_5_M','Schauer'],          # 'shower rain'
              '09n' : ['n_5_M','Schauer'],          # 'shower rain'
              '10d' : ['d_55_M','Regen'],           # 'Rain'
              '10n' : ['n_55_M','Regen'],           # 'Rain'
              '11d' : ['d_9_M','Gewitter'],         # 'Thunderstorm'
              '11n' : ['n_9_M','Gewitter'],         # 'Thunderstorm'
              '13d' : ['d_61_M','Schnee'],          # 'snow'
              '13n' : ['n_61_M','Schnee'],          # 'snow'
              '50d' : ['d_4_M','Nebel'],            # 'mist'
              '50n' : ['n_4_M','Nebel']             # 'mist'
                }    

#---------------------------------------------------------------------------------------------
def srvcmd_gpio(server_cmd,client_words,client_args):

	# examples
	# "gpio", "set", "gpio7", "1"
	# "gpio", "set", "gpio7", "0"
	# "gpio", "check", "gpio7"
 
		if verbose_level > 2:  
			print "++++ srvcmd_gpio()"
		server_reply = "unf: srvcmd_gpio"

		if client_words[1] == "set":
			GPIO = client_words[2]
			LEDValue = client_words[3]
			file = "/sys/class/gpio/"+GPIO+"/value"
			f = open(file, 'w')
			f.write(LEDValue)
			f.close
			server_reply = "Written " + LEDValue + " to " + GPIO
		elif client_words[1] == "check":
			GPIO = client_words[2]
			file = "/sys/class/gpio/"+GPIO+"/value"
			f = open(file, 'r')
			server_reply = f.read()
		else:
			server_reply = "wrong command"


		return(server_reply)

#---------------------------------------------------------------------------------------------
def systemInfo(server_cmd,client_words,client_args): # von Mario

		if verbose_level > 2:  
			print "++++ systemInfo()"
		server_reply = "unf: systemInfo"

		# vcgencmd measure_clock arm    Taktfrequenz abfragen
	 	# clock: arm, core, h264, isp, v3d, uart, pwm, emmc, pixel, vec, hdmi, dpi.

		# vcgencmd measure_temp					Temperatur auslesen

		# vcgencmd get_mem arm/gpu

		# vcgencmd measure_volts core  	Spannung abfragen
		# volts:  core, sdram_c, sdram_i, sdram_p

		hardware = client_words[1]
		hardware = hardware.lower()
		info     = client_words[2]
		info = info.lower()

		if hardware == "cpu":
			 if info == "temp":
			 		res = os.popen('vcgencmd measure_temp').readline()
					server_reply = (res.replace("temp="," ").replace("'C\n",""))
		elif info == "use":
	 			server_reply = "bald"
				 						 	 			 
		return(server_reply)

#---------------------------------------------------------------------------------------------
def ow_id2icon(id):
    if verbose_level > 2:  
       print "++++ ow_id2icon()"
       print "id = ", id
    
    id_entry = id_dict_name.get(id)
    icon_name = id_entry[0]
    icon_text = id_entry[1]
        
    if verbose_level > 2:
       print  icon_name
       print  icon_text   
       
    return(icon_name,icon_text)

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
def ow_read_field(ow_city,owField):
    #
	# NetIO: Wetter {city} {field}
	# fields provided using field help - see below
	if verbose_level > 2:  print "++++ ow_read_field()"
	server_reply = "unf: ow_read_field"

	ow_file_cur = openweather_path + "/ow_" + ow_city + "_cur.json"
	try:
		with open(ow_file_cur, 'r') as json_file:
   			json_out_cur = json.load(json_file)
	except:
		server_reply = "PANIC: cannot open file: "  + ow_file_cur
		sys.stderr.write(server_reply)
		return(server_reply)

	ow_file_for = openweather_path + "/ow_" + ow_city + "_for7.json"
	try:
		with open(ow_file_for, 'r') as json_file:
			json_out_for = json.load(json_file)
	except:
		server_reply = "PANIC: cannot open file: "  + ow_file_for
		return(server_reply)

	for_count = 7
 
	UX_Fcst  = json_out_cur['dt']              # read UNIX Timestamp from JSON file
	DT_Fcst  = datetime.fromtimestamp(UX_Fcst) # create datetime object using UNIX timestamp
	DayDelta = timedelta(days=1)               # define delta to add
 
 
	if owField == "help":
		server_reply = "stand, temp, tempmax, tempmin, wind, windg, windr, aufgang, untergang, feuchte, druck, wolken, himmel, icon, owid, tag"
   
	elif owField == "tag":
		server_reply = DT_Fcst.strftime("%a")       # get weekday from datetime object
		print server_reply
		for x in range(0,for_count):
			DayX = DT_Fcst + timedelta(days=x+1)      # calculate foredcast date
			server_reply += "  " + DayX.strftime("%a")# get weekday from datetime object 

 	elif owField == "stand":
   		status = datetime.fromtimestamp(json_out_cur['dt']).strftime('%Y-%m-%d %H:%M')
		server_reply = "Stand: " + status
	elif owField == "aufgang":
		aufgang = datetime.fromtimestamp(json_out_cur['sys']['sunrise']).strftime('%H:%M')
		server_reply = "SonnenAufgang: " + aufgang
	elif owField == "untergang":
		untergang = datetime.fromtimestamp(json_out_cur['sys']['sunset']).strftime('%H:%M')
		server_reply = "SonnenUntergang: " + untergang


	elif owField == "temp":
		server_reply = "Temp: " + str(temp_k2c ( json_out_cur['main']['temp'] )) + " Grad"
		for x in range(0,for_count):
			server_reply += " | " + str(temp_k2c ( json_out_for['list'][x]['temp']['day'] ))
   
	elif owField == "tempmax":
		server_reply = "Temp Max: " + str(int(temp_k2c ( json_out_cur['main']['temp_max'] ))) + " Grad"
		for x in range(0,for_count):
			server_reply += " | " + str(int(temp_k2c ( json_out_for['list'][x]['temp']['max'] )))

	elif owField == "tempmin":
		server_reply = "Temp Min: " + str(int(temp_k2c ( json_out_cur['main']['temp_min'] ))) + " Grad"
		for x in range(0,for_count):
			server_reply += " | " + str(int(temp_k2c ( json_out_for['list'][x]['temp']['min'] )))

	elif owField == "windg":
   		wind_speed = json_out_cur['wind']['speed']
		wind_speed = speed_mps2ms(wind_speed)
		server_reply = "Windgeschwindigkeit: " + str(wind_speed) + " m/s"
		for x in range(0,for_count):
			server_reply += " | " + str(speed_mps2ms( json_out_for['list'][x]['speed']))

	elif owField == "windr":
		server_reply = "Windrichtung: " + str(json_out_cur['wind']['deg'])   + " Grad"
		for x in range(0,for_count):
			server_reply += " | " + str(int( json_out_for['list'][x]['deg']))

	elif owField == "wind":
		server_reply = wind_deg2txt(json_out_cur['wind']['deg'])
		for x in range(0,for_count):
			server_reply += " | " + wind_deg2txt(json_out_for['list'][x]['deg'])

	elif owField == "wolken":
		server_reply = "Wolken: " + str(json_out_cur['clouds']['all']) + "%"
		for x in range(0,for_count):
			server_reply += " | " + str(json_out_for['list'][x]['clouds'])

	elif owField == "himmel":
		icon = ow_id2icon(json_out_cur['weather'][0]['icon'])   
		server_reply = icon[1]
		for x in range(0,for_count):
			icon = ow_id2icon(json_out_for['list'][x]['weather'][0]['icon'])
			server_reply += " " + icon[1]	
      
	elif owField == "image":
		icon = ow_id2icon(json_out_cur['weather'][0]['icon'])
		server_reply = " " + icon[0]	
		for x in range(0,for_count):
			icon = ow_id2icon(json_out_for['list'][x]['weather'][0]['icon'])
			server_reply += " " + icon[0]	


	elif owField == "icon":
		server_reply = "Himmel Icon: " + str(json_out_cur['weather'][0]['icon']) + ""
		for x in range(0,for_count):
			server_reply += " | " + str(json_out_for['list'][x]['weather'][0]['icon'])

	elif owField == "owid":
		server_reply = "Himmel ID: " + str(json_out_cur['weather'][0]['id']) + ""
		for x in range(0,for_count):
			server_reply += " | " + str(json_out_for['list'][x]['weather'][0]['id'])

	elif owField == "feuchte":
		server_reply = "Feuchte: " + str(json_out_cur['main']['humidity']) + " %"
		for x in range(0,for_count):
			server_reply += " | " + str(int( json_out_for['list'][x]['humidity'] ))

	elif owField == "druck":
		DruckVortag = int(json_out_cur['main']['pressure'])
		server_reply = str(DruckVortag) + " h"
		for x in range(0,for_count):
			DruckAktuell = int( json_out_for['list'][x]['pressure'])
			server_reply += " | " + str(DruckAktuell)
			DruckDelta = DruckVortag - DruckAktuell
			DruckTendenz = 10
			if (DruckDelta > 20): 
			   server_reply += " N"  # fallend
			elif (DruckDelta > 10): 
			   server_reply += " NW"  # leicht fallend
			elif (DruckDelta < -20): 
			   server_reply += " SW"  # steigend
			elif (DruckDelta < -10): 
			   server_reply += " S"  # leicht steigend			
			else:
			   server_reply += " W"   # gleich
			DruckVortag = DruckAktuell

	else:
		server_reply = "unknown field: " +  owField
   
	print server_reply

	return(server_reply)

#---------------------------------------------------------------------------------------------
def srvcmd_weather(server_cmd,client_words,client_args):
	# examples
	# "send", "Wetter", "Wiehl", "Temp"

	if verbose_level > 2:  print "++++ srvcmd_weather()"
	if verbose_level > 2:
		print "weather client_words : ", client_words
		print "weather client_args  : ", client_args

	if (client_args < 3):
		server_reply = "not enougth arguments for command " + client_cmd
		print server_reply
		return (server_reply)

	# get name of field provided as second argument
	OwCity  = client_words[1] # 2nd argument
	OwCity  = OwCity.lower()
	OwField = client_words[2] # 3rd argument
	OwField = OwField.lower()
	if (OwField == "vor"):
		if (client_args < 4):
			server_reply = "not enougth arguments for command " + client_cmd
		else:
			OwDay = client_words[3] # 4th argument
			server_reply =  ow_read_field_fcst(OwCity,OwDay)
	else:
		server_reply =  ow_read_field(OwCity,OwField)
	return(server_reply)


#---------------------------------------------------------------------------------------------
def unix_cmd(os_cmd):

	# cmd = 'echo "Hello world!"'   # to be used as test for checking popen
	server_reply = "unix_cmd()"
	
	if debug_level == 0:
		# OLD - process = os.popen(os_cmd)
		if verbose_level > 0: print "subprocess.Popen:", os_cmd
		process = subprocess.Popen(os_cmd, shell=True,stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		system_reply = process.communicate()
		
		# process.poll() poll response - but doe not wait for process to be finished
		process.wait()

		system_retcode = process.returncode
		if system_retcode:
			server_reply= "ERROR: " + str( system_retcode)  + ": " + str(system_reply)
		else:
			server_reply= "ok: " + str( system_retcode)   + ": " + str(system_reply)
		if verbose_level > 0:
			print server_reply

	else:
		print "DEBUG do not execute os-cmd " , os_cmd


	return(system_retcode,server_reply)

#---------------------------------------------------------------------------------------------
def lan_status(host_name):
	
	os_cmd_string = "ping -c 1 " + host_name
	unix_reply = unix_cmd(os_cmd_string)
	
	if unix_reply[0] ==0:
		server_reply = "host up / 1"
	else:
		server_reply = "ERROR host down / 0 / " + unix_reply[1]
		
	
	return(server_reply)
#---------------------------------------------------------------------------------------------
def lan_wakeup(host_name):
	os_cmd_string = "wakeonlan " + host_name
	unix_reply = unix_cmd(os_cmd_string)

	wake_reply = unix_reply[1]
	if wake_reply.find('Sending magic') >-1:
		server_reply = "wake up send / 1"
	else:
		server_reply = "ERROR wake on lan failed / 0 / " + unix_reply[1]


	return(server_reply)
#---------------------------------------------------------------------------------------------
def lan_shutdown(host_name):
	try:
		host_ip = socket.gethostbyname(host_name)
	except:
		return("ip address unkown -> please maintain /etc/hosts")
		
	host_data = lan_dict.get(host_name)
	if verbose_level > 3: print host_data
	host_os   = host_data[0]
	host_user = host_data[1]
	host_pw   = host_data[2]
	
	os_cmd_string = "net rpc SHUTDOWN -C 'NetIO shutdown' -f -I " + host_ip + " -U " +host_user +"%" +host_pw
	unix_reply = unix_cmd(os_cmd_string)
	
	if unix_reply[0] ==0:
		server_reply = "host shutdown succesfull / 1"
	else:
		server_reply = "ERROR shutdown failed " + unix_reply[1]
		sys.stderr.write(server_reply)	
	
	return(server_reply)
#---------------------------------------------------------------------------------------------
def lan_sleep(host_name):
	server_reply = unix_cmd("echo 'no clue what to do'")
	return(server_reply)
	
#---------------------------------------------------------------------------------------------
def srvcmd_lan(server_cmd,client_words,client_args):
	# examples
	# "send", "Wohnz", "An"
	# "send", "Wohnz", "Aus"
	# "send", "Wohnz", "status"
	# "send", "Wohnz"

	if verbose_level > 2:  print "++++ srvcmd_lan()"	
	if verbose_level > 3:
		print "lan client_words : ", client_words
		print "lan client_args  : ", client_args
	
	if (client_args < 2):
		server_reply = "not enougth arguments for command " + client_cmd
		print server_reply
		return (server_reply)
			
	# get name of light provided as second argument
	LanName    = client_words[1]
	LanCmd = client_words[2]
	LanCmd = LanCmd.lower()
	
	if verbose_level > 2:
		print "Host:", LanName
		print "L.Cmd:", LanCmd
	# retrieve ID form dictionary
	LanID = lan_dict.get(LanName)
	if (None == LanID):
		print "Computer unknown : " , LanName
		server_reply = "Computer unknwon"
		return (server_reply)			
			
	if verbose_level > 2:
		print "Der Computer " + LanName + " mit id " + str(LanID) + " wird angesprochen"
		
	if LanCmd == LanCmdOn:
		server_reply = lan_wakeup(LanName)
	elif LanCmd == LanCmdOff:
		server_reply = lan_shutdown(LanName)
	elif LanCmd == LanCmdStatus:
		server_reply = lan_status(LanName)
	else:
		server_reply = "unknown command: " +  LanCmd
		sys.stderr.write(server_reply)
    								
	return(server_reply)

#---------------------------------------------------------------------------------------------
def srvcmd_timer(server_cmd,send433,client_words,client_args):
	# examples
	# "Timer", "Wohnz", "An 30"
	# "Timer", "Wohnz", "Stop"
	# "Timer", "Wohnz", "Status"
	global t, light_state, timer_state

	if verbose_level > 2:
		print "++++ srvcmd_timer()"
		print "timer client_words : ", client_words
		print "timer client_args  : ", client_args

	if verbose_level > 2:  print "srvcmd_timer()"
	server_reply="unkown command for timer"

	if (client_args < 3):
		server_reply = "not enougth arguments for command " + client_cmd
		print server_reply
		return (server_reply)

	# get name of light provided as second argument
	Light    = client_words[1]
	LightCmd = client_words[2]
	LightCmd = LightCmd.lower() # convert to lower case, e.g. An -> an

	if verbose_level > 1:
		print "Light  :", Light
		print "L.Cmd  :", LightCmd

	print timer_state
	print timer_state[Light]
	timer_status = timer_state[Light]
	# timer_no = 1

	if (LightCmd == LightCmdOn) or (LightCmd == LightCmdOff):
		if verbose_level > 2:  print "establish timer, Mode ", timer_mode
		# when timer is running, stop timer
		# if timer[timer_no] == 1:
		if timer_status == 1:
			t.cancel

		# Mode 1: switch to [state] when timer starts and to ![state] when elapsed
		if (timer_mode == 1) or (timer_mode == '1'):
			if verbose_level > 2: print "timer mode 1 ... switch light to ", LightCmd
			srvcmd_light(oscmd_Light,send433,["Licht",client_words[1],LightCmd],3)
			if LightCmd == LightCmdOn:
				client_words[2]=LightCmdOff
			else:
				client_words[2]=LightCmdOn
			if verbose_level > 2: print "timer mode 1 ... new light cmd ", client_words[2]

		duration = int(client_words[3]) * time_multi
		client_light = ["Licht",client_words[1],client_words[2],client_words[3]]
		if verbose_level > 3: print client_light
		t = threading.Timer(duration, srvcmd_timcmd, [oscmd_Light,send433,client_light,3])
		# t = threading.Timer(duration, srvcmd_light, [oscmd_Light,client_light,3])
		# timer[timer_no]=1 # set flag that timer is running
		timer_state[Light] = 1
		t.start()
		server_reply=str(duration)

	if LightCmd == LightCmdStop:
		if verbose_level > 0:  print "stop timer"
		# if (timer[timer_no] == 0) or (timer[timer_no] == '0'):
		if (timer_status == 0) or (timer_status == '0'):
			server_reply="timer not running"
		else:
			# timer_no = 1
			# timer[timer_no]=0 # set flag that timer is running
			timer_state[Light] = 0
			server_reply="timer on hold / cancelled"
			t.cancel()

	if LightCmd == LightCmdStatus:
		if verbose_level > 2:  print "timer status"
		# if (timer[timer_no] == 0) or (timer[timer_no] == '0'):
		if (timer_status == 0) or (timer_status == '0'):
			server_reply = "timer not running "
		else:
			server_reply = "timer is  running "

	return(server_reply)
#---------------------------------------------------------------------------------------------
# need this function in the middle to reset timer status
def srvcmd_timcmd(server_cmd,send433,client_words,client_args):
	srvcmd_light(server_cmd,send433,client_words,client_args)
	timer_state[client_words[1]] = 0
	# timer_no = 1
	# timer[timer_no]=0


#---------------------------------------------------------------------------------------------
def srvcmd_light(server_cmd,send433,client_words,client_args):
	# examples
	# "send", "Wohnz", "An"
	# "send", "Wohnz", "Aus"
	# "send", "Wohnz", "status"
	# "send", "Wohnz"

	if verbose_level > 2:  print "++++ srvcmd_light()"
	if verbose_level > 2:
		print "light client_words : ", client_words
		print "light client_args  : ", client_args

	if (client_args < 2):
		server_reply = "not enougth arguments for command " + client_cmd
		print server_reply
		return (server_reply)

	# get name of light provided as second argument
	Light    = client_words[1]
	LightCmd = client_words[2]
	LightCmd = LightCmd.lower()

	if verbose_level > 2:
		print "Light:", Light
		print "L.Cmd:", LightCmd
	# retrieve ID form dictionary
	LightID = light_dict.get(Light)
	if (None == LightID):
		print "Light unknown : " , Light
		server_reply = "Light unknwon"
		return (server_reply)

	if verbose_level > 2:
		print "Die Leuchte " + Light + " mit id " + str(LightID) + " wird angesprochen"
		
	if LightCmd == LightCmdOn:
		switch_light(server_cmd,send433,str(LightID),"1",Light)
		server_reply = LightCmdOn
	elif LightCmd == LightCmdOff: 
		switch_light(server_cmd,send433,str(LightID),"0",Light)
		server_reply = LightCmdOff
	elif LightCmd == LightCmdStatus: 
		server_reply = check_light(Light)
	else:
		server_reply = "unknown command: " +  LightCmd
		sys.stderr.write(server_reply)
    								
	return(server_reply)
#---------------------------------------------------------------------------------------------
def switch_light(server_cmd,send433,LightID,State,LightName):
	# instead of os.popen subprocess could be used
	# subprocess.call([server_cmd, cmd_args])
	global light_state
	
	if verbose_level > 2:  
		print "++++ switch_light()"	
		print "send433   :", send433
		print "server_cmd:", server_cmd
		print "LightID   :", LightID
		print "State     :", State

	if (send433 == 1) or (send433 == '1'):
		LE = LightID.split(' ')
		cmd = server_cmd + " -k " + LE[0] + " -d " + LE[1]+ " -s " + State
	else:
		cmd = server_cmd + " " + LightID + " " + State
		
	# cmd = 'echo "Hello world!"'   # to be used as test for checking popen
	if debug_level == 0:
		# OLD - process = os.popen(cmd)
		if verbose_level > 2: print "subprocess.Popen:", cmd
		process = subprocess.Popen(cmd, shell=True,stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		system_reply = process.communicate()
		
		# process.poll() poll response - but doe not wait for process to be finished
		process.wait()

		system_retcode = process.returncode
		if system_retcode:
			server_reply= "ERROR: " + str( system_retcode)  + ": " + str(system_reply)
		else:
			server_reply= "ok: " + str( system_retcode)   + ": " + str(system_reply)
		if verbose_level > 1:
			print server_reply

	else:
		print "DEBUG do not execute os-cmd " , cmd
		
	light_state[LightName]=State
	if verbose_level > 2: print light_state
	pickle.dump( light_state, open( pickle_file, "wb" ) )

	return(0)
#---------------------------------------------------------------------------------------------
def check_light(LightName):
	if verbose_level > 2:  print "++++ check_light()"	
	
	light_val = light_state[LightName]
	if verbose_level > 2:  
		print "Licht" , LightName, " - Status: ", light_val

	if (light_val == 0) or (light_val == '0') :
		server_reply = LightName + " Aus / " + str(light_val)
	else:
		server_reply = LightName + " An  / " + str(light_val)
	
	if verbose_level > 3:  
		print light_val
		print server_reply
	
	return(server_reply)
  
#---------------------------------------------------------------------------------------------
def read_sensor(Sensor):

	if verbose_level > 2:  
		print "++++ read_sensor()"	
		print "sensor:" , Sensor
	if debug_level == 0:
		# get 1-Wire id from dictionary
		sensor_slave = str(sensor_dict.get(Sensor))
		# Open 1-wire slave file
		sensor_device = '/sys/bus/w1/devices/' + str(sensor_slave) + '/w1_slave'
		if verbose_level > 2:  
			print "open: ", sensor_device
		try:
			file = open(sensor_device)
			filecontent = file.read()                         # Read content from 1-wire slave file
			stringvalue = filecontent.split("\n")[1].split(" ")[9] # Extract temperature string
			if stringvalue[0].find("YES") > 0: # 2nd try
				sys.stderr.write("read_sensor_ CRC error")
				time.sleep(0.5) # grace period
				filecontent = file.read() 											# Read content from 1-wire slave file
				stringvalue = filecontent.split("\n")[1].split(" ")[9]	
				if stringvalue[0].find("YES") > 0:
					sys.stderr.write("read_sensor_ CRC error")
					temp =  999
				else:
					temp = float(stringvalue[2:]) / 1000  													 
			else:
				temp = float(stringvalue[2:]) / 1000            # Convert temperature value
               
			file.close()	# Close 1-wire slave file
			temp=str(temp)
		except IOError:
			print "PANIC read_sensor - Cannot find file >" + sensor_slave + "< in /sys/bus/w1/devices/"
			print "No sensor attached"
			sys.stderr.write( "check with > cat /sys/devices/w1_bus_master1/w1_master_slaves")
			temp=("Sensor not attached")
	else:
		# this is dummy function generating a random number
		# ony used for testing purposes
		temp = random.randrange(-10, 30, 2) + 0.3
		temp = Sensor + " " + str(temp)
		
	return(temp) # exit function read_sensor

#---------------------------------------------------------------------------------------------
class MyTCPHandler(SocketServer.BaseRequestHandler):
	"""
	The RequestHandler class for our server.

	It is instantiated once per connection to the server, and must
	override the handle() method to implement communication to the
	client. 
	"""
	
	def handle(self):
		while 1:
			# self.request is the TCP socket connected to the client
			self.data = self.request.recv(1024).strip()
			if not self.data: break
			
			client_ip = self.client_address[0]
			client_data = self.data
			if verbose_level >-1 : 
				status = "################# client >" + client_ip + "< send >" + client_data + "<"
				print status
				log_buffer.append(status)
		
			client_words = client_data.split(' ')
			client_cmd   = client_words[0]
			client_args  = len(client_words)
			if verbose_level >2 : print "client command >", client_cmd, "< with ", client_args, " arguments"

		
			# translate client command into server task
			client_cmd = client_cmd.lower()  # convert to lower case to avoid sensitivity
			server_cmd = str(server_dict.get(client_cmd))
		
			# if command is not listed in dictionary, return value is None
			if "None" == server_cmd: 
				print "ERROR: client requested unknown command ", client_cmd
				print "-> please check spelling"
				print "-> commands are defined in server_dict{}, valid commands:"
				print server_dict.keys()
				print
				
				server_reply = "my dear client, your command is unknown: "
			else:
				if verbose_level >2 : print "client requested valid command", client_cmd
				# default message - should be set depending on command
				server_reply = "server will now process your command " + server_cmd	

				# Netio - SetUp
				#   is sending "read commands" as a standard to poll status
				if ( "read" == client_cmd):
					# server_reply = "reply to netio std command " + client_cmd
					server_reply = 'listening'
					print server_reply   
					
				# Netio - SetUp
				# 	Item			Label
				# 	reads			dict
				#   interval 		2000
				if ( "dict" == client_cmd):
					server_reply= str(light_state)

				if ( "log" == client_cmd):
					buff = "server log:\n"
					# ascending:
                    # for i in log_buffer.get():
					#descending:
					for i in (max_log_entries-1,-1,-1):
						if str(i) != 'None':
							buff += str(i) + "\n"
					server_reply = buff
					print server_reply
					

				# NetIO - SetUp
				# 	Item			Switch
				#   onValue			1
				#   onText			An
				#   offText			Aus
				# 	onSend			Licht Wohnz An
				# 	offSend 	 	Licht Wohnz Aus
				# 	reads			Licht Wohnz Status
				#   parseResponse   \d+
				#   formatResponse  {0}
				if ( "licht" == client_cmd):
					server_reply = srvcmd_light(server_cmd,0,client_words,client_args)

				if ( "licht2" == client_cmd):
					server_reply = srvcmd_light(server_cmd,1,client_words,client_args)

				# NetIO - SetUp
				# 	Item			Switch
				# 	onSend			Timer Wohnz An 30
				# 	offSend 	 	Timer Wohnz Stop
				# 	reads			Timer Wohnz
				if ( "timer" == client_cmd):
					server_reply = srvcmd_timer(server_cmd,0,client_words,client_args)

					
				# NetIO - SetUp
				# 	Item			Label
				# 	reads			temp [Sensor Name]
				# 	interval 	 	2000
				# 	parseResponse	\d+
				#	formatResponse	{0},{1}°C
				if ( "temp" == client_cmd):
					Sensor = client_words[1]
					# print "die Temperatur wird vom 1-Wire Sensor oder aus der DB gelesen"
					server_reply = read_sensor(Sensor)

				# NetIO - SetUp
				# 	Item			Label
				# 	onSend			Linux [Sensor Name]
				if ( "linux" == client_cmd):
					server_reply = srvcmd_linux(server_cmd,client_words,client_args)

				# NetIO - SetUp
				# 	Item			Label
				# 	onSend			Lan [Host Name]
				if ( "lan" == client_cmd):
					server_reply = srvcmd_lan(server_cmd,client_words,client_args)


				if ( "wetter" == client_cmd):
					server_reply = srvcmd_weather(server_cmd,client_words,client_args)
					
				# NetIO - SetUp
				# 	Item			Label
				# 	reads			System CPU Temp
				if ( "system" == client_cmd):
					server_reply = systemInfo(server_cmd,client_words,client_args)

				# NetIO - SetUp
				# 	Item		Button
				# 	onSend  gpio set gpio7 1
				if ( "gpio" == client_cmd):
					server_reply = srvcmd_led(server_cmd,client_words,client_args)

			# send feedback to client
			if verbose_level >1: print "server reply: " , server_reply
			log_buffer.append(server_reply)

			self.request.sendall(server_reply)

#------------------------------------------------------------------------------------------------------
def srvcmd_linux(server_cmd,client_words,client_args):
	# examples
	# "Linux", "date"
	# "Linux", "pwd"

	system_cmd = []

	# print client_words
	# print client_args
	
	system_cmd.append(client_words[1])
	if client_args >2:
		system_arg = client_words[2]
		system_cmd.append(system_arg)
	print system_cmd

	if verbose_level > 2:  
		print "++++ srvcmd_linux()"	
		print "command:" , system_cmd
		
	if debug_level == 0:
		# http://jimmyg.org/blog/2009/working-with-python-subprocess.html
		process = subprocess.Popen(system_cmd, shell=False,stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		system_reply = process.communicate()
		# system_reply = process.stdout.readline()
		print system_reply
		
		# process.poll() poll response - but doe not wait for process to be finished
		process.wait()

		system_retcode = process.returncode
		if system_retcode:
			server_reply= "ERROR: " + str( system_retcode)  + ": " + str(system_reply)
		else:
			server_reply= "ok: " + str( system_retcode)   + ": " + str(system_reply)
		print server_reply
	else:
		# this is dummy function generating a feedback
		# ony used for testing purposes
		server_reply = "test test"
		
	return(server_reply) # exit function read_sensor	
#------------------------------------------------------------------------------------------------------ 
def displayText(text, size, line, color, clearScreen):
 
    """Used to display text to the screen. displayText is only configured to display
    two lines on the TFT. Only clear screen when writing the first line"""
    if clearScreen:
        screen.fill((0, 0, 0))
 
    font = pygame.font.Font(None, size)
    text = font.render(text, 0, color)
    textRotated = pygame.transform.rotate(text, -90)
    textpos = textRotated.get_rect()
    textpos.centery = 80  
    if line == 1:
         textpos.centerx = 90
         screen.blit(textRotated,textpos)
    elif line == 2:
        textpos.centerx = 40
        screen.blit(textRotated,textpos)
	print "tft: ", text

#---------------------------------------------------------------------------------------------
def server_init(mode):
	global t, light_state, timer_state

	if verbose_level > 2:  	print "++++ server_init()"

	status = "init light status"
	print status
	log_buffer.append(status)

	# get number of entries in dictionary
	light_count = len(light_dict)
	# print "No. of lights: ", light_count

	# create light state array
	lights=light_dict.keys()
	# print lights
	for x in range(0,light_count):
		# print lights[x]
		light_state[lights[x]] = 0
		timer_state[lights[x]] = 0
	if verbose_level >2 :
		print "lights state:\n" , light_state
		print "timer  state:\n" , timer_state

	# a) power down all light devices
	if(mode == "reset"):
		x1 = ["Licht","xx",LightCmdOff,""]
		server_cmd = str(server_dict.get("licht"))
		for x in range(0,light_count):
			light = lights[x]
			print "send reset light", light
			x1[1] = light
			if verbose_level >1: print x1
			# srvcmd_light(server_cmd,0,clients_words,client_args)
			srvcmd_light(server_cmd,0,x1,4)
	elif(mode == "lightson"):
		x1 = ["Licht","xx",LightCmdOn,""]
		server_cmd = str(server_dict.get("licht"))
		for x in range(0,light_count):
			light = lights[x]
			print "send on to light", light
			x1[1] = light
			if verbose_level >1: print x1
			# srvcmd_light(server_cmd,0,clients_words,client_args)
			srvcmd_light(server_cmd,0,x1,4)
	else:
		print "read state from file"
		try:
			light_state = pickle.load( open( pickle_file, "rb" ) )
			print "lights state:" , light_state
		except IOError:
			print "Warning: file ", pickle_file, "does not exist, assuming all lights are off"


	return (0)

#---------------------------------------------------------------------------------------------
if __name__ == "__main__":

	# example
	# netio_server.py     # start server with default parameters
	# netio_server.py -h  # help : show brief description of options
	# netio_server.py -r  # reset: switch off all lights when starting server and create new pickle file
	# netio_server.py -r -v 3 -H 192.168.178.21 -P 5431
	parser = argparse.ArgumentParser(description='server for NetIO client by Thomas Hoeser / 2013')
	parser.add_argument("-r", "--reset", action='store_const', dest='reset',
                    const='value-to-store', help="switch off all lights when starting server and create new pickle file")
	parser.add_argument("-l", "--lightson", action='store_const', dest='lightson',
                    const='value-to-store', help="switch on all lights when starting server and create new pickle file")
	parser.add_argument("-n", "--noserver", action='store_const', dest='noserver',
                    const='value-to-store', help="do not start server, stop after init")
	parser.add_argument("-t", "--time", action='store_const', dest='time',
                    const='value-to-store', help="1: value are seconds, 60: value should be minutes")
	parser.add_argument("-v", "--verbose", default=False,
                    dest='verbose', help="increase output verbosity", type=int)
	parser.add_argument("-d", "--debug", action='store_const', dest='debug',
                    const='value-to-store', help="debug mode - will prevent executing send command or reading 1-wire sensor")
	parser.add_argument("-H", "--Host", default=False,
                    dest='host', help="define Host", type=str)
	parser.add_argument("-P", "--Port", default=False,
                    dest='port', help="define Port", type=int)
	parser.add_argument("-s", "--show", action='store_const', dest='show',
                    const='value-to-store', help="show configuration")
	parser.add_argument('--version', action='version', version='%(prog)s 0.2')

	args = parser.parse_args()

	if args.verbose	:  verbose_level = args.verbose
	if args.time	:  time_multi = args.time
	if args.reset	:  server_init_mode = "reset"
	if args.lightson:  server_init_mode = "lightson"
	if args.debug	:  debug_level = 1
	if args.port	:  PORT = args.port
	if args.host	:  HOST = args.host

	if args.show	:
		print "Host        : " , HOST
		print "PORT        : " , PORT
		print "pickle file : " , pickle_file
		print "server dict : "
		print server_dict
		print "sensor dict : "
		print sensor_dict
		print "light  dict : "
		print light_dict
		sys.exit(1)

	server_init(server_init_mode) #reset used to switch off all lights

	if args.noserver	:  sys.exit(0)

	try:
		# Create the server, binding to localhost on port 9999
		print "create socket server"
		server = SocketServer.TCPServer((HOST, PORT), MyTCPHandler)

		# Activate the server; this will keep running until you
		# interrupt the program with Ctrl-C
		print "server established on host", HOST, "and port", PORT
		server.serve_forever()

	except socket.error, msg:
		sys.stderr.write("[ERROR] %s\n" % msg[1])
		sys.exit(1)
