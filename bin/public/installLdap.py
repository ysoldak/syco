#!/usr/bin/env python
'''
Install LDAP client and server.

Read more:
http://www.skills-1st.co.uk/papers/security-with-ldap-jan-2002/security-with-ldap.html
http://docs.redhat.com/docs/en-US/Red_Hat_Enterprise_Linux/5/html/Deployment_Guide/ch-ldap.html
http://www.openldap.org/doc/admin24/OpenLDAP-Admin-Guide.pdf

# Enable sudo with LDAP
http://electromech.info/sudo-ldap-with-rhds-linux-open-source.html


# ENable ldap on clients
http://directory.fedoraproject.org/wiki/Howto:PAM

LDAP Read
http://www.linux.com/archive/feature/114074
http://www.howtoforge.com/linux_ldap_authentication
http://www.debuntu.org/ldap-server-and-linux-ldap-clients
http://www.yolinux.com/TUTORIALS/LDAP_Authentication.html

# 2-factor auth
http://www.wikidsystems.com/
http://www.wikidsystems.com/support/wikid-support-center/how-to/how-to-add-two-factor-authentication-to-openldap-and-freeradius
http://freeradius.org/

Directory service
http://wiki.centos.org/HowTos/DirectoryServerSetup
http://docs.redhat.com/docs/en-US/Red_Hat_Directory_Server/8.2/pdf/Installation_Guide/Red_Hat_Directory_Server-8.2-Installation_Guide-en-US.pdf
http://docs.redhat.com/docs/en-US/Red_Hat_Directory_Server/8.2/html/Administration_Guide/index.html
http://docs.redhat.com/docs/en-US/Red_Hat_Directory_Server/8.2/html/Administration_Guide/User_Account_Management.html
http://www.oreillynet.com/sysadmin/blog/2006/07/a_new_favorite_fedora_director.html
http://www.linux.com/archive/feature/114074

TODO: LDAP vs SSL vs TLS vs SASL vs KERBEROS vs Radius?
TODO: Store hosts in ldap?
TODO: Setup kickstart to use LDAP
      http://web.archiveorange.com/archive/v/YcynVMg4S203uVyu3ZFc
TODO: ldap.cert ska kopieras till klienterna
      /usr/sbin/cacertdir_rehash /etc/openldap/cacerts
      eller k�ra authconfig efter�t.
TODO: Update ldif files.

'''

__author__ = "daniel.lindh@cybercow.se"
__copyright__ = "Copyright 2011, The System Console project"
__maintainer__ = "Daniel Lindh"
__email__ = "syco@cybercow.se"
__credits__ = ["???"]
__license__ = "???"
__version__ = "1.0.0"
__status__ = "Production"

import re

import app
import general
import version
from general import shell_exec, shell_run
from iptables import iptables

# The version of this module, used to prevent
# the same script version to be executed more then
# once on the same host.
SCRIPT_VERSION = 1

SLAPD_FN = "/etc/openldap/slapd.conf"
LDAP_SERVER_HOST_NAME = "ldap.fareonline.net"

def build_commands(commands):
  commands.add("install-ldap-server", install_ldap_server, help="Install ldap server.")
  commands.add("install-ldap-client", install_ldap_client, help="Install ldap client.")  
  commands.add("uninstall-ldap", uninstall_ldap, help="Uninstall ldap client/server.")  

def install_ldap_server(args):
  '''
  Install ldap server on current host.

  '''
  app.print_verbose("Install ldap server version: %d" % SCRIPT_VERSION)
  version_obj = version.Version("InstallLdapServer", SCRIPT_VERSION)
  version_obj.check_executed()

  # Setup ldap dns/hostname used by slapd  
  value="127.0.0.1 " + LDAP_SERVER_HOST_NAME
  general.set_config_property("/etc/hosts", value, value)

  shell_exec("yum -y  install openldap.x86_64 openldap-servers.x86_64 authconfig nss_ldap")

  _setup_slapd_config()
  _import_ldif_files():
  _setup_tls()

  shell_exec("chown -R ldap /var/lib/ldap")
  shell_exec("/sbin/service ldap start")
  shell_exec("chkconfig ldap on")  

  _add_iptables_rules()

  install_ldap_client(args)

  version_obj.mark_executed()

def install_ldap_client(args):
  '''
  Install ldap client on current host and connect to networks ldap server.

  '''
  app.print_verbose("Install ldap server version: %d" % SCRIPT_VERSION)
  version_obj = version.Version("InstallLdapServer", SCRIPT_VERSION)
  version_obj.check_executed()

  # TODO: Copy cert

  # Enable as a client
  shell_exec("authconfig --enableldap --enableldaptls --enableldapauth --disablenis --enablecache " +
    "--ldapserver=" + LDAP_SERVER_HOST_NAME + " --ldapbasedn=dc=fareonline,dc=net " +
    "--updateall")

  version_obj.mark_executed()

def uninstall_ldap(args):
  '''
  Uninstall both ldap client and server.

  '''
  app.print_verbose("Uninstall ldap client/server")
  shell_exec("yum -y erase openldap openldap-servers")
  shell_exec("rm /etc/openldap/slapd.conf.rpmsave")
  shell_exec("rm -r /var/lib/ldap")
  shell_exec("rm -r /etc/openldap")
  shell_exec("rm -r /etc/ldap.conf.rpmnew")
  shell_exec("rm -r /etc/ldap.conf.rpmsave")

  _remove_iptables_rules()

  version_obj = version.Version("InstallLdapServer", SCRIPT_VERSION)
  version_obj.mark_uninstalled()

def _setup_slapd_config():
  general.set_config_property(SLAPD_FN, ".*suffix.*", 'suffix "dc=fareonline,dc=net"')
  general.set_config_property(SLAPD_FN, ".*rootdn.*Manager.*", 'rootdn "cn=Manager,dc=fareonline,dc=net"')

  # Not needed for local changes.
  # hash_password = shell_exec('slappasswd -c "%s" -s ' + password)
  # general.set_config_property(SLAPD_FN, ".*rootpw.*[{]crypt[}].*", 'rootpw ' + hash_password)

  # Access Control
  # Users can change their own passwords
  # Everyone can read everything except passwords
  if (not general.grep(SLAPD_FN, "access to attrs=userPassword")):
    f = open(SLAPD_FN, "a")
    f.write("access to attrs=userPassword\n")
    f.write("  by self write\n")
    f.write("  by anonymous auth\n")
    f.write("  by * none\n")
    f.write("access to *\n")
    f.write("  by * read\n")
    f.close()

def _import_ldif_files():
  shell_exec("cp /etc/openldap/DB_CONFIG.example /var/lib/ldap/DB_CONFIG")
  shell_exec("slapadd -l " + app.SYCO_PATH + "var/ldap/common.ldif")
  shell_exec("slapadd -l " + app.SYCO_PATH + "var/ldap/groups.ldif")
  shell_exec("slapadd -l " + app.SYCO_PATH + "var/ldap/users.ldif")

  # TODO http://www.openldap.org/software/man.cgi?query=slapo-ppolicy&apropos=0&sektion=5&manpath=OpenLDAP+2.3-Release&format=html
  #shell_exec("slapadd -l " + app.SYCO_PATH + "var/ldap/passwordpolicy.ldif")

def _add_iptables_rules():
  '''
  Setup iptables for ldap.

  '''
  app.print_verbose("Setup iptables for nfs")
  _remove_iptables_rules()

  iptables("-N syco_ldap")

  # LDAP non TLS and with TLS
  iptables("-A syco_ldap -m state --state NEW -p tcp --dport 389  -j ACCEPT")

  iptables("-I INPUT  -p ALL -j ldap")

def _remove_iptables_rules():
  iptables("-D INPUT  -p ALL -j ldap")  
  iptables("-F syco_ldap")
  iptables("-X syco_ldap")

def _setup_tls():
  '''
  Create TLS cert and setup slapd to use them.
  
  '''
  app.print_verbose("Setup TLS")
  
  # Create dir
  certdir = "/etc/openldap/tls"
  shell_exec("mkdir -p " + certdir)
  
  # Create CA  
  ca_pass_phrase = app.get_ca_password()
  shell_run("openssl genrsa -des3 -out ca.key 2048",
    cwd=certdir,
    events={
      r'Enter pass phrase for ca.key:': ca_pass_phrase + "\n",
      r'Verifying.*Enter pass phrase for ca.key:': ca_pass_phrase + "\n",
    }
  )

  # Create CA cert.
  shell_run("openssl req -new -x509 -days 365 -key ca.key -out ca.cert",
    cwd=certdir,
    events={
      re.compile('Enter pass phrase for ca.key:'): ca_pass_phrase + "\n",
      re.compile('Country Name \(2 letter code\) \[GB\]\:'): config.get_country_name() + "\n",
      re.compile('State or Province Name \(full name\) \[Berkshire\]\:'): config.get_state() + ".\n",
      re.compile('Locality Name \(eg, city\) \[Newbury\]\:'): config.get_locality() + ".\n",
      re.compile('Organization Name \(eg, company\) \[My Company Ltd\]\:'): config.get_organization_name() + ".\n",
      re.compile('Organizational Unit Name \(eg, section\) \[\]\:'): config.get_organizational_unit_name() + "\n",
      re.compile('Common Name \(eg, your name or your server\'s hostname\) \[\]\:'): config.get_organizational_unit_name() + "CA\n",
      re.compile('Email Address \[\]\:'): config.get_admin_email() + "\n",
    }
  )
  
  # Create ldap cert
  shell_exec("openssl genrsa -out ldap.key 1024", cwd=certdir)
  shell_run("openssl req -new -key ldap.key -out ldap.csr",
    cwd=certdir,
    events={
      re.compile('Country Name \(2 letter code\) \[GB\]\:'): config.get_country_name() + "\n",
      re.compile('State or Province Name \(full name\) \[Berkshire\]\:'): config.get_state() + ".\n",
      re.compile('Locality Name \(eg, city\) \[Newbury\]\:'): config.get_locality() + ".\n",
      re.compile('Organization Name \(eg, company\) \[My Company Ltd\]\:'): config.get_organization_name() + ".\n",
      re.compile('Organizational Unit Name \(eg, section\) \[\]\:'): config.get_organizational_unit_name() + "\n",
      re.compile('Common Name \(eg, your name or your server\'s hostname\) \[\]\:'): LDAP_SERVER_HOST_NAME + "\n",
      re.compile('Email Address \[\]\:'): config.get_admin_email() + "\n",
      re.compile('A challenge password \[\]\:'): "\n",
      re.compile('An optional company name \[\]\:'): "\n",
    }
  )
  
  # Sign ldap cert with CA.
  shell_run("openssl x509 -req -in ldap.csr -out ldap.cert -CA ca.cert -CAkey ca.key -CAcreateserial -days 365",
    cwd=certdir,
    events={
      r'Enter pass phrase for ca.key:': ca_pass_phrase + "\n",
    }
  )

  shell_exec("cp /etc/openldap/tls/ca.cert /etc/openldap/cacerts")
  shell_exec("cat /etc/openldap/tls/ldap.key > /etc/openldap/cacerts/ldap.pem")
  shell_exec("cat /etc/openldap/tls/ldap.cert >> /etc/openldap/cacerts/ldap.pem")

  # Configure slapd for TLS
  value = "TLSCertificateFile /etc/openldap/cacerts/ldap.pem"
  general.set_config_property(SLAPD_FN, ".*" + value + ".*", value)

  value = "TLSCertificateKeyFile /etc/openldap/tls/ldap.pem"
  general.set_config_property(SLAPD_FN, ".*" + value + ".*", value)

  value = "TLSCACertificateFile /etc/openldap/cacerts/ca.cert"
  general.set_config_property(SLAPD_FN, ".*" + value + ".*", value)

  # http://www.openldap.org/doc/admin24/guide.html#Authentication Methods
  value = "security ssf=1 update_ssf=112 simple_bind=64"
  general.set_config_property(SLAPD_FN, ".*" + value +".*", value)