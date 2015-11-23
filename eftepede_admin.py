#! /usr/bin/python

import sys
import eftepede_server
import eftepede_globals
import pprint
import os

class eftepedeConsoleAdmin(object):
    
    def __init__(self):
        self.command = None
        self.server = eftepede_server.eftepede_server()
        
    def run(self):
        if not self.parse_input_args():
            return self.show_help()
            
        return self.command(*self.args)
    
    def parse_input_args(self):
        
        mode = None
        self.args = []
        
        for index, arg in enumerate(sys.argv):
            if index > 0:
                keyword = arg.lower()
                
                if keyword in ('list', 'add', 'del', ):
                    mode = keyword

                elif keyword in ('help', '/?', '--help', ):
                    if mode == None:
                        self.command = self.show_help
                    else:
                        return False
                        
                elif keyword == 'users':
                    if mode == 'list':
                        self.command = self.list_users
                    else:
                        return False
                        
                elif keyword == 'user':
                    if mode == 'add':
                        self.command = self.add_user
                        self.args = sys.argv[index+1:]
                    elif mode == 'del':
                        self.command = self.del_user
                        self.args = sys.argv[index+1:]
                    else:
                        return False
                        
        return self.command is not None
    
    def show_help(self):
        print "USAGE: %s ACTION [ARGUMENTS]" % (sys.argv[0], )
        print
        print "where ACTION is one of:"
        print 
        print " LIST USERS ................................................. lists all users"
        print " ADD USER name password [homedir [perm [login [logoff]]]] ... create a new user"
    
    def list_users(self):
        pattern = "%20s | %25s | %20s | %10s | %18s | %10s"
        print pattern % ("Name", "Password", "Homedir", "Permission", "Login", "Logoff", )
        print "_" * 120

        for line in eftepede_globals.Database.list_users():
            print pattern % tuple(line)

    def add_user(self, username, password, homedir=".", perm='elr', msg_login="Login successful.", msg_quit="Goodbye."):        
        if homedir == ".":
            homedir = os.getcwd()
            
        return self.server.authorizer.add_user(username,  password, homedir, perm, msg_login, msg_quit)

    def del_user(self, *usernames):
        for username in usernames:
            self.server.authorizer.remove_user(username)
            
if __name__ == "__main__":    
    eftepedeConsoleAdmin().run()
