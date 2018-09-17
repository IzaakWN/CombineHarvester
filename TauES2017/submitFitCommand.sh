#! /bin/bash

printf "###############################################\n"
printf "##   Run MadGraph for sample %-16s##\n" "$1"
printf "###############################################\n"

echo ">>> arguments are \"$@\""
#NTOYS=100
#while getopts c:d:i:M:N:n:s: option; do case "${option}" in
#  c) NCORES=${OPTARG};;
#  d) WORKSPACE=${OPTARG};;
#  M) MASS=${OPTARG};;
#  N) NTOYS=${OPTARG};;
#  n) JOBNAME=${OPTARG};;
#  s) SEED=${OPTARG};;
#esac done

#[ ! $WORKSPACE ] && ">>> ERROR: No datacard given!" && exit 1
#[ ! $JOBNAME   ] && ">>> ERROR: No jobname given!" && exit 1
#[ ! $MASS      ] && ">>> ERROR: No mass given!" && exit 1
#[ ! $SEED      ] && SEED=`date +%s%N | cut -b11-18`
#[   $NCORES    ] && EXTRAOPTS="--parallel $NCORES "

#OUTPUT="higgsCombine.*.root"
#LOGFILES="myout.txt myerr.txt"
#JOBDIR="submitToys"
CMSSWDIR="/shome/ineuteli/analysis/CMSSW_8_1_0"
BASEDIR="$CMSSWDIR/src/CombineHarvester/TauES2017"
WORKDIR="$BASEDIR" #"/scratch/$USER/$JOBDIR/$JOBNAME"
#OUTDIR="$BASEDIR/gof/jobs"
REPORTDIR="$BASEDIR/$JOBDIR"



##### JOB PARAMETERS #####################################################################

cat <<EOF

###########################################
##            JOB PARAMETERS:            ##
###########################################
  \$@=$@
EOF

mkdir -p /shome/ineuteli/analysis/CMSSW_8_1_0/src/CombineHarvester/TauES2017/submitFitCommand
#$ -e /shome/ineuteli/analysis/CMSSW_8_1_0/src/CombineHarvester/TauES2017/submitFitCommand
#$ -o /shome/ineuteli/analysis/CMSSW_8_1_0/src/CombineHarvester/TauES2017/submitFitCommand

DATE_START=`date +%s`
echo "Job started at " `date`
function peval { echo ">>> $@"; eval "$@"; }



##### SET ENVIRONMENT ####################################################################

#if [ -e "$WORKDIR" ]; then
#   echo "ERROR: WORKDIR ($WORKDIR) already exists!" >&2
#   peval "ls $WORKDIR" >&2
#   exit 1
#fi
#mkdir -p $WORKDIR
#if [ ! -d $WORKDIR ]; then
#   echo "ERROR: Failed to create workdir ($WORKDIR)! Aborting..." >&2
#   exit 1
#fi
#mkdir -p $OUTDIR
#if [ ! -d $OUTDIR ]; then
#   echo "ERROR: Failed to create output dir ($OUTDIR)! Aborting..." >&2
#   exit 1
#fi

cat <<EOF

###########################################
##             JOB SETTINGS:             ##
###########################################
  \$BASEDIR=$BASEDIR
  \$WORKDIR=$WORKDIR
  \$OUTDIR=$OUTDIR
  \$REPORTDIR=$REPORTDIR
EOF



##### MAIN FUNCTIONALITY CODE ############################################################

echo " "
echo "###########################################"
echo "##         MY FUNCTIONALITY CODE         ##"
echo "###########################################"

echo ">>> setting up CMSSW"
peval "source $VO_CMS_SW_DIR/cmsset_default.sh" || exit 1
peval "export SCRAM_ARCH=slc6_amd64_gcc530" || exit 1
peval "cd $CMSSWDIR/src"  || exit 1
eval `scramv1 runtime -sh`
if test $? -ne 0; then
   echo "ERROR: Failed to source scram environment" >&2
   exit 1
fi

# MAIN code
cd "$WORKDIR"
peval "./doFit_TES.sh $@"



##### RETRIEVAL OF OUTPUT FILES AND CLEANING UP ##########################################

cd $WORKDIR
if [ 0"$DBG" -gt 0 ]; then
    echo " " 
    echo "########################################################"
    echo "##   OUTPUT WILL BE MOVED TO \$RESULTDIR and \$OUTDIR   ##"
    echo "########################################################"
    echo "  \$RESULTDIR=$RESULTDIR"
    echo "  \$REPORTDIR=$REPORTDIR"
    echo "  \$PWD=$PWD"
    peval "-maxdepth 2 -ls"
    peval "ls $OUTDIR"
fi

## LOG
#if [ -e $LOGFILES ]; then
#  mkdir -p $REPORTDIR
#  if [ ! -e "$REPORTDIR" ]; then
#    echo "ERROR: Failed to create $REPORTDIR ...Aborting..." >&2
#    exit 1
#  fi
#  for n in $LOGFILES; do
#    NEWLOGFILE="$REPORTDIR/${JOBNAME}.${JOB_ID}.${n}"
#    echo ">>> copying $n to $NEWLOGFILE"
#    if test ! -e $WORKDIR/$n; then
#      echo "WARNING: Cannot find output file $WORKDIR/$n. Ignoring it" >&2
#    else
#      cp -a $WORKDIR/$n $NEWLOGFILE
#      [ $? -ne 0 ] && echo "ERROR: Failed to copy $WORKDIR/$n to $NEWLOGFILE" >&2
#    fi
#  done
#fi

## MAIN output
#for f in $OUTPUT; do
#  peval "cp $f $OUTDIR/"
#  [ $? -ne 0 ] && echo "ERROR: Failed to copy $f to $OUTDIR" >&2
#done
#rm -rf $WORKDIR



##########################################################################################

DATE_END=`date +%s`
RUNTIME=$((DATE_END-DATE_START))
printf "\n#####################################################"
printf "\n    Job finished at %s" "$(date)"
printf "\n    Wallclock running time: %02d:%02d:%02d" "$(( $RUNTIME / 3600 ))" "$(( $RUNTIME % 3600 /60 ))" "$(( $RUNTIME % 60 ))"
printf "\n#####################################################\n\n"

exit 0
