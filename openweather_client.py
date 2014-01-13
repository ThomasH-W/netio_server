#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# client for openweather API
# - call PAI
# - translate fields if required
# - save JSON format in a file
# add this programm to crontab: crontab -e
# examle below will be excecuted every 15 minutes
# */15 * * * * python /home/pi/433/openweather_client.py Berlin > crontab_ow_client.log 2>&1

# 2013-06-29 V0.3 by Thomas Hoeser
#

import urllib2, json, sys, pprint, argparse
from time import *

verbose_level = 0
debug_level = 0

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

   print "openweather client V0.3"
   lt = localtime()
   print strftime("Datum und Zeit:  %d.%m %H:%M", lt)

   ow_city =   args.city     # set your city from command line
   ow_country   = "de"
   ow_url_api   = "http://api.openweathermap.org/data/2.5/"
   ow_url_cur   = ow_url_api + "weather?q=" + ow_city + "," + ow_country
   ow_url_fcst  = ow_url_api + "forecast?q=" + ow_city + "," + ow_country
   ow_url_fcst7 = ow_url_api + "forecast/daily?q=" + ow_city + "," + ow_country

   ow_city      = ow_city.lower()
   ow_file_cur  = "ow_" + ow_city + "_cur.json"
   ow_file_for  = "ow_" + ow_city + "_for.json"
   ow_file_for7 = "ow_" + ow_city + "_for7.json"
   
   # file_cur = open(ow_file_cur, 'w')
   # file_for = open(ow_file_for, 'w')

   print "--------------------- GET CURRENT DATA"
   if verbose_level > 1:
		print "# fetchHTML(): "
		print ow_url_cur
   try:
   		print "URL - Request",
		req 			= urllib2.Request(ow_url_cur)
   		print " - Open",
		response		= urllib2.urlopen(req)
   		print " - Read Response"
		output_cur   		= response.read()
   		#output   = fetchHTML(ow_url_cur)
   		json_out_cur 	= json.loads(output_cur)
   		# print json_out_cur
   		if verbose_level > 2: pp.pprint(json_out_cur)
   except:
   		print "Panic: cannot read url:", ow_url_cur

   print "--------------------- GET FORECAST DATA"
   if verbose_level > 1:
		print "# fetchHTML(): "
		print ow_url_fcst
   try:
   		print "URL - Request",
		req 			= urllib2.Request(ow_url_fcst)
   		print " - Open",
		response		= urllib2.urlopen(req)
   		print " - Read Response"
		output_fcst   	= response.read()
   		json_out_fcst 	= json.loads(output_fcst)
   		# print json_out_cur
   		if verbose_level > 2: pp.pprint(json_out_fcst)
   except:
   		print "Panic: cannot read url:", ow_url_fcst

   print "--------------------- GET FORECAST DATA - 7 DAYS"
   if verbose_level > 1:
		print "# fetchHTML(): "
		print ow_url_fcst7
   try:
       print "URL - Request",
       req 			= urllib2.Request(ow_url_fcst7)
       print " - Open",
       response		= urllib2.urlopen(req)
       print " - Read Response"
       output_fcst7   	= response.read()
       json_out_fcst7 	= json.loads(output_fcst7)
       # print json_out_cur
       if verbose_level > 2: pp.pprint(json_out_fcst7)
   except:
          print "Panic: cannot read url:", ow_url_fcst7
      
   print "dump json"
   with open(ow_file_cur, 'w') as outfile:
  		json.dump(json_out_cur, outfile)

   with open(ow_file_for, 'w') as outfile:
  		json.dump(json_out_fcst, outfile)

   with open(ow_file_for7, 'w') as outfile:
  		json.dump(json_out_fcst7, outfile)
