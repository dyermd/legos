__author__ = 'mattdyer'

#This class is responsible for writing the different job wrappers use at TRI
class TemplateWriter:

    ## The constructor
    # @param self The object pointer
    # @params outputDirectory The output directory
    # @param softwareDirectory The software root directory
    def __init__(self, outputDirectory, softwareDirectory):
        #save the output directories
        self.__outputDirectory = outputDirectory
        self.__softwareDirectory = softwareDirectory

    ## Write the analysis template
    # @param self The object pointer
    # @param job The json job object
    # @returns A string to the shell script file to be run
    def writeTemplate(self, job):
        #create the output file
        outputFile = '%s/job.sh' % (self.__outputDirectory)
        fileHandle = open(outputFile, 'w')

        #now depending on the analysis time, add the content we need
        if job['analysis']['type'] == 'qc_tvc':
            #we want to merge, QC, then call variants
            self.__writeHeader(job, fileHandle)
            self.__writeStatusChange('running', job['json_file'], fileHandle, False, job['sample_name'])
            self.__writeCovTVCTemplate(job, fileHandle)
            self.__writeStatusChange('finished', job['json_file'], fileHandle, True, job['sample_name'])
        elif job['analysis']['type'] == 'qc_compare':
            print 'hit'
            self.__writeHeader(job, fileHandle)
            self.__writeStatusChange('running', job['json_file'], fileHandle, False, job['sample_name'])
            self.__writeQCCompareTemplate(job, fileHandle)
            self.__writeStatusChange('finished', job['json_file'], fileHandle, True, job['sample_name'])
        elif job['analysis']['type'] == 'qc_sample':
            self.__writeHeader(job, fileHandle)
            self.__writeStatusChange('running', job['json_file'], fileHandle, False, job['sample_name'])
            self.__writeQCSampleTemplate(job, fileHandle)
            self.__writeStatusChange('finished', job['json_file'], fileHandle, True, job['sample_name'])

        #close the file handle
        fileHandle.close()

        #return the file string
        return(outputFile)

    ## Write the header stuff for a job
    # @param self The object pointer
    # @param job The json job object
    # @param file The file handle
    def __writeHeader(self, job, fileHandle):
        #this is just a dummy holder for now
        fileHandle.write('#! /bin/bash\n')
        fileHandle.write('#$ -wd %s\n' % self.__outputDirectory)
        if 'sample' in job:
            fileHandle.write('#$ -N %s.%s.%s\n' % (job['project'], job['sample'], job['name']))
        else:
            fileHandle.write('#$ -N %s.%s.%s\n' % (job['project'], job['sample_name'], job['analysis']['type']))
        fileHandle.write('#$ -V\n')
        fileHandle.write('#$ -S /bin/bash\n\n')

    ## Write the code for merging BAM files
    # @param self The object pointer
    # @param job The json job object
    # @param file The file handle
    def __writeMergeTemplate(self, job, fileHandle):
        #create a seperate job for each file in the directory
        print ''

    ## Write the code for updating the status in the JSON file
    # @param self The object pointer
    # @param status The json job object
    # @param jsonFile The json file to update the status in
    # @param file The file handle
    # @param wrap Boolean of whether or not to wrap the status
    def __writeStatusChange(self, status, jsonFile, fileHandle, wrap, sample_name):
        #set the status and wrap if requested
        if not wrap:
            fileHandle.write('python %s/scripts/update_json.py -j %s -s %s\n' % (self.__softwareDirectory, jsonFile, status))
			# I'm not sure how to send emails the normal way so I set up ssmtp on the linux server.
            fileHandle.write('echo "%s beginning analysis" | ssmtp -vvv jlaw@childhooddiseases.org' % (job['sample_name']))
        else:
            fileHandle.write('if [ $? -ne 0 ]; then\n')
            fileHandle.write('\tpython %s/scripts/update_json.py -j %s -s %s\n' % (self.__softwareDirectory, jsonFile, "failed"))
            #if 'emails' in job and 'sample_name' in job:
            fileHandle.write('\techo "%s finished with a status of %s" | ssmtp -vvv jlaw@childhooddiseases.org' % (job['sample_name'], "failed"))
            fileHandle.write('else\n')
            fileHandle.write('\tpython %s/scripts/update_json.py -j %s -s %s\n' % (self.__softwareDirectory, jsonFile, status))
            fileHandle.write('\techo "%s finished with a status of %s" | ssmtp -vvv jlaw@childhooddiseases.org' % (job['sample_name'], status))
            fileHandle.write('fi\n')


    ## Write the code for running coverage analysis and tvc
    # @param self The object pointer
    # @param job The json job object
    # @param file The file handle
    def __writeCovTVCTemplate(self, job, fileHandle):
        #default is to not flag dups
        dupFlag = '--remove_dup_flags'

        #see if settings want to mark dups though
        if 'mark_dups' in job['analysis']['settings']:
            #if it is set to true, then we change the flag
            if job['analysis']['settings']['mark_dups'] == 'true':
                print 'here'
                dupFlag = '--flag_dups'

        #default is AmpliSeq for coverage analysis
        coverageAnalysisFlag = '--ampliseq'

        #see if the settings say targetseq
        if 'capture_type' in job['analysis']['settings']:
            #if it is set to true, then we change the flag
            if job['analysis']['settings']['capture_type'].lower() == 'targetseq' or job['analysis']['settings']['capture_type'].lower() == 'target_seq':
                coverageAnalysisFlag = '--targetseq'

        for file in job['analysis']['files']:
            fileHandle.write('bash %s/scripts/runTVC_COV.sh --ptrim PTRIM.bam --cleanup %s %s --cov %s %s --tvc %s %s --output_dir %s %s/%s\n' % (self.__softwareDirectory, dupFlag, coverageAnalysisFlag, job['analysis']['settings']['qc_merged_bed'], job['analysis']['settings']['qc_unmerged_bed'], job['analysis']['settings']['tvc_bed'], job['analysis']['settings']['tvc_parameter_json'], job['output_folder'], job['output_folder'], file))

    ## Write the code for running qc comparisons
    # @param self The object pointer
    # @param job The json job object
    # @param file The file handle
    def __writeQCCompareTemplate(self, job, fileHandle):
        #default is to analyze all chromsomes
        chrFlag = '-chr chr1'
        # default is to cleanup
        cleanupFlag='-cl'

        # if analyze_all_chromosomes is set to true in the json file, then take off the chrFlag
        if job['analysis']['settings']['analyze_all_chromosomes'] == True:
            chrFlag = ''

        # If cleanup is specified to false in the json file, then remove the cleanupFlag
        if 'cleanup' in job['analysis']['settings'] and job['analysis']['settings']['cleanup'] == False:
            cleanupFlag = ''

        #let's check the type
        if job['analysis']['settings']['type'] == 'germline':
            #germline sample
            fileHandle.write('bash %s/scripts/QC/QC_sample.sh --beg_bed %s --end_bed %s -s %s -g %s %s %s %s -a %s -b %s %s %s\n' % (self.__softwareDirectory, job['analysis']['settings']['beg_bed'], job['analysis']['settings']['end_bed'], job['sample_folder'], job['analysis']['settings']['tvc_parameter_json'], job['analysis']['settings']['min_base_coverage'], job['analysis']['settings']['wt_cutoff'], job['analysis']['settings']['hom_cutoff'], job['analysis']['settings']['min_amplicon_coverage'], job['analysis']['settings']['project_bed'], chrFlag, cleanupFlag))
        elif job['analysis']['settings']['type'] == 'tumor_normal':
            #tumor_normal sample
            fileHandle.write('bash %s/scripts/QC/QC_sample.sh --beg_bed %s --end_bed %s -s %s -all %s %s %s %s %s %s %s %s -a %s -b %s %s %s\n' % (self.__softwareDirectory, job['analysis']['settings']['beg_bed'], job['analysis']['settings']['end_bed'], job['sample_folder'], job['analysis']['settings']['normal_tvc_json'], job['analysis']['settings']['normal_min_base_coverage'], job['analysis']['settings']['normal_wt_cutoff'], job['analysis']['settings']['normal_hom_cutoff'], job['analysis']['settings']['tumor_tvc_json'], job['analysis']['settings']['tumor_min_base_coverage'], job['analysis']['settings']['tumor_wt_cutoff'], job['analysis']['settings']['tumor_hom_cutoff'], job['analysis']['settings']['min_amplicon_coverage'], job['analysis']['settings']['project_bed'], chrFlag, cleanupFlag))
        #add other types later


    ## Write the code for running qc comparisons
    # @param self The object pointer
    # @param job The json job object
    # @param file The file handle
    def __writeQCSampleTemplate(self, job, fileHandle):
		# the settings should all be contained within the json file.
        fileHandle.write('python2.7 %s/scripts/QC/QC_sample.py --json %s \n'%(self.__softwareDirectory, job['json_file']))
		# use this for if the samples you're running don't have the cutoffs set or need to have teh pass/fail status set
        #fileHandle.write('python %s/scripts/QC/QC_sample.py --json %s --update_cutoffs /home/ionadmin/jeff/PNET.json --pass_fail \n'%(self.__softwareDirectory, job['json_file']))
        #add other types later


    ## Write the code for running TVC
    # @param self The object pointer
    # @param job The json job object
    # @param file The file handle
    def __writeTVCTemplate(self, job, fileHandle):
        #this is just a dummy holder for now
        print ''
