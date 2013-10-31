#!/usr/bin/env python
'''
Backup script by Mattias

Script send data from clients to backup server by adding commands to crontab script.
The scripts process an backup.cfg file and sets up commands to backup.


1. first run set up backup server to setup correct users and folders on backup server.

2. Run backup clients on backup clients to setup backup rules for the klients to copy data

3. Run backupserver-lockdown that will disable passwords on backup useres on backup server.

'''

__author__ = "matte@elino.se"
__copyright__ = "Copyright 2011, The System Console project"
__maintainer__ = "Daniel Lindh"
__email__ = "syco@cybercow.se"
__credits__ = ["Daniel LIndh"]
__license__ = "???"
__version__ = "1.0.0"
__status__ = "Production"

import os
import shutil
import stat
import sys
import time
import traceback
import ConfigParser, re
import socket
import app
import general
import version
import config
from config import get_servers, host
from general import x ,shell_run
from scopen import scOpen

# The version of this module, used to prevent
# the same script version to be executed more then
# once on the same host.
script_version = 1

def build_commands(commands):
  '''
  Defines the commands that can be executed through the syco.py shell script.

  '''
  commands.add("install-backup-rsync", install_backup_r, help="Install Backup Rync server / Client")
  commands.add("uninstall-backup-rsync", uninstall_backup_r, help="Un-Install Backup Rync server / Client")


def _setup_sshkeys():
	'''
	Setting up ssh keys for the backup clients
	'''
	settings = _get_settings()
	print "removing old keys"
	x("rm -rf /root/.ssh")
	shell_run("ssh-keygen -t rsa",events={
		"^.*":"\n",
		"^.*":"\n",
		})
	print "Adding to host"
	x("ssh-keyscan "+settings['backup_host']+" > /root/.ssh/known_hosts")
	print "Copy ID"
	shell_run("ssh-copy-id backup_"+ socket.gethostname() +"@"+ settings['backup_host'], events={
		"(?i)password:.*":app.get_mysql_backup_password() +"\n"
		})




def _making_backup_users():
	'''
	Creating backup users for backup server
	'''
	print "backup server useres"
	x("adduser thebackup")
	
	print "Add user for all servers"
	sshd_config = scOpen("/etc/ssh/sshd_config")
	for server in get_servers():
		#x("adduser -G thebackup backup_"+server)
		shell_run("passwd backup_"+server, events={
      "(?i)New password:*": app.get_mysql_backup_password() +"\n",
      "(?i)Retype new password.*":app.get_mysql_backup_password()+ "\n",
      
    })
		print "Only allowing backup user to loggin from host"
		sshd_config.replace_add("^AllowUsers backup_"+server+"@.*","AllowUsers backup_"+server+"@"+config.host(server).get_front_ip())
	x("/etc/init.d/sshd restart")





def _setting_backup_folder():
	'''
	Creating the backup folder
	'''
	settings = _get_settings()
	if os.path.isdir(settings['backup_dest']):
		print "Backup folder is there"
	else:
		print "no backup folder creating"
		x("mkdir "+settings['backup_dest'])
		for server in get_servers():
			x("mkdir "+settings['backup_dest']+"/"+server)



		x("chown thebackup:thebackup -R "+settings['backup_dest'])
		x("chmod 771 -R "+settings['backup_dest'])



def _get_settings():
	'''
	Getting backup settings from the config file
	'''
	#Setting upp settings from configfile
	config = ConfigParser.ConfigParser()
	config.readfp(open('/opt/syco/var/backup/backup.cfg'))
	
	#Setting up backup settings
	settings={}
	options = config.options('settings')
	settings['backup_host'] = config.get('settings', 'host')
	settings['backup_pass'] = config.get('settings', 'password')
	settings['backup_local_user'] = config.get('settings', 'backup_user')
	settings['backup_dest'] = config.get('settings', 'dest')

	return settings



def _setup_backup():
	#Setting up general backup settings for all servers
	settings = _get_settings()


	#Setting upp rsync daily.
	f = open("/etc/cron.daily/syco_rsync", "w")
	f.write("#!/bin/bash\n")
	f.write("#Syco Autogenerted file DO NOT EDIT\n")

	def _add_rsync(section,options):
		#Adding rsync derictives to backup file
		f.write("rsync -a "+ str(config.get(section, options))+" -e ssh backup_"+socket.gethostname()+"@"+settings['backup_host']+":"+settings['backup_dest']+"/"+socket.gethostname()+"/ \n")




	config = ConfigParser.ConfigParser()
	config.readfp(open('/opt/syco/var/backup/backup.cfg'))
	options = config.options('general-backup')
	for option in options:
		if re.compile('^rsync.*').match(option):
			_add_rsync('general-backup',option)	
	
	
	#Setting upp cutom host backup config
	try:
		c_options = config.options(socket.gethostname())
		for c_option in c_options:
			if re.compile('^rsync.*').match(c_option):
				_add_rsync(socket.gethostname(),c_option)
		
	except ConfigParser.NoSectionError:
		print "no custom config"

	f.close()
	x("chmod 700 /etc/cron.daily/syco_rsync")


def install_backup_r(args):
	'''
	Install the backup server / client
	'''
	if (len(args) != 2):
		raise Exception("use syco install-backup-rsync server / client | to install backup server ore client]")

	



	if 'server' == args[1]:
		print "Print setting upp backup server"
		_making_backup_users()
		_setting_backup_folder()

	elif 'client' == args[1]:
		print "Print setting upp backup client"
		_setup_sshkeys()
		_setup_backup()

	else:
		print "use syco install-backup-rsync server | to install backup server"
		print "use syco install-backup-rsync client | to install backup client"


def uninstall_backup_r(args):
	'''
	Install the backup server / client
	'''
	print argS
