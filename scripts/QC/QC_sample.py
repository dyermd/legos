#! /usr/bin/env python

from optparse import OptionParser
import os
import os.path
import sys
import re
import json

class QC_Sample:
	def __init__(self, options):
		self.options = options
		self.sample_json = json.load(open(options.json))
		self.__softwareDirectory = "/rawdata/legos"
		self.__QCDirectory = "/rawdata/legos/scripts/QC"
		self.no_errors = True
	
	def runCommandLine(self, systemCall):
		#run the call and return the status
		print 'Starting %s' % (systemCall)
		status = os.system(systemCall)
		return(status)

	# will find all of the runs in a sample and QC them with each other
	def QC_all_runs(self):
		# if this is a germline sample, QC all of the normal runs with each other.
		if self.sample_json['sample_type'] == 'germline':
			# QC the normal runs with each other
			self.QC_normal_runs(self.sample_json['runs'])
		# if this is a tumor_normal sample, find the normal and tumor runs, and then QC them with each other.
		elif self.sample_json['sample_type'] == 'tumor_normal':
			normal_runs = []
			tumor_runs = []
			for run in self.sample_json['runs']:
				run_json = json.load(open(run))
				if run_json['run_type'] == 'normal':
					normal_runs.append(run)
				elif run_json['run_type'] == 'tumor':
					tumor_runs.append(run)
				else:
					print "ERROR run type is not normal or tumor."
			if self.sample_json['analysis']['settings']['type'] == 'all_tumor_normal':
				# QC the normal runs with each other
				self.QC_normal_runs(normal_runs, 'normal_')
				# QC the tumor runs with each other
				self.QC_tumor_runs(tumor_runs, 'tumor_')
				# now QC the tumor and normal runs together.
				self.QC_normal_tumor_runs(normal_runs, tumor_runs)
			elif self.sample_json['analysis']['settings']['type'] == 'normal_only':
				# QC the normal runs with each other
				self.QC_normal_runs(normal_runs, 'normal_')
			elif self.sample_json['analysis']['settings']['type'] == 'tumor_only':
				# QC the tumor runs with each other
				self.QC_tumor_runs(tumor_runs, 'tumor_')
			# need to run TVC and COV first still...
			#elif self.sample_json['analysis']['settings']['type'] == 'tumor_normal_only':
			#	# now QC the tumor and normal runs together.
			#	self.QC_normal_tumor_runs(self, normal_runs, tumor_runs):

	# QC the normal runs with each other
	def QC_normal_runs(self, normal_runs, pref=''):
		# first run TVC_CV and get the Run info to prepare for QC2Runs
		for normal_run1 in normal_runs:
			self.runTVC_COV(normal_run1, pref)
			self.getRunInfo(normal_run1, pref)
		for normal_run1 in normal_runs:
			normal_run1_json = json.load(open(normal_run1))
			for normal_run2 in normal_runs:
				normal_run2_json = json.load(open(normal_run2))
				# check to see if these two runs should be QC'd together.
				if int(normal_run1_json['run_num']) < int(normal_run2_json['run_num']):
					self.QC_2Runs(normal_run1, normal_run2, pref, pref)

	# QC the tumor runs with each other
	def QC_tumor_runs(self, tumor_runs, pref):
		# first run TVC_CV and get the Run info to prepare for QC2Runs
		for tumor_run1 in tumor_runs:
			self.runTVC_COV(tumor_run1, pref)
			self.getRunInfo(tumor_run1, pref)
		for tumor_run1 in tumor_runs:
			tumor_run1_json = json.load(open(tumor_run1))
			for tumor_run2 in tumor_runs:
				tumor_run2_json = json.load(open(tumor_run2))
				# check to see if these two runs should be QC'd together.
				if int(tumor_run1_json['run_num']) < int(tumor_run2_json['run_num']):
					self.QC_2Runs(tumor_run1, tumor_run2, pref, pref)

	# now QC the tumor and normal runs together.
	def QC_normal_tumor_runs(self, normal_runs, tumor_runs):
		for normal_run in normal_runs:
			for tumor_run in tumor_runs:
					# QC the normal and tumor runs together
					self.QC_2Runs(normal_run, tumor_run, 'normal_', 'tumor_')

	# @param run the run for which to run TVC and coverage analysis
	def runTVC_COV(self, run, pref):
	   #default is to not flag dups
		dupFlag = '--remove_dup_flags'
	
	   #see if settings want to mark dups though
		if 'mark_dups' in self.sample_json['analysis']['settings']:
		   #if it is set to true, then we change the flag
		   if self.sample_json['analysis']['settings']['mark_dups'] == 'true':
			  dupFlag = '--flag_dups'
	
	   #default is AmpliSeq for coverage analysis
		coverageAnalysisFlag = '--ampliseq'
	
	   #see if the settings say targetseq
		if 'capture_type' in self.sample_json['analysis']['settings']:
		   #if it is set to true, then we change the flag
		   if self.sample_json['analysis']['settings']['capture_type'].lower() == 'targetseq' or self.sample_json['analysis']['settings']['capture_type'].lower() == 'target_seq':
			   coverageAnalysisFlag = '--targetseq'
	
		run_json = json.load(open(run))
		print run_json 
	
		for file in run_json['analysis']['files']:
			command = 'bash %s/scripts/runTVC_COV.sh '%self.__softwareDirectory + \
					'--ptrim PTRIM.bam ' + \
					'--cleanup %s %s '%(dupFlag, coverageAnalysisFlag) + \
					'--cov %s %s '%(self.sample_json['analysis']['settings']['qc_merged_bed'], self.sample_json['analysis']['settings']['qc_unmerged_bed']) + \
					'--tvc %s %s '%(self.sample_json['analysis']['settings']['project_bed'], self.sample_json['analysis']['settings']['%stvc_json'%pref]) + \
					'--output_dir %s %s/%s '%(run_json['run_folder'], run_json['run_folder'], file)
			# run TVC and Cov analysis on this sample.
			status = self.runCommandLine(command)
			if status != 0:
				sys.stderr.write("%s runTVC_COV.sh had an error!!\n"%run)
				self.no_errors = False

	# @param run the json file of the run
	def getRunInfo(self, run, pref):
		run_json = json.load(open(run))
	
		# QC_getRunInfo.sh gets the following metrics: % amps covered at the beg and end, Ts/Tv ratio,	# Total variants,	# HET variants, 	# HOM variants
		# It also gets the metrics from the report.pdf if it is available.
		# I had to put it all on one line because python kept complaining about formatting issues.
		qcgetruninfo="bash %s/QC_getRunInfo.sh "%self.__QCDirectory + \
				"--run_dir %s "%run_json['run_folder'] + \
				"--out_dir %s/Analysis_Files/temp_files "%run_json['run_folder'] + \
				"--amp_cov_cutoff %s "%self.sample_json['analysis']['settings']['min_amplicon_coverage'] + \
				"--depth_cutoff %s "%self.sample_json['analysis']['settings']['%smin_base_coverage'%pref] + \
				"--wt_hom_cutoff %s %s "%(self.sample_json['analysis']['settings']['%swt_cutoff'%pref], self.sample_json['analysis']['settings']['%shom_cutoff'%pref])+ \
				"--beg_bed  %s "%self.sample_json['analysis']['settings']['beg_bed'] + \
				"--end_bed %s "%self.sample_json['analysis']['settings']['end_bed'] + \
				"--project_bed %s "%str(self.sample_json['analysis']['settings']['project_bed']) + \
				"--ptrim_json %s/PTRIM.bam "%run_json['run_folder']

		#if [ "$CDS_BED" != "" ]; then
		#	qcgetruninfo="$qcgetruninfo --cds_bed $CDS_BED "
		# QC_getRunInfo's will run the pool dropout script 
		if self.sample_json['analysis']['settings']['pool_dropout'] == True:
			qcgetruninfo += "--pool_dropout "
		# cleanup will be done at the end of this script
	
		#run the qcgetruninfo command
		status = self.runCommandLine(qcgetruninfo)
	
		if status == 1:
			sys.stderr.write("%s QC_getRunInfo.sh had an error!!\n"%run)
			self.no_errors = False
		if status == 4:
			sys.stderr.write("%s QC_getRunInfo.sh got a file not found error...\n"%run)
			self.no_errors = False
		if status == 8:
			sys.stderr.write("%s QC_getRunInfo.sh got a usage error...\n"%run)
			self.no_errors = False

	# QC two runs with each other
	# For Tumor / Normal pairs, Run1 should be the normal run, and Run2 should be the tumor run.
	# Output will be put into a dir like: sample1/QC/Run1vsRun2
	def QC_2Runs(self, run1, run2, pref1, pref2):
		# This if statement is not needed, it's just an extra catch
		if run1 != run2:
			run1_json = json.load(open(run1))
			run2_json = json.load(open(run2))
	
			if 'results_QC_json' in self.sample_json:
				output_json = self.sample_json['results_QC_json']
			else:
				output_json = "%s/results_QC.json"%self.sample_json['output_folder']
			
			# QC these two runs for every chr type that is listed in chromosomes to analyze.
			for chromosome in self.sample_json['analysis']['settings']['chromosomes_to_analyze']:
				# QC these two runs. QC_2Runs.sh takes the two run dirs and finds a .bam, .vcf, and .cov.xls file in the same dir as the .bam file
				qc2runs = "bash %s/QC_2Runs.sh "%self.__QCDirectory + \
				"--run_dirs %s %s "%(run1_json['run_folder'], run2_json['run_folder']) + \
				"--json_out %s "%output_json + \
				"--project_bed %s "%self.sample_json['analysis']['settings']['project_bed'] + \
				"-a %s "%self.sample_json['analysis']['settings']['min_amplicon_coverage'] + \
				"-jp %s %s "%(self.sample_json['analysis']['settings']['%stvc_json'%pref1], self.sample_json['analysis']['settings']['%stvc_json'%pref2]) + \
				"-d %s %s "%(self.sample_json['analysis']['settings']['%smin_base_coverage'%pref1], self.sample_json['analysis']['settings']['%smin_base_coverage'%pref2]) + \
				"-gt %s %s %s %s "%(self.sample_json['analysis']['settings']['%swt_cutoff'%pref1], self.sample_json['analysis']['settings']['%shom_cutoff'%pref1], self.sample_json['analysis']['settings']['%swt_cutoff'%pref2], self.sample_json['analysis']['settings']['%shom_cutoff'%pref2]) 

				# now set the output_dir
				output_dir = "%s/%s%svs%s"%(self.sample_json['output_folder'], chromosome, run1_json['run_name'], run2_json['run_name'])
				if chromosome != "all":
					qc2runs += "--subset_chr %s "%chromosome
					output_dir = "%s/%s%svs%s"%(self.sample_json['output_folder'], chromosome, run1_json['run_name'], run2_json['run_name'])
				qc2runs += "--output_dir %s "%output_dir
				#if [ "$CDS_BED" != "" ]; then
				#	qc2runs="$qc2runs -cb $CDS_BED "
				#if [ "$SUBSET_BED" != "" ]; then
				#	qc2runs="$qc2runs --subset_bed $SUBSET_BED "
				#if [ "$RUN_GATK_CDS" == "True" ]; then
				#	qc2runs="$qc2runs --run_gatk_cds "
				# The cleanup will be done at the end of this script because the PTRIM.bam is needed for QC_getRunInfo.sh, and the chr_subset is needed for each run comparison
				#if [ "$CLEANUP" == "True" ]; then
				#	qc2runs="$qc2runs --cleanup "
	
				#run the qcgetruninfo command
				status = self.runCommandLine(qc2runs)
			
				if status == 1:
					sys.stderr.write("%s QC_2Runs.sh had an error!!\n"%run)
					self.no_errors = False
				if status == 4:
					sys.stderr.write("%s QC_2Runs.sh got a file not found error...\n"%run)
					self.no_errors = False
				if status == 8:
					sys.stderr.write("%s QC_2Runs.sh got a usage error...\n"%run)
					self.no_errors = False

if __name__ == '__main__':

	# set up the option parser
	parser = OptionParser()
	
	# add the options to parse
	parser.add_option('-j', '--json', dest='json', help="A sample's json file which contains the necessary options and list of runs to QC with each other")

	(options, args) = parser.parse_args()

	# check to make sure the inputs are valid
	if not options.json:
		print "USAGE-ERROR-- --json is required"
		parser.print_help()
		sys.exit(1)
	if not os.path.isfile(options.json):
		print "ERROR-- %s not found"%options.json
		parser.print_help()
		sys.exit(1)

	qc_sample = QC_Sample(options)
	qc_sample.QC_all_runs()

