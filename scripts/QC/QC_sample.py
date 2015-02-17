#! /usr/bin/env python2.7

import traceback
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

	# move the old 3x3 tables to the flag "old_GTs" 
	def recalc_3x3_tables(self):
		# load the output QC json. will be used to check if this combination has already been made.
		qc_json_data = {}
		if os.path.isfile(qc_json):
			qc_json_data = json.load(open(qc_json))
		# if the user specified to recalculate the 3x3 tables, do that here.
		if self.options.recalc_3x3_tables and 'QC_comparisons' in qc_json_data:
			# rearrange the old 3x3 tables to calculate the new 3x3 tables usingn the updated GT cutoffs
			qc_json_data['old_GTs'] = qc_json_data['QC_comparisons']
			del qc_json_data['QC_comparisons']
			self.write_json(qc_json, qc_json_data)
	

	# will find all of the runs in a sample and QC them with each other
	def QC_merge_runs(self):
		# if this is a germline sample, QC all of the normal runs with each other.
		if self.sample_json['sample_type'] == 'germline':
			# Use the sample_status here to not re-run the QC and to not overwrite run status. The 'sample_status' should be reset to 'pushed' when new runs are pushed..
			#if self.sample_json['sample_status'] != 'pending_merge' and self.sample_json['sample_status'] != 'pending_3x3_review' and self.sample_json['sample_status'] != 'merged':
			# if the user specified the '--pass_fail' option, then run this part still
			if self.sample_json['sample_status'] == 'pushed' or self.options.pass_fail or self.options.qc_all or self.options.recalc_3x3_tables:
				# QC the normal runs with each other
				self.QC_runs(self.sample_json['runs'])
	
			#TODO what if there is only one run that passes all of the metrics?
			# Check to see if the normal runs are ready to be merged.
			merge_dir, passing_bams, merge_count = self.check_merge(self.sample_json['runs'])
			if merge_dir != '':
				# merge the normal and/or tumor runs. Will only merge the passing runs with each other.
				pass_fail = self.merge_runs(passing_bams, merge_dir, 'germline', "Merged%d"%merge_count)
	
				# Set the sample_status
				self.sample_json['sample_status'] = 'merged'
	
				# cleanup the individual run bam files
				if pass_fail == "pass":
					self.cleanup_sample.delete_runs(self.sample_json['runs'], self.sample_json['analysis']['settings']['cleanup'], self.no_errors)

				# Cleanup the merged dir 
				#self.cleanup_sample.cleanup_runs(self.sample_json['runs'], self.sample_json['analysis']['settings']['cleanup'], self.no_errors)

		# if this is a tumor_normal sample, find the normal and tumor runs, and then QC them with each other.
		elif self.sample_json['sample_type'] == 'tumor_normal':
			# Separate the runs into tumor and normal lists
			normal_runs, tumor_runs = self.getTumor_Normal()
	
			if self.sample_json['analysis']['settings']['type'] == 'all_tumor_normal':
				# Use the sample_status here to not re-run the QC and to not overwrite run status. The 'sample_status' should be reset to 'pushed' when new runs are pushed..
				#if self.sample_json['sample_status'] != 'pending_merge' and self.sample_json['sample_status'] != 'pending_3x3_review' and self.sample_json['sample_status'] != 'merged':
				# if the user specified the '--pass_fail' option, then run this part still
				if self.sample_json['sample_status'] == 'pushed' or self.options.pass_fail or self.options.qc_all or self.options.recalc_3x3_tables:
					# QC the normal or tumor runs with each other
					self.QC_runs(normal_runs, 'normal_')
					self.QC_runs(tumor_runs, 'tumor_')
					# now QC the tumor and normal runs together.
					self.QC_normal_tumor_runs(normal_runs, tumor_runs)
					# make the excel spreadsheet containing the data and copy it back to the proton
					self._make_xlsx()
					# write the sample json file
					self.write_json(self.sample_json['json_file'], self.sample_json)
	
				# Check to see if the normal runs are ready to be merged.
				normal_merge_dir, normal_passing_bams, normal_merge_count = self.check_merge(normal_runs, 'Normal/', 'normal_')
				if normal_merge_dir != '':
					# merge the normal and/or tumor runs. Will only merge the passing runs with each other.
					self.merge_runs(normal_passing_bams, normal_merge_dir, 'normal', 'NMerged%d'%normal_merge_count, 'normal_')
	
				# Check to see if the tumor runs are ready to be merged.
				tumor_merge_dir, tumor_passing_bams, tumor_merge_count = self.check_merge(tumor_runs, 'Tumor/', 'tumor_')
				if tumor_merge_dir != '':
					self.merge_runs(tumor_passing_bams, tumor_merge_dir, 'tumor', 'TMerged%d'%tumor_merge_count, 'tumor_')
	
				# If any runs were merged, QC them. If there are only 1 normal and tumor run, they won't be QCd again. 
				if normal_merge_dir != '' or tumor_merge_dir != '' or (len(normal_passing_bams) == 1 and len(tumor_passing_bams) == 1):	
					# now QC the tumor and normal merged bams together if both normal and tumor runs are ready.
					if 'final_normal_json' in self.sample_json and 'final_tumor_json' in self.sample_json:
						qc_json = self.QC_2Runs(self.sample_json['final_normal_json'], self.sample_json['final_tumor_json'], 'normal_', 'tumor_', '_merged')
						merged_perc_avail_bases = self.update_3x3_runs_status(self.sample_json['final_normal_json'], self.sample_json['final_tumor_json'], qc_json)
						# update the merged run status 
						json_type = self.update_merged_run_status(self.sample_json['final_normal_json'], merged_perc_avail_bases)
						json_type = self.update_merged_run_status(self.sample_json['final_tumor_json'], merged_perc_avail_bases)

						# cleanup the individual bam files, but don't delete the final bam if it is in the original list of runs.
						runs = self.sample_json['runs']
						if self.sample_json['final_normal_json'] in runs:
							del runs[runs.index(self.sample_json['final_normal_json'])]
						if self.sample_json['final_tumor_json'] in runs:
							del runs[runs.index(self.sample_json['final_tumor_json'])]
						# cleanup the individual run bam files
						self.cleanup_sample.delete_runs(runs, self.sample_json['analysis']['settings']['cleanup'], self.no_errors)

						# Cleanup after the merging QC is done.
						self.cleanup_sample.cleanup_runs([self.sample_json['final_normal_json'], self.sample_json['final_tumor_json']], self.sample_json['analysis']['settings']['cleanup'], self.no_errors)

					# Set the sample_status
					self.sample_json['sample_status'] = 'merged'

		# Cleanup the PTRIM.bam and chr bam files after all of the QC is done.
		# are there any other files to clean up?
		self.cleanup_sample.cleanup_runs(self.sample_json['runs'], self.sample_json['analysis']['settings']['cleanup'], self.no_errors)
		# make the excel spreadsheet containing the data and copy it back to the proton
		self._make_xlsx()
				
		# print the final status
		if self.no_errors == False:
			print "%s finished with errors. See %s/sge.log for more details"%(self.sample_json['sample_name'], self.sample_json['output_folder'])
			self.sample_json['sample_status'] == 'failed'
			self.write_json(self.sample_json['json_file'], self.sample_json)
			sys.exit(1)
		else:
			print "%s finished with no errors!"%(self.sample_json['sample_name'])

		# write the sample json file
		self.write_json(self.sample_json['json_file'], self.sample_json)


	# Separate the runs into tumor and normal lists
	def getTumor_Normal(self):
		normal_runs = []  
		tumor_runs = []
		for run in self.sample_json['runs']:
			run_json = json.load(open(run))
			# temp fix for runs that have old JSON files (i.e. SEGA)
			if 'run_type' not in run_json or 'run_num' not in run_json:
				if re.search('N-', run):
					run_json['run_type'] = 'normal'
				else:
					run_json['run_type'] = 'tumor'
				run_json['pass_fail_status'] = 'pending'
				run_json['json_type'] = 'run'
				run_json['json_file'] = run
				run_json['run_name'] = run_json['name']
				run_json['run_num'] = run_json['run_name'][-1]
				run_json['sample_name'] = run_json['sample']
				if re.search('-', run_json['sample_folder']):
					run_json['run_folder'] = '/'.join(run.split('/')[:-1])
					run_json['sample_folder'] = os.path.abspath('/'.join(run.split('/')[:-1]) + "/../..")
				self.write_json(run, run_json)
				# temp fix over
			if run_json['run_type'] == 'normal':
				normal_runs.append(run)
			elif run_json['run_type'] == 'tumor':
				tumor_runs.append(run)
			else:
				print "ERROR run type is not normal or tumor."
		return normal_runs, tumor_runs


	# QC the normal runs with each other 
	def QC_runs(self, runs, pref=''):
		# first run TVC_CV and get the Run info to prepare for QC2Runs
		for run in runs:
			run_json = json.load(open(run))
			# only run these if this run has a status of pending.
			# This way the pass_fail_status can be manually overwritten.
			if run_json['pass_fail_status'] == "pending" or self.options.pass_fail:
				self.runTVC_COV(run, pref)
				self.getRunInfo(run, pref)
				# Update the run status based on the metrics gathered by QC_getRunInfo.sh
				self.update_run_status(run, len(runs))
		# if there is only one run for this sample, then set the status to 'pending_merge' so that the only run will be set as the 'final_json'
		passing_runs = self.get_runs_status(runs)[0]
		if len(passing_runs) == 1:
			self.sample_json['sample_stats'] == 'pending_merge'
		else:
			for run1 in runs:
				run1_json = json.load(open(run1))
				for run2 in runs:
					run2_json = json.load(open(run2))
					# check to see if these two runs should be QC'd together. Only QC the runs that pass the single run QC metrics.
					if int(run1_json['run_num']) < int(run2_json['run_num']) and ((run1_json['pass_fail_status'] == 'pass' and run2_json['pass_fail_status'] == 'pass') or self.options.qc_all): 
						qc_json = self.QC_2Runs(run1, run2, pref, pref)
						self.update_3x3_runs_status(run1, run2, qc_json)


	# now QC the tumor and normal runs together.
	def QC_normal_tumor_runs(self, normal_runs, tumor_runs):
		for normal_run in normal_runs:
			for tumor_run in tumor_runs:
				normal_json = json.load(open(normal_run))
				tumor_json = json.load(open(tumor_run))
				# Only QC the runs that pass the single run QC metrics.
				if (normal_json['pass_fail_status'] == 'pass' and tumor_json['pass_fail_status'] == 'pass') or self.options.qc_all: 
					qc_json = self.QC_2Runs(normal_run, tumor_run, 'normal_', 'tumor_')
					self.update_3x3_runs_status(normal_run, tumor_run, qc_json)


	# get the separate the runs of the sample by status
	def get_runs_status(self, runs):
		passing_runs = []
		pending_runs = []
		for run in runs:
			try:
				run_json = json.load(open(run))
				if run_json['pass_fail_status'] == 'pending':
					pending_runs.append(run)
				# only the runs that pass both of these cutoffs will be used to merge
				elif run_json['pass_fail_status'] == 'pass':
					if len(runs) > 1:
						if 'pass_fail_3x3_status' in run_json and (run_json['pass_fail_3x3_status'] == 'pending' or run_json['pass_fail_3x3_status'] == 'pass'):
							passing_runs.append(run)
					# if there is only 1 run, then it won't have a pass_fail_3x3_status. it passes.
					else:
						passing_runs.append(run)
			except ValueError:
				pass
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
		if 'run_data' in run_json and 'ts_tv' in run_json['run_data'] and 'beg_amp_cov' in run_json['run_data'] and 'num_het' in run_json['run_data'] \
				and 'amp_cov' in run_json['run_data'] \
				and ('pools_total' in run_json['run_data'] or self.sample_json['analysis']['settings']['pool_dropout'] != True):
			print "%s already has the needed metrics. Skipping getRunInfo.sh"%run
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
			if status != 0:
				sys.stderr.write("%s QC_getRunInfo.sh had an error!!\n"%run)
				self.no_errors = False
		# if the median read length was not gathered from the report PDF, or if this is a merged bam file, then calculate the median read length
		# TODO calculate the mean read length as well.
		new_run_json = json.load(open(run))
		if 'run_data' in new_run_json and ('median_read_length' not in new_run_json['run_data'] or str(new_run_json['run_data']['median_read_length']) == ""):
			#print "Gathering 'median_read_length'"
			# Align_Stats is imported from alignment_stats.py
			align_stats = Align_Stats()
			new_run_json['run_data']['median_read_length'] = align_stats.calcMedianFromBam("%s/%s"%(new_run_json['run_folder'], new_run_json['analysis']['files'][0]))
			# cleanup the ionstats_error_summary.h5 file here as well.
			if os.path.isfile('ionstats_error_summary.h5'):
				os.remove('ionstats_error_summary.h5')
		#else:
			#print "'median_read_length' already gathered: ", new_run_json['run_data']['median_read_length']
		if 'run_data' in new_run_json and 'cutoffs' in self.sample_json['analysis']['settings'] and 'exp_median_read_length' in self.sample_json['analysis']['settings']['cutoffs']:
			# Now set the perc_exp_median_read_length
			new_run_json['run_data']['perc_exp_median_read_length'] = float(new_run_json['run_data']['median_read_length']) / float(self.sample_json['analysis']['settings']['cutoffs']['exp_median_read_length'])
		#write new json file
		self.write_json(run, new_run_json)


	# QC two runs with each other
	# For Tumor / Normal pairs, Run1 should be the normal run, and Run2 should be the tumor run.
	# Output will be put into a dir like: sample1/QC/Run1vsRun2
	def QC_2Runs(self, run1, run2, pref1, pref2, merged=''):
		run1_json = json.load(open(run1))
		run2_json = json.load(open(run2))
	
		# set the paths
		if 'results_qc_json' in self.sample_json and 'qc_folder' in self.sample_json:
			qc_json = self.sample_json['results_qc_json']
			qc_folder = self.sample_json['qc_folder']
		else:
			qc_json = "%s/QC/results_qc.json"%self.sample_json['output_folder']
			self.sample_json['results_qc_json'] = qc_json
			self.sample_json['qc_folder'] = "%s/QC"%self.sample_json['output_folder']
			qc_folder = self.sample_json['qc_folder']
	
		# load the output QC json. will be used to check if this combination has already been made.
		qc_json_data = {}
		if os.path.isfile(qc_json):
			qc_json_data = json.load(open(qc_json))

		# run1 vs run2:
		run1vsrun2 = '%svs%s'%(run1_json['run_name'], run2_json['run_name'])

		if 'chromosomes_to_analyze'+merged not in self.sample_json['analysis']['settings']:
			if self.sample_json['project'] == 'PNET':
				self.sample_json['analysis']['settings']['chromosomes_to_analyze'+merged] = ['all']
			else:
				self.sample_json['analysis']['settings']['chromosomes_to_analyze'+merged] = self.sample_json['analysis']['settings']['chromosomes_to_analyze']
		
		# IDEA: If the 'all' comparison has already been made, then pull the chr combination out of it.
		# Only the runs that pass the single run QC metrics will be QC'd together.
		# QC these two runs for every chr type that is listed in chromosomes to analyze.
		for chromosome in self.sample_json['analysis']['settings']['chromosomes_to_analyze'+merged]:
			# now set the output_dir
			output_dir = "%s/%s%svs%s"%(qc_folder, chromosome, run1_json['run_name'], run2_json['run_name'])
			comp_type = run1_json['run_type'] + "_" + run2_json['run_type']
	
			# If this QC comparison has already been made, skip it.
			if 'QC_comparisons' in qc_json_data and chromosome in qc_json_data['QC_comparisons'] and \
					comp_type in qc_json_data['QC_comparisons'][chromosome] and run1vsrun2 in qc_json_data['QC_comparisons'][chromosome][comp_type]:
				print "%s has already run QC_2runs. Skipping."%output_dir
			#if 1 != 1:
			#	pass	
			else:
				# QC these two runs. QC_2Runs.sh takes the two run dirs and finds a .bam, .vcf, and .cov.xls file in the same dir as the .bam file
				qc2runs = "bash %s/QC_2Runs.sh "%self.__QCDirectory + \
				"--run_dirs %s %s "%(run1_json['run_folder'], run2_json['run_folder']) + \
				"--json_out %s "%qc_json + \
				"--output_dir %s "%output_dir + \
				"--project_bed %s "%self.sample_json['analysis']['settings']['project_bed'] + \
				"-a %s "%self.sample_json['analysis']['settings']['min_amplicon_coverage'] + \
				"-jp %s %s "%(self.sample_json['analysis']['settings']['%stvc_json'%pref1], self.sample_json['analysis']['settings']['%stvc_json'%pref2]) + \
				"-d %s %s "%(self.sample_json['analysis']['settings']['%smin_base_coverage'%pref1], self.sample_json['analysis']['settings']['%smin_base_coverage'%pref2]) + \
				"-gt %s %s %s %s "%(self.sample_json['analysis']['settings']['%swt_cutoff'%pref1], self.sample_json['analysis']['settings']['%shom_cutoff'%pref1], self.sample_json['analysis']['settings']['%swt_cutoff'%pref2], self.sample_json['analysis']['settings']['%shom_cutoff'%pref2])

				# subset this specified chromosome
				if chromosome != "all":
					qc2runs += "--subset_chr %s "%chromosome
	
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
				if status != 0:
					sys.stderr.write("%s vs %s QC_2Runs.sh had an error!!\n"%(run1, run2))
					self.no_errors = False
		return qc_json

	
	# @param run_json Update the pass/fail status of this run according to the cutoffs specified here.
	def update_run_status(self, run, num_runs):
		run_json = json.load(open(run))
		status = 'pass'
		# Update differently for runs vs merged bam files
		if 'json_type' not in run_json:
			print "ERROR: %s/%s unable to check the pass/fail cutoffs because the 'json_type' of 'run'/'merged' is not found in the json file"%(run_json['sample'], run_json['run_name'])
			return
		if 'cutoffs' not in self.sample_json['analysis']['settings']:
			print "Unable to update run status based on cutoffs because cutoffs are unavailable"
		elif run_json['json_type'] == 'run':
			# first check the % expected median read length. If this is an ffpe sample, then we don't fail the read length cutoff.
			if 'perc_exp_median_read_length' in self.sample_json['analysis']['settings']['cutoffs'] \
					and run_json['run_data']['perc_exp_median_read_length'] < self.sample_json['analysis']['settings']['cutoffs']['perc_exp_median_read_length'] \
					and not ('ffpe' in self.sample_json['analysis']['settings'] and self.sample_json['analysis']['settings']['ffpe'] == True):
				print "%s/%s fialed the 'perc_exp_median_read_length' flag. %.2f < %.2f"%(run_json['sample'], run_json['run_name'], run_json['run_data']['perc_exp_median_read_length'], self.sample_json['analysis']['settings']['cutoffs']['perc_exp_median_read_length'])
				status = 'fail'
			# check the coverage at the +10 and -10 positions
			if 'begin_end_amp_cov' in self.sample_json['analysis']['settings']['cutoffs'] \
					and run_json['run_data']['begin_amp_cov'] < self.sample_json['analysis']['settings']['cutoffs']['begin_end_amp_cov']:
				print "%s/%s fialed the 'begin_amp_cov' flag. %.2f < %.2f"%(run_json['sample'], run_json['run_name'], run_json['run_data']['begin_amp_cov'], self.sample_json['analysis']['settings']['cutoffs']['begin_end_amp_cov'])
				status = 'fail'
			if 'begin_end_amp_cov' in self.sample_json['analysis']['settings']['cutoffs'] \
					and run_json['run_data']['end_amp_cov'] < self.sample_json['analysis']['settings']['cutoffs']['begin_end_amp_cov']:
				print "%s/%s fialed the 'end_amp_cov' flag. %.2f < %.2f"%(run_json['sample'], run_json['run_name'], run_json['run_data']['end_amp_cov'], self.sample_json['analysis']['settings']['cutoffs']['begin_end_amp_cov'])
				status = 'fail'
			# checck the coverage
			if 'run_amp_cov' in self.sample_json['analysis']['settings']['cutoffs'] \
					and run_json['run_data']['amp_cov'] < self.sample_json['analysis']['settings']['cutoffs']['run_amp_cov']:
				print "%s/%s fialed the 'run_amp_cov' flag. %.2f < %.2f"%(run_json['sample'], run_json['run_name'], run_json['run_data']['amp_cov'], self.sample_json['analysis']['settings']['cutoffs']['run_amp_cov'])
				status = 'fail'
			# check the pool coverage
			if self.sample_json['analysis']['settings']['pool_dropout'] and 'pools_between_10_and_50' in run_json['run_data'] and 'pools_less_than_10' in run_json['run_data']:
				# currently the only options are 10, 50, and 75 so just stick with this.
				if run_json['run_data']['pools_between_10_and_50'] > 0 or run_json['run_data']['pools_less_than_10'] > 0:
					print "%s/%s has pools with < 50%% covergae"%(run_json['sample'], run_json['run_name'])
					status = 'fail'
		# Update the merged bam status differently 
		elif run_json['json_type'] == 'merged':
			if 'merged_amp_cov' in self.sample_json['analysis']['settings']['cutoffs'] and run_json['run_data']['amp_cov'] < self.sample_json['analysis']['settings']['cutoffs']['merged_amp_cov']:
				print "%s/%s fialed the 'merged_amp_cov' flag. %.2f < %.2f"%(run_json['sample'], run_json['run_name'], run_json['run_data']['amp_cov'], self.sample_json['analysis']['settings']['cutoffs']['merged_amp_cov'])
				status = 'fail'
		# set the pass fail status for this run
		run_json['pass_fail_status'] = status
		# write this run's updated status to the json file
		self.write_json(run, run_json)

	# Update run status based on the 3x3 table error rates.
	#- If any of the 3x3 table error rates fail, then the runs for this sample won't be merged until the 3x3 tables are manually reviewed to determine the faulty run, or if the sample needs to be resequenced.
	def update_3x3_runs_status(self, run1, run2, qc_json):
		perc_avail_bases = 0
		qc_data = json.load(open(qc_json))
		# set the default sample_status to be 'pending_merge' if it has not yet been set.
		# Otherwise it will be set to 'pending_3x3_review' if any of the 3x3 table comparisons failed the 'error_rate' cutoff
		if self.sample_json['sample_status'] != 'pending_3x3_review':
			self.sample_json['sample_status'] = 'pending_merge'
		# load the jsons
		run1_json = json.load(open(run1))
		run2_json = json.load(open(run2))
		# set the default status to pass for each run if it has not yet been set so as to not overwrite a run that is already set to 'fail' to 'pass' in the case of tumor/normal comparisons
		if 'pass_fail_3x3_status' not in run1_json or run1_json['pass_fail_3x3_status'] == 'pending':
			run1_json['pass_fail_3x3_status'] = "pass"
		if 'pass_fail_3x3_status' not in run2_json or run2_json['pass_fail_3x3_status'] == 'pending':
			run2_json['pass_fail_3x3_status'] = "pass"
		if 'cutoffs' in self.sample_json['analysis']['settings'] and 'error_rate' in self.sample_json['analysis']['settings']['cutoffs']:
			# run1vsrun2:
			comp_type = run1_json['run_type'] + "_" + run2_json['run_type']
			run1vsrun2 = run1_json['run_name'] + "vs" + run2_json['run_name']
			for chr in qc_data['QC_comparisons']:
				# Check to see if this comparison passes the 'error_rate' cutoff
				#if 'error_rate' not in self.sample_json['analysis']['settings']['cutoffs']:
					# Use this a default error_rate cutoff of 3.0e-05
					#self.sample_json['analysis']['settings']['cutoffs']['error_rate'] = 0.00003
				if comp_type in qc_data['QC_comparisons'][chr] and run1vsrun2 in qc_data['QC_comparisons'][chr][comp_type] \
						and qc_data['QC_comparisons'][chr][comp_type][run1vsrun2]['error_rate'] > self.sample_json['analysis']['settings']['cutoffs']['error_rate']:
					print "%s%svs%s Failed with an error rate too high of %.3e"%(chr, run1_json['run_name'], run2_json['run_name'], qc_data['QC_comparisons'][chr][comp_type][run1vsrun2]['error_rate'])
					run1_json['pass_fail_3x3_status'] = "fail"
					run2_json['pass_fail_3x3_status'] = "fail"
					self.sample_json['sample_status'] = 'pending_3x3_review'

				# add this variable for the final merged normal/tumor comparison
				if comp_type in qc_data['QC_comparisons'][chr] and run1vsrun2 in qc_data['QC_comparisons'][chr][comp_type]:
					perc_avail_bases = qc_data['QC_comparisons'][chr][comp_type][run1vsrun2]['perc_avail_bases']
		else:
			# if teh cutoffs are not available, then don't merge the runs yet.
			self.sample_json['sample_status'] = 'pending_3x3_review'
		# write the runs updated status to the json file
		self.write_json(run1, run1_json)
		self.write_json(run2, run2_json)

		#return the perc_avail_bases for the merged normal/tumor comparison
		return perc_avail_bases


	# Update the final merged run status
	# @returns the json_type so that we wil know if we can delete the individual runs or not
	def update_merged_run_status(self, run, merged_perc_avail_bases):
		json_type = ''
		pass_fail_merged_status = 'pass'
		# check to see if >90% of the bases are shared between the tumor normal comparison 
		if 'merged_amp_cov' in self.sample_json['analysis']['settings']['cutoffs'] and merged_perc_avail_bases != '':
			if merged_perc_avail_bases < self.sample_json['analysis']['settings']['cutoffs']['merged_amp_cov']:
				pass_fail_merged_status = 'fail'
			# write the final statuses here
			run_json = json.load(open(run))
			run_json['pass_fail_merged_status'] = pass_fail_merged_status
			self.write_json(run, run_json)
			json_type = run_json['json_type']
		return json_type


	# @param runs the runs of a sample 
	# @param run_name either '', 'Normal/' or 'Tumor/'
	# @param pref the prefix of this type of merge. either 'normal_' 'tumor_' or ''
	# @returns a list of the passing bam files to merge, and the path to the merged dir.
	def check_merge(self, runs, run_name='', pref=''):
		# vars to return
		merged_dir = ''	
		passing_bams = []
		# Use this count so that we won't have to write over past merges if there are multiple merges.
		if 'merged_%scount'%pref not in self.sample_json:
			self.sample_json['merged_%scount'%pref] = 0
	
		# first check to see if all of the runs pass. 
		# Get all of the passing bam files for this sample.
		pending_runs, passing_runs = self.get_runs_status(runs)
		if len(pending_runs) != 0:
			print "Not merging. After QC_runs, runs should either be 'pass' or 'fail', not 'pending'. Pending runs: ", pending_runs
		elif len(passing_runs) < 1:
			# if none of the runs are passing, then don't do anything.
			pass
		elif self.sample_json['sample_status'] != "pending_merge" and self.sample_json['sample_status'] != "merged":
			# If any runs of the sample are not ready to be merged either because of 3x3 table error rate questions or other reasons, don't merge this sample.
			print "%s the 'sample_status' is '%s'. Needs to be 'pending_merge' to merge the runs."%(self.sample_json['sample_name'], self.sample_json['sample_status'])
		elif self.sample_json['sample_status'] == 'pending_merge':
			# Merge these runs.
			# First get the passing bams from the passing runs.
			passing_bams = []
			for run in passing_runs:
				run_json = json.load(open(run))
				passing_bams.append("%s/%s"%(run_json['run_folder'], run_json['analysis']['files'][0]))
	
			# If this sample has already been merged:  If the runs to generate the merged bam don't match the current list: 
				# then delete the last created bam file and merge these runs
			# else don't remerge these files
			if len(passing_bams) == 1:
				# There is only one run, so don't merge it. Set the "final_%sjson"%pref flag to show what the final run is
				self.sample_json["final_%sjson"%pref] = run
			# use the 'merged_json' flag rather than the 'final_json' flag because 'final_json' can be set by a single non-merged run.
			elif 'merged_%sjson'%pref in self.sample_json and os.path.isfile(self.sample_json['merged_%sjson'%pref]):
				merged_json_data = json.load(open(self.sample_json['merged_%sjson'%pref]))
				# If the runs used to generate the current merged.bam file dont match the current passing_bams, then merge them. Otherwise don't
				if merged_json_data['json_type'] == 'merged' and set(passing_bams) != set(merged_json_data['bams_used_to_merge']):
					# in order to manage space, delete the last merged folder that was created.
					if self.sample_json['analysis']['settings']['cleanup'] == True: 
						# IDEA delete the entire folder? Or just the bam file?
						merged_bam = "%s/%s"%(merged_json_data['run_folder'], merged_json_data['analysis']['files'][0])
						print "	Deleting the old merged bam file: %s"%merged_bam
						os.remove(merged_bam)
					# Add one to the merged_count
					self.sample_json['merged_%scount'%pref] += 1
					# set new path to the merged_json
					merged_dir = "%s/%sMerged_%d"%(self.sample_json['sample_folder'], run_name, self.sample_json['merged_%scount'%pref])
				else:
					# Don't merge these runs because they've already been merged.
					print "%s the runs: '%s' have already been merged"%(self.sample_json['sample_name'], passing_bams)
			else:
				# Merge these runs
				merged_dir = "%s/%sMerged"%(self.sample_json['sample_folder'], run_name)
				# Add one to the merged_count
				self.sample_json['merged_%scount'%pref] += 1
	
		return merged_dir, passing_bams, self.sample_json['merged_%scount'%pref]


	# merge the runs of a sample
	# @param runs the bam files to merge
	# @param output_dir the ouptut_dir in which to place the merged bam file
	# @param pref the prefix (either '', 'normal_', or 'tumor')
	# @param run_type either germline, normal, or tumor.
	# @param run_name either Merged, Normal_Merged or Tumor_Merged. Used for the titles of the 3x3 tables.
	def merge_runs(self, passing_bams, output_dir, run_type, run_name='', pref=''):
		# if the file already exists, then merging must have finished, and don't merge again.
		merged_json_file = "%s/merged.json"%output_dir
		if os.path.isfile(merged_json_file):
			print "%s already exists so not merging the bam files again"%merged_json_file
		else:
			merger = Merger(passing_bams, output_dir, self.sample_json['sample_name'])
	
			# now set the json files
			# create the merged_bam's json file here so that the merger.py script can run on its own if necessary.
			merged_json = {
					'analysis': {
						'files': ['merged.bam'] 
						},
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
					"sample": self.sample_json['sample_name'], 
					"sample_folder": self.sample_json['sample_folder'],
					"sample_json": self.sample_json['json_file']
				}
			#write new json file
			self.write_json(merger.merged_json, merged_json)
			merged_json_file = 	merger.merged_json
				
		# QC the merged run.
		self.runTVC_COV(merged_json_file, pref)
		self.getRunInfo(merged_json_file, pref)
		
		# Update the merge pass/fail status based on the metrics gathered by QC_getRunInfo.sh
		self.update_run_status(merged_json_file, 1)

		# Also store the path to this merged bam file in the sample's json file. Not really necessary, but it seems like a good idea.
		#if 'merged' not in self.sample_json['analysis']['files']:
		#	self.sample_json['analysis']['files']['merged'] = {}
		#self.sample_json['analysis']['files']['merged']['%sbam'%pref] = merger.path_to_merged_bam	
		# store the path to this merged bam folder in the sample's json file.
		#self.sample_json['merged_%sjson'%pref] = output_dir

		# If the merge_json passes the cutoffs, set it as the final_json
		merge_json = json.load(open(merged_json_file))
		# add the path to this merge even if it doesn't pass
		self.sample_json["merged_%sjson"%pref] = merged_json_file
		if merge_json['pass_fail_status'] == 'pass':
			# Add a path to the final merged_json
			self.sample_json["final_%sjson"%pref] = merged_json_file
			return "pass"
		else:
			return "fail"

	# make the xlsx file to be copied back to the proton
	def _make_xlsx(self):
		xlsx_file = '%s/%s_QC.xlsx'%(self.sample_json['qc_folder'], self.sample_json['sample_name'])
		
		make_xlsx_command = "python2.7 %s/QC_generateSheets.py "%self.__QCDirectory + \
			"--sample_path %s "%self.sample_json['sample_folder'] + \
			"--sheet_per_sample " + \
			"--out %s "%xlsx_file + \
			"--ex_json %s "%(self.sample_json['json_file'])

		status  = self.runCommandLine(make_xlsx_command)
		if status != 0:
			print "unable to generate the excel file"
		else:
			print "Generated the QC spreadsheet successfully!"
			# TODO it would be really really cool if I could send them an email with the xlsx file!!
			# I tried this but the server was unable to send the file... $ mail -s "hello" "jlaw@childhooddiseases.org"
			# I will copy the .xlsx file to every run of the sample
			for run in self.sample_json['runs']:
				run_json = json.load(open(run))
				if 'ip_address' in run_json and 'orig_filepath_plugin_dir' in run_json:
					copy_command = "scp %s ionadmin@%s:%s "%(xlsx_file, run_json['ip_address'], run_json['orig_filepath_plugin_dir'])
					status = self.runCommandLine(copy_command)
					if status == 0:
						print "Copied the QC.xlsx file back to %s successfully!  %s"%(run_json['proton'], copy_command)
					else:
						print "Failed to copy the QC.xlsx file back to %s...  %s"%(run_json['proton'], copy_command)
					# try to copy the log file back as well.
					copy_command = "scp %s/sge.log ionadmin@%s:%s/QC.log "%(self.sample_json['sample_folder'], run_json['ip_address'], run_json['orig_filepath_plugin_dir'])
					status = self.runCommandLine(copy_command)
					# try to add the log file to the plugin's log file.
					# this didn't work... 
					#copy_command = "ssh ionadmin@%s:%s/QC.log 'cat %s/QC.log >> %s/drmaa_stdout.txt"%(run_json['ip_address'], run_json['orig_filepath_plugin_dir'], run_json['orig_filepath_plugin_dir'], run_json['orig_filepath_plugin_dir'])
					#status = self.runCommandLine(copy_command)


if __name__ == '__main__':

	# set up the option parser
	parser = OptionParser()
	
	# add the options to parse
	parser.add_option('-j', '--json', dest='json', help="A sample's json file which contains the necessary options and list of runs to QC with each other")
	#parser.add_option('-m', '--merge', dest='merge', help="Merge the runs of a sample. Currently Automatic 'pass/fail' status is not updated, so this script must be run again after cutoffs are figured out.")
	parser.add_option('-q', '--qc_all', dest='qc_all', action='store_true', help="Generate the 3x3 tables for all run comparisons, even if they fail.")
	parser.add_option('-p', '--pass_fail', dest='pass_fail', action='store_true', help="Overwrite the 'pass/fail' status of each run according to the cutoffs found in the json file. Normally this step is skipped if all runs have finished the QC process, but this option will overwrite the 'pass/fail' status found.")
	parser.add_option('-r', '--recalc_3x3_tables', dest='recalc_3x3_tables', action='store_true', help="recalculate the 3x3 tables (original use was for the new GT cutoffs")
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
	if options.update_cutoffs and not os.path.isfile(options.update_cutoffs):
		print "ERROR: the update_cutoffs json file '%s' is not found"%options.update_cutoffs
		parser.print_help()
		sys.exit(4)

	try:
		qc_sample = QC_Sample(options)

		# if the update_json flag is specified, then update the cutoffs found in the normal json file.
		if options.update_cutoffs:
			qc_sample.update_cutoffs()

		# if the recalc_3x3_tables flag is specified, then rearrange the results_QC.json file so that the 3x3 tables will be recalculated.
		if options.recalc_3x3_tables:
			qc_sample.recalc_3x3_tables()

		# QC and merge all of the runs
		qc_sample.QC_merge_runs()

	except ValueError as e:
		#print sys.exc_traceback
		print traceback.format_exc().strip()
		print "Error: the JSON file is probably malformed"

