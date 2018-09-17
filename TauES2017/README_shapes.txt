Comparisons of shape templates from the inputs to combine. For stacked plots, see <a href="../controlPlots">here</a>.

Plots contain ZTT enriched region with
 - IsoMu24 and IsoMu27 trigger
 - baseline selections (see <a href="https://ineuteli.web.cern.ch/ineuteli/TauPOG/slides/selections.pdf">selections.pdf</a>) including oldDMs (<a href="?match=DM0">DM0</a>, <a href="?match=DM1(?!0)&regexp=on">DM1</a>, <a href="?match=DM10">DM10</a>)
 - signal regions:
     <a href="?match=ZTTregion(?!2)&regexp=on">ZTTregion</a>:   mT&lt;50 && 50&lt;m_vis&lt;85 && Dzeta&gt;-25 (see <a href="../controlPlots/?match=ZTTregion(?!2).*TES1p000&regexp=on">control plots</a>)
     <a href="?match=ZTTregion2" >ZTTregion2</a>:  mT&lt;50 && 50&lt;m_vis&lt;100 (see <a href="../controlPlots/?match=ZTTregion2.*TES1p000&regexp=on">control plots</a>)
     <a href="?match=mtlt50"     >mtlt50</a>:      mT&lt;50 (see <a href="../controlPlots/?match=mtlt50.*TES1p000&regexp=on">control plots</a>)
 - variables
     tau mass <a href="?match=m_2">m_2</a>
     visible mass <a href="?match=m_vis">m_vis</a>
 - restricted tau mass m_2 (to prevent boundary effects):
     <a href="?match=m_2.*DM1(?!0)&regexp=on">DM1</a>:   [ 0.30 - dm, 1.3*sqrt(pt/100) + dm ] -> <b>[ 0.35, 1.2 ]</b>
     <a href="?match=m_2.*DM10&regexp=on"    >DM10</a>:  [ 0.8, 1.5 ]  ->  <b>[ 0.85, 1.40 ]</b>
   with binning:
     <a href="?match=m_2%28%28%3F%21_0p%29.%29*%24&regexp=on">0.04 GeV</a> (if not mentioned otherwise in the name)
     <a href="?match=_0p05">0.05 GeV</a>
 - shape variations for processes <a href="?match=TTT">TTT</a>, <a href="?match=TTT">TTJ</a>, <a href="?match=ZTT">ZTT</a>, <a href="?match=ZJ">ZJ</a>, <a href="?match=ZL">ZL</a>, <a href="?match=STT">STT</a>, <a href="?match=JTF">JTF</a>, <a href="?match=VV">VV</a> include
     <a href="?match=TES.p.*-.p.*&regexp=on">TES</a>:         tau energy scale (TES, -6 to +6%)
     <a href="?match=shape_m_"              >shape_m</a>:     muon energy scale (MES, &plusmn;1%)
     <a href="?match=jetTauFake"            >jetTauFake</a>:  jet tau fake energy scale (JTF, &plusmn;10%)
     <a href="?match=mTauFake"              >mTauFake</a>:    muon tau fake energy scale (&plusmn;3%)
     <a href="?match=shape_dy"              >shape_dy</a>:    Z pT reweighting (down: not applied, up: twice applied)
     <a href="?match=jes"                   >jes</a>:         jet energy scale (JES)
     <a href="?match=jer"                   >jer</a>:         jet energy resolution (JER)
     <a href="?match=uncEn"                 >uncEn</a>:       MET energy unclustering
