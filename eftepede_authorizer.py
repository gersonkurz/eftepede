#! -*- Encoding: Latin-1 -*-

import os
import threading
import logging
import logging.handlers
import eftepede_globals
import pyftpdlib.ftpserver
import eftepede_password

class Authorizer(pyftpdlib.ftpserver.DummyAuthorizer):

    def __init__(self, config, logger):   
        pyftpdlib.ftpserver.DummyAuthorizer.__init__(self)
        self.config = config
        self.logger = logger
        self.db = eftepede_globals.Database
        self.user_cache = {}

    def add_user(self, username, password, homedir, perm='elr', msg_login="Login successful.", msg_quit="Goodbye."):        
        if self.db.has_user(username):
            raise pyftpdlib.ftpserver.AuthorizerError('User "%s" already exists' %username)
        if not os.path.isdir(homedir):
            raise pyftpdlib.ftpserver.AuthorizerError('No such directory: "%s"' %homedir)
        homedir = os.path.realpath(homedir)
        self._check_permissions(username, perm)
        self.db.add_user(username, eftepede_password.encode(password), homedir, perm, msg_login, msg_quit)

    def add_anonymous(self, homedir, **kwargs):
        return self.add_user('anonymous', '', homedir, **kwargs)

    def remove_user(self, username):
        self.db.remove_user(username)  
        try:        
            del self.user_cache[username]
        except KeyError:
            pass

    def validate_authentication(self, username, given_password):
        self.logger.info("validate_authentication(%r, %r) called" % (username, given_password, ))
        # NB: this may be tricky, for the sake of unicode names returned from the database...
        result = self.db.identify(username)
        if result is None:
            self.logger.warn("Warning, validate_authentication(%r) failed: no such user" % (username, ))
            return False
            
        actual_password, homedir, perm, msg_login, msg_quit = result
        
        if (username != 'anonymous') and (eftepede_password.encode(given_password) != actual_password):
            self.logger.warn("Warning, validate_authentication(%r) failed: invalid password" % (username, ))
            return False

        dic = {'home': str(homedir),
               'perm': str(perm),
               'operms': {},
               'msg_login': str(msg_login),
               'msg_quit': str(msg_quit)
               }
        self.user_table[username] = dic
        self.logger.info("User %r logged in successfully..." % (username, ))
        return True

if __name__ == "__main__":
    import eftepede_server
    eftepede_server.main()
