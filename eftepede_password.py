#! -*- Encoding: Latin-1 -*-

import random
import base64
import Crypto.Cipher.AES 

def encode(password):
    if isinstance(password, unicode):
        password = password.encode("latin-1")
    assert isinstance(password, str)
    
    data = "h987://p-n@nd-q."
    assert len(data) == 16
    
    algorithm = Crypto.Cipher.AES    
    if not password:
        password = " "
    key = (password * 32)[:32]
    assert len(key) == 32
    
    mode = algorithm.MODE_ECB   
    instance = algorithm.new(key, mode, "")
    return base64.b64encode(instance.encrypt(data))
