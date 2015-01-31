#! /bin/bash

# Goal: Navigate a project Dir by plate, then by sample.
# Get Coverage Metrics for each run of each sample.
# QC all of the multiple run bam files in each sample with each other (i.e. Run1 vs Run2, Run1 vs Run3, Run2 vs Run3)

#$ -S /bin/bash
#$ -cwd
#$ -N QC_Sample
#$ -o qc_sample_out.log
#$ -e qc_sample_out.log
#$ -q all.q
#$ -V


# Default file paths:
SOFTWARE_ROOT="/rawdata/legos"
QC_SCRIPTS="${SOFTWARE_ROOT}/scripts/QC"

function usage {
cat << EOF
USAGE: bash QC_sample.sh 
	-h | --help
	-s | --sample_dir <path/to/Sample_Dir>
	-g | --germline <path/to/TVC/parameters.json> <Depth Cutoff> <WT Cutoff> <HOM Cutoff>
	-all | --all_tumor_normal <Json_Normal> <Depth_N> <WT_N> <HOM_N> <Json_T> <Depth_T> <WT_T> <HOM_T>
	-tn | --tumor_normal <Json_Normal> <Depth_N> <WT_N> <HOM_N> <Json_T> <Depth_T> <WT_T> <HOM_T>
	-tt | --tumor_tumor <TVC Json_T> <Depth_T> <WT_T> <HOM_T>
	-nn | --normal_normal <TVC Json_Normal> <Depth_N> <WT_N> <HOM_N> 
	-b | --bed <path/to/bed> 
	-cb | --cds_bed <path/to/CDS_bed> (This option should only be used if the user wants to run TVC using the Project bed, and then intersect the results with the CDS bed.)
	-sb | --subset_bed <path/to/subset_bed> (If the user want to subset out certain genes from the Project_Bed)
	-a | --amp_cov_cutoff (Cutoff for # of amplicon reads.) 
	-rgc | --run_gatk_cds (Normally, GATK is run using the subset of the beds specified above. If the cds_bed is specified, and this option is specified, GATK will be run twice.)
	-chr | --subset_chr <chr#> (The chromosome specified here (for example: chr1) will be used to subset the VCF and BAM files)
	-ro | --run_info_only (Will skip QC_2Runs and run only QC_getRunInfo)
	-qo | --qc_2runs_only (Will skip QC_getRunInfo and run only QC_2Runs)
	-bb | --beg_bed <path/to/startLoci.bed> (Required unless --no_run_info is specified. bed file with only the 10th pos of the amplicons)
	-eb | --end_bed <path/to/endLoci.bed> (Required unless --no_run_info is specified. bed file with only the 10th pos from the end of the amplicons)
	-pl | --pool_dropout	(Optional. Will include the pool dropout script.)
	-cl | --cleanup (Will delete temporary files used to generate the QC metrics)
EOF
exit 8
}

# Checks to ensure that the files provided exist and are readable. 
# @param $1 should be a list of files.
function checkFiles {
	files=$1
	for file in ${files[@]}; do
		if [ "$file" != "" ]; then
			if [ ! "`find ${file} -maxdepth 0 2>/dev/null`" ]; then
				echo "-- ERROR -- '${file}' not found or not readable" 1>&2
				exit 4
			fi
		fi
	done
}

#for arguments
if [ $# -lt 5 ]; then
	usage
fi

# Default Options
GERMLINE="False" # Treat the file system as germline and generate QC tables for them. 
TUMOR_NORMAL="False" # Treat the file system as Tumor / Normal pairs and generate QC tables for them. 
TUMOR_TUMOR="False" # Treat the file system as Tumor / Tumor pairs and generate QC tables for them. 
NORMAL_NORMAL="False" # Treat the file system as Normal / Normal pairs and generate QC tables for them. 
GET_RUN_INFO="True" # Option to generate run information about each sample
POOL_DROPOUT="False" # Option to delete the temporary files. Not yet implemented.
CLEANUP="False" # Option to delete the temporary files. Not yet implemented.
NO_ERRS="True" # used for cleanup
AMP_COV_CUTOFF=30 # The minimum amount of coverage each amplicon needs to have. Default is 30

RUNNING="Starting QC using these option: "
counter=0
while :
do
	let "counter+=1"
	# If not enough inputs were given for an option, the while loop will just keep going. Stop it and print this error if it loops more than 100 times
	if [ $counter -gt 100 ]; then
		echo "USAGE: not all required inputs were given for options." 1>&2
		echo "$RUNNING"
		exit 8
	fi
	case $1 in
		-h | --help)
			usage
			;;
		-s | --sample_dir)
			SAMPLE_DIR=$2
			RUNNING="$RUNNING --sample_dir: $2, "
			shift 2
			;;
		-g | --germline)
			if [ "$5" == "" ]; then
				echo "ERROR: all 5 options are needed for --germline"
				exit 8
			fi			
			JSON_PARAS=$2
			DEPTH_CUTOFF=$3
			WT_CUTOFF=$4
			HOM_CUTOFF=$5
			RUNNING="$RUNNING --germline: Json_paras: $2, Depth_cutoff: $2, WT_cutoff:$3, HOM_cutoff:$4, "
			GERMLINE="True"
			shift 5
			;;
		-all | --all_tumor_normal)
			if [ "$9" == "" ]; then
				echo "ERROR: all 8 options are needed for --all_tumor_normal"
				exit 8
			fi
			JSON_PARAS_NORMAL=$2
			DEPTH_CUTOFF_NORMAL=$3
			WT_CUTOFF_NORMAL=$4
			HOM_CUTOFF_NORMAL=$5
			JSON_PARAS_TUMOR=$6
			DEPTH_CUTOFF_TUMOR=$7
			WT_CUTOFF_TUMOR=$8
			HOM_CUTOFF_TUMOR=$9
			RUNNING="$RUNNING --all_tumor_normal: Json_parasN: $2, Depth_cutoffN: $3 WT_N:$4 HOM_N:$5 Json_parasT: $6, Depth_cutoffT: $7 WT_T:$8 HOM_T:$9, "
			TUMOR_NORMAL="True"
			TUMOR_TUMOR="True"
			NORMAL_NORMAL="True"
			shift 9
			;;
		-tn | --tumor_normal)
			if [ "$9" == "" ]; then
				echo "ERROR: all 8 options are needed for --tumor_normal"
				exit 8
			fi			
			JSON_PARAS_NORMAL=$2
			DEPTH_CUTOFF_NORMAL=$3
			WT_CUTOFF_NORMAL=$4
			HOM_CUTOFF_NORMAL=$5
			JSON_PARAS_TUMOR=$6
			DEPTH_CUTOFF_TUMOR=$7
			WT_CUTOFF_TUMOR=$8
			HOM_CUTOFF_TUMOR=$9
			RUNNING="$RUNNING --tumor_normal: Json_parasN: $2, Depth_cutoff1: $3 WT_N:$4 HOM_N:$5 Json_parasT: $6, Depth_cutoffT: $7 WT_T:$8 HOM_T:$9, "
			TUMOR_NORMAL="True"
			shift 9
			;;
		-tt | --tumor_tumor)
			if [ "$5" == "" ]; then
				echo "ERROR: all 5 options are needed for --tumor_tumor"
				exit 8
			fi			
			JSON_PARAS_TUMOR=$3
			DEPTH_CUTOFF_TUMOR=$3
			WT_CUTOFF_TUMOR=$4
			HOM_CUTOFF_TUMOR=$5
			RUNNING="$RUNNING --tumor_tumor: Json_paras: $2, Depth_cutoff: $2 WT_cutoff:$3 HOM_cutoff:$4, "
			TUMOR_TUMOR="True"
			shift 5
			;;
		-nn | --normal_normal)
			if [ "$5" == "" ]; then
				echo "ERROR: all 5 options are needed for --normal_normal"
				exit 8
			fi			
			JSON_PARAS_NORMAL=$2
			DEPTH_CUTOFF_NORMAL=$3
			WT_CUTOFF_NORMAL=$4
			HOM_CUTOFF_NORMAL=$5
			RUNNING="$RUNNING --normal_normal: Json_paras: $2, Depth_cutoff: $2 WT_cutoff:$3 HOM_cutoff:$4, "
			NORMAL_NORMAL="True"
			shift 5
			;;

		-ro | --run_info_only)
			RUN_INFO_ONLY="True"
			RUNNING="$RUNNING --run_info_only, "
			shift
			;;
		-qo | --qc_2runs_only)
			QC_2RUNS_ONLY="True"
			RUNNING="$RUNNING --qc_2runs_only, "
			shift
			;;
		-b | --bed)
			PROJECT_BED=$2
			RUNNING="$RUNNING --bed: $2, "
			shift 2
			;;
		-cb | --cds_bed)
			CDS_BED=$2
			RUNNING="$RUNNING --cds_bed: $2, "
			shift 2
			;;
		-bb | --beg_bed)
			BEG_BED=$2
			RUNNING="$RUNNING --plus10: $2, "
			shift 2
			;;
		-eb | --end_bed)
			END_BED=$2
			RUNNING="$RUNNING --minus10: $2, "
			shift 2
			;;
		-a | --amp_cov_cutoff)
			AMP_COV_CUTOFF=$2
			RUNNING="$RUNNING --amp_cov_cutoff: $2, "
			shift 2
			;;
		-sb | --subset_bed)
			SUBSET_BED=$2
			RUNNING="$RUNNING --subset_bed: $2, "
			shift 2
			;;
		-rgc | --run_gatk_cds)
			RUN_GATK_CDS="True"
			RUNNING="$RUNNING --run_gatk_cds, "
			shift 
			;;
		-chr | --subset_chr)
			CHR=$2
			RUNNING="$RUNNING --subset_chr: $2, "
			shift 2
			;;
		-pl | --pool_dropout)
			POOL_DROPOUT="True"
			RUNNING="$RUNNING --pool_dropout "
			shift
			;;
		-cl | --cleanup)
			CLEANUP="True"
			RUNNING="$RUNNING --cleanup "
			shift
			;;
		-*)
			# If an unkown option was given, then give a warning
			printf >&2 'WARNING: Unknown option (ignored): %s\n' "$1"
			shift
			;;
		*)  # no more options. Stop while loop
			# If an unkown option was given, then give a warning
			if [ "$1" != "" ]; then
				printf >&2 'WARNING: Unknown argument (ignored): %s\n' "$1"
				shift
			else
				break
			fi
			;;
	esac
done

# RUNNING contains all of the specified options
echo "$RUNNING at `date`"

files=("$SAMPLE_DIR" "$PROJECT_BED" "$BEG_BED" "$END_BED" "$CDS_BED")
checkFiles $files

if [ "$CDS_BED" == "" -a "$RUN_GATK_CDS" == "True" ]; then
	echo "ERROR: No CDS bed was given. Cannot run gatk using the CDS bed!!"
	exit 8
fi

if [ "$GET_RUN_INFO" == "True" ]; then
	if [ "$BEG_BED" == "" -o "$END_BED" == "" ]; then
		echo "USAGE ERROR: --plus10bed and --minus10bed options are required." 
		echo "Use --no_run_info to skip gathering each run's info"
		exit 8
	fi
fi


# ----------------------------------------------------
# ------------ FUNCTIONS DEFINED HERE ----------------
# ----------------------------------------------------

# THIS FUNCTION IS NOT YET IMPLEMENTED
# $1: Run_Dir $2: The output dir $3 the depth cutoff $4 the WT_Cutoff $5 the HOM_Cutoff  $6: the TVC Json file needed to regenerate the PTRIM file.
function QC_getRunInfo {
	# QC_getRunInfo.sh gets the following metrics: % amps covered at the beg and end, Ts/Tv ratio,	# Total variants,	# HET variants, 	# HOM variants
	# It also gets the metrics from the backupPDF.pdf if it is available.
	# updated QC_getRunInfo includes Matt's pool drop-out script 
	qcgetruninfo="bash ${QC_SCRIPTS}/QC_getRunInfo.sh --run_dir $1 --out_dir $2 --amp_cov_cutoff $AMP_COV_CUTOFF --depth_cutoff $3 --wt_hom_cutoff $4 $5 --beg_bed $BEG_BED --end_bed $END_BED  --project_bed $PROJECT_BED --ptrim_json $6"
	if [ "$CDS_BED" != "" ]; then
		qcgetruninfo="$qcgetruninfo --cds_bed $CDS_BED "
	fi
	# QC_getRunInfo's will run the pool dropout script 
	if [ "$POOL_DROPOUT" == "True" ]; then
		qcgetruninfo="$qcgetruninfo --pool_dropout "
	fi
	# QC_getRunInfo's cleanup will just cleanup the output of TVC if the PTRIM was generated
	if [ "$CLEANUP" == "True" ]; then
		qcgetruninfo="$qcgetruninfo --cleanup "
	fi
	$qcgetruninfo
	status="$?"
	if [ $status -eq 1 ]; then
		echo "$QCd QC_getRunInfo.sh had an error!! " 1>&2
		NO_ERRS="False"
	elif [ $status -eq 4 ]; then
		echo "$QCd got a file not found error..." 1>&2
		NO_ERRS="False"
	elif [ $status -eq 8 ]; then
		echo "$QCd got a usage error..." 1>&2
		NO_ERRS="False"
	fi
}

# For Tumor / Normal pairs, Run1 should be the normal run, and Run2 should be the tumor run.
# $1 1st Run's dir name (i.e. sample1/Run1), $2: 2nd Run's dir name (i.e. sample1/Run2), 
# $3: JSON_PARAS1, $4: JSON_PARAS2
# $5: Depth1, $6: Depth2, $7: WT1, $8: HOM1, $9: WT2, $10: HOM2
# Output will be put into a dir like: sample1/QC/Run1vsRun2
function QC_2Runs {
	# This if statement is not needed, it's just an extra catch
	if [ "$1" != "$2" ]; then
		run1_name="`find $1 -maxdepth 0 -type d -printf "%f\n" 2>/dev/null`"
		run2_name="`find $2 -maxdepth 0 -type d -printf "%f\n" 2>/dev/null`"
		QCd="${SAMPLE_DIR}/QC/${CHR}${run1_name}vs${run2_name}"
		if [ "`find ${SAMPLE_DIR}/QC/*_QC.json* -type f 2>/dev/null`" ]; then
			json="`find ${SAMPLE_DIR}/QC/*_QC.json* -type f 2>/dev/null`"
		else
			json="${SAMPLE_DIR}/QC/results_QC.json"
		fi
		# QC these two runs. QC_2Runs.sh takes the two run dirs and finds a .bam, .vcf, and .cov.xls file in the same dir as the .bam file
		# If there is a PRITM.bam, it uses that. If there is not, it uses the other .bam file available.
		# I need to fix the parameters still... Should the user specify a .cov.xls and .vcf file? or just a bam file?
		qc2runs="bash ${QC_SCRIPTS}/QC_2Runs.sh --run_dirs $1 $2 --output_dir $QCd --json_out $json --project_bed $PROJECT_BED -a $AMP_COV_CUTOFF -jp $3 $4 -d $5 $6 -gt $7 $8 $9 ${10} "
		if [ "$CDS_BED" != "" ]; then
			qc2runs="$qc2runs -cb $CDS_BED "
		fi
		if [ "$SUBSET_BED" != "" ]; then
			qc2runs="$qc2runs --subset_bed $SUBSET_BED "
		fi
		if [ "$RUN_GATK_CDS" == "True" ]; then
			qc2runs="$qc2runs --run_gatk_cds "
		fi
		if [ "$CHR" != "" ]; then
			qc2runs="$qc2runs --subset_chr $CHR "
		fi
		# The cleanup will be done at the end of this script because the PTRIM.bam is needed for QC_getRunInfo.sh, and the chr_subset is needed for each run comparison
#		if [ "$CLEANUP" == "True" ]; then
#			qc2runs="$qc2runs --cleanup "
#		fi

		# now run QC_2Runs
		$qc2runs
		status="$?"
		if [ $status -eq 1 ]; then
			echo "$QCd QC_2Runs.sh had an error!! moving it to ${QCd}_Error" 1>&2
			NO_ERRS="False"
#			mv $QCd ${QCd}_Error
		elif [ $status -eq 4 ]; then
			echo "$QCd got a file not found error..." 1>&2
			NO_ERRS="False"
		elif [ $status -eq 8 ]; then
			echo "$QCd got a usage error..." 1>&2
			NO_ERRS="False"
		fi
	fi
}

# ---------------------------------------
# ------ PROGRAM STARTS HERE ------------
# ---------------------------------------

echo "$SAMPLE_DIR is starting QC"

# ---------------------------------- START GERMLINE ---------------------------------------
if [ "$GERMLINE" == "True" ]; then
	# Find all of the runs in this sample. The printf option makes it so only the name of the dir is printed
	runs="`find ${SAMPLE_DIR}/Run[0-9]* -maxdepth 0 -type d 2>/dev/null`"
	# QC the Multiple Runs
	for run1 in $runs; do
		run1_num=`echo "$run1" | grep -Eo "[0-9]$"`
		# If there are more than two run_bams for this sample, then QC them with each other.
		for run2 in $runs; do
			run2_num=`echo "$run2" | grep -Eo "[0-9]$"`
			if [ $run1_num -lt $run2_num ]; then
				# Make the QC table for this combination.
				if [ "$RUN_INFO_ONLY" != "True" ]; then
					QC_2Runs $run1 $run2 \
						$JSON_PARAS $JSON_PARAS \
						$DEPTH_CUTOFF $DEPTH_CUTOFF \
						$WT_CUTOFF $HOM_CUTOFF \
						$WT_CUTOFF $HOM_CUTOFF
				fi
			fi
		done
		# the call to QC_getRunInfo.sh must be after QC_2Runs.sh because the PTRIM.bam output after TVC is necessary to the beg and end amplicon cov metrics. 
		# If the user did not specify to get this run's info, then get this run's info.
		if [ "$QC_2RUNS_ONLY" != "True" ]; then
			#get_Run_Info $sample ${sample}/Analysis_files/gatk_out
			QC_getRunInfo $run1 ${run1}/Analysis_Files/temp_files $DEPTH_CUTOFF $WT_CUTOFF $HOM_CUTOFF $JSON_PARAS
		fi
	done
fi
# ---------------------------------- END GERMLINE ---------------------------------------

# $1 1st Run's dir name (i.e. sample1/Run1), $2: 2nd Run's dir name (i.e. sample1/Run2), 
# $3: JSON_PARAS1, $4: JSON_PARAS2
# $3: Depth1, $4: Depth2, $5: WT1, $6: HOM1, $7: WT2, $8: HOM2

# ---------------------------------- Start Somatic ---------------------------------------
if [ "$TUMOR_NORMAL" == "True" ]; then
	# QC the Tumor runs with the normal runs.
	normal_runs="`find ${SAMPLE_DIR}/Normal/N-[0-9_]* -maxdepth 0 -type d 2>/dev/null`"
	tumor_runs="`find ${SAMPLE_DIR}/Tumor/T-[0-9_]* -maxdepth 0 -type d 2>/dev/null`"
	for normal_run in $normal_runs; do
		for tumor_run in $tumor_runs; do
			# Make the QC table for this combination.
			if [ "$RUN_INFO_ONLY" != "True" ]; then
				QC_2Runs $normal_run $tumor_run \
					$JSON_PARAS_NORMAL $JSON_PARAS_TUMOR \
					$DEPTH_CUTOFF_NORMAL $DEPTH_CUTOFF_TUMOR \
					$WT_CUTOFF_NORMAL $HOM_CUTOFF_NORMAL \
					$WT_CUTOFF_TUMOR $HOM_CUTOFF_TUMOR
			fi

			# the call to QC_getRunInfo.sh must be after QC_2Runs.sh because the PTRIM.bam output after TVC is necessary to the beg and end amplicon cov metrics. 
			# If the user did not specify to get this run's info, then get this run's info.
			if [ "$QC_2RUNS_ONLY" != "True" -a "$TUMOR_TUMOR" != "True" ]; then
				QC_getRunInfo $tumor_run ${tumor_run}/Analysis_Files/temp_files $DEPTH_CUTOFF_TUMOR $WT_CUTOFF_TUMOR $HOM_CUTOFF_TUMOR $JSON_PARAS_TUMOR
			fi
		done		
		# also get the Run Info for the normal runs.
		if [ "$QC_2RUNS_ONLY" != "True" -a "$NORMAL_NORMAL" != "True" ]; then
			QC_getRunInfo $normal_run ${normal_run}/Analysis_Files/temp_files $DEPTH_CUTOFF_NORMAL $WT_CUTOFF_NORMAL $HOM_CUTOFF_NORMAL $JSON_PARAS_NORMAL
		fi
	done
fi

if [ "$TUMOR_TUMOR" == "True" ]; then
	# QC the Tumor runs with the tumor runs.
	tumor_runs="`find ${SAMPLE_DIR}/Tumor/T-[0-9_]* -maxdepth 0 -type d 2>/dev/null`"
	for tumor_run1 in $tumor_runs; do
		t1_num=`echo "$tumor_run1" | grep -Eo "[0-9]$"`
		for tumor_run2 in $tumor_runs; do
			t2_num=`echo "$tumor_run2" | grep -Eo "[0-9]$"`
			if [ $t1_num -lt $t2_num ]; then
				if [ "$RUN_INFO_ONLY" != "True" ]; then
					# Make the QC table for this combination.
					QC_2Runs $tumor_run1 $tumor_run2 \
						$JSON_PARAS_TUMOR $JSON_PARAS_TUMOR \
						$DEPTH_CUTOFF_TUMOR $DEPTH_CUTOFF_TUMOR \
						$WT_CUTOFF_TUMOR $HOM_CUTOFF_TUMOR \
						$WT_CUTOFF_TUMOR $HOM_CUTOFF_TUMOR
				fi
			fi
		done		
		# the call to QC_getRunInfo.sh must be after QC_2Runs.sh because the PTRIM.bam output after TVC is necessary to the beg and end amplicon cov metrics. 
		# If the user did not specify to get this run's info, then get this run's info.
		if [ "$QC_2RUNS_ONLY" != "True" ]; then
			QC_getRunInfo $tumor_run1 ${tumor_run1}/Analysis_Files/temp_files $DEPTH_CUTOFF_TUMOR $WT_CUTOFF_TUMOR $HOM_CUTOFF_TUMOR  $JSON_PARAS_TUMOR
		fi
	done
fi

if [ "$NORMAL_NORMAL" == "True" ]; then
	# QC the Tumor runs with the normal runs.
	normal_runs="`find ${SAMPLE_DIR}/Normal/N-[0-9_]* -maxdepth 0 -type d 2>/dev/null`"
	for normal_run1 in $normal_runs; do
		n1_num=`echo "$normal_run1" | grep -Eo "[0-9]$"`
		for normal_run2 in $normal_runs; do
			n2_num=`echo "$normal_run2" | grep -Eo "[0-9]$"`
			if [ $n1_num -lt $n2_num ]; then
				if [ "$RUN_INFO_ONLY" != "True" ]; then
					# Make the QC table for this combination.
					QC_2Runs $normal_run1 $normal_run2 \
						$JSON_PARAS_NORMAL $JSON_PARAS_NORMAL \
						$DEPTH_CUTOFF_NORMAL $DEPTH_CUTOFF_NORMAL \
						$WT_CUTOFF_NORMAL $HOM_CUTOFF_NORMAL \
						$WT_CUTOFF_NORMAL $HOM_CUTOFF_NORMAL
				fi
			fi
		done		
		# the call to QC_getRunInfo.sh must be after QC_2Runs.sh because the PTRIM.bam output after TVC is necessary to the beg and end amplicon cov metrics. 
		# If the user did not specify to get this run's info, then get this run's info.
		if [ "$QC_2RUNS_ONLY" != "True" ]; then
			QC_getRunInfo $normal_run1 ${normal_run1}/Analysis_Files/temp_files $DEPTH_CUTOFF_NORMAL $WT_CUTOFF_NORMAL $HOM_CUTOFF_NORMAL $JSON_PARAS_NORMAL
		fi
	done
fi
	
	# ---------------------------------- END Somatic ---------------------------------------

if [ "$NO_ERRS" == "False" ]; then
	echo "Not cleaning up. There was an error"
	echo "$SAMPLE_DIR Finished WITH ERRORS at `date`"
	echo "----------------------------------------------"
	exit 1
fi
	
# Cleanup and done.
if [ "$CLEANUP" == "True" ]; then
	# remove the temp files. (Mainly the PTRIM.bam because it takes up more space)
	temp_dirs=`find ${SAMPLE_DIR}/QC -name "temp_files" -type d 2>/dev/null`
	for temp_dir in $temp_dirs; do
		rm -rf $temp_dir
	done
	if [ "$CHR" != "" ]; then
		# Remove the chr subsets if they were created.
		chr_subsets=`find ${SAMPLE_DIR} -name "${CHR}" -type d 2>/dev/null`
		for chr_subset in $chr_subsets; do
			rm -rf $chr_subset
		done
	fi
	# Remove the PTRIM.bams
	ptrims=`find ${SAMPLE_DIR} -name "PTRIM.bam*" -type f 2>/dev/null`
	for ptrim in $ptrims; do
		rm $ptrim
	done
fi

echo "$SAMPLE_DIR Finished QC_sample at `date`"
echo "----------------------------------------------"

