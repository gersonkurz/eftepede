#!/usr/bin/python
#! -*- Encoding: Latin-1 -*-

import ConfigParser
import os
import threading
import logging
import logging.handlers
import eftepede_globals
import re
import socket
import pyftpdlib.servers
import pyftpdlib.handlers
import eftepede_authorizer
try:
    import _winreg
except:
    _winreg = None

class config(object):
    pass

class eftepede_server(object):
    def __init__(self):
        self.read_configuration()
        self.logger.info("eftepede! Server %s starting up..." % (eftepede_globals.CURRENT_VERSION, ))
        
    def read_configuration(self):
        # read configuration file 
        self.config_file = ConfigParser.SafeConfigParser()
        self.config_file.read(os.path.join(os.getcwd(), "eftepede_config.ini"))
        self.logger = logging.getLogger('eftepede')
        self.logger.setLevel(logging.CRITICAL)
            
        if self.get_setting("Enabled", True, bool, "Trace"):
            
            LOG_FILENAME = self.get_setting("Filename", os.path.join(os.getcwd(), "eftepede.log"), None, "Trace")

            # Set up a specific logger with our desired output level
            self.logger.setLevel(logging.DEBUG)

            # Add the log message handler to the logger
            handler = logging.handlers.RotatingFileHandler(LOG_FILENAME, 
                maxBytes = self.get_setting("MaxSize", 1024*1024*10, int, "Trace"),
                backupCount = self.get_setting("BackupCount", 3, int, "Trace"))
                
            formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
            handler.setFormatter(formatter)

            self.logger.addHandler(handler)   
            
        self.logger.info("_" * 90);
            
        self.config = config()
        self.config.database_provider = self.get_setting("database_provider", "")
        self.config.ftp_portnum = self.get_setting("portnum", 21, int)
        self.config.ftp_address = self.get_setting("address", "")
        self.config.max_cons = self.get_setting("max_cons", 256, int)
        self.config.max_cons_per_ip = self.get_setting("max_cons_per_ip", 5, int)
        self.config.anonymous_enabled = self.get_setting("anonymous_enabled", False, bool)
        if self.config.anonymous_enabled:
            self.config.anonymous_homedir = self.get_setting("anonymous_homedir", os.getcwd())
        self.config.masquerade_address = self.get_setting("masquerade_address", "")
        
        for index, item in enumerate(dir(self.config)):
            if not item.startswith("_"):
                self.logger.info("%30s: %r" % (item, getattr(self.config, item), ))
                
        self.logger.info("_" * 90);
        if self.config.database_provider == "sqlite":
            import eftepede_using_sqlite
            
            eftepede_globals.Database = eftepede_using_sqlite.SQLite3Database(self, self.logger)
            
        elif self.config.database_provider == "postgresql":
            import eftepede_using_postgresql
            
            eftepede_globals.Database = eftepede_using_postgresql.PostgresqlDatabase(self, self.logger)

        elif self.config.database_provider == "mysql":
            import eftepede_using_mysql
            
            eftepede_globals.Database = eftepede_using_mysql.MySQLDatabase(self, self.logger)
            
        else:
            raise Exception("No valid database provider configured, please check eftepede_config.ini")

        self.logger.info("eftepede_globals.Database: %r" % (eftepede_globals.Database, ))
        
        self.authorizer = eftepede_authorizer.Authorizer(self.config, self.logger)
        
        pyftpdlib.servers.log = self.logger.info
        pyftpdlib.servers.logline = self.logger.info
        pyftpdlib.servers.logerror = self.logger.error
               
        if self.config.anonymous_enabled:        
            self.authorizer.add_anonymous(self.config.anonymous_homedir)

        
    def get_setting(self, variable, default, mapfunc = None, section = "Settings"):    
        try:
            result = self.config_file.get(section, variable)
            if mapfunc is not None:
                if mapfunc == bool:
                    if result.lower() == "true":
                        result = True
                    elif result.lower() == "false":
                        result = False
                    else:
                        result = mapfunc(result)
                else:
                    result = mapfunc(result)
            
            return result
        except Exception, e:
            return default        

    def run(self): 
        # Instantiate FTP handler class
        self.ftp_handler = pyftpdlib.handlers.FTPHandler
        self.ftp_handler.authorizer = self.authorizer

        # Define a customized banner (string returned when client connects)
        self.ftp_handler.banner = "eftepede %s ready, thanks to Python, pyftpdlib, sqlite and a host of others..." % (pyftpdlib.__ver__, )                

        # Specify a masquerade address and the range of ports to use for
        # passive connections.  Decomment in case you're behind a NAT.
        if self.config.masquerade_address:
            self.ftp_handler.masquerade_address = masquerade_address
        
        #if self.config.passive_ports:
        #    self.ftp_handler.passive_ports = range(60000, 65535)

        # Instantiate FTP server class and listen to 0.0.0.0:21
        address = (self.config.ftp_address, self.config.ftp_portnum)
        self.ftpd = pyftpdlib.servers.FTPServer(address, self.ftp_handler)

        # set a limit for connections
        self.ftpd.max_cons = self.config.max_cons
        self.ftpd.max_cons_per_ip = self.config.max_cons_per_ip        
        
        self.ftpd.serve_forever()
        
def main():
    eftepede_server().run()

if __name__ == "__main__":
    main()
    
    