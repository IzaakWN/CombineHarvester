#! /usr/bin/env python
# Author: Izaak Neutelings (January 2018)

from argparse import ArgumentParser
import CombineHarvester.CombineTools.ch as ch
from CombineHarvester.CombineTools.ch import CombineHarvester, MassesFromRange, SystMap, BinByBinFactory, CardWriter, SetStandardBinNames, AutoRebin
import CombineHarvester.CombinePdfs.morphing as morphing
from CombineHarvester.CombinePdfs.morphing import BuildRooMorphing
from ROOT import RooWorkspace, TFile, RooRealVar
import ROOT
import os, sys

argv = sys.argv
description = '''This script makes datacards with CombineHarvester.'''
parser = ArgumentParser(prog="harvesterDatacards_TES",description=description,epilog="Succes!")
parser.add_argument( "-t", "--tag",       dest="tag", type=str, default="", action='store',
                     metavar="TAG",       help="tag for a file" )
parser.add_argument( "-w", "--isoWP",     dest="isoWPs", type=str, nargs='*', default="", action='store',
                     metavar="TAU_ISO_ID_WP", help="working point for the tau MVA iso ID" )
parser.add_argument( "-d", "--decay",     dest="decay", type=str, default="", action='store',
                     metavar="DECAY",     help="decay" )
parser.add_argument( "-o", "--obs",       dest="observables", nargs='*', type=str, default="", action='store',
                     metavar="MASS",      help="name of mass observable" )
parser.add_argument( "-c", "--use-CR",    dest="useCR1",  default=False, action='store_true',
                                          help="use emu control region" )
parser.add_argument( "--use-CR-pass",     dest="useCR2",  default=False, action='store_true',
                                          help="use emu control region with pass region" )
parser.add_argument( "--use-CR-pass-fail", dest="useCR3",  default=False, action='store_true',
                                          help="use emu control region with pass/fail region" )
parser.add_argument( "-n", "--no-shapes", dest="noShapes",  default=False, action='store_true',
                                          help="do not include shape uncertainties" )
parser.add_argument( "-v", "--verbose",   dest="verbose",  default=False, action='store_true',
                                          help="set verbose" )
args = parser.parse_args()

INPUT_DIR   = "./input"
verbosity   = args.verbose
doShapes    = not args.noShapes #and False
observables = args.observables
emuCR       = 1 if args.useCR1 else 2 if args.useCR2 else 3 if args.useCR3 else 0
tag         = args.tag
isoWPs      = [wp for wp in args.isoWPs if '#' not in wp]



def harvest(channel,var,isoWP,**kwargs):
    """Harvest cards."""
    print green("\n>>> harvest datacards for %s for %s"%(var,isoWP))
    
    emuCR    = kwargs.get('emuCR',False)
    cats     = { }
    binsCR   = [ ]
    analysis = 'ttbar'
    era      = '13TeV'
    
    # CATEGORIES
    cats['all'] = [
        ( 1, "pass-%s"%isoWP ),
        ( 2, "fail-%s"%isoWP ),
    ]
    
    # CATEGORIES EMU CR
    if emuCR==1:
      print green(">>> including emu control region...")
      cats['emuCR'] = [( 3, "emuCR" )]
    elif emuCR>1:
      print green(">>> including emu control region with pass/fail regions...")
      cats['emuCR'] = [( 3, "pass-%s-emuCR"%isoWP ),
                       ( 4, "fail-%s-emuCR"%isoWP )]
    cats['SR']   = cats['all'][:]
    cats['all'] += cats["emuCR"][:]
    
    print ">>> categories:"
    print ">>>   %s"%cats['all']
    
    # PROCESSES
    procs    = {
        'sig':   [ 'TTT', 'ZTT', 'STT' ],
        #'sigCR': [ 'TTT', ],
        'bkg':   [ 'TTJ', 'ZJ', 'ZL', 'W', 'STJ', 'QCD', 'VV' ],
        #'bkgCR': [ 'TTJ', 'STJ' ],
        'DY':    [ 'ZTT', 'ZJ', 'ZL' ],
        'TT':    [ 'TTT', 'TTJ' ],
        'ST':    [ 'STT', 'STJ' ],
    }
    procs['SR'] = procs['sig']  +procs['bkg']
    filterEmu = ['STT','ZTT','ZJ','ZL','W','QCD','VV'] if emuCR>1 else [ ]
    
    # HARVESTER
    harvester = CombineHarvester()
    harvester.AddObservations( ['*'], [analysis], [era], [channel],                 cats['all']          )
    harvester.AddProcesses(    ['*'], [analysis], [era], [channel], procs['bkg'],   cats['all'],   False )
    harvester.AddProcesses(    [''],  [analysis], [era], [channel], procs['sig'],   cats['all'],   True  )
    
    # FILTER
    if filterEmu:
      harvester.FilterAll(lambda obj: obj.bin_id() in [3,4] and obj.process() in filterEmu)
    
    # NUISSANCE PARAMETERS
    print green(">>> defining nuissance parameters ...")
    
    harvester.cp().process(['TTT','TTJ','ZTT','ZJ','ZL','STT','STJ','VV']).AddSyst(
        harvester, 'CMS_lumi', 'lnN', SystMap()(1.025))
    
    for id, region in cats['emuCR']:
      harvester.cp().process(['W']).bin_id([id]).AddSyst(
        harvester, 'CMS_lumi', 'lnN', SystMap()(1.025))
    
    #harvester.cp().process(['QCD']).AddSyst(
    #    harvester, 'CMS_lumi', 'lnN', SystMap()(0.97)) # anti-correlated
    
    harvester.cp().process(['TTT','TTJ','ZTT','ZJ','ZL','STT','STJ','VV']).AddSyst(
        harvester, 'CMS_eff_m', 'lnN', SystMap()(1.02))
    
    for id, region in cats['emuCR']:
      harvester.cp().bin_id([id]).AddSyst(
        harvester, 'CMS_eff_e', 'lnN', SystMap()(1.02))
    
    # absorb tracking efficiency into tau ID SF
    #harvester.cp().process(['TTT','TTJ','ZTT','ZJ','ZL','STT','STJ','VV']).AddSyst(
    #    harvester, 'CMS_eff_tracking', 'lnN', SystMap()(1.04)) # tau
    #
    #if emuCR>1: # emu + tau
    #  for id, region in cats['emuCR']:
    #    harvester.cp().process(['W']).bin_id([id]).AddSyst(		
    #      harvester, 'CMS_eff_tracking', 'lnN', SystMap()(1.04)) # tau
    
    harvester.cp().process(['QCD']).AddSyst(
        harvester, 'CMS_$ANALYSIS_qcdSyst_$CHANNEL_$ERA', 'lnN', SystMap()(1.30))
    
    harvester.cp().process(['W']).bin_id([1,2]).AddSyst(
        harvester, 'CMS_$ANALYSIS_wNorm_$ERA', 'lnN', SystMap()(1.15))
    
    for id, region in cats['emuCR']:
      harvester.cp().process(['W']).bin_id([id]).AddSyst(
        harvester, 'CMS_$ANALYSIS_wXsec_$ERA', 'lnN', SystMap()(1.05))
    
    #harvester.cp().process(procs['sig']).AddSyst(
    #    harvester, 'CMS_$ANALYSIS_qcd_scale_$ERA', 'lnN', SystMap('channel')
    #        (channels, 1.005))
    
    harvester.cp().process(procs['DY']).AddSyst(
        harvester, 'CMS_$ANALYSIS_zjXsec_$ERA', 'lnN', SystMap()(1.30)) # uncertainty on Z+b jet
    
    harvester.cp().process(procs['TT']).AddSyst(
        harvester, 'CMS_$ANALYSIS_ttjXsec_$ERA', 'lnN', SystMap()(1.06))
    
    harvester.cp().process(procs['ST']).AddSyst(
        harvester, 'CMS_$ANALYSIS_stXsec_$ERA', 'lnN', SystMap()(1.05))
    
    harvester.cp().process(['VV']).AddSyst(
        harvester, 'CMS_$ANALYSIS_vvXsec_$ERA', 'lnN', SystMap()(1.05))
    
    #harvester.cp().process(procs['sig']).AddSyst(
    #    harvester, 'CMS_$ANALYSIS_pdf_scale_$ERA', 'lnN', SystMap()(1.015))
    
    harvester.cp().process(['ZL']).AddSyst(
        harvester, 'CMS_$ANALYSIS_rate_mTauFake_$ERA', 'lnN', SystMap()(1.25))
    
    harvester.cp().process(['TTT','TTJ','ZTT','ZJ','ZL','STT','STJ','VV']).AddSyst(
        harvester, 'CMS_$ANALYSIS_btag_$ERA', 'lnN', SystMap()(1.10)) # 3% -> 10%
    
    for id, region in cats['emuCR']:
      harvester.cp().process(['W']).bin_id([id]).AddSyst(
        harvester, 'CMS_$ANALYSIS_btag_$ERA', 'lnN', SystMap()(1.10)) # 3% -> 10%
    
    #harvester.cp().AddSyst( 
    #    harvester, 'topReweight', 'shape', SystMap('channel', 'process')
    #    (['mt'], ['TTT', 'TTJ'], 1.0))
    
    for proc in ['TTJ','ZJ','STJ','W']:
      for id, region in [(1,"Pass"),(2,"Fail")]:
        harvester.cp().process([proc]).bin_id([id]).AddSyst(
            harvester, 'CMS_$ANALYSIS_rate_jetTauFake%s_%s_$ERA'%(region,proc), 'lnN', SystMap()(1.20))
      for id, region in cats['emuCR']:
        #if proc not in procs['bkgCR']: continue
        region = "Pass" if "pass" in region else "Fail" if "fail" in region else ""
        harvester.cp().process([proc]).bin_id([id]).AddSyst(
            harvester, 'CMS_$ANALYSIS_rate_jetTauFake%s_%s_$ERA'%(region,proc), 'lnN', SystMap()(1.20))
    
    if doShapes:
      harvester.cp().process(['TTT','ZTT','STT']).bin_id([1,2]).AddSyst(
        harvester, 'CMS_$ANALYSIS_shape_t_mt_$ERA', 'shape', SystMap()(1.0))
      
      harvester.cp().process(['TTJ','ZJ','STJ','W']).AddSyst(
        harvester, 'CMS_$ANALYSIS_shape_jetTauFake_$ERA', 'shape', SystMap()(1.0))
      
      harvester.cp().AddSyst(
        harvester, 'CMS_$ANALYSIS_shape_jes_$ERA', 'shape', SystMap()(1.0))
      
      harvester.cp().AddSyst(
        harvester, 'CMS_$ANALYSIS_shape_jer_$ERA', 'shape', SystMap()(1.0))
      
      harvester.cp().AddSyst(
        harvester, 'CMS_$ANALYSIS_shape_uncEn_$ERA', 'shape', SystMap()(1.0))
      
      for id, region in cats['emuCR']:
        harvester.cp().bin_id([id]).AddSyst(
          harvester, 'CMS_$ANALYSIS_shape_e_em_$ERA',      'shape', SystMap()(1.0))
        harvester.cp().process(['TTJ','STJ']).bin_id([id]).AddSyst(
          harvester, 'CMS_$ANALYSIS_shape_jetTauFake_$ERA', 'shape', SystMap()(1.0))
    
    # EXTRACT SHAPES
    print green(">>> extracting shapes...")
    filename = "%s/%s_%s_tid_%s.inputs-%s%s.root"%(INPUT_DIR,analysis,channel,var,era,tag)
    #checkFile(filename)
    print ">>>   file %s" % (filename)
    harvester.cp().bin_id([1,2]).channel([channel]).backgrounds().ExtractShapes( filename, "$BIN/$PROCESS",      "$BIN/$PROCESS_$SYSTEMATIC"     )
    harvester.cp().bin_id([1,2]).channel([channel]).signals().ExtractShapes(     filename, "$BIN/$PROCESS$MASS", "$BIN/$PROCESS$MASS_$SYSTEMATIC") #$MASS
    for id, region in cats['emuCR']:
      filenameCR = "%s/%s_em_tid_%s.inputs-%s%s.root"%(INPUT_DIR,analysis,var,era,tag)
      #checkFile(filenameCR)
      print ">>>   file %s (CR)" % (filenameCR)
      harvester.cp().bin_id([id]).channel([channel]).backgrounds().ExtractShapes( filenameCR, "$BIN/$PROCESS",      "$BIN/$PROCESS_$SYSTEMATIC"     )
      harvester.cp().bin_id([id]).channel([channel]).signals().ExtractShapes(     filenameCR, "$BIN/$PROCESS$MASS", "$BIN/$PROCESS$MASS_$SYSTEMATIC") #$MASS
    
    # AUTOREBIN
    print green(">>> automatically rebin (30%)...")
    rebin = AutoRebin().SetBinThreshold(0.).SetBinUncertFraction(0.30).SetRebinMode(1).SetPerformRebin(True).SetVerbosity(1)
    rebin.Rebin(harvester,harvester)
    
    # BINS
    print green(">>> generating unique bin names...")
    bins = harvester.bin_set()
    #SetStandardBinNames(harvester) # breaks combine MaxLikelihoodFit with TagAndProbe's POI "SF"
    
    # BIN NAMES
    print green(">>> generating bbb uncertainties...")
    bbb = BinByBinFactory()
    bbb.SetAddThreshold(0.0).SetFixNorm(False)
    #.SetFixNorm(False)
    bbb.AddBinByBin(harvester.cp().process(procs['sig']+procs['bkg']), harvester)
    #bbb.MergeBinErrors(harvester.cp().process(procs['sig'] + ['W', 'QCD', 'ZJ', 'ZL']))
    #bbb.SetMergeThreshold(0.0)
    if verbosity>0:
      print green("\n>>> print observation...\n")
      harvester.PrintObs()
      print green("\n>>> print processes...\n")
      harvester.PrintProcs()
      print green("\n>>> print systematics...\n")
      harvester.PrintSysts()
      print green("\n>>> print parameters...\n")
      harvester.PrintParams()
      print "\n"
    
    # WRITER
    print green(">>> writing datacards...")
    outputdir    = "output"
    datacardtxt  = "$TAG/$ANALYSIS_$CHANNEL_%s-$BINID%s-$ERA.txt"%(var,tag)
    datacardroot = "$TAG/$ANALYSIS_$CHANNEL_%s-%s%s.input-$ERA.root"%(var,isoWP,tag)
    writer = CardWriter(datacardtxt,datacardroot)
    writer.SetVerbosity(1)
    writer.SetWildcardMasses([ ])
    writer.WriteCards(outputdir, harvester)
    
    # REPLACE bin ID by bin name
    for bin, region in cats['all']:
      if "emuCR" in region and isoWP not in region: region = region.replace("emuCR","%s-emuCR"%isoWP)
      oldfilename = datacardtxt.replace('$TAG',outputdir).replace('$ANALYSIS',analysis).replace('$CHANNEL',channel).replace('$BINID',str(bin)).replace('$ERA',era)
      newfilename = datacardtxt.replace('$TAG',outputdir).replace('$ANALYSIS',analysis).replace('$CHANNEL',channel).replace('$BINID',region).replace('$ERA',era)
      if os.path.exists(oldfilename):
        os.rename(oldfilename, newfilename)
        print '>>> renaming "%s" -> "%s"'%(oldfilename,newfilename)
      else:
        print '>>> Warning! "%s" does not exist!'%(oldfilename)
    


def green(string,**kwargs):
    return "\x1b[0;32;40m%s\033[0m"%string

def ensureDirectory(dirname):
    """Make directory if it does not exist."""
    if not os.path.exists(dirname):
      os.makedirs(dirname)
      print ">>> made directory " + dirname
    return dirname

def checkFile(filename):
    """Check existence of the file."""
    if not os.path.exists(filename):
      print ">>> ERROR! %s does not exist!"%(filename)
      exit(1)
    


def main():
    
    global isoWPs, emuCR
    
    channels = [ 'mt', ] #'et', ]
    vars     = [ 'pfmt_1',] #'m_vis', ]
    if not isoWPs:
      isoWPs   = [ 'loose',
                   'medium',
                   'tight',
                   'vtight',
                   'vvtight',
      ]
    if observables: vars = observables

    #print "isoWPs =",isoWPs
    for channel in channels:
      for var in vars:
        for isoWP in isoWPs:
          harvest(channel,var,isoWP,emuCR=emuCR)




if __name__ == '__main__':
    main()
    print ">>>\n>>> done\n"
    

