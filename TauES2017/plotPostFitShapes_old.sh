#! /bin/bash

CHECKS="0p970 0p980 0p990 1p000 1p010 1p010 1p020 1p030"
DMS="DM0 DM1 DM10"
VARS="m_vis m_2"
TAG="_ZTTregion2 _ZTTregion2_0p05"
#TAG="_mtlt50"

function peval { # print and evaluate given command
  echo -e ">>> $(tput setab 0)$(tput setaf 7)$@$(tput sgr0)"
  eval "$@";
}

for tag in $TAG; do
  for var in $VARS; do
    [ $var == "m_vis" ] && [[ $tag == "_"*"_0p"* ]] && continue
    for dm in $DMS; do
      [ $var == "m_2" -a $dm = "DM0" ] && continue
      for tes in $CHECKS; do
          peval "python checkShapes_TES.py output/ztt_mt_${var}-${dm}${tag}-13TeV_TES${tes}.shapes.root --postfit --out-dir postfit --dirname $dm -t ${tag}_TES${tes} --pdf"
      done
    done
  done
done
