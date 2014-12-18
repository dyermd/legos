__author__ = 'mattdyer'

from optparse import OptionParser

class Mutation:
    ## The constructor
    # @param self The object pointer
    # @param mutation The mutation
    # @param cellLine The cell line
    # @param coverage The coverage
    def __init__(self, mutation, cellLine, coverage):
        self.__mutation = mutation
        self.__cellLine = cellLine
        self.__coverage = coverage

    ## Get the coverage
    # @param self The object pointer
    # @returns The coverge
    def getCoverage(self):
        return(self.__coverage)

    ## Get the mutation
    # @param self The object pointer
    # @returns The mutation
    def getMutation(self):
        return(self.__mutation)

    ## Get the cell line
    # @param self The object pointer
    # @returns The cell line
    def getCellLine(self):
        return(self.__cellLine)

class Gene:
    ## The constructor
    # @param self The object pointer
    # @param geneName The gene name
    # @param uniprotID The uniprotID
    def __init__(self, geneName, uniprotID):
        #set up the new object
        self.__geneName = geneName
        self.__uniprotID = uniprotID
        self.__sensitive = []
        self.__unsensitive = []
        self.__coverage = 0

    ## Add cell line
    # @param cellLine The cell line name
    # @param mutation The mutation
    # @param coverage The coverage
    # @param isSensitive Boolean to state if line is sensitive or not
    def addCellLine (self, cellLine, mutation, coverge, isSensitive):
        #create a new mutation object
        mutation = Mutation(mutation, cellLine, coverge)

        #see if is sensitive or not
        if isSensitive:
            self.__sensitive.append(mutation)
        else:
            self.__unsensitive.append(mutation)

    ## Get the gene name
    # @returns The gene name
    def getGeneName(self):
        return(self.__geneName)

    ## Get the uniprot ID
    # @returns The uniprot ID
    def getUniprotID(self):
        return(self.__uniprotID)

    ## Get the sensitive list
    # @returns sensitive list
    def getSensitiveList(self):
        sensitiveList = []

        for mutation in self.__sensitive:
            mutationString = '%s:%s:%i' % (mutation.getMutation(), mutation.getCellLine(), mutation.getCoverage())
            sensitiveList.append(mutationString)

        return(sensitiveList)

    ## Get the unsensitive list
    # @returns unsensitive list
    def getUnsensitiveList(self):
        unsensitiveList = []

        for mutation in self.__unsensitive:
            mutationString = '%s:%s:%i' % (mutation.getMutation(), mutation.getCellLine(), mutation.getCoverage())
            unsensitiveList.append(mutationString)

        return(unsensitiveList)

    ## Get the sensitive specific variants
    # @returns Sensitive specific list
    def getSensitiveSpecificVariants(self):
        uniqueVariants = []
        uniqueCellLines = {}

        for variant1 in self.__sensitive:
            foundMatch = False

            for variant2 in self.__unsensitive:
                if variant1.getMutation() == variant2.getMutation():
                    foundMatch = True

            #if we didn't find a match add the string
            if not foundMatch:
                mutationString = '%s:%s:%i' % (variant1.getMutation(), variant1.getCellLine(), variant1.getCoverage())
                uniqueVariants.append(mutationString)
                uniqueCellLines[variant1.getCellLine()] = 1

        #return the set
        return(uniqueVariants, uniqueCellLines)


#start here when the script is launched
if (__name__ == '__main__'):

    #set up the option parser
    parser = OptionParser()

    #add the options to parse
    parser.add_option('-c', '--ccle', dest='ccle', help='The ccle mutation file')
    parser.add_option('-u', '--uniprot', dest='uniprot', help='The uniprot map file')
    parser.add_option('-g', '--group', dest='group', help='The group file')
    parser.add_option('-o', '--output', dest='output', help='The output folder')
    parser.add_option('-x', '--coverage', dest='coverage', help='Minimum coverage to count variant')
    (options, args) = parser.parse_args()

    #read in the uniprot map and store the uniprot to gene name info
    genes = {}
    file = open(options.uniprot, 'r')

    #loop over the file
    for line in file:
        line = line.rstrip('\n\r')
        tokens = line.split('\t')

        gene = Gene(tokens[1], tokens[0])
        genes[gene.getGeneName()] = gene

    #close the file
    file.close()

    #now lets read in the group file
    cellLineMap = {}
    file = open(options.group, 'r')

    #loop over the group file
    for line in file:
        line = line.rstrip('\n\r')
        tokens = line.split('\t')

        cellLineMap[tokens[0].upper()] = tokens[1]

    #close the file
    file.close()

    #read in CCLE file and create two sets
    file = open(options.ccle, 'r')

    for line in file:
        line = line.rstrip('\n\r')
        if not line.startswith('#'):
            tokens = line.split('\t')

            #grab info we want
            geneName = tokens[0]
            type = tokens[1]
            sample = tokens[3].upper()
            genomicCoord = tokens[4]
            cDNACoord = tokens[5]
            alternativeCoverage = int(tokens[8])
            referenceCoverage = int(tokens[9])
            coverage = alternativeCoverage + referenceCoverage

            if geneName in genes and sample in cellLineMap and coverage >= int(options.coverage):
                gene = genes[geneName]

                #see if we have cDNA change
                mutation = genomicCoord

                if not cDNACoord == '':
                    mutation = cDNACoord

                #see if sensitive or not and add info to gene
                if cellLineMap[sample] == 'sensitive':
                    gene.addCellLine(sample, mutation, coverage, True)
                elif cellLineMap[sample] == 'unsensitive':
                    gene.addCellLine(sample, mutation, coverage, False)
                else:
                    print 'Improper group used in group file'

    #now lets print out the data
    file = open('%s/%s' % (options.output, 'summary.txt'), 'w')
    file.write('Gene\tUniprot\tSensitive Mutation Count\tSensitive Mutations\tUnsensitive Mutation Count\tUnsensitive Mutations\tUnique Mutation Count\tUnique Mutations\tUnique Cell Line Count\tUnique Cell Lines\n')

    for geneName in genes:
        gene = genes[geneName]

        if not len(gene.getSensitiveList()) == 0 and not len(gene.getUnsensitiveList()) == 0:
            uniqueVariants, uniqueCellLines = gene.getSensitiveSpecificVariants()
            file.write('%s\t%s\t%i\t%s\t%i\t%s\t%i\t%s\t%i\t%s\n' % (gene.getGeneName(), gene.getUniprotID(), len(gene.getSensitiveList()), gene.getSensitiveList(), len(gene.getUnsensitiveList()), gene.getUnsensitiveList(), len(uniqueVariants), uniqueVariants, len(uniqueCellLines), uniqueCellLines.keys()))

    #close the file
    file.close()