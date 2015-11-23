#! /usr/bin/python

import os
import sys
import eftepede_server
import threading

if os.fork() == 0:
    os.setsid()
    sys.stdout = open("/dev/null","w")
    sys.stdin = open("/dev/null","r")
    
    threading.Thread( target = eftepede_server.main ).start()
    
    # that was easy, right?
