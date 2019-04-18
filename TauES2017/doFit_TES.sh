#! /bin/bash
# Author: Izaak Neutelings (January 2018)
# https://twiki.cern.ch/twiki/bin/viewauth/CMS/SWGuideHiggsAnalysisCombinedLimit
# CombineHarvester/CombinePdfs/python/TagAndProbeModel.py
START=`date +%s`

# SET INPUT
ANALYSIS="ztt"              # process
CHANNELS="mt #et"           # channels
DMS="DM0 DM1 DM10 DM11"     # decay mode categories
VARS="m_2 m_vis"            # variables
POI="tes"                   # parameter of interest
DYXS="CMS_ztt_zjXsec_13TeV" # nuissance parameter of DY cross section
WJXS="CMS_ztt_wNorm_13TeV"  # nuissance parameter of WJ normalization
RANGE="0.940,1.060"         # range of TES
DYRANGE="0.50,1.20"         # range of DY cross section
WJRANGE="0.50,1.50"         # range of WJ normalization
SEED="123456"               # random seed
CHECKS="0.980 0.990 1.000 1.010 1.020" # values to check pre-/post-fit #0.960 0.970 0.980 0.990 1.000 1.010 1.020 1.030
NPOINTS="121"               # number of points for grid fit
TOL="0.2"                   # tolerance
NTOYS="1000"                # number of toys
TAGS="_mtlt50"              # tag in datacards (for selections)
EXTRATAG=""                 # extra tag in datacards (for checks)

# DIRS
DIR_DATACARDS="input"
DIR="./" #"/shome/ineuteli/analysis/CMSSW_8_1_0/src/CombineHarvester/TauES2017"

# USER INPUT
VERBOSITY=0
BREAKDOWN=0
BIASTEST=0
DOFIT=1
IMPACTS=0
POSTFIT=0
MDF=0
HARVESTER=1
FIRST=0
LAST=0
ASIMOV=0
while getopts "AbBc:d:e:F:hiL:Mm:N:no:pPt:vs:" option; do case "${option}" in
  A) ASIMOV=1;;
  b) BREAKDOWN=1;;
  B) BIASTEST=1;;
  c) CHECKS=`echo ${OPTARG} | tr ',' ' '`;;
  d) DMS=`echo ${OPTARG} | tr ',' ' '`;;
  F) FIRST=${OPTARG};;
  L) LAST=${OPTARG};;
  h) HARVESTER=0;;
  i) IMPACTS=1;;
  M) MDF=1;;
  m) VARS=`echo ${OPTARG} | tr ',' ' '`;;
  N) NTOYS=${OPTARG};;
  o) VARS=${OPTARG};;
  t) TAGS=`echo ${OPTARG} | tr ',' ' '`;;
  e) EXTRATAG=${OPTARG};;
  s) SEED=${OPTARG};;
  n) DOFIT=0;;
  p) POSTFIT=1;;
  v) VERBOSITY=1;;
esac done

# SCRIPTS
HARV="./harvestDatacards_TES.py"
PLOT="./plotParabola_TES.py"
WORK="text2workspace.py" #../../../HiggsAnalysis/CombinedLimit/scripts/text2workspace.py"
PULL="../../HiggsAnalysis/CombinedLimit/test/diffNuisances.py"
PPULL="pulls.py"
COMB="combineCards" #../../../HiggsAnalysis/CombinedLimit/scripts/combineCards.py"

# OPTIONS
set -o pipefail # for exit after tee
[ $MDF -gt 0 ] && POINTS=61 && RANGE="0.970,1.030"
POINTA=`echo $RANGE | grep -Po '\d+\.?\d*(?=,)'`
CHECKS=`echo $CHECKS | grep -Po '\b(?<!#)\d+\.\d+\b' | xargs`
VARS=`echo $VARS | grep -Po '\b(?<!#)\w+\b' | xargs`
DMS=`echo $DMS | grep -Po '\b(?<!#)\w+\b' | xargs`
SAVE="--saveSpecifiedNuis all" #${DYXS},${WJXS},CMS_eff_t,CMS_eff_m,CMS_ztt_shape_jetTauFake_13TeV,CMS_ztt_rate_jetTauFake_13TeV" #--saveWithUncertainties
ALGO="--algo=grid --points ${NPOINTS} --alignEdges=1" # --saveWorkspace --saveFitResult
#POI_OPTS="--redefineSignalPOIs ${POI},${DYXS} --setParameterRanges ${POI}=${RANGE}:${DYXS}=${DYRANGE} -P tes --floatOtherPOIs 1 $SAVE"
#POI_OPTS="--redefineSignalPOIs ${POI} --setParameterRanges ${POI}=${RANGE}:${DYXS}=${DYRANGE} --setParameters ${POI}=1,${DYXS}=1,r=1 --freezeParameters r --floatParameters ${DYXS} $SAVE"
#POI_OPTS="--redefineSignalPOIs ${POI} --setParameters ${POI}=1,${DYXS}=1 --setParameterRanges ${POI}=${RANGE}:${DYXS}=${DYRANGE} --floatParameters ${DYXS} $SAVE"
POI_OPTS="-P ${POI} --setParameterRanges ${POI}=${RANGE} -m 90 --setParameters r=1 --freezeParameters r " # --setParameters r=1 --freezeParameters r #--redefineSignalPOIs ${POI}
FIT_OPTS="--robustFit=1 --setRobustFitAlgo=Minuit2 --setRobustFitStrategy=0 --setRobustFitTolerance=${TOL}" #--preFitValue=1.
XRTD_OPTS="--X-rtd FITTER_NEW_CROSSING_ALGO --X-rtd FITTER_NEVER_GIVE_UP --X-rtd FITTER_BOUND" #--X-rtd FITTER_DYN_STEP
CMIN_OPTS="--cminFallbackAlgo Migrad,0:0.5 --cminFallbackAlgo Migrad,0:1.0 --cminPreScan" # --cminPreFit 1 --cminOldRobustMinimize 0"
HARV_OPTS="--shift-range $RANGE -o $VARS -d $DMS "
[ $ASIMOV -gt 0 ] && FIT_OPTS+=" -t -1"
[ $MDF -gt 0 ] && HARV_OPTS+="--multiDimFit " && DMS="MDF"
[ "$TAGS" ] && HARV_OPTS+="--tag $TAGS "
[ $EXTRATAG ] && HARV_OPTS+="--extra-tag $EXTRATAG "
[ $VERBOSITY -gt 0 ] && HARV_OPTS+="-v "



# MAIN ROUTINE
function main {
  
  cd $DIR
  ensureDir "log"
  ensureDir "postfit"
  ensureDir "impacts"
  ensureDir "biastest"
  ensureDir "biastest/log"
  ensureDir "toys"
  echo
  
  # HARVEST
  if [ $HARVESTER -gt 0 ]; then
    header "Harvest datacards"
    peval "python $HARV $HARV_OPTS" || exit 1
  fi
  cd "$DIR/output"
  
  # LOOP over tags
  for tag in $TAGS; do
    [[ $tag == "#"* ]] && continue
    
    # LOOP over channels
    for channel in $CHANNELS; do
      [[ $channel == "#"* ]] && continue
      
      # LOOP over variables
      for var in $VARS; do
        [[ $var == "#"* ]] && continue
        [ $var == "m_vis" ] && [[ $tag == "_"*"_0p"* ]] && continue
        [ $var == "m_2"   ] && [[ $tag == *"_85"*    ]] && continue
        [ $var == "m_2"   ] && [[ $tag == *"_45"*    ]] && continue
        
        # LOOP over DMS
        for dm in $DMS; do
            [[ $dm == "#"* ]] && continue
            [ $var == "m_2" -a $dm = "DM0" ] && continue
            [ $dm == "DM11" ] && [[ $tag != *"newDM"* ]] && continue
            header "${channel}: combine var $var for $dm"
            
            # INPUT
            BINLABEL="${channel}_${var}-${dm}${tag}${EXTRATAG}-13TeV"
            DATACARD="${ANALYSIS}_${BINLABEL}.txt"
            WORKSPACE="${ANALYSIS}_${BINLABEL}.root"
            LOG="log/${ANALYSIS}_${BINLABEL}.log"
            TOY_OPTS=""
            [ $HARVESTER -gt 0 -o $DOFIT -gt 0 ] && echo `date` > ../$LOG
            
            # COMBINE CARDS for MDF
            if [ $MDF -gt 0 ]; then
              NDMS=0
              POI_OPTS=""
              RANGES_DM=""
              DATACARD_DMS="" #"${ANALYSIS}_${channel}_${var}-DM*${tag}${EXTRATAG}_MDF-13TeV.txt"
              for dm2 in DM0 DM1 DM10 DM11; do
                [ $var == "m_2" -a $dm2 = "DM0" ] && continue
                [ $dm2 == "DM11" ] && [[ $tag != *"newDM"* ]] && continue
                DATACARD_DM="${ANALYSIS}_${channel}_${var}-${dm2}${tag}${EXTRATAG}_MDF-13TeV.txt"
                [ ! -e $DATACARD_DM ] && continue
                NDMS=$((NDMS+1))
                POI_OPTS+="-P tes_${dm2} "
                [ "$RANGES_DM" ] && RANGES_DM+=":"
                RANGES_DM+="tes_${dm2}=${RANGE}"
                [ "$DATACARD_DMS" ] && DATACARD_DMS+=" "
                DATACARD_DMS+="${dm2}=$DATACARD_DM "
              done
              if [ $NDMS -lt 2 ]; then
                echo "ERROR! Did not find enough DMs cards ($NDMS) to combine!"
                continue
              fi 
              POINTS=`echo "${POINTS}^${NDMS}" | bc`
              ALGO="--algo=grid --points $POINTS --alignEdges=1"
              POI_OPTS+="--setParameterRanges $RANGES_DM -m 90"
              if [ $LAST -gt 0 ]; then
                ALGO+=" --firstPoint $FIRST --lastPoint $LAST"
                BINLABEL+="_p${FIRST}-${LAST}"
                [ $HARVESTER -lt 1 -a ! -e $DATACARD ] && echo ">>> $DATACARD does not exist (yet?)! Waiting 30 seconds..." && sleep 30
              fi
              [ $HARVESTER -gt 0 ] && { peval "combineCards.py $DATACARD_DMS > $DATACARD" 2>&1 | tee -a ../$LOG || exit 1; }
            fi
            
            # WORKSPACE
            if [ $HARVESTER -gt 0 ]; then
              peval "text2workspace.py $DATACARD -o $WORKSPACE" 2>&1 | tee -a ../$LOG || exit 1
            fi
            
            # ASIMOV
            if [ $ASIMOV -gt 0 ]; then
              tes="1.000"
              POI_OPTS3="--setParameters ${POI}=${tes} --freezeParameters ${POI} --expectSignal=1 -m 90"
              PVAL=`percentage $tes`
              TESLABEL=`echo "_TES${tes}" | sed 's/\./p/'`
              [[ $BINLABEL == *"_asimov"* ]] && BINLABEL="${BINLABEL//_asimov/_asimov$TESLABEL}" || BINLABEL+="_asimov${TESLABEL}"
              TOY="higgsCombine.${BINLABEL}.GenerateOnly.mH90.123456.root"
              TOY_OPTS="--toysFile $TOY"
              peval "combine -M GenerateOnly -n .$BINLABEL $WORKSPACE -t -1 --saveToys $POI_OPTS3" 2>&1 | tee -a ../$LOG || exit 1 #--toysFile $TOYS
            fi
            
            # COMBINE multidimensional fit
            if [ $DOFIT -gt 0 ]; then
              peval "combine -M MultiDimFit -n .$BINLABEL $WORKSPACE $ALGO $POI_OPTS $TOY_OPTS $FIT_OPTS $XRTD_OPTS $CMIN_OPTS --saveNLL $SAVE" 2>&1 | tee -a ../$LOG || exit 1
            fi
            
            # BREAKDOWN
            if [ $BREAKDOWN -gt 0 ]; then
              POI_OPTS_ALL="${POI_OPTS//--freezeParameters r/--freezeParameters all}"
              if [ $DOFIT -gt 0 ]; then
                peval "combine -M MultiDimFit -n .$BINLABEL $WORKSPACE $ALGO $POI_OPTS $TOY_OPTS $FIT_OPTS $XRTD_OPTS $CMIN_OPTS --saveNLL $SAVE" 2>&1 | tee -a ../$LOG || exit 1;
              fi
              peval "combine -M MultiDimFit -n .bin-${BINLABEL} --freezeNuisanceGroups sys $WORKSPACE $ALGO $POI_OPTS $TOY_OPTS $FIT_OPTS $XRTD_OPTS $CMIN_OPTS --saveNLL" 2>&1 | tee -a ../$LOG || exit 1
              peval "combine -M MultiDimFit -n .stat-${BINLABEL} $WORKSPACE $ALGO $POI_OPTS_ALL $TOY_OPTS $FIT_OPTS $XRTD_OPTS $CMIN_OPTS --saveNLL --fastScan" 2>&1 | tee -a ../$LOG || exit 1
              #peval "combine -M MultiDimFit -n .stat-${BINLABEL} --fastScan --freezeParameters all,r $WORKSPACE $ALGO $POI_OPTS $FIT_OPTS $XRTD_OPTS $CMIN_OPTS --saveNLL" 2>&1 | tee -a ../$LOG || exit 1
              # WANRING!!! notice freeze r !
            fi
            
            # IMPACTS
            if [ $IMPACTS -gt 0 ]; then
              title "impacts"
              peval "cp $WORKSPACE ../impacts/"
              [ "$TOY_OPTS" ] && peval "cp ${TOY_OPTS//* higgs/higgs} ../impacts/"
              peval "cd ../impacts"
              IMPA_NAME="impacts_${BINLABEL}"
              OUTPUT_IMPA="${IMPA_NAME}.json"
              ILOG="postfit/${IMPA_NAME}.log"; echo `date` > ../$ILOG
              peval "combineTool.py -M Impacts -n $BINLABEL -d $WORKSPACE $FIT_OPTS --points ${NPOINTS} --redefineSignalPOIs ${POI} $POI_OPTS $TOY_OPTS $XRTD_OPTS $CMIN_OPTS --doInitialFit" 2>&1 | tee -a ../$ILOG || exit 1
              peval "combineTool.py -M Impacts -n $BINLABEL -d $WORKSPACE $FIT_OPTS --points ${NPOINTS} --redefineSignalPOIs ${POI} $POI_OPTS $TOY_OPTS $XRTD_OPTS $CMIN_OPTS --doFits --parallel 4" 2>&1 | tee -a ../$ILOG || exit 1
              peval "combineTool.py -M Impacts -n $BINLABEL -d $WORKSPACE $FIT_OPTS --points ${NPOINTS} --redefineSignalPOIs ${POI} $POI_OPTS $TOY_OPTS $XRTD_OPTS $CMIN_OPTS -o $OUTPUT_IMPA" 2>&1 | tee -a ../$ILOG || exit 1
              peval "plotImpacts.py -i $OUTPUT_IMPA -o ../postfit/$IMPA_NAME" 2>&1 | tee -a ../$ILOG || exit 1
              peval "convert -density 160 -trim ../postfit/${IMPA_NAME}.pdf[0] -quality 100 ../postfit/${IMPA_NAME}.png"
              peval "cd ../output"
            fi
            
            # POSTFIT
            if [ $POSTFIT -gt 0 ]; then
              for tes in $CHECKS; do
                [[ $tes == "#"* ]] && continue
                header "Post-fit check for var $var for $dm in TES point $tes"
                
                POI_OPTS2="--setParameters ${POI}=${tes} --freezeParameters ${POI} --rMin 1 --rMax 1 -m 90"
                PVAL=`percentage $tes`
                TESLABEL=`echo "_TES${tes}" | sed 's/\./p/'`
                DMLABEL=`latexDM $dm`
                TESTAG="$tag$EXTRATAG$TESLABEL"
                BINLABELT="${BINLABEL}${TESLABEL}"
                FITDIAGN="fitDiagnostics.${BINLABELT}.root"
                SHAPES="${ANALYSIS}_${BINLABELT}.shapes.root"
                LOGT="postfit/${ANALYSIS}_${BINLABELT}.log"
                PULLT="postfit/pulls_${BINLABELT}.txt"
                echo `date` > ../$LOGT
                
                # COMBINE FIT
                peval "combine -M FitDiagnostics -n .$BINLABELT $WORKSPACE $POI_OPTS2 $FIT_OPTS $XRTD_OPTS $CMIN_OPTS --saveShapes" 2>&1 | tee -a ../$LOGT || exit 1
                
                # POSTFIT SHAPES
                echo
                peval "PostFitShapesFromWorkspace -o $SHAPES -f ${FITDIAGN}:fit_s --postfit --freeze ${POI}=$tes --sampling --print -d $DATACARD -w $WORKSPACE" 2>&1 | tee -a ../$LOGT || exit 1
                
                # DRAW
                peval "cd .."
                peval "python checkShapes_TES.py output/$SHAPES --postfit --pdf --out-dir postfit --dirname $dm -t $TESTAG" 2>&1 | tee -a $LOGT || exit 1
                
                # PULLS
                echo
                peval "python $PULL --vtol=0.0001 output/$FITDIAGN | sed 's/[!,]/ /g' | tail -n +3 > $PULLT" 2>&1 | tee -a $LOGT || exit 1
                peval "python pulls.py -b -f $PULLT -o postfit/pulls_${BINLABELT} -t '$var, $DMLABEL, $PVAL TES'" 2>&1 | tee -a $LOGT || exit 1
                peval "cd output"
                
              done
            fi
            
            # BIASTEST
            if [ $BIASTEST -gt 0 ]; then
              peval "cp $WORKSPACE ../toys/; cd ../toys"
              for tes in $CHECKS; do
                [[ $tes == "#"* ]] && continue
                header "Bias test for var $var for $dm in TES point $tes"
                
                POI_OPTS3="--setParameters ${POI}=${tes} --freezeParameters ${POI} --expectSignal=1 -m 90"
                PVAL=`percentage $tes`
                TESLABEL=`echo "_TES${tes}" | sed 's/\./p/'`
                TESTAG="$tag$EXTRATAG$TESLABEL"
                BINLABELT="${BINLABEL}${TESLABEL}"
                [ $NTOYS == -1 ] && BINLABELT+="_asimov" || BINLABELT+="_toys"
                TOYS="higgsCombine.${BINLABELT}.GenerateOnly.mH90.${SEED}.root"
                LOGT="biastest/log/${ANALYSIS}_${BINLABELT}_${SEED}.log"
                echo `date` > ../$LOGT
                
                # TOYS
                #peval "combine -M GenerateOnly -n .$BINLABELT $WORKSPACE --toysFrequentist -t $NTOYS --saveToys -s $SEED $POI_OPTS3" 2>&1 | tee -a ../$LOGT || exit 1
                peval "combine -M GenerateOnly -n .$BINLABELT $WORKSPACE -t $NTOYS --saveToys -s $SEED $POI_OPTS3" 2>&1 | tee -a ../$LOGT || exit 1
                peval "combine -M MultiDimFit -n .$BINLABELT $WORKSPACE --toysFile $TOYS -t $NTOYS -s $SEED $ALGO $POI_OPTS --expectSignal=1 $FIT_OPTS $XRTD_OPTS $CMIN_OPTS --saveNLL" 2>&1 | tee -a ../$LOGT || exit 1
                
              done
              peval "cd ../output"
            fi
          
        done
      
        ## COMBINE DMs
        #header "${channel}: combine DMs for $var"
        #
        #BINLABELC="${channel}_${var}-combined${tag}"
        #BINLABEL="${channel}_${var}-DM*${tag}"
        #DATACARD="${ANALYSIS}_${BINLABELC}-13TeV.txt"
        #DATACARDS=`ls ${ANALYSIS}_${BINLABEL}-13TeV.txt | xargs`
        #WORKSPACE="${ANALYSIS}_${BINLABELC}-13TeV.root"
        #LOG="log/${ANALYSIS}_${BINLABELC}.log"
        #echo `date` > ../$LOG
        #    
        #peval "combineCards.py $DATACARDS > $DATACARD | tee -a ../$LOG" || exit 1
        #peval "$WORK $DATACARD -o $WORKSPACE | tee -a ../$LOG" || exit 1
        #peval "combine -M MultiDimFit -n .$BINLABELC $WORKSPACE --algo grid --points $POINTS --setPhysicsModelParameterRanges ${POI}=${RANGE} --redefineSignalPOIs ${POI} --robustFit 1 --preFitValue 1.0 --minimizerAlgoForMinos Minuit2 --minimizerAlgo Minuit2 --minimizerStrategy 0 --minimizerTolerance ${TOLERANCE} --cminFallbackAlgo Minuit2,0:1.0 --saveNLL | tee -a ../$LOG" || exit 1
      
      done
    done    
  done;
  
  ## COMBINE VARS
  #for bin in $DMS; do
  #    [[ $bin == "#"* ]] && continue
  #    [ $bin = "DM0" -o $bin = "all" ] && continue
  #    
  #    header "${channel}: combine vars for $bin"
  #    
  #    BINLABELC="${channel}_${bin}-combined${tag}"
  #    BINLABEL="${channel}_*-${bin}${tag}"
  #    DATACARD="${ANALYSIS}_${BINLABELC}-13TeV.txt"
  #    DATACARDS=`ls ${ANALYSIS}_${BINLABEL}-13TeV.txt | xargs`
  #    WORKSPACE="${ANALYSIS}_${BINLABELC}-13TeV.root"
  #    LOG="log/${ANALYSIS}_${BINLABELC}.log"
  #    echo `date` > ../$LOG
  #    
  #    # COMBINE
  #    (peval "combineCards.py $DATACARDS > $DATACARD" 2>&1 || exit 1) | tee -a ../$LOG
  #    (peval "$WORK $DATACARD -o $WORKSPACE" 2>&1 || exit 1) | tee -a ../$LOG
  #    (peval "combine -M MultiDimFit -n .$BINLABELC $WORKSPACE --algo grid --points $POINTS --setPhysicsModelParameterRanges ${POI}=${RANGE} --redefineSignalPOIs ${POI} --robustFit 1 --preFitValue 1.0 --minimizerAlgoForMinos Minuit2 --minimizerAlgo Minuit2 --minimizerStrategy 0 --minimizerTolerance ${TOLERANCE} --cminFallbackAlgo Minuit2,0:1.0 --saveNLL" 2>&1 || exit 1) | tee -a ../$LOG
  #    
  #done
  
  # PLOTS
  [ $LAST -gt 0 ] && return;
  if [ $BREAKDOWN -gt 0 ]; then
    cd ..
    peval "python plotParabola_TES.py $HARV_OPTS" || exit 1
    cd -
  elif [ $DOFIT -gt 0 ]; then
    cd ..
    peval "python plotParabola_TES.py $HARV_OPTS" || exit 1
    peval "python plotPostFitScan_TES.py $HARV_OPTS" || exit 1
    cd -
  fi
  
}



# PRINT
A="$(tput setab 0)$(tput setaf 7)"
R="$(tput setab 0)$(tput bold)$(tput setaf 1)"
E="$(tput sgr0)"

function peval { # print and evaluate given command
  echo -e ">>> $(tput setab 0)$(tput setaf 7)$@$(tput sgr0)"
  eval "$@";
}

function header { # print box around given string
  local HDR="$@"
  local BAR=`printf '#%.0s' $(seq 1 ${#HDR})`
  printf "\n\n\n"
  echo ">>>     $A####${BAR}####$E"
  echo ">>>     $A#   ${HDR}   #$E"
  echo ">>>     $A####${BAR}####$E"
  echo ">>> ";
}

function title { # print box around given string
  echo; echo ">>> $(tput setab 0)$(tput setaf 7)# $@ # $(tput sgr0)"
}

function filterHash { # filter out words starting with hash #
  echo "$@" | grep -Po '\b(?<!#)\w+\b' | xargs;
}

function percentage { # print tes value as percentage
  printf "%+f%%" `echo "($1-1)*100" | bc` | sed 's/\.*0*%/%/';
}

function ensureDir {
  [ -e "$1" ] || { echo ">>> making $1 directory..."; mkdir "$1"; }
}

function runtime {
  END=`date +%s`; RUNTIME=$((END-START))
  printf "%d minutes %d seconds" "$(( $RUNTIME / 60 ))" "$(( $RUNTIME % 60 ))"
}

function latexDM {
  case "$@" in
    "DM0")  echo "h^{#pm}";;
    "DM1")  echo "h^{#pm}#pi^{0}";;
    "DM10") echo "h^{#pm}h^{#mp}h^{#pm}";;
    "DM11") echo "h^{#pm}h^{#mp}h^{#pm}#pi^{0}";;
    "MDF")  echo "DMs combined";;
  esac;
}


# RUN
main
echo ">>> "
echo ">>> ${A}done fitting in $(runtime)$E"
echo

exit 0
