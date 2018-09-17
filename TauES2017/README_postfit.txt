Several tau energy scale point are selected for post-fit analysis (e.g. "_TES0p990" is -1% TES).

Please note that due to techinical reasons, the post-fit shapes and pulls have been created with <b>FitDiagnostics</b> (while fixing TES), which might show small differences to <b>MultiDimFit</b> which is used for the TES scan of the NLL parabola.

This directory contains:
 - <a href="?match=^postfit&regexp=on">postfit-comparison</a>: comparison between post-fit values of nuisance parameters. These post-fit values correspond to the central values of the pulls. Created with MultiDimFit.
 - <a href="?match=_p*fit&regexp=on"  >p*fit</a>:              pre-/post-fit plots with FitDiagnostics.
 - <a href="?match=pulls"             >pulls</a>:              pulls created with FitDiagnostics.
 - <a href="?match=impacts"           >impacts</a>:            impacts created with MultiDimFit via <a href="https://cms-hcomb.gitbooks.io/combine/content/part3/nonstandard.html#nuisance-parameter-impacts">combineTool.py</a>.

Plots contain ZTT enriched region with
 - IsoMu24 and IsoMu27 trigger
 - baseline selections (see <a href="https://ineuteli.web.cern.ch/ineuteli/TauPOG/slides/selections.pdf">selections.pdf</a>) including oldDMs (<a href="?match=DM0">DM0</a>, <a href="?match=DM1(?!0)&regexp=on">DM1</a>, <a href="?match=DM10">DM10</a>)
 - signal regions:
     <a href="?match=ZTTregion(?!2)&regexp=on">ZTTregion</a>:   mT&lt;50 && 50&lt;m_vis&lt;85 && Dzeta&gt;-25 (see <a href="../controlPlots/?match=ZTTregion(?!2).*TES1p000&regexp=on">control plots</a>)
     <a href="?match=ZTTregion2" >ZTTregion2</a>:  mT&lt;50 && 50&lt;m_vis&lt;100 (see <a href="../controlPlots/?match=ZTTregion2.*TES1p000&regexp=on">control plots</a>)
     <a href="?match=mtlt50"     >mtlt50</a>:      mT&lt;50 (see <a href="../controlPlots/?match=mtlt50.*TES1p000&regexp=on">control plots</a>)
 - pre-fit and post-fit plots for
     tau mass <a href="?match=^m_2&regexp=on">m_2</a>
     visible mass <a href="?match=^m_vis&regexp=on">m_vis</a>
   where the hatched area on MC includes both the statistical and systematic uncertainties
 - restricted tau mass m_2 (to prevent boundary effects):
     <a href="?match=m_2.*DM1(?!0)&regexp=on">DM1</a>:   [ 0.30 - dm, 1.3*sqrt(pt/100) + dm ] -> <b>[ 0.35, 1.2 ]</b>
     <a href="?match=m_2.*DM10&regexp=on"    >DM10</a>:  [ 0.8, 1.5 ]  ->  <b>[ 0.85, 1.40 ]</b>
   with binning:
     <a href="?match=m_2%28%28%3F%21_0p%29.%29*%24&regexp=on">0.04 GeV</a> (if not mentioned otherwise in the name)
     <a href="?match=_0p05">0.05 GeV</a>
