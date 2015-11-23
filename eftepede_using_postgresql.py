#! /usr/bin/python

import sys
import os
import pgdb
import datetime
import threading

class PostgresqlDatabase(object):   
    
    def __init__(self, config, logger):
        
        self.logger = logger
        self.last_message_id = None
        self.mutex = threading.Lock()
        
        kwargs = {
            'database' : config.get_setting("postgresql_database", "eftepede"),
            'dsn' : config.get_setting("postgresql_hostname", "localhost"),
            'user' : config.get_setting("postgresql_username", ""),
            'password' : config.get_setting("postgresql_password", ""),
        }
        
        self.logger.info("Using PostgreSQL database \\\\%(dsn)s\\%(database)s with username %(user)r" % kwargs)
        
        self.db = pgdb.connect(**kwargs)
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
                result = c.execute("COMMIT")
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
            c.close()
        finally:
            self.mutex.release()

    def disconnect(self):    
        self.db.close()
        self.db = None           

    def does_table_exist(self, name):
        c = self.db.cursor()
        try:
            args = { 'name' : name.lower() }
            c.execute("SELECT tablename FROM pg_catalog.pg_tables WHERE tablename=%(name)s", args)            
            result = c.fetchone()
            return result is not None
        finally:
            c.close()

    def create_default_tables(self):      
        # a user is a mailbox on the system. a system can have any number of mailboxes. 
        # WARNING: the password is stored in clear-text, because some authorization methods require this
        # Even if you aren't paranoid, you're strongly recommended to use a non-standard password 'ere.
        
        c = self.db.cursor() 
        
        if not self.does_table_exist("users"):
            c.execute("""CREATE TABLE users (
name TEXT PRIMARY KEY,
password TEXT,
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
        stmt = """INSERT INTO users (name, password, homedir, perm, msg_login, msg_quit) 
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
        stmt = "SELECT password,homedir,perm,msg_login,msg_quit FROM users WHERE name=%(username)s;"
        args = { 'username' : username }
        for row in self.select(stmt, args):
            return tuple(row)
        return None
        
    def has_user(self, username):
        stmt = "SELECT password FROM users WHERE name=%(username)s;"
        args = { 'username' : username }
        for row in self.select(stmt, args):
            return True
        return False
        
    def list_users(self):
        return self.select("SELECT name,password,homedir,perm,msg_login,msg_quit FROM users ORDER BY name", [])
        
            
if __name__ == "__main__":
    import eftepede_server
    eftepede_server.main()
