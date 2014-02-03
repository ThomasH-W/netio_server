#Use a SocketServer in order to keep the program running on a certain port instead of closing the connection when the netIO is closed on the phone.
import SocketServer
import os
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
                        print "{} wrote:".format(self.client_address[0])
                        print self.data
                        os.popen('sudo /home/pi/raspberry-remote/./send %s' % self.data)
                        # just send back the same data, but upper-cased
                        self.request.sendall('100')
if __name__ == "__main__":
    HOST, PORT = "", 54321
    # Create the server, binding to localhost on port 9999
    server = SocketServer.TCPServer((HOST, PORT), MyTCPHandler)
    # Activate the server; this will keep running until you
    # interrupt the program with Ctrl-C
    server.serve_forever()