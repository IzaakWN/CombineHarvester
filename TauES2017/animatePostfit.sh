#! /bin/bash

# SET INPUT
ACHANNELS="mt #et"           # channels
ADMS="DM0 DM1 DM10"        # decay mode categories
AVARS="m_2 #m_vis"           # variables
ACHECKS=`seq -f "%.3f" 0.90 0.002 1.06 | xargs` # values to check pre-/post-fit
TAG="_mtlt50"               # extra label in datacards (for checks)

ONLYANIMATE=0
while getopts d:m:o:t:a option; do case "${option}" in
  d) ADMS=${OPTARG};;
  m) AVARS=${OPTARG};;
  o) AVARS=${OPTARG};;
  t) TAG=${OPTARG};;
  a) ONLYANIMATE=1;;
esac done

# MAIN ROUTINE
function animate {
  
  ensureDir "animation"
  echo
  
  # LOOP over channels
  for channel in $ACHANNELS; do
    [[ $channel == "#"* ]] && continue
    
    # LOOP over variables
    for var in $AVARS; do
      [[ $var == "#"* ]] && continue
      
      # LOOP over DMS
      for dm in $ADMS; do
          [[ $dm == "#"* ]] && continue
          [ $var = "m_2" -a $dm = "DM0" ] && continue
          
          # FIT
          if [ $ONLYANIMATE -lt 1 ]; then
            peval "./doFit_TES.sh -o $var -d $dm -c '$ACHECKS' -t $TAG -p -n -g animation" || exit 1
          fi
          
          # JOIN
          for tes in $ACHECKS; do
            TESLABEL=`echo "TES${tes}" | sed 's/\./p/'`
            PNG_IN="animation/${var}*${dm}${TAG}*${TESLABEL}*fit.png"
            PNG_IN=`ls $PNG_IN | sort -r | xargs`
            PNG_OUT="animation/${var}_${dm}${TAG}_${TESLABEL}_bothfits.png"
            peval "convert $PNG_IN +append $PNG_OUT" || exit 1
          done
          
          # ANIMATE fits
          PNGS="animation/${var}_${dm}${TAG}_TES*_bothfits.png"
          GIF="animation/animation_${var}_${dm}${TAG}.gif"
          peval "convert $(for p in $PNGS; do printf -- '-delay 25 %s ' $p; done; ) $GIF" || exit 1
          peval "convert $GIF -coalesce -duplicate 1,-2-1 -layers OptimizePlus -loop 0 $GIF.tmp # patrol/boomerang"
          peval "mv $GIF.tmp $GIF"
          
          # ANIMATE pulls
          PNGS="animation/pulls*${var}*${dm}${TAG}-13TeV*TES*.png" || exit 1
          GIF="animation/animation_pulls_${var}_${dm}${TAG}.gif" || exit 1
          peval "convert $(for p in $PNGS; do printf -- '-delay 25 %s ' $p; done; ) $GIF" || exit 1
          peval "convert $GIF -coalesce -duplicate 1,-2-1 -layers OptimizePlus -loop 0 $GIF.tmp" # patrol/boomerang
          peval "mv $GIF.tmp $GIF"
          
      done
    done
  done;
    
}



# PRINT
function peval { # print and evaluate given command
  echo -e ">>> $(tput setab 0)$(tput setaf 7)$@$(tput sgr0)"
  eval "$@";
}

function ensureDir {
  [ -e "$1" ] || { echo ">>> making $1 directory..."; mkdir "$1"; }
}


# RUN
animate
echo ">>> "
echo ">>> done animating"
echo

exit 0
