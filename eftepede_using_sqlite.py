#! /usr/bin/python

import sys
import os
import sqlite3
import datetime
import threading
import Queue

class SQLiteThread(threading.Thread):
    def __init__(self, config, logger):
        threading.Thread.__init__(self)
        self.setDaemon(True)
        self.filename = config.get_setting("sqlite_filename", "")        
        self.logger = logger
        self.msgport = Queue.Queue()
    
    def run(self):
        self.logger.info("SQLite uses filename %r" % (self.filename, ))
        self.db = sqlite3.connect(self.filename)
        self.create_default_tables()

        while True:
            msg = self.msgport.get()            
            msg[0](*msg[1:])

    def create_default_tables(self):

        # a user is a mailbox on the system. a system can have any number of mailboxes. 
        self.db.execute("""CREATE TABLE IF NOT EXISTS users (
name TEXT PRIMARY KEY,
password TEXT,
homedir TEXT,
perm TEXT,
msg_login TEXT,
msg_quit TEXT);""")

        self.db.commit()
        
    def select(self, stmt, params, result):
        result.put([line for line in self.db.execute(stmt, params)])

    def commit(self, stmt, params, result):
        t = self.db.execute(stmt, params)
        self.db.commit()
        result.put(t)

    def execute_many(self, stmt, params, result):
        t = self.db.executemany(stmt, params)
        self.db.commit()
        result.put(t)

    def disconnect(self):    
        self.db.close()
        self.db = None           
        
class SQLite3Database(object):   
    
    def __init__(self, config, logger):
        self.sqlite_thread = SQLiteThread(config, logger)
        self.logger = logger
        self.sqlite_thread.start()
        
    def select(self, stmt, params):
        result = Queue.Queue()
        self.sqlite_thread.msgport.put([self.sqlite_thread.select, stmt, params, result])
        return result.get()

    def commit(self, stmt, params):
        result = Queue.Queue()
        self.sqlite_thread.msgport.put([self.sqlite_thread.commit, stmt, params, result])
        return result.get()

    def execute_many(self, stmt, params):
        result = Queue.Queue()
        self.sqlite_thread.msgport.put([self.sqlite_thread.execute_many, stmt, params, result])
        return result.get()
        
    def add_user(self, username, password, homedir, perm, msg_login, msg_quit):
        stmt = "INSERT INTO users (name, password, homedir, perm, msg_login, msg_quit) VALUES (?,?,?,?,?,?);"
        args = (username, password, homedir, perm, msg_login, msg_quit, )
        return self.commit(stmt, args)

    def remove_user(self, username):
        stmt = "DELETE FROM users WHERE name=?;"
        args = (username, )
        return self.commit(stmt, args)

        result = self.db.identify(username)
        if result is None:
            self.logger.warn("Warning, validate_authentication(%r) failed: no such user" % (username, ))
            return False
            
    def identify(self, username):
        stmt = "SELECT password,homedir,perm,msg_login,msg_quit FROM users WHERE name=?"
        args = (username, )
        for row in self.select(stmt, args):
            return tuple(row)
        return None
        
    def has_user(self, username):
        stmt = "SELECT password FROM users WHERE name=?"
        args = (username, )
        for row in self.select(stmt, args):
            return True
        return False
        
    def list_users(self):
        return self.select("SELECT name,password,homedir,perm,msg_login,msg_quit FROM users ORDER BY name", [])
              
if __name__ == "__main__":
    import eftepede_server
    eftepede_server.main()
