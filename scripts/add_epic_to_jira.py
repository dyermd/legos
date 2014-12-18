from jira.client import JIRA
from jira.client import GreenHopper
from optparse import OptionParser
import time

__author__ = 'mattdyer'


#this class manages creating the individual issues that we are parsing from a file
class IssueManager:

    ## The constructor
    # @param self The object pointer
    # @param options The option hash
    def __init__(self, options):
        self.__jiraUser = options.user
        self.__jiraPassword = options.password
        self.__jiraURL = options.site
        self.startSession()

    ## Create the connection
    # @param self Teh object pointer
    def startSession(self):
        #now make the connection
        options = {
            'server':self.__jiraURL,
            'verify':False
        }
        self.__jira = JIRA(options, basic_auth=(self.__jiraUser, self.__jiraPassword))
        self.__greenhopper = GreenHopper(options, basic_auth=(self.__jiraUser, self.__jiraPassword))

    ## Kill the jira connection
    # @param self The object pointer
    def killSession(self):
        self.__jira.kill_session()
        self.__greenhopper.kill_session()

    ## Create a new epic
    # @param self The object pointer
    # @param options The option dictionary
    # @returns The JIRA issue identifier
    def createEpic(self, options):
        #create an epic by setting up the dictionary
        issueDict = {
            #'assignee': {'name':'Unassigned'},
            'project': {'key':options.project},
            'priority' : {'name':options.priority},
            'summary': options.epic,
            'customfield_10401': options.epic,
            'description': options.description,
            'issuetype' : {'name':'Epic'},
            'labels':[
                   'AddedViaAPI',
                   'APISetFixVersion'
            ],
        }

        #set up software / hardware product type
        #if we list more than one product that set the product flag to multiple
        productLabel = options.product

        if(';' in options.product):
             productLabel = 'Multiple'

        #see if we are hardware of software
        if options.type == 'Hardware':
            #hardware product
            issueDict['customfield_11200'] = {'value':productLabel}
        else:
            #software product
            issueDict['customfield_11100'] = {'value':productLabel}

        #add the components if there are any
        if(not options.components == ''):
            issueDict['components'] = self.addComponents(options.components)

        #now create the issue
        #print issueDict
        newIssue = self.__greenhopper.create_issue(fields=issueDict)

        #return the id
        return(newIssue.key)

    ## Link two issues
    # @param self The object pointer
    # @param jiraID1 The JIRA id of the first issue
    # @param jiraID2 The JIRA id of the second issue
    # @param linkType The type of connect
    def linkIssues(self, jiraID1, jiraID2, linkType):
        #now link the two issues
        print "Linking %s and %s" % (jiraID1, jiraID2)
        self.__jira.create_issue_link(type=linkType, inwardIssue=jiraID2, outwardIssue=jiraID1)

    ## Create an array from a ";"-separated list, used for populating components
    # @param self The object pointer
    # @param componentString The string to be parsed
    # @returns The array of components
    def addComponents(self, componentString):
        tokens = componentString.split(';')
        components = []

        #populate the array
        for token in tokens:
            components.append( {'name':token} )

        return(components)


#start here when the script is launched
if (__name__ == '__main__'):
    #set up the option parser
    parser = OptionParser()

    #add the options to parse

    #script options
    parser.add_option('-a', '--type', dest='type', help='The story type, Software or Hardware')

    #task options
    parser.add_option('-c', '--components', dest='components', help='The ;-delimited list of components')
    parser.add_option('-d', '--product', dest='product', help='The software product to attach the story too')
    parser.add_option('-n', '--description', dest='description', help='The story description', default='')
    parser.add_option('-e', '--epic', dest='epic', help='The epic you want to create')
    parser.add_option('-v', '--version', dest='version', help='The fix version')
    parser.add_option('-x', '--project', dest='project', help='The JIRA project')
    parser.add_option('-y', '--priority', dest='priority', help='The priority of the story')

    #jira options
    parser.add_option('-p', '--password', dest='password', help='The JIRA user password')
    parser.add_option('-s', '--site', dest='site', help='The JIRA site URL including the https:// part')
    parser.add_option('-u', '--user', dest='user', help='The JIRA user')
    (options, args) = parser.parse_args()

    #set up the issue manager
    manager = IssueManager(options)

    #create the issue and implement / test tasks
    issueID = manager.createEpic(options)

    print '%s\t%s' % (issueID, options.epic)

    #kill the connection
    manager.killSession()




