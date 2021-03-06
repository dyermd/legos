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

    ## Add the epic link to an issue
    # @param self The object pointer
    # @param issue The issue ID
    # @param epic The epic ID
    def attachEpic(self, issue, epic):
        #attach the epic
        self.__greenhopper.add_issues_to_epic(epic, [issue])

    ## Create an issue set by calling the createIssue and createSubtask methods
    # @param self The object pointer
    # @param options The option dictionary
    # @returns A dictionary of issues that were created
    def createIssueSet(self, options):
        #dictionary to store jira issues
        issues = {}

        #set up the description
        description = '<h3>User Experience</h3>%s<h3>Acceptance Criteria</h3><ul><li></li></ul>' % (options.description)

        #create the parent issue
        parentID = self.createIssue(options.story, 'Story', description, options)
        issues[parentID] = '%s\t%s\t%s' % (parentID, 'Story', options.story)

        #create the tasks for development and testing depending on the product
        for specificProduct in options.product.split(';'):
            issue1 = self.createIssue('Implementation (%s): %s' % (specificProduct, options.story), 'Implement', '', options)
            issues[issue1] = '%s\t%s\t%s' % (issue1, 'Implement', options.story)
            issue2 = self.createIssue('Create Unit Tests (%s): %s' % (specificProduct, options.story), 'Unit Test', '', options)
            issues[issue2] = '%s\t%s\t%s' % (issue2, 'Unit Test', options.story)
            issue3 = self.createIssue('Verification (%s): %s' % (specificProduct, options.story), 'Verification Test', '', options)
            issues[issue3] = '%s\t%s\t%s' % (issue3, 'Verification Test', options.story)

            #create the links
            self.linkIssues(parentID, issue1, 'Develop')
            self.linkIssues(parentID, issue2, 'Verify')
            self.linkIssues(parentID, issue3, 'Verify')

        #print the ids
        return(parentID, issues)

    ## Create a new issue
    # @param self The object pointer
    # @param summary The summary of the issue
    # @param description The description of the issue
    # @param issueType The type of the issue
    # @param options The option dictionary
    # @returns The JIRA issue identifier
    def createIssue(self, summary, issueType, description, options):
        #create an issue by setting up the dictionary
        issueDict = {
            #'assignee': {'name':'Unassigned'},
            'project': {'key':options.project},
            'priority' : {'name':options.priority},
            'summary': summary,
            'description': description,
            'issuetype' : {'name':issueType},
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


        #if it is a story type then we want ot add a label for acceptance criteria too
        if issueType == 'Story':
            issueDict['labels'].append('NeedAcceptanceCriteria')

        #add the components if there are any
        if(not options.components == ''):
            issueDict['components'] = self.addComponents(options.components)

        #now create the issue
        print issueDict
        newIssue = self.__jira.create_issue(fields=issueDict)

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
    parser.add_option('-e', '--epic', dest='epic', help='The epic ID')
    parser.add_option('-n', '--description', dest='description', help='The story description', default='')
    parser.add_option('-r', '--req', dest='requirement', help='The requirement ID')
    parser.add_option('-t', '--story', dest='story', help='The story you want to create')
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
    issueID, issues = manager.createIssueSet(options)

    #link to the requirement / epic
    manager.linkIssues(issueID, options.requirement, 'Requirement')
    manager.attachEpic(issueID, options.epic)

    #kill the connection
    manager.killSession()




