#! /usr/bin/python

import sys
import win32serviceutil
import win32service
import win32event
import threading
import os
import eftepede_server
import traceback
import _winreg

class eftepedeService(win32serviceutil.ServiceFramework):
    _svc_name_ = "eftepede"
    _svc_display_name_ = "eftepede! FTP Server"
    
    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hStopSignal = win32event.CreateEvent(None, 0, 0, None)
    
    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.hStopSignal)
        
    def SvcDoRun(self):
        fh = open("C:\\temp\\eftepede-stderr.log","w")
        sys.stderr = fh
        sys.stdout = fh
        try:
            key = _winreg.OpenKey( _winreg.HKEY_LOCAL_MACHINE, "SYSTEM\\CurrentControlSet\\Services\\eftepede", _winreg.KEY_READ)
            value, datatype = _winreg.QueryValueEx(key, "ImagePath")
            
            directory = os.path.split(value)[0].replace('"','')
            os.chdir(directory)
            _winreg.CloseKey(key)
            
            threading.Thread( target = eftepede_server.main ).start()
            win32event.WaitForSingleObject(self.hStopSignal, win32event.INFINITE)
        except:
            traceback.print_exc( file = sys.stdout )

if __name__=='__main__':
    win32serviceutil.HandleCommandLine(eftepedeService)

