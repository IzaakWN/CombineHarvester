#! /bin/bash

DMS="DM0 DM1 DM10 #all"     # decay mode categories
VARS="m_2 m_vis"            # variables
TAG="_mtlt50"               # tag in datacards (for selections)

while getopts "d:m:o:t:" option; do case "${option}" in
  d) DMS=${OPTARG};;
  m) VARS=${OPTARG};;
  o) VARS=${OPTARG};;
  t) TAG=${OPTARG};;
esac done

# OPTIONS
VARS=`echo $VARS | grep -Po '\b(?<!#)\w+\b' | xargs`
DMS=`echo $DMS | grep -Po '\b(?<!#)\w+\b' | xargs`
echo $VARS
echo $DMS

# MAIN ROUTINE
function main {
  
  # LOOP over variables
  for var in $VARS; do
    [[ $var == "#"* ]] && continue
    [ $var == "m_vis" ] && [[ $TAG == "_"*"_0p"* ]] && continue
    [ $var == "m_2"   ] && [[ $TAG == *"_85"*    ]] && continue
    
    # LOOP over DMS
    for dm in $DMS; do
      echo ">>> $var for $dm"
      
      BINLABEL="mt_${var}-${dm}${TAG}${EXTRATAG}-13TeV"
      TESLABEL="_TES1p000"
      TESTAG="$TAG$TESLABEL"
      BINLABELT="${BINLABEL}${TESLABEL}"
      SHAPES="ztt_${BINLABELT}.shapes.root"
      
      peval "python checkShapes_TES.py output/$SHAPES --postfit --out-dir postfit --dirname $dm -t $TESTAG --pdf" || exit 1
      #python checkShapes_TES.py output/ztt_mt_m_2-DM10_mtlt50_0p05-13TeV_TES1p000.shapes.root --postfit --out-dir postfit --dirname DM10 -t _mtlt50_0p05_TES1p000

    done
  done
}

function peval { # print and evaluate given command
  echo -e ">>> $(tput setab 0)$(tput setaf 7)$@$(tput sgr0)"
  eval "$@";
}

main
exit 0
