#! /bin/bash

function peval { echo ">>> $@"; eval "$@"; }

while getopts m:t:r option; do case "${option}" in
  t) TAG=${OPTARG};;
  m) MESSAGE=${OPTARG};;
  r) RM=1;;
esac done
[ $TAG ] && [[ $TAG != _* ]] && TAG="_${TAG}"

HOST="ineuteli@lxplus.cern.ch"
DIR="TauPOG/plots/TauES"
EOS="/eos/user/i/ineuteli/www/$DIR"
TMP="$(date +%Y%m%d)$TAG"

# SETUP command
CMD="cd $EOS"
[ $RM ] && CMD+="; echo \">>> removing old $TMP directory...\"; rm -r $TMP"
CMD+="; echo \">>> extracting tarball...\""
CMD+="; tar xf - --overwrite"
[ "$MESSAGE" ] && CMD+="; { echo; echo \"$MESSAGE\"; echo; } >> $TMP/README.txt"

peval "cp README_shapes.txt shapes/README.txt"
peval "cp README_control.txt controlPlots/README.txt"
peval "cp README_postfit.txt postfit/README.txt"
[ -e "animation" ] && [ `ls animation/ -1 | wc -l` -gt 2 ] && peval "cp animation/animation* .gif postfit/"
#FILES="doFit_TES.sh harvestDatacards_TES.py README.txt log/* $(find output/*.txt plots/para* plots/meas* -ctime 0 | xargs) shapes controlPlots postfit" #-daystart
FILES="doFit_TES.sh harvestDatacards_TES.py README.txt log/* output/*.txt plots/para* plots/meas* shapes controlPlots postfit"
[ -e $TMP ] && echo ">>> removing local $TMP" && peval "rm -r $TMP"
echo ">>> copying files to temporary directory $TMP..."
peval "mkdir $TMP && cp -r $FILES $TMP/" #|| exit 1
echo ">>> copying compressed files to $EOS..."
peval "tar cf - $TMP | ssh $HOST '$CMD'"
peval "rm -r $TMP"
echo ">>> please visit www.cern.ch/ineuteli/$DIR/$TMP/"
