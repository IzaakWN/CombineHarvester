Plots contain ttbar enriched
 - baseline selections (see <a href="https://ineuteli.web.cern.ch/ineuteli/TauPOG/slides/selections.pdf">selections.pdf</a>) including oldDMs (<a href="?match=DM0">DM0</a>, <a href="?match=DM1(?!0)&regexp=on">DM1</a>, <a href="?match=DM10">DM10</a>)
 - at least one b tag (see <a href="../../../emu_geq1b/">emu</a> and <a href="../../../mutau_geq1b/">mutau control plots</a>)
 - tau MVA isolation ID with training on 2017MC_v1
 - observables include transverse mass (<a href="?match=pfmt_1">pfmt_1</a>) and visible mass (<a href="?match=m_vis">m_vis</a>)
 - emu+tau control region: tau ID pass region <i>with</i> ("<a href="?match=_withEmuPassFailCR">_withEmuPassFailCR</a>") and <i>without</i> fail region ("<a href="?match=_withEmuPassCR">_withEmuPassCR</a>")
 - pfmt<100 is applied to pfmt_1 in a separate check for the impact of any mismodeling in the tail (see "<a href="?match=_mtlt100">_mtlt100</a>")
 - stacked plots for
     tau mass <a href="?match=^m_2&regexp=on">m_2</a>
     visible mass <a href="?match=^m_vis&regexp=on">m_vis</a>
 - shape variations for processes <a href="?match=TTT">TTT</a>, <a href="?match=TTT">TTJ</a>, <a href="?match=ZTT">ZTT</a>, <a href="?match=ZJ">ZJ</a>, <a href="?match=ZL">ZL</a>, <a href="?match=STT">STT</a>, <a href="?match=STJ">STJ</a>, <a href="?match=W">W</a>, <a href="?match=QCD">QCD</a>, <a href="?match=VV">VV</a> include
     <a href="?match=t"         >t</a>:           tau energy scale (TES, &plusmn;3%)
     <a href="?match=jetTauFake">jetTauFake</a>:  jet tau fake energy scale (JTF, &plusmn;10%)
     <a href="?match=jes"       >jes</a>:         jet energy scale (JES)
     <a href="?match=jer"       >jer</a>:         jet energy resolution (JER)
     <a href="?match=uncEn"     >uncEn</a>:       MET energy unclustering
