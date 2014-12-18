#this script is responsible for managing / driving the execution of jobs for Atlas

import glob
import json
import shutil
import os
import logging
import time
import datetime
import fnmatch
from runner import Runner
from template_writer import TemplateWriter
import sys
from optparse import OptionParser

__author__ = 'mattdyer'

## simple method to get a time stamp
# @returns A timestamp
def getTimestamp():
    #get the time / timestamp
    currentTime = time.time()
    timeStamp = datetime.datetime.fromtimestamp(currentTime).strftime('%Y-%m-%d_%H-%M-%S')

    #return the stamp
    return(timeStamp)

#start here when the script is launched
if (__name__ == "__main__"):
    #set up the logging
    logging.basicConfig(level=logging.DEBUG)

    #set up the option parser
    parser = OptionParser()

    #add the options to parse
    parser.add_option('-u', '--user', dest='user', help='The JIRA user')
    parser.add_option('-e', '--epics', dest='epics', help='The TAB epics file (id, epic)')
    parser.add_option('-p', '--password', dest='password', help='The JIRA user password')
    parser.add_option('-s', '--site', dest='site', help='The JIRA site URL including the https:// part')
    parser.add_option('-r', '--reqs', dest='requirements', help='The TAB requirements file (id, name, priority)')
    parser.add_option('-t', '--stories', dest='stories', help='The TAB user stories file (requirements id, name, product, priority)')
    parser.add_option('-x', '--project', dest='project', help='The JIRA project')
    parser.add_option('-o', '--output', dest='output', help='The output file')
    (options, args) = parser.parse_args()





