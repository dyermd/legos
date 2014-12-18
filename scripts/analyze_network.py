import networkx as nx
import matplotlib.pyplot as plt
from optparse import OptionParser

__author__ = 'mattdyer'

#start here when the script is launched
if (__name__ == '__main__'):
    #set up the option parser
    parser = OptionParser()

    #add the options to parse
    parser.add_option('-n', '--network', dest='network', help='Protein interaction network file')
    parser.add_option('-o', '--output', dest='output', help='The output directory')
    (options, args) = parser.parse_args()

    #build a graph
    graph = nx.Graph()

    #parse the file now
    file = open(options.network, 'r')

    #loop over the file and build the network
    for line in file:
        line = line.rstrip('\n\r')
        tokens = line.split('\t')
        protein1 = tokens[0]
        protein2 = tokens[2]

        #exclude self interactions and see if the graph already has the edge or not
        if not protein1 == protein2 and not graph.has_edge(protein1, protein2) and not graph.has_edge(protein2, protein1):
            graph.add_edge(protein1, protein2)

    #close the file
    file.close()

    #get the degrees and centrality of each protein
    centrality = nx.betweenness_centrality(graph, normalized=True)
    degree = nx.degree(graph)

    #print the results
    file = open(options.output, 'w')
    file.write('#protein\tdegree\tcentrality\n')

    for protein in centrality:
        file.write('%s\t%s\t%s\n' % (protein, str(degree[protein]), str(centrality[protein])))

    #close the file
    file.close()