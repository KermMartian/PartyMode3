#!/bin/bash

SCREEN_NAME="partymode"

# Create the screen
screen -S $SCREEN_NAME -d -m -s /bin/bash

# Made the windows, with bash
screen -S $SCREEN_NAME -X screen -t "webserver"

# Now actually get the two pieces set up
screen -S $SCREEN_NAME -p 0 -X stuff "cd /home/r00t/partymode3; sudo ./server.py\r\n"
sleep 10                           # Make sure the server is running and ready to accept connections
screen -S $SCREEN_NAME -p 1 -X stuff "cd /home/r00t/partymode3; ./webserver/webserver.py\r\n"
