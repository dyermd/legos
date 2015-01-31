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


# @param out_file_name the name of the outuput xlsx
##### @returns a format of dictionary
def setupWorkbook():
	#Dictionary containing all of the different formats
	global formats 
	# initialize formats with a blank string in case there are times where there is no format
	# this dictionary will hold all of the formats to be used by QC_genSheets
	formats = {'': ''}
	
	# The color for each alternating sample
	alt_sample_color = "#d5e8f8" # This color is considered azure by the color wheel. Go to this website to choose a new color
	
	# Adding formats for red cells, and the borders for the table.
	formats['header_format'] = workbook.add_format()
	formats['header_format'].set_bold()
	formats['header_format'].set_font_size(12)
	formats['header_format'].set_align('center')
	formats['header_format'].set_text_wrap()
	formats['header_format2'] = workbook.add_format()
	formats['header_format2'].set_bold()
	formats['header_format2'].set_font_size(14)
	
	#formats['header_format'] = workbook.add_format()
	#formats['header_format'].set_bold()
	#formats['header_format'].set_font_size(12)
	#formats['header_format'].set_align('center')
	#formats['header_format'].set_text_wrap()
	#formats['header_format2'] = workbook.add_format()
	formats['header_format3'] = workbook.add_format()
	#formats['header_format3'].set_bold()
	formats['header_format3'].set_font_size(12)

	formats['center'] = workbook.add_format()
	formats['center'].set_align('center')
	
	formats['_azure'] = workbook.add_format()
	formats['_azure'].set_bg_color(alt_sample_color)
	formats['_azure'].set_align('center')
	
	formats['red'] = workbook.add_format()
	formats['red'].set_bg_color('#FF0000')
	formats['red'].set_align('center')
	
	formats['num_format'] = workbook.add_format({'num_format': '#,##0'})
	formats['num_format'].set_align('center')
	formats['perc_format'] = workbook.add_format({'num_format': '0.00%'})
	formats['perc_format'].set_align('center')
	formats['dec3_format'] = workbook.add_format({'num_format': '0.000'})
	formats['dec3_format'].set_align('center')
	formats['num_format_azure'] = workbook.add_format({'num_format': '#,##0'})
	formats['num_format_azure'].set_align('center')
	formats['num_format_azure'].set_bg_color(alt_sample_color)
	formats['perc_format_azure'] = workbook.add_format({'num_format': '0.00%'})
	formats['perc_format_azure'].set_align('center')
	formats['perc_format_azure'].set_bg_color(alt_sample_color)
	formats['dec3_format_red'] = workbook.add_format({'num_format': '0.000'})
	formats['dec3_format_red'].set_align('center')
	formats['dec3_format_red'].set_bg_color('#FF0000')
	formats['dec3_format_azure'] = workbook.add_format({'num_format': '0.000'})
	formats['dec3_format_azure'].set_align('center')
	formats['dec3_format_azure'].set_bg_color(alt_sample_color)
	
	formats['top'] = workbook.add_format()
	formats['top'].set_top(2)
	formats['right'] = workbook.add_format()
	formats['right'].set_right(2)
	formats['bottom'] = workbook.add_format()
	formats['bottom'].set_bottom(2)
	formats['left'] = workbook.add_format()
	formats['left'].set_left(2)
	
#	return formats
	
# Function to check if a value is greater than the maximum value (i.e. WT to HET is greater than 10 or something), then write it in red
def check_max_and_write(row, col, value, Max):
	if int(value) > int(Max):
		# write this cell in red
		MRsheet.write(row, col, value, formats['red'])
	else:
		MRsheet.write(row, col, value)
		# write this cell in normal white


# Complex function to write cells. 
# @param write_format is the format to write the cell in. 
# @param Max will be the maximum threshold for writing in red, unless it's 0. If max if negative, it will be treated as a minimum threshold
# MAx is not yet implemented.
# @return returns 1 so there will be one less line of code (to incrament col). Maybe it could just incrament col, I would just rather not have global variables
def check_to_write(row, col, key, write_format, metrics):
	if key in metrics:
		try:
			if re.search("=", write_format):
				if metrics[key] != "":
					cell1 = xl_rowcol_to_cell(row, col-2)
					cell2 = xl_rowcol_to_cell(row, col-1)
					QCsheet.write_formula(row, col, "=(%s-%s)/%s"%(cell1, cell2, cell1), formats[write_format[1:]])
			elif re.search("num_format", write_format):
				if not isinstance(metrics[key], int) and not isinstance(metrics[key], float):
					QCsheet.write_number(row, col, int(metrics[key].replace(',','')), formats[write_format])
				else:
					QCsheet.write_number(row, col, metrics[key], formats[write_format])
			elif re.search("perc_format", write_format):
				if float(metrics[key]) > 1:
					metrics[key] = metrics[key] / 100
				QCsheet.write_number(row, col, float(metrics[key]), formats[write_format])
			elif re.search("dec3_format", write_format):
				QCsheet.write_number(row, col, float(metrics[key]), formats[write_format])
			# special case to write the formula for the +-10 bp col
			else:
				# if write_format is blank, then formats will also be blank
				QCsheet.write(row, col, metrics[key], formats[write_format])
		except ValueError:
			QCsheet.write(row, col, metrics[key], formats[write_format])
	return 1


# @param run_metrics the dictionary containing all of the run_metrics
def writeRunMetrics(run_metrics):
	# Infosheet is where all of the metrics about each run will be written
	global QCsheet
	QCsheet = workbook.add_worksheet("QC Metrics")
	QCsheet.freeze_panes(1,2)
	
	# First write the QC metrics for each run of each sample.
	# Write the header
	col = 0
	QCsheet.write(0,col, "Sample #", formats['header_format'])
	QCsheet.set_column(col,col,None, formats['center'])
	col += 1
#	QCsheet.write(0,col, "Plate, row and column", formats['header_format'])
#	QCsheet.set_column(col,col,10, formats['center'])
#	col += 1
	QCsheet.write(0,col, "Library prep date", formats['header_format'])
	QCsheet.set_column(col,col,10, formats['center'])
	col += 1
	#QCsheet.write(0,col, "Barcode used", formats['header_format'])
	#QCsheet.set_column(col,col,12, formats['center'])
	#col += 1
	QCsheet.write(0,col, "Library concentration (ng/ul)", formats['header_format'])
	QCsheet.set_column(col,col,None, formats['center'])
	col += 1
	QCsheet.write(0,col, "Run #", formats['header_format'])
	QCsheet.set_column(col,col,5, formats['center'])
	col += 1
	QCsheet.write(0,col, "Rot ID", formats['header_format'])
	QCsheet.set_column(col,col,None, formats['center'])
	col += 1
	QCsheet.write(0,col, "Run Date", formats['header_format'])
	QCsheet.set_column(col,col,12, formats['center'])
	col += 1
	QCsheet.write(0,col, "Total M Basepairs", formats['header_format'])
	QCsheet.set_column(col,col,12, formats['center'])
	col += 1
	QCsheet.write(0,col, "% Polyclonal", formats['header_format'])
	QCsheet.set_column(col,col,12, formats['center'])
	col += 1
	QCsheet.write(0,col, "Mean Read Length", formats['header_format'])
	QCsheet.set_column(col,col,None, formats['center'])
	col += 1
	QCsheet.write(0,col, "Median Read Length", formats['header_format'])
	QCsheet.set_column(col,col,None, formats['center'])
	col += 1
	QCsheet.write(0,col, "% expected read length (out of XXX bp)", formats['header_format'])
	QCsheet.set_column(col,col,12, formats['center'])
	col += 1
	QCsheet.write(0,col,"Median Read Coverage overall", formats['header_format'])
	QCsheet.set_column(col,col,13, formats['center'])
	col += 1
	QCsheet.write(0,col, "% amplicons > 30x covered at bp +10", formats['header_format'])
	QCsheet.set_column(col,col,13, formats['center'])
	col += 1
	QCsheet.write(0,col, "% amplicons > 30x covered at bp -10", formats['header_format'])
	QCsheet.set_column(col,col,13, formats['center'])
	col += 1
	QCsheet.write(0,col, "(%covered at bp(10) - bp(n-10))/bp(10)", formats['header_format'])
	QCsheet.set_column(col,col,13, formats['center'])
	col += 1
#	QCsheet.write(0,col, "total number of bases covered at 30x (the # of bases covered in the 'covered_bases region' region.)", formats['header_format'])
#	QCsheet.set_column(col,col,18, formats['center'])
#	col += 1
#	QCsheet.write(0,col, "% covered bases (n/83046)", formats['header_format'])
#	QCsheet.set_column(col,col,13, formats['center'])
#	col += 1
#	QCsheet.write(0,col, "% targeted bases (n/84447)", formats['header_format'])
#	QCsheet.set_column(col,col,13, formats['center'])
#	col += 1
	QCsheet.write(0,col, "# of pools <10% median coverage", formats['header_format'])
	QCsheet.set_column(col,col,13, formats['center'])
	col += 1
	QCsheet.write(0,col, "# of pools between 10%-50% median coverage ", formats['header_format'])
	QCsheet.set_column(col,col,13, formats['center'])
	col += 1
	QCsheet.write(0,col, "# of pools between 50%-75% median coverage", formats['header_format'])
	QCsheet.set_column(col,col,13, formats['center'])
	col += 1
	QCsheet.write(0,col, "# of pools passed", formats['header_format'])
	QCsheet.set_column(col,col,13, formats['center'])
	col += 1
	QCsheet.write(0,col, "total # of pools", formats['header_format'])
	QCsheet.set_column(col,col,13, formats['center'])
	col += 1
	QCsheet.write(0,col, "Ts/Tv", formats['header_format'])
	QCsheet.set_column(col,col,13, formats['center'])
	col += 1
	QCsheet.write(0,col, "# Total variants (single allele)", formats['header_format'])
	QCsheet.set_column(col,col,13, formats['center'])
	col += 1
	QCsheet.write(0,col, "# HET variants (single allele rates)", formats['header_format'])
	QCsheet.set_column(col,col,13, formats['center'])
	col += 1
	QCsheet.write(0,col, "# HOM variants (single allele rates)", formats['header_format'])
	QCsheet.set_column(col,col,13, formats['center'])
	col += 1
	QCsheet.write(0,col, "HET/HOM ratio (single allele rates)", formats['header_format'])
	QCsheet.set_column(col,col,13, formats['center'])
	col += 1
	QCsheet.write(0,col, "3x3 N-N pair (whole amplicon)", formats['header_format'])
	QCsheet.set_column(col,col,13, formats['center'])
	col += 1
	QCsheet.write(0,col, "Total bases evaluated (>=30x in both runs) (whole amplicon)", formats['header_format'])
	QCsheet.set_column(col,col,13, formats['center'])
	col += 1
	QCsheet.write(0,col, "% Available Bases (whole amplicon)", formats['header_format'])
	QCsheet.set_column(col,col,13, formats['center'])
	col += 1
	QCsheet.write(0,col, "3x3 qc observed error counts  (whole amplicon)", formats['header_format'])
	QCsheet.set_column(col,col,13, formats['center'])
	col += 1
	QCsheet.write(0,col, "3x3 qc error rate  (whole amplicon)", formats['header_format'])
	QCsheet.set_column(col,col,13, formats['center'])
	col += 1
	QCsheet.write(0,col, "Z-Score error rate (whole amplicon)", formats['header_format'])
	QCsheet.set_column(col,col,13, formats['center'])
	col += 1
#	QCsheet.write(0,col, "Total bases evaluated (>=30x in both runs) (cds only)", formats['header_format'])
#	QCsheet.set_column(col,col,13, formats['center'])
#	col += 1
#	QCsheet.write(0,col, "% Available Bases (cds only)", formats['header_format'])
#	QCsheet.set_column(col,col,13, formats['center'])
#	col += 1
#	QCsheet.write(0,col, "3x3 qc observed error counts  (cds only)", formats['header_format'])
#	QCsheet.set_column(col,col,13, formats['center'])
#	col += 1
#	QCsheet.write(0,col, "3x3 qc error rate  (cds only)", formats['header_format'])
#	QCsheet.set_column(col,col,13, formats['center'])
#	col += 1
#	QCsheet.write(0,col, "Z-Score error rate (cds only)", formats['header_format'])
#	QCsheet.set_column(col,col,13, formats['center'])
#	col += 1
	QCsheet.write(0,col, "run status (does it pass qc?)", formats['header_format'])
	QCsheet.set_column(col,col,None, formats['center'])
	col += 1
	QCsheet.set_column(col,col+20,12, formats['center'])
	
	QCsheet.set_row(0,100, formats['header_format'])
	
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
			#col += check_to_write(row, col, 'sample_num', "" + azure, metrics)
			col += check_to_write(row, col, 'sample', "" + azure, metrics)
			col += check_to_write(row, col, 'lib_prep_date', "" + azure, metrics)
			#col += check_to_write(row, col, 'barcode', "" + azure, metrics)
			col += check_to_write(row, col, 'lib_conc', "" + azure, metrics)
			col += check_to_write(row, col, 'run_num', "" + azure, metrics)
			col += check_to_write(row, col, 'rotID', "" + azure, metrics)
			col += check_to_write(row, col, 'run_date', "" + azure, metrics)
			col += check_to_write(row, col, 'total_bases', "num_format" + azure, metrics)
			# Old naming sheme:
			#col += check_to_write(row, col, 'polyclonal', "perc_format" + azure, metrics)
			#col += check_to_write(row, col, 'mean', "num_format" + azure, metrics)
			#col += check_to_write(row, col, 'median', "num_format" + azure, metrics)
			col += check_to_write(row, col, 'polyclonality', "perc_format" + azure, metrics)
			col += check_to_write(row, col, 'mean_read_length', "num_format" + azure, metrics)
			col += check_to_write(row, col, 'median_read_length', "dec3_format" + azure, metrics)
			col += check_to_write(row, col, 'expected_length', "" + azure, metrics)
			col += check_to_write(row, col, 'median_coverage_overall', "num_format" + azure, metrics)
			col += check_to_write(row, col, 'begin_amp_cov', 'perc_format' + azure, metrics)
			col += check_to_write(row, col, 'end_amp_cov', 'perc_format' + azure, metrics)
			# give it the dummy 'end_amp_cov' key to write the function of +-10 bp difference. the = is for a function
			col += check_to_write(row, col, 'end_amp_cov', "=dec3_format" + azure, metrics)
#			col += check_to_write(row, col, 'total_covered', 'num_format' + azure, metrics)
#			col += check_to_write(row, col, 'perc_expected', 'perc_format' + azure, metrics)
#			col += check_to_write(row, col, 'perc_targeted', 'perc_format' + azure, metrics)
			# Old naming scheme:
			#col += check_to_write(row, col, 'tstv', 'num_format' + azure, metrics)
			col += check_to_write(row, col, 'pools_less_than_10', "num_format" + azure, metrics)
			col += check_to_write(row, col, 'pools_between_10_and_50', "num_format" + azure, metrics)
			col += check_to_write(row, col, 'pools_between_50_and_75', "num_format" + azure, metrics)
			col += check_to_write(row, col, 'pools_pass', "num_format" + azure, metrics)
			col += check_to_write(row, col, 'pools_total', "num_format" + azure, metrics)
			col += check_to_write(row, col, 'ts_tv', 'dec3_format' + azure, metrics)
			col += check_to_write(row, col, 'total_vars', 'num_format' + azure, metrics)
			col += check_to_write(row, col, 'num_het', 'num_format' + azure, metrics)
			col += check_to_write(row, col, 'num_hom', 'num_format' + azure, metrics)
			col += check_to_write(row, col, 'het_hom', 'dec3_format' + azure, metrics)
			#run_num = int(metrics['run_num'])
			#runs = int(metrics['runs'])
	
			# Now write the N-N pair and the T-T pairs
			col += check_to_write(row, col, 'same_pair', "" + azure, metrics)
			col += check_to_write(row, col, 'same_total_eligible_bases', 'num_format' + azure, metrics)
			col += check_to_write(row, col, 'same_perc_available_bases', 'perc_format' + azure, metrics)
			col += check_to_write(row, col, 'same_error_count', 'num_format' + azure, metrics)
			col += check_to_write(row, col, 'same_error_rate', 'perc_format' + azure, metrics)
			try:
				if 'same_zscore' in metrics and float(metrics['same_zscore']) > 3:
					QCsheet.write_number(row, col, float(metrics['same_zscore']), dec3_format_red)
					metrics['same_status'] = 'Fail'
					col += 1
				else:
					col += check_to_write(row, col, 'same_zscore', 'dec3_format' + azure, metrics)
			except ValueError:
				col += check_to_write(row, col, 'tn_zscore', '' + azure, metrics)
			col += check_to_write(row, col, 'same_status', "" + azure, metrics)
	
		# Now write the T-N pairs
			col += check_to_write(row, col, 'tn_pair', "" + azure, metrics)
			col += check_to_write(row, col, 'tn_total_evaluated', 'num_format' + azure, metrics)
			col += check_to_write(row, col, 'tn_perc_available_bases', 'perc_format' + azure, metrics)
			col += check_to_write(row, col, 'tn_error_count', 'num_format' + azure, metrics)
			col += check_to_write(row, col, 'tn_error_rate', 'perc_format' + azure, metrics)
			try:
				if 'tn_zscore' in metrics and float(metrics['tn_zscore']) > 3:
					QCsheet.write_number(row, col, float(metrics['tn_zscore']), dec3_format_red)
					metrics['tn_status'] = 'Fail'
					col += 1
				else:
					col += check_to_write(row, col, 'tn_zscore', 'dec3_format' + azure, metrics)
			except ValueError:
				col += check_to_write(row, col, 'tn_zscore', '' + azure, metrics)
			col += check_to_write(row, col, 'tn_status', "" + azure, metrics)
		
			# Set the color of this row according to the current color
			QCsheet.set_row(row, None, formats[azure])

			row += 1
	


# Write the multiple run Info 3x3 tables if specified
# @param QC_comparisons the dictionary from all of the _QC.json files
def write3x3Tables(QC_comparisons):
	# MRsheet is the sheet where all of the 3x3 tables for each of the multiple runs of each sample will be written
	global MRsheet
	MRsheet = workbook.add_worksheet("3x3 tables")
	row = 2
	col = 2
	# now write the 3x3 tables on the mr sheet
	for sample in sorted(QC_comparisons):
		for runs_compared, table_values in sorted(QC_comparisons[sample].iteritems()):
			#first make the header for each table.
			header = "%s:   %s    -  vs  -    %s"%(sample, runs_compared.split('vs')[0], runs_compared.split('vs')[1]) # i.e. sample1  Run1  -  vs  - Run2
			MRsheet.write(row-1, col, header, formats['header_format2'])
			header_error_rate = "%s:  %.3e"% ("error rate", float(table_values["error_rate"]))
			row=row+1;
			MRsheet.write(row-1, col, header_error_rate, formats['header_format3'])
			row=row+1
			header_perc_bases = "%s:  %.2f"% ("% available bases", float(table_values["perc_avail_bases"])*100)
			MRsheet.write(row-1, col, header_perc_bases, formats['header_format3'])
			row=row+1

			#print "generating the qc tables for: " + header
			
			#now write the table headers
			MRsheet.write(row+1, col, "WT", formats['right'])
			MRsheet.write(row+2, col, "HET", formats['right'])
			MRsheet.write(row+3, col, "HOM", formats['right'])
			MRsheet.write(row+4, col, "Sum:")
			MRsheet.write(row, col+1, "WT", formats['bottom'])
			MRsheet.write(row, col+2, "HET", formats['bottom'])
			MRsheet.write(row, col+3, "HOM", formats['bottom'])
			MRsheet.write(row, col+4, "Sum:")
		
			total = int(table_values["WT_WT"]) + int(table_values["WT_HET"]) + int(table_values["WT_HOM"]) + \
					int(table_values["HET_WT"]) + int(table_values["HET_HET"]) + int(table_values["HET_HOM"]) + \
					int(table_values["HOM_WT"]) + int(table_values["HOM_HET"]) + int(table_values["HOM_HOM"])
			# If there are less than 10,000 nucleotides to compare on the QC spreadMRsheet, highlight those in red.
		#	if int(table_values['WT_WT']) < 50000:
		#		MRsheet.write(row+1, col+1, table_values["WT_WT"], formats['red'])
		#	else:
			MRsheet.write(row+1, col+1, table_values["WT_WT"])
			# add the diagonal and the sums because their formatting won't change.
			MRsheet.write(row+2, col+2, table_values["HET_HET"])
			MRsheet.write(row+3, col+3, table_values["HOM_HOM"])
			# Add the totals for each row and column
			MRsheet.write(row+4, col+1, str(int(table_values["WT_WT"])+int(table_values["HET_WT"])+int(table_values["HOM_WT"])), formats['top'])
			MRsheet.write(row+4, col+2, str(int(table_values["WT_HET"])+int(table_values["HET_HET"])+int(table_values["HOM_HET"])), formats['top'])
			MRsheet.write(row+4, col+3, str(int(table_values["WT_HOM"])+int(table_values["HET_HOM"])+int(table_values["HOM_HOM"])), formats['top'])
			MRsheet.write(row+1, col+4, str(int(table_values["WT_WT"])+int(table_values["WT_HET"])+int(table_values["WT_HOM"])), formats['left'])
			MRsheet.write(row+2, col+4, str(int(table_values["HET_WT"])+int(table_values["HET_HET"])+int(table_values["HET_HOM"])), formats['left'])
			MRsheet.write(row+3, col+4, str(int(table_values["HOM_WT"])+int(table_values["HOM_HET"])+int(table_values["HOM_HOM"])), formats['left'])
			MRsheet.write(row+4, col+4, str(total))
		
			# It could be useful to highlight cells that are especially high
#			if mr: # set different cells to red if they exceed the threshold specified
#				check_max_and_write(row+2, col+1, table_values["HET_WT"], hetMax)
#				check_max_and_write(row+3, col+1, table_values["HOM_WT"], homMax)
#				check_max_and_write(row+1, col+2, table_values["WT_HET"], hetMax)
#				check_max_and_write(row+3, col+2, table_values["HOM_HET"], hetMax)
#				check_max_and_write(row+1, col+3, table_values["WT_HOM"], homMax)
#				check_max_and_write(row+2, col+3, table_values["HET_HOM"], hetMax)
#			elif tn:
#				# write normal values
#				check_max_and_write(row+2, col+1, table_values["HET_WT"], het_wtMax)
#				check_max_and_write(row+3, col+1, table_values["HOM_WT"], hom_wtMax)
#				check_max_and_write(row+3, col+2, table_values["HOM_HET"], hom_hetMax)
#				# now write the tumor side
#				MRsheet.write(row+1, col+2, table_values["WT_HET"])
#				MRsheet.write(row+1, col+3, table_values["WT_HOM"])
#				MRsheet.write(row+2, col+3, table_values["HET_HOM"])
#			else:
#				# if no threshold is specified, then everything will stay white.
			MRsheet.write(row+2, col+1, table_values["HET_WT"])
			MRsheet.write(row+3, col+1, table_values["HOM_WT"])
			MRsheet.write(row+1, col+2, table_values["WT_HET"])
			MRsheet.write(row+3, col+2, table_values["HOM_HET"])
			MRsheet.write(row+1, col+3, table_values["WT_HOM"])
			MRsheet.write(row+2, col+3, table_values["HET_HOM"])
			# if there are more than two runs for this sample, add another table to the right.
			col += 8
			row -= 3 
		# For each sample, go back to col = 2
		row += 10
		col = 2


# start here
if (__name__ == "__main__"):
	# parse the arguments
	parser = OptionParser()
	
	# All of the arguments are specified here.
	parser.add_option('-j', '--json', dest='json', help="If the json file was already generated, you can use this option instead to just load the json file")
	parser.add_option('-J', '--qc_json', dest='qc_json', help="If the QC_comparisons json file was already generated, you can use this option instead to just load the json file")
	parser.add_option('-p', '--project_path', dest='project_path', help='REQUIRED: /path/to/the/project_dir')
	parser.add_option('-r', '--run_info_only', dest='run_info_only', action="store_true", default=False, help="Get only the individual run's info")
	parser.add_option('-q', '--qc_info_only', dest='qc_info_only', action="store_true", default=False, help="Get only the QC comparison info")
	parser.add_option('-b', '--bases', dest='bases', type="int", nargs=3, help="Specify 1: the total_expected_bases, 2: the total_targeted_bases, 3: the total_possible_bases")
	parser.add_option('-o', '--out', dest='out', default='QC.xlsx', help='Specify the output xlsx file [default: %default]')
	
	# Gets all of the command line arguments specified and puts them into the dictionary args
	(options, args) = parser.parse_args()
	
	if len(sys.argv) < 2:
		parser.print_help()
		sys.exit(8)

	# Wales bases:
	#total_expected_bases = 83046
	#total_targeted_bases = 84447
	#total_possible_bases = 124490
	
	# Ensure the user specifies a .xlsx ending if the -o/--output option is used
	if options.out[-5:] != ".xlsx":
		parser.error("-o (--out) output file must end in .xlsx")
	
	# These could be used to write red, but I haven't used them yet
	hetMax = 5
	homMax = 2
	het_wtMax = 70
	hom_wtMax = 10
	hom_hetMax = 70
	
	# setup the xlsx workbook
	global workbook
	workbook = xlsxwriter.Workbook(options.out)
	# add the formats and such to the workbook
	setupWorkbook()
	
	# first check to see if the json files were passed in
	if options.json and options.qc_json:
		json_data = json.load(open(options.json))
		QC_json_data = json.load(open(options.qc_json))
		writeRunMetrics(json_data)
		write3x3Tables(QC_json_data)
	elif options.json:
		json_data = json.load(open(options.json))
		writeRunMetrics(json_data)
	elif options.qc_json:
		QC_json_data = json.load(open(options.qc_json))
		write3x3Tables(QC_json_data)

	# if no json_data file was specified, then find the metrics in the project dir specified
	elif not options.project_path:
		print "USAGE ERROR: -p (--project_path) is required. Use -h for help"
		sys.exit(8)
	# Get the data available by finding the json files in the project_path specified.
	elif options.run_info_only:
		json_data = QC_stats.main_runs_only(options.project_path)
		writeRunMetrics(json_data)
	elif options.qc_info_only:
		QC_json_data = QC_stats.main_QC_only(options.project_path)
		write3x3Tables(QC_json_data)
	elif options.bases != None:
		json_data = QC_stats.main(options.project_path, options.bases[2]) #total_possible_bases
		# 3x3 table will still be generated, so use this still
		QC_json_data = QC_stats.main_QC_only(options.project_path)
		writeRunMetrics(json_data)
		write3x3Tables(QC_json_data)
	else:
		print "USAGE ERROR: --bases are needed for combining QC and run info"
		sys.exit(8)
	
	print "Finished generating the QC table"
	workbook.close()

