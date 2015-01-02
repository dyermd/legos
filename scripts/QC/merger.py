#! /usr/bin/env python

# Goal:  Merge and run coverage analysis on the two Samples generated.
# Output:  A mered bam file, and coverage analysis on the merged bam file.

from optparse import OptionParser
import os
import os.path
import sys
import re

class Merger:
	# @param bams_to_merge a list of the bam files to merge together
	# @param output_dir the directory in which to place the merged bam file
	# @param sample_name the name of the sample. Used for the SM tag
	# @param cleanup Flag to delete the temporary files or not. Default: false
	def __init__(self, bams_to_merge, output_dir, sample_name, cleanup=False):
		self.output_dir = output_dir
		self.cleanup = cleanup
		self.sample_name = sample_name
		self.bams_to_merge = bams_to_merge
		self.merge()
	
	# @param systemCall the command line command to run.
	def runCommandLine(self, systemCall):
		#run the call and return the status
		print 'Starting %s' % (systemCall)
		status = os.system(systemCall)
		return(status)


	# merge the following runs
	def merge(self):
		print "Sample %s is merging the following runs:  %s"%(self.sample_name, self.bams_to_merge)
	
		merge_command = "java -jar /opt/picard/picard-tools-current/MergeSamFiles.jar "
	
		# Add each run's bam file to mergeJob.sh
		for bam in self.bams_to_merge:
			if not os.path.isfile(bam) or bam[-4:] != ".bam":
				print "ERROR: the bam file '%s' does not exist!"%bam
				sys.exit(4)
			merge_command += "INPUT=%s "%bam

		# make sure the output_dir exists, or make it.
		self.runCommandLine("mkdir -p %s"%self.output_dir)
		#if not os.path.isdir(output_dir):
			#print "ERROR: the output dir '%s' does not exist!"%bam
			#sys.exit(4)
			
		# Now set the output file, and then run the merge command
		merge_command +=  "	OUTPUT=%s/merged_badHeader.bam "%self.ouput_dir
	
		if self.runCommandLine(merge_command) != 0:
			print "ERROR: $SAMPLE_DIR something went wrong with merging!"
			sys.exit(1)
	
		#echo "fixing header for %s/merged_badHeader.bam"
		correct_header_command = "samtools view -H %s/merged_badHeader.bam > %s/merged.header.sam "%(self.output_dir, self.ouptut_dir)
		if self.runCommandLine(correct_header_command) != 0:
			print "ERROR: samtools view -H failed!"
			sys.exit(1)
	
		# NEED TO TEST THIS COMMAND. Is there anything that comes before the next : that is important?
		# Change the SM: tag so that it matches for every run merged. (There should be one SM tag for each run merged)
		# This was the old command
		#sed_command = 'sed "s/SM:[a-zA-Z0-9_&/-]*/SM:%s/" %s/merged.header.sam > %s/merged.headerCorrected.sam'%(self.sample_name, self.output_dir, self.ouptut_dir)
		# this updated command will change the SM tag to match everything up to the next : after the SM tag.
		sed_command = 'sed -E "s/SM:[^:]*:/SM:%s:/" %s/merged.header.sam > %s/merged.headerCorrected.sam'%(self.sample_name, self.output_dir, self.ouptut_dir)
		if self.runCommandLine(sed_command) != 0:
			print "ERROR: sed command failed!"
			sys.exit(1)
	
		# write the new header to merged.bam
		reheader_command = "samtools reheader %s/merged.headerCorrected.sam %s/merged_badHeader.bam > %s/merged.bam "%(self.output_dir, self.output_dir, self.ouptut_dir)
		if self.runCommandLine(sed_command) != 0:
			print "ERROR: sed command failed!"
			sys.exit(1)

		# set some extra variables for the JSON file.
		self.path_to_merged_bam = "%s/merged.bam"%self.output_dir
		self.merged_json = "%s/merged.json"%self.output_dir

		# IF specified, cleanup the temporary files
		if self.cleanup:
			os.remove("%s/merged_badHeader.bam"%self.output_dir)
			os.remove("%s/merged.headerCorrected.sam"%self.output_dir)
			os.remove("%s/merged.header.sam"%self.output_dir)
	
		print "%s finished merging "%self.output_dir


if __name__ == '__main__':

	# set up the option parser
	parser = OptionParser()
	
	# add the options to parse
	parser.add_option('-o', '--output_dir', dest='output', help='The output file. If no output file is specified, output will be written to the screen')
	parser.add_option('-s', '--sample_name', dest='sample', help='The name of the sample. Will be used to fix the SM tag of the merged BAM file')
	parser.add_option('-b', '--bams', dest='bams', action='append', help='Use a -b for for each bam to include in merging')
	parser.add_option('-c', '--cleanup', dest='cleanup', action='store_true', help='option to cleanup the temporary files used in merging and such.')

	(options, args) = parser.parse_args()

	if not options.output or not options.sample or not options.bams:
		print "USAGE_ERROR: -o, -s and -b are all required."
		parser.print_help()
		sys.exit(1)

	Merger(options.bams, options.output, options.sample)

