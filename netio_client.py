#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# client for netio server
# 2013-05-12 V0.1 by Thomas Hoeser
#
import socket
import sys
import argparse # analyze command line arguments

HOST, PORT = "192.168.178.62", 54321

parser = argparse.ArgumentParser(description='NetIO client by Thomas Hoeser / 2013')
parser.add_argument("-H", "--Host", default=False, dest='host', help="define Host", type=str)
parser.add_argument("-P", "--Port", default=False, dest='port', help="define Port", type=int)
parser.add_argument('values', metavar='v', type=str, nargs='+',
                   help='values to send')
args = parser.parse_args()
	
if args.port	:  PORT = args.port
if args.host	:  HOST = args.host

data = " ".join(sys.argv[1:])

# Create a socket (SOCK_STREAM means a TCP socket)
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

try:
    # Connect to server and send data
	sock.connect((HOST, PORT))
	sock.sendall(data + "\n\n")
	print "send data >", data, "< to host", HOST, "and port", PORT

    # Receive data from the server and shut down
	received = sock.recv(1024)
	print "Sent:     {}".format(data)
	print "Received: {}".format(received)
	
except IOError:	
	print "PANIC : cannot establish connection - is server up ?"
	print "Host  :", HOST
	print "Port  :", PORT
	sys.exit(1)

finally:
    sock.close()


