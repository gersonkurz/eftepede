# A setup script showing advanced features.
#
# Note that for the NT service to build correctly, you need at least
# win32all build 161, for the COM samples, you need build 163.
# Requires wxPython, and Tim Golden's WMI module.

# Note: WMI is probably NOT a good example for demonstrating how to
# include a pywin32 typelib wrapper into the exe: wmi uses different
# typelib versions on win2k and winXP.  The resulting exe will only
# run on the same windows version as the one used to build the exe.
# So, the newest version of wmi.py doesn't use any typelib anymore.

from distutils.core import setup
import py2exe
import sys

# If run without args, build executables, in quiet mode.
if len(sys.argv) == 1:
    sys.argv.append("py2exe")
    sys.argv.append("-q")

class Target:
    def __init__(self, **kw):
        self.__dict__.update(kw)
        # for the versioninfo resources
        self.version = "0.5.0"
        self.company_name = "http://p-nand-q.com"
        self.copyright = "no copyright"
        self.name = "eftepede"


################################################################
# a NT service, modules is required
myservice = Target(
    # used for the versioninfo resource
    description = "eftepede! FTP Service",
    # what to build.  For a service, the module name (not the
    # filename) must be specified!
    modules = ["eftepede_service"]
    )

################################################################
# COM pulls in a lot of stuff which we don't want or need.

excludes = ["pywin", "pywin.debugger", "pywin.debugger.dbgcon",
            "pywin.dialogs", "pywin.dialogs.list"]

setup(
    options = {"py2exe": {#"typelibs":
                          # typelib for WMI
                          #[('{565783C6-CB41-11D1-8B02-00600806D9B6}', 0, 1, 2)],
                          # create a compressed zip archive
                          "compressed": 1,
                          "optimize": 2,
                          "excludes": excludes}},
    # The lib directory contains everything except the executables and the python dll.
    # Can include a subdirectory name.
    zipfile = "python26.zip",

    service = [myservice],
    com_server = [],
    console = [],
    windows = [],
    )
