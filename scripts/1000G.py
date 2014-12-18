# this script takes in thee 1000 Genomes data and extracts variants from specific individuals
from optparse import OptionParser
import os
import fnmatch
import subprocess

__author__ = 'mattdyer'

def runCommandLine(systemCall):
    #run the call and return the status
    print 'Starting %s' % (systemCall)
    status = os.system(systemCall)
    return(status)

#start here when the script is launched
if (__name__ == '__main__'):

    #set up the option parser
    parser = OptionParser()

    #add the options to parse
    parser.add_option('-f', '--folder', dest='folder', help='Folder with 1000G .vcf.gz files')
    parser.add_option('-o', '--output', dest='output', help='The output folder')
    parser.add_option('-s', '--sample', dest='sample', help='The sample ID')
    parser.add_option('-t', '--temp', dest='temp', help='The temp folder')
    (options, args) = parser.parse_args()

    #files to merge
    files = []

    if not os.path.isdir(options.output):
        os.mkdir(options.output)

    #first we want to grab all the .vcf.gz files
    #see if this directory exists
    if os.path.isdir(options.folder):
        for root, dirnames, filenames in os.walk(options.folder):
            for filename in fnmatch.filter(filenames, '*.vcf.gz'):
                #now parse the file name and get chromosome number
                tokens = filename.split('.')
                chromosome = tokens[1]
                number = chromosome.replace('chr','')

                #now let's run the tools we need
                systemCall = 'tabix -f -h %s/%s %s | /usr/bin/vcf-subset -f -e -c %s | cut -f1,2,3,4,5,6,7,8 > %s/%s_%s_subset.vcf' % (root, filename, number, options.sample, options.temp, options.sample, number)
                print systemCall
                runCommandLine(systemCall)

                #now we need to bgzip the file
                systemCall = 'bgzip %s/%s_%s_subset.vcf' % (options.temp, options.sample, number)
                print systemCall
                runCommandLine(systemCall)

                #now lets tabix it
                systemCall = 'tabix -f -p vcf %s/%s_%s_subset.vcf.gz' % (options.temp, options.sample, number)
                print systemCall
                runCommandLine(systemCall)

                #finally add it to the list of files to merge
                files.append('%s/%s_%s_subset.vcf.gz' % (options.temp, options.sample, number))

    #now we merge the vcf files
    systemCall = 'vcf-merge %s > %s/%s.vcf' % (' '.join(files), options.output, options.sample)
    print systemCall
    runCommandLine(systemCall)

    #now clean up
    systemCall = 'rm %s' % (' '.join(files))
    print systemCall
    runCommandLine(systemCall)