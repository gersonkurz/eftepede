#! /usr/bin/python

import sys
import os
import MySQLdb
import datetime
import threading

class MySQLDatabase(object):   
    
    def __init__(self, config, logger):
        
        self.logger = logger
        self.last_message_id = None
        self.mutex = threading.Lock()
        
        mysql_database = config.get_setting("mysql_database", "eftepede")
        mysql_hostname = config.get_setting("mysql_hostname", "localhost")
        mysql_username = config.get_setting("mysql_username", "")
        mysql_password = config.get_setting("mysql_password", "")
        
        self.logger.info("Using MySQL database \\\\%s\\%s with username %r" % (mysql_hostname, mysql_database, mysql_username, ))
               
        self.db = MySQLdb.connect(host=mysql_hostname, user=mysql_username, passwd=mysql_password, db=mysql_database)
        self.create_default_tables()

    def select(self, stmt, params = None):
        self.mutex.acquire()
        try:
            c = self.db.cursor()
            result = []
            try:        
                c.execute(stmt, params)
                result = map(tuple, c.fetchall())
            finally:
                c.close()        
            return result
        finally:
            self.mutex.release()

    def commit(self, stmt, params = None):
        self.mutex.acquire()
        try:
            c = self.db.cursor()
            try:
                result = c.execute(stmt, params)            
                self.db.commit()
            finally:
                c.close()
            return result
        finally:
            self.mutex.release()

    def execute_many(self, stmt, params = None):
        self.mutex.acquire()
        try:
            c = self.db.cursor()
            c.executemany(stmt, params)
            self.db.commit()
            c.close()
        finally:
            self.mutex.release()

    def disconnect(self):    
        self.db.close()
        self.db = None           

    def create_default_tables(self):      
        # a user is a mailbox on the system. a system can have any number of mailboxes. 
        # WARNING: the password is stored in clear-text, because some authorization methods require this
        # Even if you aren't paranoid, you're strongly recommended to use a non-standard password 'ere.
        
        c = self.db.cursor() 
        
        c.execute("""CREATE TABLE IF NOT EXISTS users (
name TEXT,
passwd TEXT,
homedir TEXT,
perm TEXT,
msg_login TEXT,
msg_quit TEXT);""")
        
        c.execute("COMMIT;")
        
    def add_user(self, username, password, homedir, perm, msg_login, msg_quit):
        args = { 'name' : username, 
                 'password' : password,
                 'homedir' : homedir, 
                 'perm' : perm, 
                 'msg_login' : msg_login, 
                 'msg_quit' : msg_quit }
        stmt = """INSERT INTO users (name, passwd, homedir, perm, msg_login, msg_quit) 
VALUES (%(name)s, %(password)s, %(homedir)s, %(perm)s, %(msg_login)s, %(msg_quit)s);"""
        return self.commit(stmt, args)

    def remove_user(self, username):
        stmt = "DELETE FROM users WHERE name=%(username)s;"
        args = { 'username' : username }
        return self.commit(stmt, args)

        result = self.db.identify(username)
        if result is None:
            self.logger.warn("Warning, validate_authentication(%r) failed: no such user" % (username, ))
            return False
            
    def identify(self, username):
        stmt = "SELECT passwd,homedir,perm,msg_login,msg_quit FROM users WHERE name=%(username)s;"
        args = { 'username' : username }
        for row in self.select(stmt, args):
            return tuple(row)
        return None
        
    def has_user(self, username):
        stmt = "SELECT passwd FROM users WHERE name=%(username)s;"
        args = { 'username' : username }
        for row in self.select(stmt, args):
            return True
        return False
        
    def list_users(self):
        return self.select("SELECT name,passwd,homedir,perm,msg_login,msg_quit FROM users ORDER BY name", [])
        
if __name__ == "__main__":   
    import eftepede_server
    eftepede_server.main()
