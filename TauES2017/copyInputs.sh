#! /bin/bash
[ $1 ] && FILES="*tes*${1}*.root" || FILES="*tes*.root"
NEW_INPUTS="/shome/ineuteli/analysis/SFrameAnalysis_ltau2017/plots/datacards/$FILES"
INPUT_DIR="input/" #/shome/ineuteli/analysis/CMSSW_7_4_8/src/CombineHarvester/LowMassTauTau/datacards/"
CMD="cp -v $NEW_INPUTS $INPUT_DIR"
echo ">>> $CMD"
$CMD
