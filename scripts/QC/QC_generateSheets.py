#! /usr/bin/env python2.7

# Goal: Create pretty 3x3 tables comparing mulitple runs, or Tumor/Normal pairs 

import sys
import os
import re
import subprocess
import json
import QC_stats
from optparse import OptionParser
try:
	import xlsxwriter
	from xlsxwriter.utility import xl_rowcol_to_cell
except ImportError:
	print "xlsxwriter is installed on python2.7 on triton. Use python2.7", sys.argv[0]
	sys.exit(1)


class XLSX_Writer():
	def __init__(self, workbook):
		#Dictionary containing all of the different self.formats
		# initialize self.formats with a blank string in case there are times where there is no format
		# this dictionary will hold all of the self.formats to be used by QC_genSheets
		self.formats = {'': ''}
		self.workbook = self.workbook
		self.__setupWorkbook()

	# @param out_file_name the name of the outuput xlsx
	##### @returns a format of dictionary
	def __setupWorkbook(self):
		# The color for each alternating sample
		alt_sample_color = "#d5e8f8" # This color is considered azure by the color wheel. Go to this website to choose a new color
		
		# Adding self.formats for red cells, and the borders for the table.
		self.formats['header_format'] = self.workbook.add_format()
		self.formats['header_format'].set_bold()
		self.formats['header_format'].set_font_size(12)
		self.formats['header_format'].set_align('center')
		self.formats['header_format'].set_text_wrap()
		self.formats['header_format2'] = self.workbook.add_format()
		self.formats['header_format2'].set_bold()
		self.formats['header_format2'].set_font_size(14)
		
		
		self.formats['center'] = self.workbook.add_format()
		self.formats['center'].set_align('center')
		
		self.formats['_azure'] = self.workbook.add_format()
		self.formats['_azure'].set_bg_color(alt_sample_color)
		self.formats['_azure'].set_align('center')
		
		self.formats['red'] = self.workbook.add_format()
		self.formats['red'].set_bg_color('#FF0000')
		self.formats['red'].set_align('center')
		
		self.formats['num_format'] = self.workbook.add_format({'num_format': '#,##0'})
		self.formats['num_format'].set_align('center')
		self.formats['perc_format'] = self.workbook.add_format({'num_format': '0.00%'})
		self.formats['perc_format'].set_align('center')
		self.formats['dec3_format'] = self.workbook.add_format({'num_format': '0.000'})
		self.formats['dec3_format'].set_align('center')
		self.formats['num_format_azure'] = self.workbook.add_format({'num_format': '#,##0'})
		self.formats['num_format_azure'].set_align('center')
		self.formats['num_format_azure'].set_bg_color(alt_sample_color)
		self.formats['perc_format_azure'] = self.workbook.add_format({'num_format': '0.00%'})
		self.formats['perc_format_azure'].set_align('center')
		self.formats['perc_format_azure'].set_bg_color(alt_sample_color)
		self.formats['dec3_format_red'] = self.workbook.add_format({'num_format': '0.000'})
		self.formats['dec3_format_red'].set_align('center')
		self.formats['dec3_format_red'].set_bg_color('#FF0000')
		self.formats['dec3_format_azure'] = self.workbook.add_format({'num_format': '0.000'})
		self.formats['dec3_format_azure'].set_align('center')
		self.formats['dec3_format_azure'].set_bg_color(alt_sample_color)
		
		self.formats['top'] = self.workbook.add_format()
		self.formats['top'].set_top(2)
		self.formats['right'] = self.workbook.add_format()
		self.formats['right'].set_right(2)
		self.formats['bottom'] = self.workbook.add_format()
		self.formats['bottom'].set_bottom(2)
		self.formats['left'] = self.workbook.add_format()
		self.formats['left'].set_left(2)
		
	#	return self.formats
		
	# Function to check if a value is greater than the maximum value (i.e. WT to HET is greater than 10 or something), then write it in red
	def __check_max_and_write(self, row, col, value, Max):
		if int(value) > int(Max):
			# write this cell in red
			self.MRsheet.write(row, col, value, self.formats['red'])
		else:
			self.MRsheet.write(row, col, value)
			# write this cell in normal white


	# Complex function to write cells. 
	# @param write_format is the format to write the cell in. 
	# @param Max will be the maximum threshold for writing in red, unless it's 0. If max if negative, it will be treated as a minimum threshold
	# MAx is not yet implemented.
	# @return returns 1 so there will be one less line of code (to incrament col). Maybe it could just incrament col, I would just rather not have global variables
	def __check_to_write(self, row, col, key, write_format, metrics):
		if key in metrics:
			try:
				if re.search("=", write_format):
					if metrics[key] != "":
						cell1 = xl_rowcol_to_cell(row, col-2)
						cell2 = xl_rowcol_to_cell(row, col-1)
						self.QCsheet.write_formula(row, col, "=(%s-%s)/%s"%(cell1, cell2, cell1), self.formats[write_format[1:]])
				elif re.search("num_format", write_format):
					if not isinstance(metrics[key], int) and not isinstance(metrics[key], float):
						self.QCsheet.write_number(row, col, int(metrics[key].replace(',','')), self.formats[write_format])
					else:
						self.QCsheet.write_number(row, col, metrics[key], self.formats[write_format])
				elif re.search("perc_format", write_format):
					if float(metrics[key]) > 1:
						metrics[key] = metrics[key] / 100
					self.QCsheet.write_number(row, col, float(metrics[key]), self.formats[write_format])
				elif re.search("dec3_format", write_format):
					self.QCsheet.write_number(row, col, float(metrics[key]), self.formats[write_format])
				# special case to write the formula for the +-10 bp col
				else:
					# if write_format is blank, then self.formats will also be blank
					self.QCsheet.write(row, col, metrics[key], self.formats[write_format])
			except ValueError:
				self.QCsheet.write(row, col, metrics[key], self.formats[write_format])
		return 1


	# @param run_metrics the dictionary containing all of the run_metrics
	def writeRunMetrics(self, run_metrics):
		# Infosheet is where all of the metrics about each run will be written
		self.QCsheet = self.workbook.add_worksheet("QC Metrics")
		self.QCsheet.freeze_panes(1,2)
		
		# First write the QC metrics for each run of each sample.
		# Write the header
		col = 0
		self.QCsheet.write(0,col, "Sample #", self.formats['header_format'])
		self.QCsheet.set_column(col,col,None, self.formats['center'])
		col += 1
	#	self.QCsheet.write(0,col, "Plate, row and column", self.formats['header_format'])
	#	self.QCsheet.set_column(col,col,10, self.formats['center'])
	#	col += 1
		self.QCsheet.write(0,col, "Library prep date", self.formats['header_format'])
		self.QCsheet.set_column(col,col,10, self.formats['center'])
		col += 1
		#self.QCsheet.write(0,col, "Barcode used", self.formats['header_format'])
		#self.QCsheet.set_column(col,col,12, self.formats['center'])
		#col += 1
		self.QCsheet.write(0,col, "Library concentration (ng/ul)", self.formats['header_format'])
		self.QCsheet.set_column(col,col,None, self.formats['center'])
		col += 1
		self.QCsheet.write(0,col, "Run #", self.formats['header_format'])
		self.QCsheet.set_column(col,col,5, self.formats['center'])
		col += 1
		self.QCsheet.write(0,col, "Rot ID", self.formats['header_format'])
		self.QCsheet.set_column(col,col,None, self.formats['center'])
		col += 1
		self.QCsheet.write(0,col, "Run Date", self.formats['header_format'])
		self.QCsheet.set_column(col,col,12, self.formats['center'])
		col += 1
		self.QCsheet.write(0,col, "Total M Basepairs", self.formats['header_format'])
		self.QCsheet.set_column(col,col,12, self.formats['center'])
		col += 1
		self.QCsheet.write(0,col, "% Polyclonal", self.formats['header_format'])
		self.QCsheet.set_column(col,col,12, self.formats['center'])
		col += 1
		self.QCsheet.write(0,col, "Mean Read Length", self.formats['header_format'])
		self.QCsheet.set_column(col,col,None, self.formats['center'])
		col += 1
		self.QCsheet.write(0,col, "Median Read Length", self.formats['header_format'])
		self.QCsheet.set_column(col,col,None, self.formats['center'])
		col += 1
		self.QCsheet.write(0,col, "% expected read length (out of XXX bp)", self.formats['header_format'])
		self.QCsheet.set_column(col,col,12, self.formats['center'])
		col += 1
		self.QCsheet.write(0,col, "% amplicons > 30x covered at bp +10", self.formats['header_format'])
		self.QCsheet.set_column(col,col,13, self.formats['center'])
		col += 1
		self.QCsheet.write(0,col, "% amplicons > 30x covered at bp -10", self.formats['header_format'])
		self.QCsheet.set_column(col,col,13, self.formats['center'])
		col += 1
		self.QCsheet.write(0,col, "(%covered at bp(10) - bp(n-10))/bp(10)", self.formats['header_format'])
		self.QCsheet.set_column(col,col,13, self.formats['center'])
		col += 1
	#	self.QCsheet.write(0,col, "total number of bases covered at 30x (the # of bases covered in the 'covered_bases region' region.)", self.formats['header_format'])
	#	self.QCsheet.set_column(col,col,18, self.formats['center'])
	#	col += 1
	#	self.QCsheet.write(0,col, "% covered bases (n/83046)", self.formats['header_format'])
	#	self.QCsheet.set_column(col,col,13, self.formats['center'])
	#	col += 1
	#	self.QCsheet.write(0,col, "% targeted bases (n/84447)", self.formats['header_format'])
	#	self.QCsheet.set_column(col,col,13, self.formats['center'])
	#	col += 1
		self.QCsheet.write(0,col, "Ts/Tv", self.formats['header_format'])
		self.QCsheet.set_column(col,col,13, self.formats['center'])
		col += 1
		self.QCsheet.write(0,col, "# Total variants (single allele)", self.formats['header_format'])
		self.QCsheet.set_column(col,col,13, self.formats['center'])
		col += 1
		self.QCsheet.write(0,col, "# HET variants (single allele rates)", self.formats['header_format'])
		self.QCsheet.set_column(col,col,13, self.formats['center'])
		col += 1
		self.QCsheet.write(0,col, "# HOM variants (single allele rates)", self.formats['header_format'])
		self.QCsheet.set_column(col,col,13, self.formats['center'])
		col += 1
		self.QCsheet.write(0,col, "HET/HOM ratio (single allele rates)", self.formats['header_format'])
		self.QCsheet.set_column(col,col,13, self.formats['center'])
		col += 1
		self.QCsheet.write(0,col, "3x3 N-N pair (whole amplicon)", self.formats['header_format'])
		self.QCsheet.set_column(col,col,13, self.formats['center'])
		col += 1
		self.QCsheet.write(0,col, "Total bases evaluated (>=30x in both runs) (whole amplicon)", self.formats['header_format'])
		self.QCsheet.set_column(col,col,13, self.formats['center'])
		col += 1
		self.QCsheet.write(0,col, "% Available Bases (whole amplicon)", self.formats['header_format'])
		self.QCsheet.set_column(col,col,13, self.formats['center'])
		col += 1
		self.QCsheet.write(0,col, "3x3 qc observed error counts  (whole amplicon)", self.formats['header_format'])
		self.QCsheet.set_column(col,col,13, self.formats['center'])
		col += 1
		self.QCsheet.write(0,col, "3x3 qc error rate  (whole amplicon)", self.formats['header_format'])
		self.QCsheet.set_column(col,col,13, self.formats['center'])
		col += 1
		self.QCsheet.write(0,col, "Z-Score error rate (whole amplicon)", self.formats['header_format'])
		self.QCsheet.set_column(col,col,13, self.formats['center'])
		col += 1
	#	self.QCsheet.write(0,col, "Total bases evaluated (>=30x in both runs) (cds only)", self.formats['header_format'])
	#	self.QCsheet.set_column(col,col,13, self.formats['center'])
	#	col += 1
	#	self.QCsheet.write(0,col, "% Available Bases (cds only)", self.formats['header_format'])
	#	self.QCsheet.set_column(col,col,13, self.formats['center'])
	#	col += 1
	#	self.QCsheet.write(0,col, "3x3 qc observed error counts  (cds only)", self.formats['header_format'])
	#	self.QCsheet.set_column(col,col,13, self.formats['center'])
	#	col += 1
	#	self.QCsheet.write(0,col, "3x3 qc error rate  (cds only)", self.formats['header_format'])
	#	self.QCsheet.set_column(col,col,13, self.formats['center'])
	#	col += 1
	#	self.QCsheet.write(0,col, "Z-Score error rate (cds only)", self.formats['header_format'])
	#	self.QCsheet.set_column(col,col,13, self.formats['center'])
	#	col += 1
		self.QCsheet.write(0,col, "run status (does it pass qc?)", self.formats['header_format'])
		self.QCsheet.set_column(col,col,None, self.formats['center'])
		col += 1
		self.QCsheet.set_column(col,col+20,12, self.formats['center'])
		
		self.QCsheet.set_row(0,100, self.formats['header_format'])
		
		row = 1
		azure = '_azure'
		
		for sample in sorted(run_metrics):
			# for each sample, change the color
			if len(run_metrics[sample]['runs']) > 0:
				if azure == "":
					azure = "_azure"
				else:
					azure = ""
			for run, metrics in sorted(run_metrics[sample]['runs'].iteritems()):
				col = 0
				#col += self.__check_to_write(row, col, 'sample_num', "" + azure, metrics)
				col += self.__check_to_write(row, col, 'sample', "" + azure, metrics)
				col += self.__check_to_write(row, col, 'lib_prep_date', "" + azure, metrics)
				#col += self.__check_to_write(row, col, 'barcode', "" + azure, metrics)
				col += self.__check_to_write(row, col, 'lib_conc', "" + azure, metrics)
				col += self.__check_to_write(row, col, 'run_num', "" + azure, metrics)
				col += self.__check_to_write(row, col, 'rotID', "" + azure, metrics)
				col += self.__check_to_write(row, col, 'run_date', "" + azure, metrics)
				col += self.__check_to_write(row, col, 'total_bases', "num_format" + azure, metrics)
				# Old naming sheme:
				#col += self.__check_to_write(row, col, 'polyclonal', "perc_format" + azure, metrics)
				#col += self.__check_to_write(row, col, 'mean', "num_format" + azure, metrics)
				#col += self.__check_to_write(row, col, 'median', "num_format" + azure, metrics)
				col += self.__check_to_write(row, col, 'polyclonality', "perc_format" + azure, metrics)
				col += self.__check_to_write(row, col, 'mean_read_length', "num_format" + azure, metrics)
				col += self.__check_to_write(row, col, 'median_read_length', "num_format" + azure, metrics)
				col += self.__check_to_write(row, col, 'expected_length', "" + azure, metrics)
				col += self.__check_to_write(row, col, 'begin_amp_cov', 'perc_format' + azure, metrics)
				col += self.__check_to_write(row, col, 'end_amp_cov', 'perc_format' + azure, metrics)
				# give it the dummy 'end_amp_cov' key to write the function of +-10 bp difference. the = is for a function
				col += self.__check_to_write(row, col, 'end_amp_cov', "=dec3_format" + azure, metrics)
	#			col += self.__check_to_write(row, col, 'total_covered', 'num_format' + azure, metrics)
	#			col += self.__check_to_write(row, col, 'perc_expected', 'perc_format' + azure, metrics)
	#			col += self.__check_to_write(row, col, 'perc_targeted', 'perc_format' + azure, metrics)
				# Old naming scheme:
				#col += self.__check_to_write(row, col, 'tstv', 'num_format' + azure, metrics)
				col += self.__check_to_write(row, col, 'ts_tv', 'num_format' + azure, metrics)
				col += self.__check_to_write(row, col, 'total_vars', 'num_format' + azure, metrics)
				col += self.__check_to_write(row, col, 'num_het', 'num_format' + azure, metrics)
				col += self.__check_to_write(row, col, 'num_hom', 'num_format' + azure, metrics)
				col += self.__check_to_write(row, col, 'het_hom', 'dec3_format' + azure, metrics)
				#run_num = int(metrics['run_num'])
				#runs = int(metrics['runs'])
		
				# This was never finished. The idea was to choose a representative 3x3 table and show its summary here, but it never really worked out.
#				# Now write the N-N pair and the T-T pairs
#				col += self.__check_to_write(row, col, 'same_pair', "" + azure, metrics)
#				col += self.__check_to_write(row, col, 'same_total_eligible_bases', 'num_format' + azure, metrics)
#				col += self.__check_to_write(row, col, 'same_perc_available_bases', 'perc_format' + azure, metrics)
#				col += self.__check_to_write(row, col, 'same_error_count', 'num_format' + azure, metrics)
#				col += self.__check_to_write(row, col, 'same_error_rate', 'perc_format' + azure, metrics)
#				try:
#					if 'same_zscore' in metrics and float(metrics['same_zscore']) > 3:
#						self.QCsheet.write_number(row, col, float(metrics['same_zscore']), dec3_format_red)
#						metrics['same_status'] = 'Fail'
#						col += 1
#					else:
#						col += self.__check_to_write(row, col, 'same_zscore', 'dec3_format' + azure, metrics)
#				except ValueError:
#					col += self.__check_to_write(row, col, 'tn_zscore', '' + azure, metrics)
#				col += self.__check_to_write(row, col, 'same_status', "" + azure, metrics)
#		
#			# Now write the T-N pairs
#				col += self.__check_to_write(row, col, 'tn_pair', "" + azure, metrics)
#				col += self.__check_to_write(row, col, 'tn_total_evaluated', 'num_format' + azure, metrics)
#				col += self.__check_to_write(row, col, 'tn_perc_available_bases', 'perc_format' + azure, metrics)
#				col += self.__check_to_write(row, col, 'tn_error_count', 'num_format' + azure, metrics)
#				col += self.__check_to_write(row, col, 'tn_error_rate', 'perc_format' + azure, metrics)
#				try:
#					if 'tn_zscore' in metrics and float(metrics['tn_zscore']) > 3:
#						self.QCsheet.write_number(row, col, float(metrics['tn_zscore']), dec3_format_red)
#						metrics['tn_status'] = 'Fail'
#						col += 1
#					else:
#						col += self.__check_to_write(row, col, 'tn_zscore', 'dec3_format' + azure, metrics)
#				except ValueError:
#					col += self.__check_to_write(row, col, 'tn_zscore', '' + azure, metrics)
#				col += self.__check_to_write(row, col, 'tn_status', "" + azure, metrics)
			
				# Set the color of this row according to the current color
				self.QCsheet.set_row(row, None, self.formats[azure])
	
				row += 1

	# Write the multiple run Info 3x3 tables if specified
	# @param QC_comparisons the dictionary from all of the _QC.json files
	def write3x3Tables(self, QC_comparisons):
		sheet = ''
		if not self.sheet_per_sample:
			# self.MRsheet is the sheet where all of the 3x3 tables for each of the multiple runs of each sample will be written
			sheet = self.workbook.add_worksheet("3x3 tables")
	
		# QC_comparisons was made by QC_stats.py and has all of the needed 3x3 table stats.
		for sample in sorted(QC_comparisons):
			print "Writing 3x3 tables for sample: " + sample
			# if specified, add a new sheet per sample
			if self.sheet_per_sample:
				# self.MRsheet is the sheet where all of the 3x3 tables for each of the multiple runs of each sample will be written
				sheet = self.workbook.add_worksheet(sample)
	
			row = 2
			col = 1
			#first make the header for sample.
			sheet.write(row-1, col, sample, self.formats['header_format2'])
	
			# iterate through the different data sizes (i.e. all, chr1, 718, etc.)
			for data_type in sorted(QC_comparisons):
				# comp_type is is either normal_normal, tumor_normal, or tumor_tumor and contains the specified types of comparisons
				# row will be updated as the 3x3 tables are written so that row will always be in teh correct place.
				if "normal_normal" in QC_comparisons[sample][data_type]:
					sheet.write(row, col, "%s: Normal vs Normal"%data_type, self.formats['header_format2'])
					row = self.__write_comparisons(sheet, data_type, QC_comparisons[sample][data_type]['normal_normal'], row+1, col)
				if "tumor_tumor" in QC_comparisons[sample][data_type]:
					sheet.write(row, col, "%s: Tumor vs Tumor"%data_type, self.formats['header_format2'])
					row = self.__write_comparisons(sheet, data_type, QC_comparisons[sample][data_type]['tumor_tumor'], row+1, col)
				if "tumor_normal" in QC_comparisons[sample][data_type]:
					sheet.write(row, col, "%s: Normal vs Tumor"%data_type, self.formats['header_format2'])
					row = self.__write_comparisons(sheet, data_type, QC_comparisons[sample][data_type]['tumor_normal'], row+1, col)

					
	# write the comparisons of a sample. 
	# Will also handle the row, col increases and such
	def __write_comparisons(sheet, data_type, qc_comparisons, start_row, start_col)
		# loop through the different comparisons of the given data_type and comparison type.
		for runs_compared, table_values in sorted(qc_comparisons.iteritems()):
			run1_num = int(runs_compared.split('vs')[0][-1])
			run2_num = int(runs_compared.split('vs')[1][-1])
			# if the run types match, then traingulate by each row being a new run2_num, and each col being a new run1_num
			if table_values['run1_type'] == table_value['run2_type']:
				row = start_row + (run2_num-2)*11
				col = start_col + (run1_num-1)*6
			# if the run types don't match (i.e. tumor normal), then traingulate by each row being a new normal run(run1_num), and each col being a new tumor run (run2_num)
			else:
				row = start_row + (run1_num-2)*11
				col = start_col + (run2_num-1)*6
			# now write the 3x3 tables on the given sheet for the given data_type and comparison type
			self.__write3x3Table(sheet, data_type, runs_compared, table_values, row, col)
	
		return row

	# function to write a 3x3 table to the given sheet
	def __write3x3Table(self, sheet, data_type, runs_compared, table_values, row, col):
		#first make the header for each table.
		header = "%s: %s    -  vs  -    %s"%(data_type, runs_compared.split('vs')[0], runs_compared.split('vs')[1]) # i.e. sample1  Run1  -  vs  - Run2
		sheet.write(row-1, col, header, self.formats['header_format2'])
	
		# Write the err rate, % available bases and the # of GTs reassigned to the spreadsheet
		header_error_rate = "%s:  %.3e"% ("error rate", float(table_values["error_rate"]))
		row =+ 1;
		sheet.write(row-1, col, header_error_rate)
		row =+ 1
		header_perc_bases = "%s:  %.2f"% ("% available bases", float(table_values["perc_avail_bases"])*100)
		sheet.write(row-1, col, header_perc_bases)
		row =+ 1
		if 'reassigned_GTs' in table_values:
			reassigned_GTs = "%s:  %d"% ("# of GTs reassigned", table_values["reassigned_GTs"])
			sheet.write(row-1, col, reassigned_GTs)
		
		#now write the table headers
		sheet.write(row+1, col, "WT", self.formats['right'])
		sheet.write(row+2, col, "HET", self.formats['right'])
		sheet.write(row+3, col, "HOM", self.formats['right'])
		sheet.write(row+4, col, "Sum:")
		sheet.write(row, col+1, "WT", self.formats['bottom'])
		sheet.write(row, col+2, "HET", self.formats['bottom'])
		sheet.write(row, col+3, "HOM", self.formats['bottom'])
		sheet.write(row, col+4, "Sum:")
		# write the diagonal cell values:
		sheet.write(row+1, col+1, table_values["WT_WT"])
		sheet.write(row+2, col+2, table_values["HET_HET"])
		sheet.write(row+3, col+3, table_values["HOM_HOM"])
		# now write the off-diagonals
		sheet.write(row+2, col+1, table_values["HET_WT"])
		sheet.write(row+3, col+1, table_values["HOM_WT"])
		sheet.write(row+1, col+2, table_values["WT_HET"])
		sheet.write(row+3, col+2, table_values["HOM_HET"])
		sheet.write(row+1, col+3, table_values["WT_HOM"])
		sheet.write(row+2, col+3, table_values["HET_HOM"])
		# Add the totals for each row and column
		total = int(table_values["WT_WT"]) + int(table_values["WT_HET"]) + int(table_values["WT_HOM"]) + \
				int(table_values["HET_WT"]) + int(table_values["HET_HET"]) + int(table_values["HET_HOM"]) + \
				int(table_values["HOM_WT"]) + int(table_values["HOM_HET"]) + int(table_values["HOM_HOM"])
		# Write the totals for each row and column
		sheet.write(row+4, col+1, str(int(table_values["WT_WT"])+int(table_values["HET_WT"])+int(table_values["HOM_WT"])), self.formats['top'])
		sheet.write(row+4, col+2, str(int(table_values["WT_HET"])+int(table_values["HET_HET"])+int(table_values["HOM_HET"])), self.formats['top'])
		sheet.write(row+4, col+3, str(int(table_values["WT_HOM"])+int(table_values["HET_HOM"])+int(table_values["HOM_HOM"])), self.formats['top'])
		sheet.write(row+1, col+4, str(int(table_values["WT_WT"])+int(table_values["WT_HET"])+int(table_values["WT_HOM"])), self.formats['left'])
		sheet.write(row+2, col+4, str(int(table_values["HET_WT"])+int(table_values["HET_HET"])+int(table_values["HET_HOM"])), self.formats['left'])
		sheet.write(row+3, col+4, str(int(table_values["HOM_WT"])+int(table_values["HOM_HET"])+int(table_values["HOM_HOM"])), self.formats['left'])
		sheet.write(row+4, col+4, str(total))
	

# start here
if (__name__ == "__main__"):
	# parse the arguments
	parser = OptionParser()
	
	# All of the arguments are specified here.
	parser.add_option('-p', '--project_path', dest='project_path', action='append', help='REQUIRED: /path/to/the/project_dir. Can provide muliple paths')
	parser.add_option('-r', '--run_info_only', dest='run_info_only', action="store_true", default=False, help="Get only the individual run's info. Default is to get both run info and the 3x3 table qc_comparisons")
	parser.add_option('-q', '--qc_info_only', dest='qc_info_only', action="store_true", default=False, help="Get only the 3x3 table QC comparison info. Default is to get both run info and the 3x3 table qc_comparisons")
	parser.add_option('-S', '--sheet_per_sample', dest='sheet_per_sample', action="store_true", default=False, help="Will write a new sheet containing the 3x3 table comparisons per sample.")
	parser.add_option('-o', '--out', dest='out', default='QC.xlsx', help='Specify the output xlsx file [default: %default]')
	
	# Gets all of the command line arguments specified and puts them into the dictionary args
	(options, args) = parser.parse_args()
	
	if not options.project_path:
		print "USAGE_ERR: --project_path is required! Use -h for help"
		parser.print_help()
		sys.exit(8)
	
	# Ensure the user specifies a .xlsx ending if the -o/--output option is used
	if options.out[-5:] != ".xlsx":
		parser.error("-o (--out) output file must end in .xlsx")
	
	# setup the xlsx workbook
	workbook = xlsxwriter.Workbook(options.out)
	# add the self.formats and such to the workbook
	xlsx_writer = XLSX_Writer(workbook)
	if options.sheet_per_sample:
		xlsx_writer.sheet_per_sample = True
	else:
		xlsx_writer.sheet_per_sample = False

	# Get the data available by finding the json files in the project_path specified.
	elif options.run_info_only:
		json_data = QC_stats.main_runs_only(options.project_path)
		xlsx_writer.writeRunMetrics(json_data)
	elif options.qc_info_only:
		QC_json_data = QC_stats.main_QC_only(options.project_path)
		xlsx_writer.write3x3Tables(QC_json_data)
	else:
		print "Generating Spreadsheets for both run_info and the 3x3 QC tables"
		json_data = QC_stats.main_runs_only(options.project_path)
		xlsx_writer.writeRunMetrics(json_data)
		QC_json_data = QC_stats.main_QC_only(options.project_path)
		xlsx_writer.write3x3Tables(QC_json_data)
	
	print "Finished generating the QC table"
	xlsx_writer.workbook.close()

