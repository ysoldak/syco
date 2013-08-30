#!/usr/bin/env python
'''
Install glassfish with optimizations, security and common plugins.

Read more
http://www.oracle.com/technetwork/middleware/glassfish/documentation/index.html
http://glassfish.java.net/
http://www.nabisoft.com/tutorials/glassfish/installing-glassfish-301-on-ubuntu
http://iblog.humani-tech.com/?p=505

'''

__author__ = "daniel.lindh@cybercow.se"
__copyright__ = "Copyright 2011, The System Console project"
__maintainer__ = "Daniel Lindh"
__email__ = "syco@cybercow.se"
__credits__ = ["???"]
__license__ = "???"
__version__ = "1.0.0"
__status__ = "Production"

import os
import re
import shutil
import stat
import sys
import traceback
import time

import app
import config
import general
import version
import iptables
import install
from general import x
from scopen import scOpen

# The version of this module, used to prevent the same script version to be
# executed more then once on the same host.
SCRIPT_VERSION = 2

# NOTE: Remember to change path in "var/glassfish/glassfish-3.1.1"
GLASSFISH_VERSION      = "glassfish-4.0"
GLASSFISH_INSTALL_FILE = GLASSFISH_VERSION + ".zip"
GLASSFISH_REPO_URL     = "http://192.168.122.12/files/" + GLASSFISH_INSTALL_FILE
GLASSFISH_INSTALL_PATH = "/usr/local/glassfish4"
GLASSFISH_DOMAINS_PATH = GLASSFISH_INSTALL_PATH + "glassfish/domains/"

# The directory where JAVA stores temporary files.
# Default is /tmp, but the partion that dir is stored on is set to "noexec", and
# java requires to exeute code from the java tmp dir.
JAVA_TEMP_PATH = GLASSFISH_INSTALL_PATH + "tmp"

# http://www.oracle.com/technetwork/java/javase/downloads/index.html
JDK_INSTALL_FILE = "jdk-7u25-linux-x64.tar.gz"
JDK_REPO_URL     = "http://192.168.122.12/files/%s" % (JDK_INSTALL_FILE)
JDK_INSTALL_PATH = "/usr/java/jdk1.7.0_25"
JDK_VERSION = "jdk1.7.0_25"

# Mysql Connector
# http://ftp.sunet.se/pub/unix/databases/relational/mysql/Downloads/Connector-J/
MYSQL_FILE_NAME="mysql-connector-java-5.1.26"
MYSQL_CONNECTOR_REPO_URL    = "http://192.168.122.12/files/"+MYSQL_FILE_NAME+".tar.gz"


# Google Guice
# Is configured in _install_google_guice.
GUICE_NAME="guice-3.0"
GUICE_URL="http://192.168.122.12/files/"+GUICE_NAME+".zip"


def build_commands(commands):
  '''
  Defines the commands that can be executed through the syco.py shell script.

  '''
  commands.add("install-glassfish4", install_glassfish, help="Install on the current server.")
  commands.add("uninstall-glassfish4", uninstall_glassfish, help="Uninstall  servers on the current server.")


def uninstall_glassfish(args):
	'''
	Uninstalling
	'''
	print "uninstalling"

def install_glassfish(arg):
	'''
	Install glassfish4
	'''
	if False ==_is_glassfish_user_installed():
		x('adduser glassfish')

	#_install_jdk()
	#_install_glassfish()
	#_setup_glassfish4()
	_install_mysql_connect()
	_install_guice()

def _is_glassfish_user_installed():
  '''
  Check if glassfish user is installed.

  '''
  for line in open("/etc/passwd"):
    if "glassfish" in line:
      return True
  return False

def asadmin_exec(command, admin_port=None, events=None):
  if (admin_port):
    cmd = GLASSFISH_INSTALL_PATH + "/bin/asadmin --port " + admin_port + " " + command
  else:
    cmd = GLASSFISH_INSTALL_PATH + "/bin/asadmin --echo " + command

  if (events):
    return general.shell_run(cmd, user="glassfish", events=events)
  else:
    return x(cmd, user="glassfish")


def _install_jdk():
  '''
  Installation of the java sdk.

  '''
  if (not os.access(JDK_INSTALL_PATH, os.F_OK)):
    os.chdir(app.INSTALL_DIR)
    if (not os.access(JDK_INSTALL_FILE, os.F_OK)):
      general.download_file(JDK_REPO_URL, user="glassfish")

      x("chmod u+rx " + JDK_INSTALL_FILE)

    if (os.access(JDK_INSTALL_FILE, os.F_OK)):
    	x("tar -zxvf "+JDK_INSTALL_FILE )
    	x("mv "+JDK_VERSION+" /usr/java")
    	x("rm -f /usr/java/deafult")
    	x("ln -s /usr/java/"+JDK_VERSION+" /usr/java/deafult")
    	x("alternatives --install /usr/bin/javac javac /usr/java/latest/bin/javac 20000")
    	x("alternatives --install /usr/bin/jar jar /usr/java/latest/bin/jar 20000")
    	x("alternatives --install /usr/bin/java java /usr/java/latest/jre/bin/java 20000")
    	x("alternatives --install /usr/bin/javaws javaws /usr/java/latest/jre/bin/javaws 20000")




    else:
      raise Exception("Not able to download " + JDK_INSTALL_FILE)

def _install_glassfish():
  '''
  Installation of the glassfish application server.

  '''
  x("yum install zip -y")
  if (not os.access(GLASSFISH_INSTALL_PATH + "/glassfish", os.F_OK)):
    os.chdir(app.INSTALL_DIR)
    if (not os.access(GLASSFISH_INSTALL_FILE, os.F_OK)):
      general.download_file(GLASSFISH_REPO_URL, user="glassfish")

    # Set executeion permissions and run the installation.
    if ".zip" in GLASSFISH_INSTALL_FILE:
      install.package("unzip")
      x("unzip " + GLASSFISH_INSTALL_FILE + " -d /usr/local/")
      x("chown glassfish:glassfish -R "+GLASSFISH_INSTALL_PATH)
    else:
      raise Exception("Only installing zip version of glassfish")

    # Install the start script
    # It's possible to do this from glassfish with "asadmin create-service",
    # but our own script is a little bit better. It creates startup log files
    # and has a better "start user" functionality.
    x(GLASSFISH_INSTALL_PATH+"/bin/asadmin create-service")


def _setup_glassfish4():
	'''
	Setting Glassfish 4 properties
	'''
	asadmin_exec("delete-jvm-options -client")
	#asadmin_exec("delete-jvm-options '-XX\:MaxPermSize=192m'")
	#asadmin_exec("delete-jvm-options -Xmx512m")
	
	asadmin_exec("create-jvm-options -server")
	#asadmin_exec("create-jvm-options -Xmx2048")
	#asadmin_exec("create-jvm-options -Xms1024")
 	#asadmin_exec("create-jvm-options '-XX\:MaxPermSize=1024'")
	asadmin_exec("set configs.config.server-config.ejb-container.ejb-timer-service.max-redeliveries=300")
	asadmin_exec("set configs.config.server-config.ejb-container.ejb-timer-service.redelivery-interval-internal-in-millis=300000")
	asadmin_exec("set-log-file-format --target server-config ulf")
	asadmin_exec("set server.admin-service.das-config.autodeploy-enabled=false")
	asadmin_exec("set server.admin-service.das-config.dynamic-reload-enabled=false")

def _install_mysql_connect():
	'''
	Install the mysql connect
	'''
	os.chdir(app.INSTALL_DIR)
	general.download_file(MYSQL_CONNECTOR_REPO_URL)
	x("tar -zxvf "+MYSQL_FILE_NAME+".tar.gz")
	x("\cp -f "+MYSQL_FILE_NAME+"/"+MYSQL_FILE_NAME+"-bin.jar "+GLASSFISH_INSTALL_PATH+"/glassfish/domains/domain1/lib/ext/")

def _install_guice():
	'''
	Installing guice to glassfish
	'''
	os.chdir(app.INSTALL_DIR)
	general.download_file(GUICE_URL)
	x("unzip "+GUICE_NAME+".zip")
	x("cp "+GUICE_NAME+ "/" +GUICE_NAME+ ".jar "+GLASSFISH_INSTALL_PATH+"/glassfish/domains/domain1/lib/ext/")
	x("cp "+GUICE_NAME+ "/guice-assistedinject* "+GLASSFISH_INSTALL_PATH+"/glassfish/domains/domain1/lib/ext/")
	x("cp "+GUICE_NAME+ "/aopalliance* "+GLASSFISH_INSTALL_PATH+"/glassfish/domains/domain1/lib/ext/")
	x("cp "+GUICE_NAME+ "/javax.inject* "+GLASSFISH_INSTALL_PATH+"/glassfish/domains/domain1/lib/ext/")