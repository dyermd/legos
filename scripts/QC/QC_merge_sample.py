#! /usr/bin/env python

from optparse import OptionParser
import os
import os.path
import sys
import re
import json
import glob
import shutil
from merger import Merger
from cleanup import Cleanup
from alignment_stats import Align_Stats

class QC_Sample:
	def __init__(self, options):
		self.options = options
		self.sample_json = json.load(open(options.json))
		self.__softwareDirectory = "/rawdata/legos"
		self.__QCDirectory = "/rawdata/legos/scripts/QC"
		self.no_errors = True
		self.cleanup_sample = Cleanup()
	

	# @param path the path of the json file
	# @json_data the json dictionary to be written
	def write_json(self, path, json_data):
		with open(path, 'w') as newJobFile:
			json.dump(json_data, newJobFile, sort_keys=True, indent=4)


	# @param systemCall the command to run by bash
	# @returns the status of either 0 or 1.
	def runCommandLine(self, systemCall):
		#run the call and return the status
		print 'Starting %s' % (systemCall)
		status = os.system(systemCall)
		return(status)

	
	# if the update_json flag is specified, then update the cutoffs found in the normal json file.
	def update_cutoffs(self):
		# load the json file
		update_json = json.load(open(self.options.update_cutoffs))
		# set the cutoff settings to the example json's cutoff settings
		self.sample_json['analysis']['settings']['cutoffs'] = update_json['analysis']['settings']['cutoffs']
		# write the updated sample's json file.
		self.write_json(self.options.json, self.sample_json)


	# will find all of the runs in a sample and QC them with each other
	def QC_merge_runs(self):
		# if this is a germline sample, QC all of the normal runs with each other.
		if self.sample_json['sample_type'] == 'germline':
			# QC the normal runs with each other
			self.QC_runs(self.sample_json['runs'])
			# Merge the passing normal runs with each other
			self.merge_runs(self.sample_json['runs'], "%s/Merged"%self.sample_json['sample_folder'], 'germline', "Merged")
			# Don't cleanup until after all of the QC is done.
			self.cleanup_sample.cleanup_runs(self.sample_json['runs'])
		# if this is a tumor_normal sample, find the normal and tumor runs, and then QC them with each other.
		elif self.sample_json['sample_type'] == 'tumor_normal':
			# Separate the runs into tumor and normal lists
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
				# QC the normal or tumor runs with each other
				self.QC_runs(normal_runs, 'normal_')
				self.QC_runs(tumor_runs, 'tumor_')
				# now QC the tumor and normal runs together.
				self.QC_normal_tumor_runs(normal_runs, tumor_runs)
				# Cleanup the PTRIM.bam and chr bam files after all of the QC is done.
				self.cleanup_sample.cleanup_runs(self.sample_json['runs'])
				# merge the normal and/or tumor runs. Will only merge the passing runs with each other.
				self.merge_runs(normal_runs, "%s/Normal/Merged"%self.sample_json['sample_folder'], 'normal_', 'normal', 'Normal_Merged')
				self.merge_runs(tumor_runs, "%s/Tumor/Merged"%self.sample_json['sample_folder'], 'tumor_', 'tumor', 'Tumor_Merged')
				# now QC the tumor and normal merged bams together if both normal and tumor runs are ready.
				if 'merged_normal_json' in self.sample_json and 'merged_tumor_json' in self.sample_json:
					self.QC_normal_tumor_runs([self.sample_json['merged_normal_json']], [self.sample_json['merged_tumor_json']])
				# Cleanup after the merging QC is done.
				self.cleanup_sample.cleanup_runs(self.sample_json['runs'])
			# Don't worry about these for now.
#			elif self.sample_json['analysis']['settings']['type'] == 'normal_only':
#				# QC the normal runs with each other
#				self.QC_runs(normal_runs, 'normal_')
#				# merge the passing normal_runs with each other
#				self.merge_runs(normal_runs, "%s/Normal/Merged"%self.sample_json['sample_folder'], 'normal_', 'normal', 'Normal_Merged')
#			elif self.sample_json['analysis']['settings']['type'] == 'tumor_only':
#				# QC the tumor runs with each other
#				self.QC_runs(tumor_runs, 'tumor_')
#				# merge the passing normal_runs with each other
#				self.merge_runs(normal_runs, "%s/Tumor/Merged"%self.sample_json['sample_folder'], 'tumor_', 'tumor', 'Tumor_Merged')


	# QC the normal runs with each other 
	def QC_runs(self, runs, pref=''):
		# first run TVC_CV and get the Run info to prepare for QC2Runs
		for run in runs:
			run_json = json.load(open(run))
			# only run these if this run has a status of pending.
			# This way the pass_fail_status can be manually overwritten.
			if run_json['pass_fail_status'] == "pending":
				self.runTVC_COV(run, pref)
				self.getRunInfo(run, pref)
				# Update the run status based on the metrics gathered by QC_getRunInfo.sh
				self.update_run_status(run)
		for run1 in runs:
			run1_json = json.load(open(run1))
			for run2 in runs:
				run2_json = json.load(open(run2))
				# check to see if these two runs should be QC'd together. Only QC the runs that pass the single run QC metrics.
				if int(run1_json['run_num']) < int(run2_json['run_num']) and run1_json['pass_fail_status'] == 'pass' and run2_json['pass_fail_status'] == 'pass':
					self.QC_2Runs(run1, run2, pref, pref)


	# now QC the tumor and normal runs together.
	def QC_normal_tumor_runs(self, normal_runs, tumor_runs):
		for normal_run in normal_runs:
			for tumor_run in tumor_runs:
				normal_json = json.load(open(normal_run))
				tumor_json = json.load(open(tumor_run))
				# Only QC the runs that pass the single run QC metrics.
				if normal_json['pass_fail_status'] == 'pass' and tumor_json['pass_fail_status'] == 'pass':
					self.QC_2Runs(normal_run, tumor_run, 'normal_', 'tumor_')


	# get the separate the runs of the sample by status
	def get_runs_status(self, runs):
		passing_runs = []
		pending_runs = []
		for run in runs:
			run_json = json.load(open(run))
			if run_json['status'] == 'pending':
				pending_runs.append(run)
			elif run_json['status'] == 'pass':
				passing_runs.append(run)
		return pending_runs, passing_runs


	# runTVC_COV will only run TVC or coverage analysis if a .vcf or .cov.xls file is not found in the sample dir.
	# @param run the run for which to run TVC and coverage analysis
	def runTVC_COV(self, run, pref):
		# load the run's json file
		run_json = json.load(open(run))
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


	# getRunInfo will only be run if one of the needed parameters is not found.
	# @param run the json file of the run
	def getRunInfo(self, run, pref):
		run_json = json.load(open(run))
		# if the following metrics have already been gathered, then skip running getRunInfo.sh
		if 'run_data' in run_json and 'ts_tv' in run_json['run_data'] and 'beg_amp_cov' in run_json['run_data'] and 'num_het' in run_json['run_data'] and ('pools_total' in run_json['run_data'] or self.sample_json['analysis']['settings']['pool_dropout'] != True):
			print "%s already has a PTRIM.bam and a VCF file. Skipping getRunInfo.sh"%run
		else:
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
		# if the median read length was not gathered from the report PDF, or if this is a merged bam file, then calculate the median read length
		new_run_json = json.load(open(run))
		if 'median_read_length' not in new_run_json or new_run_json['median_read_length'] == "":
			# Align_Stats is imported from alignment_stats.py
			Align_Stats = Align_Stats()
			new_run_json['median_read_length'] = Align_Stats.calcMedianFromBam(new_run_json['analysis']['files'][0])
			#write new json file
			self.write_json(run, new_run_json)


	# QC two runs with each other
	# For Tumor / Normal pairs, Run1 should be the normal run, and Run2 should be the tumor run.
	# Output will be put into a dir like: sample1/QC/Run1vsRun2
	def QC_2Runs(self, run1, run2, pref1, pref2):
		run1_json = json.load(open(run1))
		run2_json = json.load(open(run2))
	
		if 'results_QC_json' in self.sample_json:
			output_json = self.sample_json['results_QC_json']
		else:
			output_json = "%s/results_QC.json"%self.sample_json['output_folder']
	
		output_json_data = {}
		if os.path.isfile(output_json):
			output_json_data = json.load(open(output_json))
	
		# run1 vs run2:
		run1vsrun2 = '%svs%s'%(run1_json['run_name'], run2_json['run_name'])
		
		# IDEA: If the 'all' comparison has already been made, then pull the chr combination out of it.
		# IDEA: Only QC the runs that pass the single run QC metrics.
		# QC these two runs for every chr type that is listed in chromosomes to analyze.
		for chromosome in self.sample_json['analysis']['settings']['chromosomes_to_analyze']:
			# now set the output_dir
			output_dir = "%s/%s%svs%s"%(self.sample_json['output_folder'], chromosome, run1_json['run_name'], run2_json['run_name'])
			if chromosome != "all":
				qc2runs += "--subset_chr %s "%chromosome
				output_dir = "%s/%s%svs%s"%(self.sample_json['output_folder'], chromosome, run1_json['run_name'], run2_json['run_name'])
	
			# If this QC comparison has already been made, skip it.
			if 'QC_comparisons' in output_json_data and chromosome in output_json_data['QC_comparisons'] and run1vsrun2 in output_json_data['QC_comparisons'][chromosome]:
				print "%s has already run QC_2runs. Skipping."%output_dir
			else:
				# QC these two runs. QC_2Runs.sh takes the two run dirs and finds a .bam, .vcf, and .cov.xls file in the same dir as the .bam file
				qc2runs = "bash %s/QC_2Runs.sh "%self.__QCDirectory + \
				"--run_dirs %s %s "%(run1_json['run_folder'], run2_json['run_folder']) + \
				"--json_out %s "%output_json + \
				"--output_dir %s "%output_dir + \
				"--project_bed %s "%self.sample_json['analysis']['settings']['project_bed'] + \
				"-a %s "%self.sample_json['analysis']['settings']['min_amplicon_coverage'] + \
				"-jp %s %s "%(self.sample_json['analysis']['settings']['%stvc_json'%pref1], self.sample_json['analysis']['settings']['%stvc_json'%pref2]) + \
				"-d %s %s "%(self.sample_json['analysis']['settings']['%smin_base_coverage'%pref1], self.sample_json['analysis']['settings']['%smin_base_coverage'%pref2]) + \
				"-gt %s %s %s %s "%(self.sample_json['analysis']['settings']['%swt_cutoff'%pref1], self.sample_json['analysis']['settings']['%shom_cutoff'%pref1], self.sample_json['analysis']['settings']['%swt_cutoff'%pref2], self.sample_json['analysis']['settings']['%shom_cutoff'%pref2])
	
				#"--cleanup " # The main cleanup will be done at the end of this script because the PTRIM.bam is needed for QC_getRunInfo.sh, and the chr_subset is needed for each run comparison.
				# the main cleanup here will be the temporary files used in 3x3 table generation.
				# These are old settings we probably won't need anymore.
				#if [ "$CDS_BED" != "" ]; then
				#	qc2runs="$qc2runs -cb $CDS_BED "
				#if [ "$SUBSET_BED" != "" ]; then
				#	qc2runs="$qc2runs --subset_bed $SUBSET_BED "
				#if [ "$RUN_GATK_CDS" == "True" ]; then
				#	qc2runs="$qc2runs --run_gatk_cds "
		
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

	
	# @param run_json Update the pass/fail status of this run according to the cutoffs specified here.
	def update_run_status(self, run):
		run_json = json.load(open(run))
		status = 'pass'
		# Update differently for runs vs merged bam files
		if run_json['json_type'] == 'run':
			# first check the % expected median read length
			# check the coverage at the +10 and -10 positions
			# check the pool coverage
			# checck the coverage
			if run_json['run_data']['perc_exp_median_read_length'] < self.sample_json['analysis']['settings']['cutoffs']['perc_exp_median_read_length'] \
					or run_json['run_data']['begin_amp_cov'] < self.sample_json['analysis']['settings']['cutoffs']['begin_end_amp_cov'] \
					or run_json['run_data']['end_amp_cov'] < self.sample_json['analysis']['settings']['cutoffs']['begin_end_amp_cov'] \
					or self.sample_json['run_data']['30x_cov'] < self.sample_json['analysis']['settings']['cutoffs']['run_30x_cov']:
				status = 'fail'
			if self.sample_json['analysis']['settings']['pool_dropout']:
				# currently the only options are 10, 50, and 75 so just stick with this.
				if run_json['run_data']['pools_between_10_and_50'] > 0 or run_json['run_data']['pools_less_than_10'] > 0:
					status = 'fail'
		# Update the merged bam status differently 
		elif run_json['json_type'] == 'merged':
			if self.sample_json['run_data']['30x_cov'] < self.sample_json['analysis']['settings']['cutoffs']['merged_30x_cov']:
				status = 'fail'
			if self.sample_json['sample_type'] == "tumor_normal":
				# Check the 3x3 table's total overlapping bases.
				# IMPLEMENT need to update this setting to be 'qc_json' rather than simple an 'output_folder'
				qc_json = json.load(open("%s/results_QC.json"%self.sample_json['output_folder']))
				if qc_json['QC_comparisons']['all']['tumor_normal']['Normal_MergedvsTumor_Merged']['perc_avail_bases'] < self.sample_json['analysis']['settings']['cutoffs']['merged_30x_cov']:
					status = 'fail'
		# set the pass fail status for this run
		run_json['pass_fail_status'] = status
		# write this run's updated status to the json file
		self.write_json(run, run_json)


	# IDEA: Update run status based on the 3x3 table error rates.
	#- If any of them aren't, then check to see if a single run fails two or more different QC tables. If it did, then that is a failed run. If not, manual human intervention is needed.
	def check_err_rates(self, qc_json):
		pass


	# merge the runs of a sample
	# @param runs the bam files to merge
	# @param output_dir the ouptut_dir in which to place the merged bam file
	# @param pref the prefix (either '', 'normal_', or 'tumor')
	# @param run_type either germline, normal, or tumor.
	# @param run_name either Merged, Normal_Merged or Tumor_Merged. Used for the titles of the 3x3 tables.
	def merge_runs(self, runs, output_dir, run_type, run_name, pref=''):
		# first check to see if all of the runs pass. 
		pending_runs, passing_runs = self.get_runs_status(runs)
		if len(pending_runs) != 0:
			print "Error: After QC_runs, runs should either be 'pass' or 'fail', not 'pending'. Pending runs: ", pending_runs
		# If any runs of the sample are not ready to be merged either because of 3x3 table error rate questions or other reasons, don't merge this sample.
		elif self.sample_json['sample_status'] != "pending_merge":
			print "%s the 'sample_status' is %s. Needs to be 'pending_merge' to merge the runs."%(self.sample_json['sample_name'], self.sample_json['sample_status'])
		else:
			if self.sample_json['analysis']['settings']['cleanup'] == True and 'merged_%sjson'%pref in self.sample_json: 
				# in order to manage space, delete the last merged folder that was created.
				shutil.remove_tree(self.sample_json['merged_%sjson'%pref])
			merger = Merger(passing_runs, output_dir, self.sample_json['sample_name'])
			# now set the json files
			# create the merged_bam's json file
			merged_json = {
					'bams_used_to_merge':merger.bams_to_merge, 
					'sample_name': merger.sample_name, 
					'merged_bam': merger.path_to_merged_bam,
					'json_file': merger.merged_json,
					"json_type": "merged",
					"run_folder": merger.output_dir, 
					"run_name": run_name,
					"run_type": run_type, 
					"pass_fail_status": "pending", 
					"project": self.sample_json['project'], 
					"proton": self.sample_json['proton'],
					"sample": self.sample_json['sample'], 
					"sample_folder": self.sample_json['sample_folder'],
					"sample_json": self.sample_json['sample_json']
				}
			#write new json file
			self.write_json(merger.merged_json, merged_json)
				
			# QC the merged run.
			self.runTVC_COV(merger.merged_json, pref)
			self.getRunInfo(merger.merged_json, pref)
			# store the path to this merged bam file in the sample's json file.
			if 'merged' not in self.sample_json['analysis']['files']:
				self.sample_json['analysis']['files']['merged'] = {}
			self.sample_json['analysis']['files']['merged']['%sbam'%pref] = merger.path_to_merged_bam
			# store the path to this merged bam folder in the sample's json file.
			self.sample_json['merged_%sjson'%pref] = output_dir
			#IDEA Add a path to the final filtered VCF file.


if __name__ == '__main__':

	# set up the option parser
	parser = OptionParser()
	
	# add the options to parse
	parser.add_option('-j', '--json', dest='json', help="A sample's json file which contains the necessary options and list of runs to QC with each other")
	# this step should be done automatically without an extra option.
	#parser.add_option('-m', '--merge', dest='merge', help="Merge the runs of a sample. Currently Automatic 'pass/fail' status is not updated, so this script must be run again after cutoffs are figured out.")
	parser.add_option('-p', '--pass_fail', dest='pass_fail', action='store_true', help="Overwrite the 'pass/fail' status of each run according to the cutoffs found in the json file. Normally this step is skipped if all runs have finished the QC process, but this option will overwrite the 'pass/fail' status found.")
	parser.add_option('-u', '--update_cutoffs', dest='update_cutoffs', help="Change the cutoffs found in the JSON file using an example json file with the corrected cutoffs. Will be done before anything else in the script.")

	(options, args) = parser.parse_args()

	# check to make sure the inputs are valid
	if not options.json:
		print "USAGE_ERROR: --json is required"
		parser.print_help()
		sys.exit(8)
	if not os.path.isfile(options.json):
		print "ERROR: the json file '%s' is not found"%options.json
		parser.print_help()
		sys.exit(4)
	if options.update_json and not os.path.isfile(options.update_json):
		print "ERROR: the update_cutoffs json file '%s' is not found"%options.update_json
		parser.print_help()
		sys.exit(4)

	qc_sample = QC_Sample(options)

	# if the update_json flag is specified, then update the cutoffs found in the normal json file.
	if options.update_json:
		qc_sample.update_cutoffs()

	# QC and merge all of the runs
	qc_sample.QC_merge_runs()

