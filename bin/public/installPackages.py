#!/usr/bin/env python
'''
Install a secure mysql server.

Install httpd packages server needed for syco installations.

download from git the syco-files repository and set upp apache to deliver files.
Point you packages.XXX.XX url agains this apache server to se files


'''


__author__ = "mattias.hemmingsson@elino.se"
__copyright__ = "Copyright 2011, The System Console project"
__maintainer__ = "Mattias Hemmingsson"
__email__ = "syco@cybercow.se"
__credits__ = ["Daniel Lidh"]
__license__ = "???"
__version__ = "1.0.0"
__status__ = "Production"



import os
from general import x
import config



# The version of this module, used to prevent the same script version to be
# executed more then once on the same host.
SCRIPT_VERSION = 1


def build_commands(commands):
  commands.add("install-packages",             _install, help="Install packages repo and set up packages.XXX.XX.")
  commands.add("uninstall-packages",           _uninstall, help="Uninstall packages use 'uninstall-packages all' to remove httd and git")
  

def _install(args):
	'''
	install and setup packages
	'''
	x("yum install httpd git -y")
	os.chdir("/var/www/html")
	x("git clone https://github.com/systemconsole/syco-files.git")
	x("ln -s syco-files packages")
	x("chown apache:apache -R syco-files")
	x("chmod 664 -R syco-files")
	x("\cp -f /opt/syco/var/httpd/conf.d/002-packages /etc/httpd/conf.d/")
	x("/etc/init.d/httpd restart")

def _uninstall(args):
	x("/etc/init.d/httpd stop")
	x("rm /var/www/html/packages")
	x("rm -rf /var/www/html/syco-files")

	if args[1]=="all":
		x("yum erase httpd git -y")
