#! /bin/bash
# Author: Izaak Neutelings (May 2018)
# https://twiki.cern.ch/twiki/bin/viewauth/CMS/SWGuideHiggsAnalysisCombinedLimit
# CombineHarvester/CombinePdfs/python/TagAndProbeModel.py
START=`date +%s`

# SET INPUT
channel="mt"
ANALYSIS="ztt"              # process
CHANNELS="mt #et"           # channels
DMS="DM0 DM1 DM10 #all"     # decay mode categories
VARS="m_2 m_vis"            # variables
CHECKS="0.960 0.970 0.980 0.990 1.000 1.010 1.020 1.030 1.040"
TAGS="_ZTTregion2" #_ZTTregion2_0p05 _ZTTregion2_restr _mtlt50_0p05" # # tag in datacards (for selections)

# USER INPUT
while getopts "bBc:d:e:him:N:no:pPt:vs:" option; do case "${option}" in
  c) CHECKS=${OPTARG};;
  d) DMS=${OPTARG};;
  m) VARS=${OPTARG};;
  o) VARS=${OPTARG};;
  t) TAGS=${OPTARG};;
  s) SEED=${OPTARG};;
esac done

# OPTIONS
set -o pipefail # for exit after tee
POINTA=`echo $RANGE | grep -Po '\d+\.?\d*(?=,)'`
VARS=`echo $VARS | grep -Po '\b(?<!#)\w+\b' | xargs`
DMS=`echo $DMS | grep -Po '\b(?<!#)\w+\b' | xargs`


# MAIN ROUTINE
function main {
  
  peval "cd toys" || exit 1

  # LOOP over variables
  for tag in $TAGS; do
  
    # LOOP over variables
    for var in $VARS; do
      [[ $var == "#"* ]] && continue
      [ $var == "m_vis" ] && [[ $tag == "_"*"_0p"* ]] && continue
      [ $var == "m_2"   ] && [[ $tag == *"_restr"* ]] && continue
    
      # LOOP over DMS
      for dm in $DMS; do
        [[ $dm == "#"* ]] && continue
        [ $var == "m_2" -a $dm = "DM0" ] && continue
        header "${channel}: combine var $var for $dm"
      
        # LOOP over tes points
        for tes in $CHECKS; do
      
          TESLABEL=`echo "_TES${tes}" | sed 's/\./p/'`
          BINLABEL="${channel}_${var}-${dm}${tag}-13TeV${TESLABEL}"
          INPUT="higgs*${BINLABEL}_toys.MultiDimFit.mH90.*[^all].root"
          OUTPUT="higgsCombine.${BINLABEL}_toys.MultiDimFit.mH90.all.root"
        
          peval "ls -hlt $INPUT" || exit 1
          peval "hadd -f $OUTPUT $INPUT" || exit 1
          echo
        
        done
      done
    done
  done
  
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

function filterHash { # filter out words starting with hash #
  echo "$@" | grep -Po '\b(?<!#)\w+\b' | xargs;
}

function percentage { # print tes value as percentage
  printf "%f%%" `echo "($1-1)*100" | bc` | sed 's/\.*0*%/%/';
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
echo ">>> "
echo ">>> ${A}done fitting in $(runtime)$E"
echo

exit 0
