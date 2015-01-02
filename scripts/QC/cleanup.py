#! /usr/bin/env python

from optparse import OptionParser
import os
import os.path
import sys
import re
import json
import glob

class Cleanup:
	def __init__(self, sample_json):
		pass
	

	# @param systemCall command to run from bash
	# @returns the exit code or status of the bash command
	def runCommandLine(self, systemCall):
		#run the call and return the status
		print 'Starting %s' % (systemCall)
		status = os.system(systemCall)
		return(status)


	# @param runs loop through and cleanup each run.
	def cleanup_runs(self, runs):
		for run in runs:
			self.cleanup_run(run)


	# Cleanup the PTRIM and assorted files generated.
	def cleanup_run(self, run):
		run_json = json.load(open(run))
		# Remove the PTRIM.bam and PTRIM.bam.bai
		ptrims = glob.glob("%s/PTRIM*.bam*"%run_json['output_folder'])
		for ptrim in ptrims:
			os.remove(ptrim)
	
		# Remove any individual chromosomes subset bam files.
		chr_dirs = glob.glob("%s/chr*"%run_json['output_folder'])
		for chr_dir in chr_dirs:
			shutil.rmtree(chr_dir)
		# Remove anything else that should be removed.
		# can't think of anything else yet.


if __name__ == '__main__':

	# set up the option parser
	parser = OptionParser()
	
	# add the options to parse
	parser.add_option('-s', '--json', dest='json', help='The sample to cleanup')

	(options, args) = parser.parse_args()

	if not os.path.isfile(options.json):
		print "USAGE_ERROR: json: %s not found"%options.json
		parser.print_help()
		sys.exit(1)

	cleanup = Cleanup()
	self.sample_json = json.load(open(options.json))
	cleanup_runs(sample_json['runs'])

