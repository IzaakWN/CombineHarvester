Plots contain ttbar enriched
 - baseline selections (see <a href="https://ineuteli.web.cern.ch/ineuteli/TauPOG/slides/selections.pdf">selections.pdf</a>) including oldDMs (<a href="?match=DM0">DM0</a>, <a href="?match=DM1(?!0)&regexp=on">DM1</a>, <a href="?match=DM10">DM10</a>)
 - at least one b tag (see <a href="../../emu_geq1b/">emu</a> and <a href="../../mutau_geq1b/">mutau control plots</a>)
 - tau MVA isolation ID with training on 2017MC_v1
 - observables include transverse mass (<a href="?match=pfmt_1">pfmt_1</a>) and visible mass (<a href="?match=m_vis">m_vis</a>)
 - emu+tau control region: tau ID pass region <i>with</i> ("<a href="?match=_withEmuPassFailCR">_withEmuPassFailCR</a>") and <i>without</i> fail region ("<a href="?match=_withEmuPassCR">_withEmuPassCR</a>")
 - pfmt<100 is applied to pfmt_1 in a separate check for the impact of any mismodeling in the tail (see "<a href="?match=_mtlt100">_mtlt100</a>")

Datacards have the following naming scheme:
 - mutau pass:                            <a href="?match=pass-[^-]*-13TeV&regexp=on">ttbar_mt_$VAR-pass-$WP-13TeV.txt</a>
 - emu+tau pass:                          <a href="?match=pass-[^-]*-emuCR-13TeV&regexp=on">ttbar_mt_$VAR-pass-$WP-emuCR-13TeV.txt</a>
 - mutau pass + emu+tau pass region:      <a href="?match=_withEmuPassCR-13TeV">ttbar_mt_$VAR-$WP_withEmuPassCR-13TeV.txt</a>
 - mutau pass + emu+tau pass/fail region: <a href="?match=_withEmuPassFailCR-13TeV">ttbar_mt_$VAR-$WP_withEmuPassFailCR-13TeV.txt</a>
and similar for pulls.
