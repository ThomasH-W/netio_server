# -*- coding: utf-8 -*-

# -----------------------------------------------------------------------------------------------
# use this section to set the parameters for your setup
# -----------------------------------------------------------------------------------------------

HOST = ''	# 
PORT = 54321			# enter port number

# dictionary with for send command: [group code] [device]
light_dict  = {	"Wohnz" 		: "00101 1",
				"Flur1"   		: "00101 2",
				"Flur2"   		: "11111 3",
				"Garage" 		: "11111 4",
				"Black"  		: "11111 5",
				"Wohnzimmer"	: "10011 1",
				"Flur"			: "10011 2",
				"Kueche"		: "10011 3",
				"Brunnen"		: "10011 4",
				"Fernseher"		: "10011 5",
				"Kinderzimmer"	: "10001 1"
				}

# dictionary with for 1-wire sensors: [sensor name] [1-Wire device]
sensor_dict = {	"Wohnzimmer": "28-00000487bb70",
				"Terrasse"      : "28-000004881dd5",
				"Wintergarten"  : "28-000004885b83",
				"Aussen"        : "28-000004881b78",
				"WW_Speicher"      : "28-00000487e239",
				"Ruecklauf"  : "28-000004884121",
				"Vorlauf"        : "28-00000487ae73",
				"Pool"          : "28-000004be1337"
				}

openweather_path = "/home/pi"    # directory where JSON files are located
time_multi = 1	   # 1: value are seconds, 60: value should be minutes
debug_level   = 0  # 1 will prevent executing send command or reading 1-wire sensor

# verbose 1: display client commands // 2: 1 + display server reply // 2 + debug messages
verbose_level = 1

# this is the file where the status is stored
pickle_file  = "433_status.p"
server_init_mode = "resetno" # read pickle file , no send command
# server_init_mode = "reset" # use send command to switch off all lights when server is started

# this is the standard command to switch the ELRO 433 MHz devices
oscmd_Light  = "sudo /home/pi/raspberry-remote/./send "
# sudo /home/pi/raspberry-remote/./send  00101 5 0

# an alternative command to switch some other 433 MHz devices
oscmd_Light2 = "sudo /home/pi/433/./433send "
# sudo /home/pi/433/./433send2  -k 00101 -d 5 -s 0

# Timer: 
# Mode 0: switch to [state] when timer elapsed
# Mode 1: switch to [state] when timer starts and to ![state] when elapsed
timer_mode = 1
t = 0

# lan computers defined in /etc/host and /etc/ethers
# 				pc-name   : [operating system, username, password]
lan_dict = {	"raspi1" : ["linux","pi","raspberry"], 
				"raspi2" : ["linux","pi","raspberry"],
				"fritzi" : ["linux","pi","raspberry"],
				"mahjong": ["win7","shutdown","raspdx"],
				"avatar" : ["win8","shutdown","raspdx"],
        "phoenix": ["win8","shutdown","raspdx"]
				}

# this is the file where the status is stored
log_level = 0 # 0: no log; 1: save messages to logifle
log_file  = "netio_logfile.txt"
