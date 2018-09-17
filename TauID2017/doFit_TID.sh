#! /bin/bash
# Author: Izaak Neutelings (January 2018)
# /shome/ineuteli/analysis/CMSSW_7_4_8/src/CombineHarvester/CombinePdfs/python/TagAndProbeModel.py

# DIRS
DIR="./" #"/shome/ineuteli/analysis/CMSSW_7_4_8/src/CombineHarvester/TauID2017"
[ ! -e "log" ] && mkdir "log"

# INPUT
ANALYSIS="ttbar"        # process
CHANNELS="mt #et"       # channels
ISOWPS="vloose
        loose
        medium
        tight
        vtight
        vvtight"        # categories: VL, L, M, T VT
VARS="pfmt_1 m_vis"     # variables
doCR=2                  # 0: no emu CR, 1: emu CR, 2: emu+tau pass, 3: emu+tau pass and fail
TAG="" #_mtlt100        # extra label in datacards for checks

# FIT SETTINGS
RMIN="0.50"
RMAX="1.30"
TOL="0.1"
NP_OPTS="--setParameterRanges CMS_ttbar_shape_uncEn_13TeV=-0.5,0.5"
FIT_OPTS="--robustFit=1 --preFitValue=1. --setRobustFitAlgo=Minuit2 --setRobustFitStrategy=0 --setRobustFitTolerance=${TOL} --rMin $RMIN --rMax $RMAX"
XRTD_OPTS="--X-rtd FITTER_NEW_CROSSING_ALGO --X-rtd FITTER_NEVER_GIVE_UP --X-rtd FITTER_BOUND"
CMIN_OPTS="--cminFallbackAlgo Migrad,0:0.5 --cminFallbackAlgo Migrad,0:1.0"

# SCRIPTS
LOGS=""
HARV="./harvestDatacards_TID.py"
TAPM="../../CombineHarvester/CombinePdfs/python/TagAndProbeModel.py"
PULL="../../HiggsAnalysis/CombinedLimit/test/diffNuisances.py"
IMPA="combineTool.py" #CombineHarvester/CombineTools/scripts/combineTool.py"
PLOT_IMPA="plotImpacts.py" #CombineHarvester/CombineTools/scripts/
WORK="text2workspace.py" #../HiggsAnalysis/CombinedLimit/scripts/text2workspace.py"
COMB="combineCards" #../HiggsAnalysis/CombinedLimit/scripts/combineCards.py"
[ -e $TAPM ] || { echo ">>> ERROR! $TAPM not found!"; exit 1; }
[ -e "log" ] || { echo ">>> making log directory..."; mkdir "log"; }
[ -e "impacts" ] || { echo ">>> making impacts directory..."; mkdir "impacts"; }
#command $WORK >/dev/null 2>&1 || { echo "ERROR! $WORK command not found!"; exit 1; }
#command $COMB >/dev/null 2>&1 || { echo "ERROR! $COMB command not found!"; exit 1; }

# USER INPUT
VERBOSITY=0
POSTFIT=0
DOHARV=1
DOIMPA=0
while getopts "vc:m:o:rt:w:" option; do case "${option}" in
  c) doCR=${OPTARG};;
  m) VARS=${OPTARG};;
  o) VARS=${OPTARG};;
  r) DOHARV=0;;
  t) TAG=${OPTARG};;
  w) ISOWPS=${OPTARG};;
  v) VERBOSITY=1;;
esac done

# OPTIONS
[[ $TAG == *"mtlt100"* ]] && VARS="pfmt_1"
ISOWPS=`echo $ISOWPS | grep -Po '\b(?<!#)\w+\b' | xargs` # filter out words starting with #
VARS=`echo $VARS | grep -Po '\b(?<!#)\w+\b' | xargs`
DRAW_OPTS=""
case $doCR in
  1) DRAW_OPTS+="--use-CR ";;
  2) DRAW_OPTS+="--use-CR-pass ";;
  3) DRAW_OPTS+="--use-CR-pass-fail ";;
esac
[ $TAG ] && DRAW_OPTS+="--tag $TAG "
HARV_OPTS="-w $ISOWPS -o $VARS $DRAW_OPTS"



# MAIN ROUTINE
function main {
  
  cd $DIR
  echo
  
  # HARVEST
  if [ $DOHARV -gt 0 ]; then
    header "Harvest datacards"
    peval "python $HARV $HARV_OPTS" || exit 1
  fi
  
  # LOOP over CHANNELS
  for channel in $CHANNELS; do
    [[ $channel == "#"* ]] && continue
    
    # LOOP over VARS
    for var in $VARS; do
      [[ $var == "#"* ]] && continue
      
      # LOOP over WPs
      for isoWP in $ISOWPS; do
          [[ $isoWP == "#"* ]] && continue
          [[ $isoWP == "vvtight" ]] && RMIN=0.0 && RMAX=2.0
          header "${channel}: combine for var $var for $isoWP ID"
          
          cd "$DIR/output"
          
          # INPUT
          BINLABEL="${channel}_${var}-pass-${isoWP}${TAG}-13TeV"
          if [ $doCR == 1 ]; then
            BINLABEL_OLD="$BINLABEL"
            BINLABEL_EMU="${channel}_${var}-${isoWP}-emuCR${TAG}-13TeV"
            BINLABEL_NEW="${channel}_${var}-${isoWP}_withEmuCR${TAG}-13TeV"
            BINLABEL="$BINLABEL_NEW"
            DATACARD_OLD="${ANALYSIS}_${BINLABEL_OLD}.txt"
            DATACARD_EMU="${ANALYSIS}_${BINLABEL_EMU}.txt"
            DATACARD_NEW="${ANALYSIS}_${BINLABEL_NEW}.txt"
            peval "combineCards.py pass=$DATACARD_OLD emuCR=$DATACARD_EMU > $DATACARD_NEW"
          elif [ $doCR = 2 -o $doCR = 3 ]; then
            BINLABEL_OLD="$BINLABEL"
            BINLABEL_PASS_EMU="${channel}_${var}-pass-${isoWP}-emuCR${TAG}-13TeV"
            BINLABEL_FAIL_EMU="${channel}_${var}-fail-${isoWP}-emuCR${TAG}-13TeV"
            [ $doCR == 2 ] && BINLABEL_NEW="${channel}_${var}-${isoWP}_withEmuPassCR${TAG}-13TeV"
            [ $doCR == 3 ] && BINLABEL_NEW="${channel}_${var}-${isoWP}_withEmuPassFailCR${TAG}-13TeV"
            BINLABEL="$BINLABEL_NEW"
            DATACARD_OLD="${ANALYSIS}_${BINLABEL_OLD}.txt"
            DATACARD_PASS_EMU="${ANALYSIS}_${BINLABEL_PASS_EMU}.txt"
            DATACARD_FAIL_EMU="${ANALYSIS}_${BINLABEL_FAIL_EMU}.txt"
            DATACARD_NEW="${ANALYSIS}_${BINLABEL_NEW}.txt"
            [ $doCR == 2 ] && peval "combineCards.py pass=$DATACARD_OLD pass-emuCR=$DATACARD_PASS_EMU > $DATACARD_NEW"
            [ $doCR == 3 ] && peval "combineCards.py pass=$DATACARD_OLD pass-emuCR=$DATACARD_PASS_EMU fail-emuCR=$DATACARD_FAIL_EMU > $DATACARD_NEW"
          else
            echo ">>> no emu control region!"
          fi
          DATACARD="${ANALYSIS}_${BINLABEL}.txt"
          WORKSPACE="${ANALYSIS}_${BINLABEL}.root"
          FITDIAGN="fitDiagnostics.${BINLABEL}.root"
          SHAPES="${ANALYSIS}_${BINLABEL}.shapes.root"
          LOG="log/${ANALYSIS}_${BINLABEL}.log"
          LOGS+="$LOG "; echo `date` > ../$LOG
          
          # WORKSPACE
          peval "text2workspace.py $DATACARD -o $WORKSPACE -P CombineHarvester.CombinePdfs.TagAndProbeModel:tagAndProbe" 2>&1 | tee -a ../$LOG || exit 1 # -m 172
          
          # COMBINE FIT
          peval "combine -M FitDiagnostics -n .$BINLABEL $WORKSPACE $FIT_OPTS $XRTD_OPTS $CMIN_OPTS" 2>&1 | tee -a ../$LOG || exit 1 #--redefineSignalPOIs SF #> ../$LOG
          
          # POSTFIT SHAPES
          peval "PostFitShapesFromWorkspace -o $SHAPES -f ${FITDIAGN}:fit_s --postfit --sampling --print -d $DATACARD -w $WORKSPACE" 2>&1 | tee -a ../$LOG || exit 1 # -m 172
          
          # DRAW
          cd ..; echo
          #(peval "python draw.py output/$SHAPES -w $isoWP $DRAW_OPTS" 2>&1 || exit 1) | tee -a $LOG
          peval "python checkShapes_TES.py output/$SHAPES --postfit --out-dir plots --dirname $isoWP --tag $TAG" 2>&1 | tee -a $LOGT || exit 1
          
          # PULLS
          peval "python $PULL --poi SF --vtol=0.01 output/$FITDIAGN | sed 's/[!,]/ /g' | tail -n +4 > output/pulls_${BINLABEL}.txt" 2>&1 | tee -a $LOG || exit 1
          peval "python pulls.py -b -f output/pulls_${BINLABEL}.txt -o plots/pulls_${BINLABEL} -t '$var, $isoWP'" 2>&1 | tee -a $LOG || exit 1
          
          # IMPACTS
          if [ $DOIMPA -gt 0 ]; then
            cd "impacts"
            IMPA_NAME="impacts_${BINLABEL}"
            OUTPUT_IMPA="${IMPA_NAME}.json"
            peval "combineTool.py -M Impacts $FIT_OPTS --doInitialFit -d ../output/$WORKSPACE" 2>&1 | tee -a $LOG || exit 1
            peval "combineTool.py -M Impacts $FIT_OPTS --doFits --parallel 4 -d ../output/$WORKSPACE" 2>&1 | tee -a $LOG || exit 1
            peval "combineTool.py -M Impacts -d ../output/$WORKSPACE -o $OUTPUT_IMPA" 2>&1 | tee -a $LOG || exit 1
            peval "plotImpacts.py -i $OUTPUT_IMPA -o ../plots/$IMPA_NAME" 2>&1 | tee -a $LOG || exit 1
          fi

          
      done
    done
  done;
  
  # PLOT SFs
  peval "python plotSF.py $HARV_OPTS" 2>&1 | tee -a $LOG || exit 1
  
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

function ensureDir {
  [ -e "$1" ] || { echo ">>> making $1 directory..."; mkdir "$1"; }
}

function runtime {
  END=`date +%s`; RUNTIME=$((END-START))
  printf "%d minutes %d seconds" "$(( $RUNTIME / 60 ))" "$(( $RUNTIME % 60 ))"
}



# RUN
main
echo ">>>"
echo ">>> see log fils $LOGS"
echo ">>> ${A}done fitting in $(runtime)$E"
echo

exit 0
