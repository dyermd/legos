#!/bin/bash

# GOAL: Run TVC on both run's bam files to generate a 3x3 QC table. 
# TS version: 4.2
# Author: Jeff L

# INPUT: Two Run directoreis and the project's BED file.
# The Run directories should already have a .bam, .vcf, and .amplicon.cov.xls file in them. 

# QSUB variables

#$ -S /bin/bash
#$ -cwd
#$ -N QC_2Runs
#$ -o qc_sample_out.log
#$ -e qc_sample_out.log
#$ -q all.q
#$ -V


SOFTWARE_DIR="/rawdata/software"
QC_SCRIPTS="${SOFTWARE_DIR}/scripts/QC"
QC_MASTER_OUT="$QC_SCRIPTS/QC_Out_Files/multiple_runs.csv"
BAM_INDEXER='/opt/picard/picard-tools-current/BuildBamIndex.jar'
VARIANT_CALLER_DIR='/results/plugins/variantCaller'
GATK="${VARIANT_CALLER_DIR}/TVC/jar/GenomeAnalysisTK.jar"
REF_FASTA='/results/referenceLibrary/tmap-f3/hg19/hg19.fasta'

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

# $1: RUN1_DIR, $2: RUN2_DIR
# The RUN1_BAM and RUN2_BAM variabels will be used later.
function setupBAMs {
	# for TS v4.2, PTRIM.bam cannot be used as input to TVC.
	RUN1_BAM=`find ${1}/*.bam -maxdepth 0 -type f | grep -v "PTRIM"`
	RUN2_BAM=`find ${2}/*.bam -maxdepth 0 -type f | grep -v "PTRIM"`
	
	if [ "$CHR" != "" ]; then
		# basename gets only the nave of the progam out of the filepath.
		run1_bam_name=`basename $RUN1_BAM`
		run2_bam_name=`basename $RUN2_BAM`
		# Check to see if the index file exists. If it does, then samtools must have finished already before, and it was indexed.
		# If not, then start by getting on the specified chromosome from samtools
		if [ ! "`find ${1}/${CHR}_subset/${CHR}_${run1_bam_name}.bai -maxdepth 0 2>/dev/null`" ]; then
			rm -rf ${1}/${CHR}_subset 2>/dev/null
			mkdir -p ${1}/${CHR}_subset 2>/dev/null
			echo "Making RUN1_BAM chr subset: $RUN1_BAM" >> $log
			samtools view -b $RUN1_BAM  "$CHR" > ${1}/${CHR}_subset/${CHR}_${run1_bam_name}
		fi
		if [ ! "`find ${2}/${CHR}_subset/${CHR}_${run2_bam_name}.bai -maxdepth 0 2>/dev/null`" ]; then
			rm -rf ${2}/${CHR}_subset 2>/dev/null
			mkdir -p ${2}/${CHR}_subset 2>/dev/null
			echo "Making RUN2_BAM chr subset for: $RUN2_BAM" >> $log
			samtools view -b $RUN2_BAM  "$CHR" > ${2}/${CHR}_subset/${CHR}_${run2_bam_name}
		fi
		RUN1_BAM="${1}/${CHR}_subset/${CHR}_${run1_bam_name}"
		RUN2_BAM="${2}/${CHR}_subset/${CHR}_${run2_bam_name}"
	fi
}

# $1: the Run_Dir, $2, the Run_num
function setupVCF {
	if [ "$CHR" != "" ]; then
		if [ "`find ${1}/tvc*_out -maxdepth 0 -type d 2>/dev/null`" ]; then
			checkFiles "${1}/tvc*_out/TSVC_variants.vcf" 
			vcf="${1}/tvc*_out/TSVC_variants.vcf"
		else
			checkFiles "${1}/*.vcf"
			vcf=`find ${1}/*.vcf -type f | head -n 1`
		fi
		# what if there are multiple vcf files in the dir? Just take the first one it finds for now.
		grep "^#" $vcf > ${TEMP_DIR}/Run${2}.vcf
		# use grep to get only the specified chromosome out of the vcf file. -E: regex -P: perl regex
		grep -v "^#" $vcf | grep -P "^${CHR}\t" >> ${TEMP_DIR}/Run${2}.vcf
		bgzip -c ${TEMP_DIR}/Run${2}.vcf > ${TEMP_DIR}/Run${2}.vcf.gz 2>>${log}
		tabix -p vcf ${TEMP_DIR}/Run${2}.vcf.gz 2>>${log}
	# I need to check if the tvc_out folder is still there.
	elif [ "`find ${1}/tvc*_out -maxdepth 0 -type d 2>/dev/null`" ]; then
		#	use the files already here.
		# the vcf files are not here. Exit with a file not found error. # Maybe I could call the run TVC script instead?
		checkFiles "${1}/tvc*_out/TSVC_variants.vcf" 
		cp ${1}/tvc_out/TSVC_variants.vcf.gz ${TEMP_DIR}/Run${2}.vcf.gz
		cp ${1}/tvc_out/TSVC_variants.vcf.gz.tbi ${TEMP_DIR}/Run${2}.vcf.gz.tbi
	else
		checkFiles "${1}/*.vcf"
		# what if there are multiple vcf files in the dir? Just take the first one it finds for now.
		vcf=`find ${1}/*.vcf -type f -printf "%f\n" | head -n 1`
		#Compress the vcf files and index them
		bgzip -c ${1}/${vcf} > ${TEMP_DIR}/Run${2}.vcf.gz 2>>${log}
		tabix -p vcf ${TEMP_DIR}/Run${2}.vcf.gz 2>>${log}
	fi
}

# $1: RUN1_DIR $2: run_num
function subset_low_cov {
	if [ "`find ${1}/cov_full -maxdepth 0 -type d 2>/dev/null`" ]; then
		checkFiles "${1}/cov_full/*.amplicon.cov.xls"
		amp="${1}/cov_full/*.amplicon.cov.xls"
	else
		checkFiles "${1}/*.amplicon.cov.xls"
		amp=`find ${1}/*.amplicon.cov.xls -type f`
	fi
	# Remove the header, and then pipe that into awk to get the amplicons with only > 30x coverage. Write it to a BED file.
	tail -n +2 $amp | \
		awk -v cutoff="$AMP_COV_CUTOFF" 'BEGIN{FS=OFS="\t";} {if ($10 >= cutoff) { printf("%s\t%s\t%s\t%s\t%s\n", $1, $2 - 1, $3, $4, $5); }}' \
		> ${TEMP_DIR}/run${2}_subset.bed
}

# $1: the bam file to index
function checkBamIndex {
	if [ ! "`find ${1}.bai -maxdepth 0 2>/dev/null`" ]; then
		java -jar $BAM_INDEXER INPUT=${1} OUTPUT=${1}.bai >>$log 2>&1 #2>&1 #hides the output of picard-tools.
	fi	
}

# Run GATK depth of coverage on a PTRIM.bam file in order to get total bases covered.
# $1: the RUN_BAM file, $2: the Overlap_subset.bed file $3: the run_number
function runGATK {
	bam_file=$1
	checkBamIndex $bam_file
	mkdir ${TEMP_DIR}/gatk${3}_out 2>/dev/null
	java -jar $GATK \
		--input_file $bam_file \
		--analysis_type DepthOfCoverage \
		--reference_sequence $REF_FASTA \
		--intervals $2 \
		-o ${TEMP_DIR}/gatk${3}_out/Run${3}_Depths \
		>> $log 2>&1 \
		&
}

# $1 is the bam file to use to run TVC, $2: the JSON PARAMETERS file used for TVC. $3: is the run number
function runTVC {
	checkBamIndex $1
	mkdir ${TEMP_DIR}/tvc${3}_out 2>/dev/null
	# If the PTRIM.bam is already available, then use that to save time.
	# TVC uses the REF_FASTA file to call the variants first, and then intersects that with the --region-bed specified. Using the intersected_bed here would make no time saving difference
	${VARIANT_CALLER_DIR}/variant_caller_pipeline.py  \
		--input-bam $1 \
		--reference $REF_FASTA \
		--output-dir ${TEMP_DIR}/tvc${3}_out \
		--region-bed $BED \
		--parameters-file $2 \
		--hotspot-vcf ${TEMP_DIR}/final_Hotspot.vcf.gz \
		--postprocessed-bam=${TEMP_DIR}/tvc${3}_out/PTRIM.bam \
		--primer-trim-bed ${BED} \
		--bin-dir ${VARIANT_CALLER_DIR}  \
		>> $log 2>&1 \
		&
}

# $1: The name of the program running
function waitForJobsToFinish {
	# Wait for job to finish. If there is an error, Fail will be 1 and the error message will be displayed 
	FAIL=0
	for job in `jobs -p`; do
		wait $job || let "FAIL+=1"
	done
	if [ "$FAIL" == "0" ]; then
		echo "$OUTPUT_DIR $1 finished without problems at: `date`" 
		echo "$1 finished without problems at: `date`" >> $log
	else
		echo "-- ERROR: $1 had a problem. See ${log} for details --" 1>&2
		echo "-- ERROR: $1 had a problem. See ${log} for details --" >>$log
		exit 1
	fi
}

function usage {
cat << EOF
USAGE: bash QC_2Runs.sh 
If the output_dir specified already has the vcf files generated from QC, running TVC and GATK will be skipped. 
All options up to --gt_cutoffs are required.
	-h | --help
	-r | --run_dirs <path/to/run1_dir> <path/to/run2_dir> (Normal_Dir should always come before Tumor_Dir) (PTRIM.bam is used or generated. *.amplicon.cov.xls is used, and if the .vcf file is not in the run_dir, this script checks in the tvc_out dir)
	-o | --output_dir <path/to/output_dir> (Output dir should follow this pattern: sample1/QC/Run1vsRun2. This is important as QC_stats.py and QC_generateSheets.py split the two runs by 'vs', and use the dir before the QC dir as the sample name.)
	-b | --project_bed <path/to/project_bed> 
	-a | --amp_cov_cutoff <Amplicon_Coverage_Cutoff> (Cutoff for # of amplicon reads.) 
	-j | --json_paras <Json_parameters1> <Json_parameters2> (two json parameters files used by TVC)
	-d | --depth_cutoffs <Depth_Cutoff1> <Depth_Cutoff2> (Variants with depth < cutoff will be filtered out)
	-gt | --gt_cutoffs <WT_Cutoff1> <HOM1_Cutoff1> <WT_Cutoff2> <HOM1_Cutoff2>
	-cb | --cds_bed <path/to/CDS_bed> (This option should only be used if the user wants to run TVC using the Project bed, and then intersect the results with the CDS bed.)
	-sb | --subset_bed <path/to/subset_bed> (If the user want to subset out certain genes from the Project_Bed)
	-rgc | --run_gatk_cds (Normally, GATK is run using the subset of the beds specified above. If the cds_bed is specified, and this option is specified, GATK will be run twice.)
	-chr | --subset_chr <chr#> (The chromosome specified here (for example: chr1) will be used to subset the VCF and BAM files)
	-cl | --cleanup (Delete temp_files used to create the two Output VCF files)
	-cle | --cleanup_everything (Option not yet implemented: Delete everything but the log and the matched_variants.csv)
EOF
exit 8
}

#for arguments
if [ $# -lt 15 ]; then # Technically there should be more than 20 arguments specified by the user, but more useful error messages can be displayed below
	usage
fi

# Default Options
AMP_COV_CUTOFF=30 # The minimum amount of coverage each amplicon needs to have. Default is 30

RUNNING="Starting QC using these option: "
RUN_GATK_CDS="False"
CLEANUP="False"
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
		-r | --run_dirs)
			RUN1_DIR=$2
			RUN2_DIR=$3
			RUNNING="$RUNNING --run_dirs: $2 $3, "
			shift 3
			;;
		-o | --output_dir)
			OUTPUT_DIR=$2
			RUNNING="$RUNNING --output_dir: $2, "
			shift 2
			;;
		-b | --project_bed)
			BED=$2
			RUNNING="$RUNNING --project_bed: $2, "
			shift 2
			;;
		-a | --amp_cov_cutoff)
			AMP_COV_CUTOFF=$2
			RUNNING="$RUNNING --amp_cov_cutoff: $2, "
			shift 2
			;;
		-j | --json_paras)
			JSON_PARAS1=$2
			JSON_PARAS2=$3
			RUNNING="$RUNNING --json_paras: Json_paras1: $2 Json_paras2: $3, "
			shift 3
			;;
		-d | --depth_cutoffs) 
			DEPTH_CUTOFF1=$2
			DEPTH_CUTOFF2=$3
			RUNNING="$RUNNING --depth_cutoffs: Depth_cutoff1: $2  Depth_cutoff2: $3, "
			shift 3
			;;
		-gt | --gt_cutoffs)
			WT_CUTOFF1=$2
			HOM_CUTOFF1=$3
			WT_CUTOFF2=$4
			HOM_CUTOFF2=$5
			RUNNING="$RUNNING --gt_cutoffs: WT_1:$2 HOM_1:$3 WT_2:$4 HOM_2:$5, "
			shift 5
			;;

		-sb | --subset_bed)
			SUBSET_BED=$2
			RUNNING="$RUNNING --subset_bed: $2, "
			shift 2
			;;
		-cb | --cds_bed)
			CDS_BED=$2
			RUNNING="$RUNNING --cds_bed: $2, "
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
		-cl | --cleanup)
			CLEANUP="True"
			RUNNING="$RUNNING --cleanup "
			shift
			;;
		-*)
			printf >&2 'WARNING: Unknown option (ignored): %s\n' "$1"
			shift
			;;
		*)  # no more options. Stop while loop
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
echo "$RUNNING"

# Check to make sure the files actually exist
# Add the .amplicon.cov.xls files to check they are available for each run. Otherwise exit.
files=("$RUN1_DIR" "$RUN2_DIR" "${RUN1_DIR}/*.bam" "${RUN2_DIR}/*.bam" \
	"$BED" "$CDS_BED" "$SUBSET_BED" "$JSON_PARAS1" "$JSON_PARAS2" "$GATK" "$REF_FASTA" "$BAM_INDEXER" "$VARIANT_CALLER_DIR")
checkFiles $files

# ------------------------------------------------------------------------
# ------------ IF THERE ARE NO FILE ERRORS, START HERE -------------------
# ------------------------------------------------------------------------

mkdir -p $OUTPUT_DIR 2>/dev/null
TEMP_DIR="${OUTPUT_DIR}/temp_files"
mkdir $TEMP_DIR 2>/dev/null #This directory will hold all of the temporary files
log="${OUTPUT_DIR}/log.txt"

# If QC has already been run using the options specified, then no need to re-run it.
if [ "`find ${OUTPUT_DIR}/VCF1${CHR}_Final.vcf -type f 2>/dev/null`" -a "`find ${OUTPUT_DIR}/VCF2${CHR}_Final.vcf -type f 2>/dev/null`" \
	-a "`find ${OUTPUT_DIR}/Run1${CHR}_Depths -maxdepth 0 -type f 2>/dev/null`" -a "`find ${OUTPUT_DIR}/Run2${CHR}_Depths -maxdepth 0 -type f 2>/dev/null`" ]; then
	echo "$OUTPUT_DIR has already been QCd. Skipping QC and running QC_Match_VCFs.py"
else
	echo "$OUTPUT_DIR Creating QC tables at `date`"
	#echo "For progress and results, see $log"
	echo "Creating QC tables for $OUTPUT_DIR at `date`" >$log
	echo "----------------------------------------------" >>$log
	
	# this function finds the PTRIM.bam or bam file for each run and subsets out the chr if specified 
	# The RUN1_BAM and RUN2_BAM variables are set up in this function
	setupBAMs $RUN1_DIR $RUN2_DIR

	# this function finds the vcf files and subsets out the chr if specified.
	setupVCF $RUN1_DIR 1
	setupVCF $RUN2_DIR 2
		
	# Get the unique and common variants to each vcf file.
	# I'm not sure if I actually have to do this
	echo "--- vcf-isec (column name warnings are fine) ---" >>${log}
	vcf-isec -f -c ${TEMP_DIR}/Run1.vcf.gz ${TEMP_DIR}/Run2.vcf.gz > ${TEMP_DIR}/VCF1_unique.vcf 2>>${log}
	vcf-isec -f -c ${TEMP_DIR}/Run2.vcf.gz ${TEMP_DIR}/Run1.vcf.gz > ${TEMP_DIR}/VCF2_unique.vcf 2>>${log}
	vcf-isec -f ${TEMP_DIR}/Run1.vcf.gz ${TEMP_DIR}/Run2.vcf.gz > ${TEMP_DIR}/VCF1_VCF2_common.vcf 2>>${log}
	
	# Merge the two compressed VCF files and remove the duplicates
	echo "--- vcf-merge ---" >>${log}
	vcf-merge ${TEMP_DIR}/Run1.vcf.gz ${TEMP_DIR}/Run2.vcf.gz --remove-duplicates > ${TEMP_DIR}/merged.vcf 2>>${log}
	

	# Function to keep only the amplicons that have depth coverage >= what the user specified.
	subset_low_cov $RUN1_DIR 1
	subset_low_cov $RUN2_DIR 2
	
	echo "--- Creating subset bed files (where amp cov > $AMP_COV_CUTOFF) ---" >>${log}
	# Now intersect the two subset bed files output by the subset_low_cov function
	bedtools intersect -a ${TEMP_DIR}/run1_subset.bed -b ${TEMP_DIR}/run2_subset.bed -u -f 0.99 > ${TEMP_DIR}/low_cov_subset.bed 2>>$log
	intersected_bed="low_cov_subset.bed"
	
	# Intersect the low_cov_subset.bed with the first bed specified. This shouldn't normally be needed, but it is a good precaution.
	bed_name=`basename $BED`
	bedtools intersect -a ${TEMP_DIR}/${intersected_bed} -b ${BED} -u -f 0.99 > ${TEMP_DIR}/intersect_${bed_name} 2>>$log
	intersected_bed="intersect_${bed_name}"

	# interstect the subset.bed file with the specified subset bed files
	# if RUN_GATK_CDS is true, then the cds bed will not be subset out here so that all of the variants will be available, and  GATK can be run twice.
	if [ "$CDS_BED" != "" -a "$RUN_GATK_CDS" != "True" ]; then
		subset1_name=`basename $CDS_BED`
		# -f .99 option is not used here because the begin and end pos of the CDS region will not match up with the project bed file (it has intronic regions)
		bedtools intersect -a ${TEMP_DIR}/${intersected_bed} -b ${CDS_BED} > ${TEMP_DIR}/intersect1_${subset1_name} 2>>$log
		intersected_bed="intersect1_${subset1_name}"
	fi
	if [ "$SUBSET_BED" != "" ]; then
		subset2_name=`basename $SUBSET_BED`
		bedtools intersect -a ${TEMP_DIR}/${intersected_bed} -b ${SUBSET_BED} -u -f 0.99> ${TEMP_DIR}/intersect2_${subset2_name} 2>>$log
		intersected_bed="intersect2_${subset2_name}"
	fi
	
	# And then intersect that bed file with the merged vcf file to get only the variants that have > 30x coverage and that are found in the bed files specified.
	bedtools intersect -a ${TEMP_DIR}/merged.vcf -b ${TEMP_DIR}/${intersected_bed} > ${TEMP_DIR}/merged_intersect.vcf 2>>$log
	
	# Filtering the Hotspot before vs after did not make a difference. Will filter before.
	# Remove the variants that have a multi-allelic call (i.e. A,G). Bonnie thinks they are a sequencing artifact.
	# if FAO + FRO is < Depth_Cutoff, that variant is removed
	echo "--- Filtering Variants (multi-allelic calls, and where FAO+FRO is < $DEPTH_CUTOFF1 in VCF1 and < $DEPTH_CUTOFF2 in VCF2 ---" >>${log}
	python ${QC_SCRIPTS}/QC_Filter_Var.py ${TEMP_DIR}/merged_intersect.vcf ${TEMP_DIR}/filtered_merged_intersect.vcf --merged $DEPTH_CUTOFF1 $DEPTH_CUTOFF2 >> $log 2>&1
	if [ "$?" != "0" ]
	then
		echo "ERROR: $OUTPUT_DIR had a problem filtering variants with QC_Filter_Var.py... See $log for details" 1>&2
		exit 1
	fi
	
	echo "--- Creating the hotspot file ---" >>${log}
	# Create the hotspot file that has the variants for both of the runs.
	tvcutils prepare_hotspots -v ${TEMP_DIR}/filtered_merged_intersect.vcf -o ${TEMP_DIR}/final_Hotspot.vcf -r $REF_FASTA -s on -a on >>$log
	
	bgzip -c ${TEMP_DIR}/final_Hotspot.vcf > ${TEMP_DIR}/final_Hotspot.vcf.gz
	tabix -p vcf ${TEMP_DIR}/final_Hotspot.vcf.gz

	if [ ! "`find ${OUTPUT_DIR}/VCF1${CHR}_Final.vcf -type f 2>/dev/null`" -o ! "`find ${OUTPUT_DIR}/VCF2${CHR}_Final.vcf -type f 2>/dev/null`" ]; then
		#The Hotspot file should be good to go now. Run TVC on the two original BAM files now using the awesome Hotspot file we created!
		echo "Running TVC using the generated hotspot file" >>$log
		echo "----------------------------------------------" >>$log
		runTVC $RUN1_BAM $JSON_PARAS1 1${CHR}
		runTVC $RUN2_BAM $JSON_PARAS2 2${CHR}
		# after running the TVC result above, the TSVC_variants.vcf file created will include not only hotspot calls, but pretty much everything we filtered out prior to generating the final hotspot file. 
		#because TVC is actually run twice (1) as though there were no hotspot files defined (2) only using hotspot file. The final TSVC_variants.vcf reported is a combination of (1) and (2)  
		
		# wait for TVC to finish. Exit if TVC has a problem
		waitForJobsToFinish "TVC${CHR}"
	
		# Now, intersect the variants to the hotspot file used as input in generating the final round of TSVC_variants.vcf. 
		# This way, we will match the no of variants in both runs and we will be able to proceed with generating the QC table (if the no of variants differed in the 2 runs, we would not be able to compare apples to apples)
		# get only the variants that are listed in the Hotspot file
		echo "--- vcf-isec to get only variants listed in the Hotspot file (column name warnings are fine) ---" >>${log}
		vcf-isec -f ${TEMP_DIR}/tvc1${CHR}_out/TSVC_variants.vcf.gz ${TEMP_DIR}/final_Hotspot.vcf.gz > ${TEMP_DIR}/VCF1_Intersect_Hotspot.vcf 2>>${log}
		vcf-isec -f ${TEMP_DIR}/tvc2${CHR}_out/TSVC_variants.vcf.gz ${TEMP_DIR}/final_Hotspot.vcf.gz > ${TEMP_DIR}/VCF2_Intersect_Hotspot.vcf 2>>${log}
		
		# Finally, if the user specified a subset chr, put that in the name of the final VCF file.
		VCF1_FINAL="${OUTPUT_DIR}/VCF1${CHR}_Final.vcf"
		VCF2_FINAL="${OUTPUT_DIR}/VCF2${CHR}_Final.vcf"
		echo "--- removing duplicates entries---" >>${log}
		# I keep trying to think of ways to shortcut around having to do this extra filtering, but Ozlem is doing it all
		# because there were special cases where these steps were necessary. So I'll keep them.
		# We need to remove the duplicate entries again.
		python ${QC_SCRIPTS}/QC_Filter_Var.py ${TEMP_DIR}/VCF1_Intersect_Hotspot.vcf $VCF1_FINAL --single $DEPTH_CUTOFF1 >>$log 2>&1
		python ${QC_SCRIPTS}/QC_Filter_Var.py ${TEMP_DIR}/VCF2_Intersect_Hotspot.vcf $VCF2_FINAL --single $DEPTH_CUTOFF2 >>$log 2>&1
	fi

	# No need for another if statement here. If both TVC and GATK files already existed, then this part would've already been skipped
	# Run GATK. Not needed for hotspot creation and such, but it will be used to find the total # of eligible bases later on.
	runGATK ${TEMP_DIR}/tvc1${CHR}_out/PTRIM.bam ${TEMP_DIR}/${intersected_bed} 1${CHR}
	runGATK ${TEMP_DIR}/tvc2${CHR}_out/PTRIM.bam ${TEMP_DIR}/${intersected_bed} 2${CHR}
	
	waitForJobsToFinish "GATK${CHR}"
	mv ${TEMP_DIR}/gatk1${CHR}_out/Run1${CHR}_Depths ${TEMP_DIR}/gatk2${CHR}_out/Run2${CHR}_Depths ${OUTPUT_DIR}

fi

		 	# ------------------------------------------------------------------
		 	# ----------------------- FIX FOR CDS REGION -----------------------
		 	# ------------------------------------------------------------------
if [ "$RUN_GATK_CDS" == "True" ]; then
	if [ "`find ${OUTPUT_DIR}/VCF1${CHR}_CDS_Final.vcf -type f 2>/dev/null`" -a "`find ${OUTPUT_DIR}/VCF2${CHR}_CDS_Final.vcf -type f 2>/dev/null`" \
		-a "`find ${OUTPUT_DIR}/Run1${CHR}_CDS_Depths -maxdepth 0 -type f 2>/dev/null`" -a "`find ${OUTPUT_DIR}/Run2${CHR}_CDS_Depths -maxdepth 0 -type f 2>/dev/null`" ]; then
		echo "$OUTPUT_DIR CDS region has already been QCd. Skipping QC and running QC_Match_VCFs.py"
	elif [ ! "`find ${TEMP_DIR}/tvc1${CHR}_out/PTRIM.bam -maxdepth 0 2>/dev/null`" -o ! "`find ${TEMP_DIR}/tvc1${CHR}_out/PTRIM.bam -maxdepth 0 2>/dev/null`" ]; then
		echo "${TEMP_DIR} does not have the necessary PTRIM.bam files. QC would have to be restarted (i.e. delete $OUTPUT_DIR and start over)."
	else
		echo "$OUTPUT_DIR Creating CDS QC tables at `date`"
		echo "Creating CDS QC tables for $OUTPUT_DIR at `date`" >>$log
		echo "----------------------------------------------" >>$log

		setupBAMs $RUN1_DIR $RUN2_DIR

		# First, make sure we have the right bed files 
		if [ ! "`find ${TEMP_DIR}/low_cov_subset.bed -type f 2>/dev/null`" ]; then
			# Function to keep only the amplicons that have depth coverage > what the user specified.
			subset_low_cov $RUN1_DIR 1
			subset_low_cov $RUN2_DIR 2
			echo "--- Creating subset bed files (where amp cov > $AMP_COV_CUTOFF) ---" >>${log}
			# Now intersect the two subset bed files
			bedtools intersect -a ${TEMP_DIR}/run1_subset.bed -b ${TEMP_DIR}/run2_subset.bed -u -f 0.99 > ${TEMP_DIR}/low_cov_subset.bed 2>>$log
		fi
		intersected_bed="low_cov_subset.bed"
	
		bed_name=`basename $BED`
		if [ ! "`find ${TEMP_DIR}/intersect_${bed_name} -type f 2>/dev/null`" ]; then
			bedtools intersect -a ${TEMP_DIR}/${intersected_bed} -b ${BED} -u -f 0.99 > ${TEMP_DIR}/intersect_${bed_name} 2>>$log
		fi
		intersected_bed="intersect_${bed_name}"

		if [ "$SUBSET_BED" != "" ]; then
			subset2_name=`basename $SUBSET_BED`
			if [ ! "`find ${TEMP_DIR}/intersect2_${subset2_name} -type f 2>/dev/null`" ]; then
				bedtools intersect -a ${TEMP_DIR}/${intersected_bed} -b ${SUBSET_BED} -u -f 0.99 > ${TEMP_DIR}/intersect2_${subset2_name} 2>>$log
			fi
			intersected_bed="intersect2_${subset2_name}"
		fi

		# Now intersect the available bed file with the CDS bed.
		bedtools intersect -a ${TEMP_DIR}/${intersected_bed} -b ${CDS_BED} > ${TEMP_DIR}/CDS_subset.bed 2>>$log
		
		# Run GATK. Not needed for hotspot creation and such, but it will be used to find the total # of eligible bases later on.
		runGATK ${TEMP_DIR}/tvc1${CHR}_out/PTRIM.bam ${TEMP_DIR}/${intersected_bed} 1${CHR}
		runGATK ${TEMP_DIR}/tvc2${CHR}_out/PTRIM.bam ${TEMP_DIR}/${intersected_bed} 2${CHR}
	
		waitForJobsToFinish "CDS_GATK${CHR}"
		mv ${TEMP_DIR}/gatk1${CHR}_CDS_out/Run1${CHR}_CDS_Depths ${TEMP_DIR}/gatk2${CHR}_CDS_out/Run2${CHR}_CDS_Depths ${OUTPUT_DIR}
	
		# And then intersect that bed file with the merged vcf file to get only the variants that have > 30x coverage.
		bedtools intersect -a ${OUTPUT_DIR}/VCF1${CHR}_Final.vcf -b ${TEMP_DIR}/CDS_subset.bed > ${OUTPUT_DIR}/VCF1${CHR}_CDS_Final.vcf 2>>$log
		bedtools intersect -a ${OUTPUT_DIR}/VCF2${CHR}_Final.vcf -b ${TEMP_DIR}/CDS_subset.bed > ${OUTPUT_DIR}/VCF2${CHR}_CDS_Final.vcf 2>>$log
		# get only the variants that are listed in the Hotspot file
	fi
	
	total_elibigle_bases=`paste ${OUTPUT_DIR}/Run1${CHR}_CDS_Depths ${OUTPUT_DIR}/Run2${CHR}_CDS_Depths | \
		awk -v cutoff1=$DEPTH_CUTOFF1 -v cutoff2=$DEPTH_CUTOFF2 '{ if ($2 >= cutoff1 && $6 >= cutoff2) printf "."}' | wc -c`
	if [ "$total_eligible_bases" == "0" ]; then
		echo "ERROR: total_eligible_bases cannot =  0. ${OUTPUT_DIR}/Run1_Depths probably not found"
		exit 1
	else
		# This script takes the two VCF files generated from running TVC using the same hotspot file, matches them and outputs the info to the two csvs.
		python ${QC_SCRIPTS}/QC_Match_VCFs.py \
			${OUTPUT_DIR}/VCF1${CHR}_CDS_Final.vcf $WT_CUTOFF1 $HOM_CUTOFF1 \
			${OUTPUT_DIR}/VCF2${CHR}_CDS_Final.vcf $WT_CUTOFF2 $HOM_CUTOFF2 \
			$total_elibigle_bases \
			${OUTPUT_DIR}/matched_variants${CHR}_CDS.csv \
			${QC_MASTER_OUT}
		if [ "$?" != "0" ]; then
			echo "ERROR: on CDS $OUTPUT_DIR QC_Match_VCFs.py had a problem!! " 1>&2
			exit 
		fi
	fi
fi
		 #----------------------- FIX FOR CDS REGION END -----------------------


# Use awk to get the total_eligible_bases by getting only the base positions from both GATK outputs that have greater than the cutoff depth.
total_elibigle_bases=`paste ${OUTPUT_DIR}/Run1${CHR}_Depths ${OUTPUT_DIR}/Run2${CHR}_Depths | \
	awk -v cutoff1=$DEPTH_CUTOFF1 -v cutoff2=$DEPTH_CUTOFF2 '{ if ($2 >= cutoff1 && $6 >= cutoff2) printf "."}' | wc -c`
if [ "$total_eligible_bases" == "0" ]; then
	echo "ERROR: total_eligible_bases cannot =  0. ${OUTPUT_DIR}/Run1${CHR}_Depths probably not found"
	exit 1
else
	# This script takes the two VCF files generated from running TVC using the same hotspot file, matches them and outputs the info to the two csvs.
	python ${QC_SCRIPTS}/QC_Match_VCFs.py \
		${OUTPUT_DIR}/VCF1${CHR}_Final.vcf $WT_CUTOFF1 $HOM_CUTOFF1 \
		${OUTPUT_DIR}/VCF2${CHR}_Final.vcf $WT_CUTOFF2 $HOM_CUTOFF2 \
		$total_elibigle_bases \
		${OUTPUT_DIR}/matched_variants${CHR}.csv \
		${QC_MASTER_OUT} # This last csv is appended to by each QC combination. Will be used to generate the QC spreadsheet.
	if [ "$?" != "0" ]; then
		echo "ERROR: $OUTPUT_DIR QC_Match_VCFs.py had a problem!! " 1>&2
		exit 
	fi
fi

# Cleanup and done.
if [ "$CLEANUP" == "True" ]; then
	rm -rf ${TEMP_DIR}
fi

echo "$OUTPUT_DIR Finished QC." 
echo "----------------------------------------------"
echo "$OUTPUT_DIR Finished QC." >>$log
