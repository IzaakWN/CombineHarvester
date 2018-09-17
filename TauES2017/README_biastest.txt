Bias test by making pseudodata (toys) for each TES variation (GenerateOnly) and the measuring the TES variation again by profiling the NLL (MultiDimFit):

  $ combine -M GenerateOnly workspace.root -t 10 --saveToys --setParameters tes=1.02 --freezeParameters tes --expectSignal 1 -m 90
  $ combine -M MultiDimFit workspace.root --algo=grid --points 81 -P tes --setParameterRanges tes=0.899,1.061 --expectSignal 1 -m 90 --toysFile higgsCombine.GenerateOnly.mH90.123456.root -t 10 --saveNLL # ...

  "<a href="combine_help_MultiDimFit.txt">--expectSignal 1</a>" is to include the ZTT signal in the toy generation and MDF fit.
  "<a href="combine_help_GenerateOnly.txt">--toysFrequentist</a>" will first fit the MC to data before throwing toys, in order to constrain (non-frozen) parameters with real data.
                      This however biases the shapes (see plots in <a href="../../20180524/biastest/frequentist">frequentist</a> directory).

  <a href="https://cms-hcomb.gitbooks.io/combine/content/part3/nonstandard.html#roomultipdf-conventional-bias-studies">https://cms-hcomb.gitbooks.io/combine/content/part3/nonstandard.html#roomultipdf-conventional-bias-studies</a>
  <a href="https://hypernews.cern.ch/HyperNews/CMS/get/higgs-combination/641.html?inline=-1">https://hypernews.cern.ch/HyperNews/CMS/get/higgs-combination/641.html?inline=-1</a>

Plots contain ZTT enriched region with
 - oldDMs: <a href="?match=DM0">DM0</a>, <a href="?match=DM1(?!0)&regexp=on">DM1</a>, <a href="?match=DM10">DM10</a>
 - signal regions:
     <a href="?match=ZTTregion2" >ZTTregion2</a>:  mT&lt;50 && 50&lt;m_vis&lt;100 (see <a href="../controlPlots/?match=ZTTregion2.*TES1p000&regexp=on">control plots</a>)
     <a href="?match=mtlt50"     >mtlt50</a>:      mT&lt;50 (see <a href="../controlPlots/?match=mtlt50.*TES1p000&regexp=on">control plots</a>)
 - restricted tau mass m_2:
     <a href="?match=m_2.*DM1(?!0)&regexp=on">DM1</a>:   [ 0.30 - dm, 1.3*sqrt(pt/100) + dm ] -> <b>[ 0.35, 1.2 ]</b>
     <a href="?match=m_2.*DM10&regexp=on"    >DM10</a>:  [ 0.8, 1.5 ]  ->  <b>[ 0.85, 1.35 ]</b>
   with binning:
     0.04 GeV (if not mentioned otherwise)
     <a href="?match=_0p05">0.05 GeV</a>
 - tau energy is measured with
     <a href="?match=m_2">tau mass m_2</a>
     <a href="?match=m_vis">visible mass m_vis</a>
