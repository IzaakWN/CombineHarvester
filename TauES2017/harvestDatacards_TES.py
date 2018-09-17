#! /usr/bin/env python
# Author: Izaak Neutelings (January 2018)

import os, sys, re
from argparse import ArgumentParser
import CombineHarvester.CombineTools.ch as ch
from CombineHarvester.CombineTools.ch import CombineHarvester, MassesFromRange, SystMap, BinByBinFactory, CardWriter, SetStandardBinNames, AutoRebin
import CombineHarvester.CombinePdfs.morphing as morphing
from CombineHarvester.CombinePdfs.morphing import BuildRooMorphing
import ROOT
from ROOT import RooWorkspace, TFile, RooRealVar

argv = sys.argv
description = '''This script makes datacards with CombineHarvester.'''
parser = ArgumentParser(prog="harvesterDatacards_TES",description=description,epilog="Succes!")
parser.add_argument( '-t', "--tag",         dest="tags", type=str, nargs='+', default=[ ], action='store',
                     metavar="TAG",         help="tag for a file names" )
parser.add_argument( '-e', "--extra-tag",   dest="extratag", type=str, default="", action='store',
                     metavar="TAG",         help="extra tag for output files" )
parser.add_argument( '-d', "--decayMode",   dest="DMs", type=str, nargs='*', default=[ ], action='store',
                     metavar="DECAYMODE",   help="decay mode" )
parser.add_argument( '-o', "--observable",  dest="observables", type=str, nargs='*', default=[ ], action='store',
                     metavar="VARIABLE",    help="name of observable for TES measurement" )
parser.add_argument( '-r', "--shift-range", dest="shiftRange", type=str, default="0.940,1.060", action='store',
                     metavar="RANGE",       help="range of TES shifts" )
parser.add_argument( '-n', "--no-shapes",   dest="noShapes",  default=False, action='store_true',
                                            help="do not include shape uncertainties" )
parser.add_argument( '-M', "--multiDimFit", dest="multiDimFit",  default=False, action='store_true',
                                            help="assume multidimensional fit with a POI for each DM" )
parser.add_argument( '-v', "--verbose",     dest="verbose",  default=False, action='store_true',
                                            help="set verbose" )
args = parser.parse_args()

DIR_DC      = "./input"
verbosity   = 1 if args.verbose else 0
doShapes    = not args.noShapes #and False
multiDimFit = args.multiDimFit
morphQCD    = True and False
doFR        = True #and False
filterZJforDM10  = True #and False
signalBBB   = True #and False

TIDSF       = 1 #0.883 # https://indico.cern.ch/event/719687/contributions/2958973/attachments/1629304/2596258/tauid_30mar.pdf
observables = [o for o in args.observables if '#' not in o]

# RANGE
shiftRange  = args.shiftRange
parts = shiftRange.split(',')
if len(parts)!=2 or not parts[0].replace('.','',1).isdigit() or not parts[1].replace('.','',1).isdigit():
  print '>>> Warning! Not a valid range: "%s". Please pass two comma-separated values.'%(shiftRange); exit(1)
minshift    = float(parts[0])-1.
maxshift    = float(parts[1])-1.
steps       = 0.001
tesshifts   = [ "%.3f"%(1+s*steps) for s in xrange(int(minshift/steps),int(maxshift/steps)+1)]
print tesshifts



def harvest(channel,var,DMs,**kwargs):
    """Harvest cards."""
    
    tag      = kwargs.get('tag',      ""      )
    extratag = kwargs.get('extratag', ""      )
    era      = kwargs.get('era',      '13TeV' )
    analysis = kwargs.get('analysis', 'ztt'   )
    newDMs   = kwargs.get('newDMs',   'newDM' in tag+extratag )
    
    if newDMs: 
      cats   = [ (1, 'DM0'), (2, 'DM1'), (3, 'DM10'), (4, 'DM11') ] # (4, 'all') ]
    else:
      cats   = [ (1, 'DM0'), (2, 'DM1'), (3, 'DM10') ]
    cats     = [ (c,d) for c,d in cats if d in DMs and (d!='DM0' or var!='m_2') ]
    procs    = {
        'sig':   [ 'ZTT' ],
        'bkg':   [ 'ZJ', 'ZL', 'TTT', 'TTJ', 'W', 'QCD', 'STT', 'STJ', 'VV' ],
        'noQCD': [ 'ZJ', 'ZL', 'TTT', 'TTJ', 'W',        'STT', 'STJ', 'VV' ],
        'DY':    [ 'ZTT', 'ZJ', 'ZL' ],
        'TT':    [ 'TTT', 'TTJ' ],
        'ST':    [ 'STT', 'STJ' ],
    }
    if doFR:
      procs['bkg'].append('JTF')
    procs['morph'] = [ 'ZTT', 'QCD' ] if morphQCD else [ 'ZTT' ]
    procs['all'] = procs['sig'] + procs['bkg']
    #if doFR:
    #  for key, list in procs.iteritems():
    #    procs[key] = [b for b in list if b not in ['QCD','W','ZJ']]
    
    # HARVESTER
    harvester = CombineHarvester()
    if morphQCD:
      harvester.AddObservations(  ['*'],     [analysis], [era], [channel],                 cats         )
      harvester.AddProcesses(     ['*'],     [analysis], [era], [channel], procs['noQCD'], cats, False  )
      harvester.AddProcesses(     tesshifts, [analysis], [era], [channel], ['QCD'],        cats, False  )
      harvester.AddProcesses(     tesshifts, [analysis], [era], [channel], procs['sig'],   cats, True   )
    else:
      harvester.AddObservations(  ['*'],     [analysis], [era], [channel],                 cats         )
      harvester.AddProcesses(     ['*'],     [analysis], [era], [channel], procs['bkg'],   cats, False  )
      harvester.AddProcesses(     tesshifts, [analysis], [era], [channel], procs['sig'],   cats, True   )
    
    # FILTER
    if filterZJforDM10:
      harvester.FilterAll(lambda obj: obj.bin_id()==3 and obj.process()=='ZL')
    if doFR:
      harvester.FilterAll(lambda obj: obj.process() in ['QCD','W','ZJ','STJ'] ) #'TTJ'
    
    # NUISSANCE PARAMETERS
    print green("\n>>> defining nuissance parameters ...")
    
    harvester.cp().process(procs['DY']+procs['TT']+procs['ST']+['VV']).AddSyst(
        harvester, 'CMS_lumi', 'lnN', SystMap()(1.025))
    
    harvester.cp().process(procs['DY']+procs['TT']+procs['ST']+['VV']).AddSyst(
        harvester, 'CMS_eff_m', 'lnN', SystMap()(1.02))
    
    harvester.cp().process(['TTT','ZTT','STT']).AddSyst(
        harvester, 'CMS_eff_t_$BIN', 'lnN', SystMap()(1.03)) # Tau ID estimate from Cecile's measurements
    
    #harvester.cp().process(procs['DY']+procs['TT']+procs['ST']+['VV']).AddSyst(
    #    harvester, 'CMS_eff_tracking', 'lnN', SystMap()(1.04))
    
    harvester.cp().process(['W']).AddSyst(
        harvester, 'CMS_$ANALYSIS_wNorm_$ERA', 'lnN', SystMap()(1.15))
    
    harvester.cp().process(['QCD']).AddSyst(
        harvester, 'CMS_$ANALYSIS_qcdSyst_$CHANNEL_$ERA', 'lnN', SystMap()(1.20))  # From Tyler's studies
    
    #harvester.cp().process(procs['sig']).AddSyst(
    #    harvester, 'CMS_$ANALYSIS_qcd_scale_$ERA', 'lnN', SystMap()(1.005))
    
    harvester.cp().process(procs['DY']).AddSyst(
        harvester, 'CMS_$ANALYSIS_zjXsec_$ERA', 'lnN', SystMap()(1.20))
    
    harvester.cp().process(procs['TT']).AddSyst(
        harvester, 'CMS_$ANALYSIS_ttjXsec_$ERA', 'lnN', SystMap()(1.06))
    
    harvester.cp().process(procs['ST']).AddSyst(
        harvester, 'CMS_$ANALYSIS_stXsec_$ERA', 'lnN', SystMap()(1.05))
    
    harvester.cp().process(['VV']).AddSyst(
        harvester, 'CMS_$ANALYSIS_vvXsec_$ERA', 'lnN', SystMap()(1.05))
    
    #harvester.cp().process(procs['sig']).AddSyst(
    #    harvester, 'CMS_$ANALYSIS_pdf_scale_$ERA', 'lnN', SystMap()(1.015))
    
    harvester.cp().process(['ZL']).AddSyst(
        harvester, 'CMS_$ANALYSIS_rate_mTauFake_$BIN_$ERA', 'lnN', SystMap()(1.25))
    
    if doFR:
      harvester.cp().process(['JTF']).AddSyst(
          harvester, 'CMS_$ANALYSIS_rate_jetTauFake_$BIN_$ERA', 'lnN', SystMap()(1.15))
    else:
      harvester.cp().process(['TTJ','ZJ','STJ','W','QCD']).AddSyst(
          harvester, 'CMS_$ANALYSIS_rate_jetTauFake_$ERA', 'lnN', SystMap()(1.20)) # decorrelate?
    
    if doShapes:
      if doFR:
        harvester.cp().process(['JTF']).AddSyst(
          harvester, 'CMS_$ANALYSIS_shape_jetTauFake_$BIN_$ERA', 'shape', SystMap()(1.00))
      else:
        harvester.cp().process(['TTJ','W','STJ','QCD']).AddSyst( #'ZJ'
          harvester, 'CMS_$ANALYSIS_shape_jetTauFake_$BIN_$ERA', 'shape', SystMap()(1.00))
      
      if 'm_vis' in var:
        harvester.cp().process(['ZL']).bin_id([1,2]).AddSyst(
         harvester, 'CMS_$ANALYSIS_shape_mTauFake_$BIN_$ERA', 'shape', SystMap()(1.00))
      
      harvester.cp().process(['ZTT']).AddSyst(
        harvester, 'CMS_$ANALYSIS_shape_dy_$CHANNEL_$ERA', 'shape', SystMap()(1.00))
      harvester.cp().process(['ZL']).bin_id([1,2]).AddSyst(
        harvester, 'CMS_$ANALYSIS_shape_dy_$CHANNEL_$ERA', 'shape', SystMap()(1.00))
      
      #harvester.cp().process(['ZTT','ZJ','ZL','TTT','TTJ','STT','STJ','W','QCD','JTF']).AddSyst(
      #  harvester, 'CMS_$ANALYSIS_shape_m_$CHANNEL_$ERA', 'shape', SystMap()(1.00))
      
      #harvester.cp().process(['ZJ','TTT','TTJ','STT','STJ','W','QCD']).AddSyst(
      #  harvester, 'CMS_$ANALYSIS_shape_jes_$ERA', 'shape', SystMap()(1.00))
      
      #harvester.cp().process(['ZJ','TTT','TTJ','STT','STJ','W','QCD']).AddSyst(
      #  harvester, 'CMS_$ANALYSIS_shape_jer_$ERA', 'shape', SystMap()(1.00))
      
      #harvester.cp().process(['ZJ','TTT','TTJ','STT','STJ','W','QCD']).AddSyst(
      #  harvester, 'CMS_$ANALYSIS_shape_uncEn_$ERA', 'shape', SystMap()(1.0))
    
    # EXTRACT SHAPES
    print green(">>> extracting shapes...")
    filename = "%s/%s_%s_tes_%s.inputs-%s%s.root"%(DIR_DC,analysis,channel,var,era,tag)
    print ">>>   file %s" % (filename)
    if morphQCD:
      harvester.cp().channel([channel]).process(procs['noQCD']).ExtractShapes( filename, "$BIN/$PROCESS",          "$BIN/$PROCESS_$SYSTEMATIC")
      harvester.cp().channel([channel]).process(     ['QCD']  ).ExtractShapes( filename, "$BIN/$PROCESS_TES$MASS", "$BIN/$PROCESS_TES$MASS_$SYSTEMATIC")
      harvester.cp().channel([channel]).signals(              ).ExtractShapes( filename, "$BIN/$PROCESS_TES$MASS", "$BIN/$PROCESS_TES$MASS_$SYSTEMATIC")
    elif doFR:
      harvester.cp().channel([channel]).backgrounds().ExtractShapes( filename, "$BIN/$PROCESS",          "$BIN/$PROCESS_$SYSTEMATIC")
      harvester.cp().channel([channel]).signals().ExtractShapes(     filename, "$BIN/$PROCESS_TES$MASS", "$BIN/$PROCESS_TES$MASS_$SYSTEMATIC")
    else:
      #harvester.cp().channel([channel]).backgrounds(          ).ExtractShapes( filename, "$BIN/$PROCESS",          "$BIN/$PROCESS_$SYSTEMATIC")
      harvester.cp().channel([channel]).process(procs['noQCD']).ExtractShapes( filename, "$BIN/$PROCESS",          "$BIN/$PROCESS_$SYSTEMATIC")
      harvester.cp().channel([channel]).process(     ['QCD']  ).ExtractShapes( filename, "$BIN/$PROCESS_TES1.000", "$BIN/$PROCESS_TES1.000_$SYSTEMATIC")
      harvester.cp().channel([channel]).signals(              ).ExtractShapes( filename, "$BIN/$PROCESS_TES$MASS", "$BIN/$PROCESS_TES$MASS_$SYSTEMATIC")
    
    # SCALE on the fly
    #if TIDSF!=1.0:
    #  harvester.cp().process(['ZTT','TTT','STT']).ForEachProc(lambda proc: scaleProcess(proc,TIDSF))
    
    # AUTOREBIN
    #print green(">>> automatically rebin (30%)...")
    #rebin = AutoRebin().SetBinThreshold(0.).SetBinUncertFraction(0.30).SetRebinMode(1).SetPerformRebin(True).SetVerbosity(1)
    #rebin.Rebin(harvester,harvester)
    
    # BINS
    print green(">>> generating unique bin names...")
    bins = harvester.bin_set()
    #SetStandardBinNames(harvester,"%s_$BINID_$ERA"%(var))
    
    ### BIN NAMES
    print green(">>> generating bbb uncertainties...")
    procsBBB = procs['bkg'] + procs['sig'] if signalBBB else procs['bkg']
    bbb = BinByBinFactory()
    bbb.SetAddThreshold(0.0)
    ###.SetFixNorm(False)
    bbb.AddBinByBin(harvester.cp().process(procsBBB), harvester)
    ###bbb.MergeBinErrors(harvester.cp().process(procs['sig'] + ['W', 'QCD', 'ZJ', 'ZL']))
    ###bbb.SetMergeThreshold(0.0)
    
    # ROOVAR
    pois = [ ]
    workspace = RooWorkspace(analysis,analysis)
    if multiDimFit:
      for bin in bins:
        tesname = "tes_%s"%(bin)
        tes = RooRealVar(tesname,tesname,1.+minshift,1.+maxshift);
        tes.setConstant(True)
        pois.append(tes)
    else:
      tes = RooRealVar('tes','tes',1.+minshift,1.+maxshift);
      tes.setConstant(True)
      pois = [tes]*len(bins)
        
   
    # MORPHING
    print green(">>> morphing...")
    debugdir  = ensureDirectory("debug")
    debugfile = TFile("%s/morph_debug_%s_%s%s.root"%(debugdir,channel,var,tag+extratag), 'RECREATE')
    verboseMorph = verbosity>0
    for bin, poi in zip(bins,pois):
      print '>>>   bin "%s"...'%(bin)
      for proc in procs['morph']:
        #print ">>> bin %s, proc %s"%(bin,proc)
        BuildRooMorphing(workspace, harvester, bin, proc, poi, "norm", True, verboseMorph, False, debugfile)
    debugfile.Close()
    
    # EXTRACT PDFs
    print green(">>> add workspace and extract pdf...")
    harvester.AddWorkspace(workspace, False)
    harvester.cp().process(procs['morph']).ExtractPdfs(harvester, analysis, "$BIN_$PROCESS_morph", "")
    
    # NUISANCE PARAMETER GROUPS
    print green(">>> setting nuisance parameter groups...")
    harvester.SetGroup( "all",      [ ".*"               ])
    harvester.SetGroup( "bin",      [ ".*_bin_.*"        ])
    harvester.SetGroup( "sys",      [ "^((?!bin).)*$"    ]) # everything except bin-by-bin
    harvester.SetGroup( "lumi",     [ ".*_lumi"          ])
    harvester.SetGroup( "JTF",      [ ".*_jetTauFake_.*" ])
    #harvester.RemoveGroup(  "syst", [ "lumi_.*" ])
    
    # PRINT
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
    datacardtxt  = "$TAG/$ANALYSIS_$CHANNEL_%s-$BINID%s-$ERA.txt"%(var,tag+extratag)
    datacardroot = "$TAG/$ANALYSIS_$CHANNEL_%s%s.input-$ERA.root"%(var,tag+extratag)
    writer = CardWriter(datacardtxt,datacardroot)
    writer.SetVerbosity(1)
    writer.SetWildcardMasses([ ])
    writer.WriteCards(outputdir, harvester)
    
    # REPLACE bin ID by bin name
    for bin, DM in cats:
      oldfilename = datacardtxt.replace('$TAG',outputdir).replace('$ANALYSIS',analysis).replace('$CHANNEL',channel).replace('$BINID',str(bin)).replace('$ERA',era)
      newfilename = datacardtxt.replace('$TAG',outputdir).replace('$ANALYSIS',analysis).replace('$CHANNEL',channel).replace('$BINID',DM).replace('$ERA',era)
      if os.path.exists(oldfilename):
        os.rename(oldfilename, newfilename)
        print '>>> renaming "%s" -> "%s"'%(oldfilename,newfilename)
      else:
        print '>>> Warning! "%s" does not exist!'%(oldfilename)
    

def scaleProcess(process,scale):
  """Helpfunction to scale a given process."""
  #print '>>> scaleProcess("%s",%.3f):'%(process.process(),scale)
  #print ">>>   rate before = %s"%(process.rate())
  process.set_rate(process.rate()*scale)
  #print ">>>   rate after  = %s"%(process.rate())

def green(string,**kwargs):
    return kwargs.get('pre',"")+"\x1b[0;32;40m%s\033[0m"%string

def ensureDirectory(dirname):
    """Make directory if it does not exist."""
    if not os.path.exists(dirname):
      os.makedirs(dirname)
      print ">>> made directory " + dirname
    return dirname



def main():
    
    channels = [ 'mt', ] #'et', ]
    vars     = [ 'm_2', 'm_vis', ]
    DMs      = [ 'DM0','DM1','DM10', ]
    
    DMs      = args.DMs if args.DMs else DMs
    vars     = observables if observables else vars
    extratag = args.extratag
    if multiDimFit:
      extratag += "_MDF"
    
    for tag in args.tags:
      if "_0p" in tag: vars = [ v for v in vars if v!='m_vis' ]
      if "_85" in tag: vars = [ v for v in vars if v!='m_2'   ]
    
      for channel in channels:
        for var in vars:
          harvest(channel,var,DMs,tag=tag,extratag=extratag)
    



if __name__ == '__main__':
    main()
    print ">>>\n>>> done harvesting\n"
    

