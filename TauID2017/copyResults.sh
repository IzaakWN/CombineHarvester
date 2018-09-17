#! /bin/bash

function peval { echo ">>> $@"; eval "$@"; }

while getopts m:t:r option; do
case "${option}" in
  t) TAG=${OPTARG};;
  m) MESSAGE=${OPTARG};;
  r) RM=1;;
esac
done
[ $TAG ] && [[ $TAG != _* ]] && TAG="_${TAG}"

HOST="ineuteli@lxplus.cern.ch"
DIR="TauPOG/plots/TauID/ttbarMeasurement"
EOS="/eos/user/i/ineuteli/www/$DIR"
TMP="$(date +%Y%m%d)$TAG"

# SETUP command
CMD="cd $EOS"
[ $RM ] && CMD+="; rm -r $TMP"
CMD+="; echo \">>> extracting tarball...\""
CMD+="; tar xf - --overwrite"
[ $MESSAGE ] && CMD+="; { echo; echo '$MESSAGE'; echo; } >> $TMP/README.txt"

peval "cp README_shapes.txt shapes/README.txt"
peval "cp README_control.txt controlPlots/README.txt"
FILES="doFit_TID.sh harvestDatacards_TID.py README.txt $(find output/*.txt log/* plots/* -ctime 0 | xargs) shapes controlPlots" #-daystart
[ -e "$TMP" ] && echo ">>> removing local $TMP" && peval "rm -r $TMP"
echo ">>> copying files to temporary directory $TMP..."
peval "mkdir $TMP && cp -r $FILES $TMP/" || exit 1
echo ">>> copying compressed files to $EOS..."
peval "tar cf - $TMP | ssh $HOST '$CMD'"
peval "rm -r $TMP"
echo ">>> please visit www.cern.ch/ineuteli/$DIR/$TMP/"
