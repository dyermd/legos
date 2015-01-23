#! /usr/bin/env python

from optparse import OptionParser
import os
import os.path
import sys
import re
import json
import glob
import shutil

class Cleanup:
	def __init__(self):
		pass
	

	# @param systemCall command to run from bash
	# @returns the exit code or status of the bash command
	def runCommandLine(self, systemCall):
		#run the call and return the status
		print 'Starting %s' % (systemCall)
		status = os.system(systemCall)
		return(status)


	# @param runs loop through and cleanup each run.
	def cleanup_runs(self, runs, cleanup_flag=True, no_errors=True):
		if cleanup_flag == True and no_errors == True:
			for run in runs:
				self.cleanup_run(run)


	# Cleanup the PTRIM and assorted files generated.
	def cleanup_run(self, run):
		try:
			run_json = json.load(open(run))
			# Remove the PTRIM.bam and PTRIM.bam.bai
			ptrims = glob.glob("%s/PTRIM*.bam*"%run_json['run_folder'])
			for ptrim in ptrims:
				os.remove(ptrim)
		
			# Remove any individual chromosomes subset bam files.
			chr_dirs = glob.glob("%s/chr*"%run_json['run_folder'])
			for chr_dir in chr_dirs:
				shutil.rmtree(chr_dir)
			# Remove the temporary files used in making the QC tables
			temp_dirs = glob.glob("%s/QC/*%s*/temp_files"%(run_json['sample_folder'], run_json['run_name']))
			for temp_dir in temp_dirs:
				shutil.rmtree(temp_dir)
			# Remove anything else that should be removed.
			# can't think of anything else yet.
		except KeyError, ValueError:
			pass


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
