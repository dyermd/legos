from optparse import OptionParser
import subprocess
import os

script = '/home/ionadmin/matt/1000G.py'

__author__ = 'mattdyer'

## Run a job on via SGE
# @param queue The queue to submit the job to
# @param outputFolder The output folder
# @param sample The sample id
# @param file The the shell script to run
# @returns The SGE job number
def submitToSGE(queue, outputFolder, sample, file):
    #build the command call
    systemCall = 'qsub -q %s -e %s/%s_sge.log -o %s/%s_sge.log %s' % (queue, outputFolder, sample, outputFolder, sample, file)

    #submit to SGE and grab the job id
    print systemCall
    status = os.system(systemCall)
    #return("1")

#start here when the script is launched
if (__name__ == '__main__'):

    #set up the option parser
    parser = OptionParser()

    #add the options to parse
    parser.add_option('-o', '--output', dest='output', help='The output folder')
    parser.add_option('-s', '--samples', dest='samples', help='The samples file')
    (options, args) = parser.parse_args()

    #open the file
    fileHandle = open('%s' % (options.samples), 'r')

    #read through file now
    for line in fileHandle.readlines():
        #remove the return
        sampleID = line.rstrip('\n')

        #now create the shell script file
        fileWriterHandle = open('%s/%s.sh' % (options.output, sampleID), 'w')

        #build sh file that will be submitted
        fileWriterHandle.write('#! /bin/bash\n')
        fileWriterHandle.write('#$ -wd %s\n' % options.output)
        fileWriterHandle.write('#$ -N Exome_Extraction.1000G.%s\n' % (sampleID))
        fileWriterHandle.write('#$ -V\n')
        fileWriterHandle.write('#$ -S /bin/bash\n\n')
        fileWriterHandle.write('python %s -f /mnt/Despina/projects/1000G/ -o /mnt/Despina/projects/1000G/individuals/ -s %s -t %s\n' % (script, sampleID, options.output))

        #close the file
        fileWriterHandle.close()

        #now submit the file for analysis
        submitToSGE('all.q', options.output, sampleID, '/tmp/%s.sh' % (sampleID))

    #close the file
    fileHandle.close()