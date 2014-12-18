#this script is responsible for generating the human protein feature vectors
__author__ = 'mattdyer'

from optparse import OptionParser

#start here when the script is launched
if (__name__ == '__main__'):
    #set up the option parser
    parser = OptionParser()

    #add the options to parse
    parser.add_option('-n', '--network', dest='network', help='The network attribute file')
    parser.add_option('-g', '--go', dest='go', help='The GO annotation file')
    parser.add_option('-o', '--output', dest='outputfile', help='The output file')
    (options, args) = parser.parse_args()

    #load the network file
    file = open(options.network, 'r')

    #loop over file
    proteinNetworkAttributes = {}
    proteins = {}

    for line in file:
        line = line.rstrip('\n\r')
        tokens = line.split('\t')

        #store the centrality and degree for the protein since
        proteinNetworkAttributes[tokens[0]] = '%s\t%s' % (tokens[1], tokens[2])
        proteins[tokens[0]] = 1

    #close the file
    file.close()

    #now do the same for GO
    proteinGOAttributes = {}
    goIDs = {}
    file = open(options.go, 'r')

    for line in file:
        line = line.rstrip('\n\r')
        tokens = line.split('\t')

        #see if we have seen this protein before
        if not tokens[0] in proteinGOAttributes:
            proteinGOAttributes[tokens[0]] = {}

        proteinGOAttributes[tokens[0]][tokens[1]] = 1
        goIDs[tokens[1]] = 1
        proteins[tokens[0]] = 1

    #close the file
    file.close()

    #now let's print our output file
    file = open(options.outputfile, 'w')

    #print out headers
    file.write('#protein\tdegree\tcentrality')

    for id in goIDs:
        file.write('\t%s' % (id))

    file.write('\n')

    #now print the data for each protein
    for protein in proteins:
        file.write('%s' % (protein))

        #see if network info is there or not
        if protein in proteinNetworkAttributes:
            file.write('\t%s' % proteinNetworkAttributes[protein])
        else:
            file.write('\t0\t0')

        #print out go ids
        for id in goIDs:
            if protein in proteinGOAttributes:
                if id in proteinGOAttributes[protein]:
                    file.write('\t1')
                else:
                    file.write('\t0')
            else:
                file.write('\t0')

        #break to next line
        file.write('\n')

    #close the file
    file.close()