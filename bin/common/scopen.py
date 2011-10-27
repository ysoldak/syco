#!/usr/bin/env python
'''
Classes to manipulate files.

'''

__author__ = "daniel.lindh@cybercow.se"
__copyright__ = "Copyright 2011, The System Console project"
__maintainer__ = "Daniel Lindh"
__email__ = "syco@cybercow.se"
__credits__ = ["???"]
__license__ = "???"
__version__ = "1.0.0"
__status__ = "Production"

from general import x

class scOpen():
    '''
    Class to manipulate files.

    All funcitons execute shell commands (cat, sed) to manipulate files. All
    commands can be printed to screen, and the cut&pasted for manual execution.

    '''
    filename = None

    def __init__(self, filename):
        self.filename = filename

    def add(self, value):
        '''
        Add value to end off file with cat.

        '''
        x("""cat >> %s << EOF\n%s\nEOF""" % (self.filename, value))

    def remove(self, search):
        '''
        Remove a value from a file using sed.

        '''
        x("sed -i '/%s/d' %s" % (search, self.filename))

    def replace(self, search, replace):
        '''
        Replace search string with replace string using sed.

        '''
        x("sed -i 's/%s/%s/g' %s" % (search, replace, self.filename))

    def remove_eof(self, lines):
        '''
        Remove the last N lines of the file using head.

        '''
        x("head -n-%s %s > /tmp/syco-remove-eof" % (lines, self.filename))
        x("cp /tmp/syco-remove-eof " + self.filename)
