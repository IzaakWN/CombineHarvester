#! /usr/bin/env python
# Author: Izaak Neutelings (January 2018)
#
# Copy file:
#  https://root.cern.ch/doc/master/classTFile.html#aaf0edbf57091f9d941caf134f1207156
#
# Poisson errors:
#  https://twiki.cern.ch/twiki/bin/view/CMS/StatisticsCommittee
#  https://github.com/DESY-CMS-SUS/cmgtools-lite/blob/8_0_25/TTHAnalysis/python/plotter/mcPlots.py#L70-L102
#  https://github.com/DESY-CMS-SUS/cmgtools-lite/blob/8_0_25/TTHAnalysis/python/plotter/susy-1lep/RcsDevel/plotDataPredictWithSyst.py#L12-L21
#  https://root.cern.ch/doc/master/TH1_8cxx_source.html#l08344
#  https://root.cern.ch/doc/master/group__QuantFunc.html
#
# Asimov dataset
#  https://twiki.cern.ch/twiki/bin/view/Main/LearningRoostats#4_Asimov_datasets
#

import sys, os, re
import glob
from argparse import ArgumentParser
#import CMS_lumi, tdrstyle
import ROOT
from ROOT import gPad, gROOT, gStyle, TFile, TVectorD, Math, Double,\
                 TCanvas, TLegend, TLatex, TText,\
                 TH1, TH1D, TH1F, TH2F, THStack, TF1, TGraph, TGraphErrors, TGraphAsymmErrors,\
                 kBlack, kRed, kBlue, kAzure, kGreen, kGreen, kYellow, kOrange, kMagenta, kViolet,\
                 kSolid, kDashed, kDotted, kDashDotted
from math import sqrt, log, floor, ceil
ROOT.gROOT.SetBatch(ROOT.kTRUE)
gStyle.SetOptStat(0)

argv = sys.argv
description = """This script runs combine on data cards, extracts limits from the output and plot them."""
parser = ArgumentParser(prog="plotLimits",description=description,epilog="Succes!")
parser.add_argument( "-v", "--verbose", dest="verbose", default=False, action='store_true',
                     help="set verbose" )
parser.add_argument( "-f", "--force", dest="force", default=False, action='store_true',
                     help="force overwriting of existing files" )
args = parser.parse_args()

# PLOT OPTIONS
IN_DIR      = "./input"
OUT_DIR     = IN_DIR
DIR         = "./output" #"/shome/ineuteli/analysis/CMSSW_7_4_8/src/CombineHarvester/LowMassTauTau/output"
mylabel     = "_Moriond" # ICHEP
force       = args.force
verbosity   = 1*args.verbose



# REBIN histograms
def rebinHistograms(oldfilename,xmin,xmax,**kwargs):
    """Rebin given histograms in a given file. (Set bin content and error of bins outside range to zero.)"""
    print '>>> rebinHistograms histogram in "%s"'%(green(oldfilename))
    
    newtag      = kwargs.get( 'tag',    "_rebinned"  )
    newfilename = kwargs.get( 'out',     ""          )
    dirnames    = kwargs.get( 'dirs',    [ ]         )
    forceEdit   = kwargs.get( 'force',   False       )
    
    if not newfilename:
      if ".root" not in oldfilename[-5:]:
        oldfilename += ".root"
      newfilename = oldfilename.replace('.root',"%s.root"%newtag)
    
    print '>>> rebin histograms \n>>>   from   "%s"\n>>>   to     "%s"'%(oldfilename,newfilename)
    oldfile = ensureTFile(oldfilename)
    newfile = None
    if newfilename != oldfilename:
      if not forceEdit and os.path.exists(newfilename):
        error('rebinHistograms: New filenames "%s" already exists! Use the -f flag if you are certain you want to edit this file.'%(newfilename))
      succes  = oldfile.Cp(newfilename,True)
      newfile = ensureTFile(newfilename,'UPDATE')
    elif forceEdit:
      warning('rebinHistograms: Old and new filenames are the same "%s"')
      newfile = oldfile
    else:
      error('rebinHistograms: Old and new filenames are the same "%s"! Use the -f flag if you are certain you want to edit this file.'%(newfilename))
    if not oldfile:
      error('rebinHistograms: Could not open "%s".'%(oldfilename))
    if not newfile:
      error('rebinHistograms: Could not open "%s".'%(newfilename))
    if oldfile!=newfile:
      oldfile.Close()
    
    # DIRS
    if not dirnames:
      dirnames = findTDirs(newfile)    
    for dirname in dirnames:
        print ">>>\n>>>   directory %s"%(dirname)
        subdir = newfile.Get(dirname)
        if not subdir:
          error('rebinHistograms: Could not open directory "%s" in "%s"!'%(dirname,newfilename))
        subdir.cd()
        rebinHistogramsInDir(subdir,xmin,xmax,**kwargs)
    newfile.Close()
    print ">>>"
    
# REBIN histograms in TDirectory
def rebinHistogramsInDir(dir,xmin,xmax,**kwargs):
    """Help function (for recursive use) to rebin histograms in given TDirectory."""
    
    dir.cd()
    keylist = [k for k in dir.GetListOfKeys()]
    nkeys   = len(keylist)
    #print ">>>    looping over %d keys"%(nkeys)
    for i, key in enumerate(keylist):
      #if i and i%10==0: print ">>>       %d, key %s"%(i,key)
      keyname  = key.GetName()
      keyclass = gROOT.GetClass(key.GetClassName())
      if keyclass.InheritsFrom("TDirectory"):
        rebinHistogramsInDir(key,xmin,xmax,**kwargs)
      elif keyclass.InheritsFrom("TH1"):
        newhist = dir.Get(keyname).Clone()
        rebinHistogram(newhist,xmin,xmax)
        newhist.Write(keyname,TFile.kOverwrite)
    
# REBIN histogram
def rebinHistogram(hist,xmin,xmax,**kwargs):
    """Rebin given histogram, by setting a bin's content and error to zero if the bin fall out of the given range."""
    for i in range(0,hist.GetXaxis().GetNbins()+2):
      if xmin!=None:
        xlow = hist.GetXaxis().GetBinLowEdge(i)
        if xlow<xmin:
          hist.SetBinContent(i,0)
          hist.SetBinError(i,0)
      if xmax!=None:
        xup  = hist.GetXaxis().GetBinUpEdge(i)
        if xup>xmax:
          hist.SetBinContent(i,0)
          hist.SetBinError(i,0)
    


# MAKE ASIMOV dataset
def makeAsimovDataSet(oldfilename,backgrounds,**kwargs):
    """Make an Asimove data set from the background processes in a datacard and replace
    the data_obs histogram in a copy of the file."""
    
    newtag      = kwargs.get( 'tag',    "_Asimov"   )
    newfilename = kwargs.get( 'out',     ""          )
    dirnames    = kwargs.get( 'dirs',    [ ]         )
    forceEdit   = kwargs.get( 'force',   False       )
    
    if not newfilename:
      if ".root" not in oldfilename[-5:]:
        oldfilename += ".root"
      newfilename = oldfilename.replace('.root',"%s.root"%newtag)
    
    print '>>> making Asimov data set \n>>>   from   "%s"\n>>>   to     "%s"'%(oldfilename,newfilename)
    oldfile = ensureTFile(oldfilename)
    newfile = None
    if newfilename != oldfilename:
      if not forceEdit and os.path.exists(newfilename):
        error('makeAsimovDataSet: New filenames "%s" already exists! Use the -f flag if you are certain you want to edit this file.'%(newfilename))
      succes  = oldfile.Cp(newfilename,True)
      newfile = ensureTFile(newfilename,'UPDATE')
    elif forceEdit:
      warning('makeAsimovDataSet: Old and new filenames are the same "%s"')
      newfile = oldfile
    else:
      error('makeAsimovDataSet: Old and new filenames are the same "%s"! Use the -f flag if you are certain you want to edit this file.'%(newfilename))
    if not newfile:
      error('makeAsimovDataSet: Could not open "%s".'%(newfilename))
    
    if not dirnames:
      dirnames = findObjectInTDir("TDirectory",oldfile)
    
    for dirname in dirnames:
        print ">>>\n>>> checking directory %s:%s/"%(oldfilename,dirname)
        
        # DIRs
        oldsubdir = oldfile.Get(dirname)
        newsubdir = newfile.Get(dirname)
        if not oldsubdir:
          error('makeAsimovDataSet: Could not open directory "%s" in "%s"!'%(dirname,oldfilename))
        if not newsubdir:
          error('makeAsimovDataSet: Could not open directory "%s" in "%s"!'%(dirname,newfilename))
        newsubdir.cd()
        #print "%s"%(subdir.ls())
        
        # DATA
        olddata = oldsubdir.Get("data_obs")
        if not olddata:
          error('makeAsimovDataSet: Could not find "data_obs" histogram in %s:%s!'%(oldfilename,dirname))
        name, title = "data_obs_new", olddata.GetTitle() #olddata.GetName()
        N, a, b     = olddata.GetNbinsX(), olddata.GetXaxis().GetXmin(), olddata.GetXaxis().GetXmax()
        newdata = TH1F(name, title, N, a, b)
        print '>>>   made TH1F("%s", "%s",%d,%g,%g)'%(name,title,N,a,b)
        newdata.Sumw2(True)
        #newdata.SetBinErrorOption(olddata.GetBinErrorOption()) #TH1F.kPoisson)
        
        # BACKGROUNDs
        for background in backgrounds:
          hist = oldsubdir.Get(background)
          if not hist: continue
          print ">>>   adding %-6s (integral %5.1f)"%('"%s"'%hist.GetName(),hist.Integral())
          newdata.Add(hist)
        print '>>>   "data_obs" has integral %.1f'%(newdata.Integral())
        print '>>>   overwriting "data_obs"...'
        newdata.Write("data_obs",TFile.kOverwrite)
    oldfile.Close()
    newfile.Close()
    


# MAKE ASIMOV dataset
def replaceDataSet(filename1,filename2,**kwargs):
    """Replace dataset of datacard 1 with that of datacard 2."""
    return
    


# RENAME histograms
def renameHistograms(filename,histnames,**kwargs):
    """Rename given histograms."""
    
    dirnames    = kwargs.get( 'dirs',       [ ]     )
    doRegex     = kwargs.get( 'regex',      True    )
    forceEdit   = kwargs.get( 'force',      False   )
    deleteOld   = kwargs.get( 'deleteOld',  True    )
    
    print '>>> renaming histogram in "%s"'%(green(filename))
    if not os.path.exists(filename):
      error('renameHistograms: File "%s" does not exists!'%(filename))
    file = ensureTFile(filename,"UPDATE")
    
    if not file:
      error('renameHistograms: Could not open "%s".'%(filename))
    
    # DIRS
    if not dirnames:
      print ">>>\n>>>   directory ./"
      renameHistogramsInDir(file,histnames,**kwargs)
      dirnames = findTDirs(file)    
    for dirname in dirnames:
        print ">>>\n>>>   directory %s"%(dirname)
        
        subdir = file.Get(dirname)
        if not subdir:
          error('renameHistograms: Could not open directory "%s" in "%s"!'%(dirname,filename))
        subdir.cd()
        
        renameHistogramsInDir(subdir,histnames,**kwargs)
    
    file.Close()
    print ">>>"
    
# RENAME histograms in TDirectory
def renameHistogramsInDir(dir,histnames,**kwargs):
    """Help function (for recursive use) to rename histograms in given TDirectory."""
    
    doRegex     = kwargs.get( 'regex',      True    )
    forceEdit   = kwargs.get( 'force',      False   )
    deleteOld   = kwargs.get( 'deleteOld',  True    )
    
    # REGEX
    if doRegex:
      patterns  = histnames[:]
      histnames = [ ]
      for key in dir.GetListOfKeys():
        if gROOT.GetClass(key.GetClassName()).InheritsFrom('TH1'):
          oldhistname = key.GetName()
          for find, replace in patterns:
            if re.findall(find,oldhistname):
              newhistname = re.sub(find,replace,oldhistname)
              histnames.append(( oldhistname, newhistname ))
              #print ( oldhistname, newhistname )
              break # assume no other matches
      if not histnames:
        print ">>>     no matches found"
    
    # RENAME
    for oldhistname, newhistname in histnames:
      oldhist = dir.Get(oldhistname)
      if not oldhist:
        warning('Did not find "%s"'%(oldhistname),pre="    ")
        continue
      if not oldhist.InheritsFrom('TH1'): #isinstance(oldhist,TH1):
        warning('Object "%s" is not a TH1 object!'%(oldhistname),pre="    ")
        continue
      checkExistingHistogram(dir,newhistname,delete=forceEdit)
      print ">>>     renaming %s -> %s"%('"%s"'%oldhistname,'"%s"'%newhistname)
      #newhist = oldhist.Clone()
      #newhist.SetName(newhistname)
      oldhist.Write(newhistname,TFile.kOverwrite)
      if deleteOld:
        #print '>>>       deleting old "%s"'%(oldhist.GetName())
        dir.Delete("%s;*"%oldhistname)
    


# SUM histograms
def sumHistograms(filename,sumhistname,histnames,**kwargs):
    """SUM given histograms."""
    
    dirnames    = kwargs.get( 'dirs',         [ ]    )
    recursive   = kwargs.get( 'recursive',    True   )
    forceEdit   = kwargs.get( 'force',        False  )
    systematics = kwargs.get( 'systematics',  False  )
    
    print '>>> renaming histogram in "%s"'%(green(filename))
    if not os.path.exists(filename):
      error('renameHistograms: File "%s" does not exists!'%(filename))
    file = ensureTFile(filename,"UPDATE")
    
    # DIRS
    if not dirnames:
      print ">>>\n>>>   directory ./"
      sumHistogramsInDir(file,sumhistname,histnames,**kwargs)
      dirnames = findTDirs(file)    
    for dirname in dirnames:
        print ">>>\n>>>   directory %s"%(dirname)
        subdir = file.Get(dirname)
        if not subdir:
          error('renameHistograms: Could not open directory "%s" in "%s"!'%(dirname,filename))
        subdir.cd()
        sumHistogramsInDir(subdir,sumhistname,histnames,**kwargs)
    file.Close()
    print ">>>"
    
# SUM histograms in TDirectory
def sumHistogramsInDir(dir,sumhistname,histnames,**kwargs):
    """Help function (for recursive use) to SUM histograms in given TDirectory."""
    
    forceEdit   = kwargs.get( 'force',       False  )
    systematics = kwargs.get( 'systematics', False  )
    
    # GET histnames
    nHistsMax = 0
    histnames_dict = { }
    for histname in histnames:
      histnames_dict[histname] = findHistogramsInTDir(dir,histname,regex=False)
      nHists = len(histnames_dict[histname])
      if nHists==0:
        warning('sumHistogramsInDir: did not find "%s", skipping this directory'%(histname),pre="    ")
        return
      if nHists>1:
        warning('sumHistogramsInDir: found more than 1 (%d) for "%s"'%(nHists,histname),pre="    ")
      if nHistsMax>nHists:
        nHistsMax = nHists
    
    # SYSTEMATICS
    shift_histname_dict = { }
    if systematics:
      for histkey in histnames_dict:
        histname0 = histnames_dict[histkey][0]
        for shift in ['Up','Down']:
          histpattern  = "%s_.*%s"%(histname0,shift)
          shiftpattern = "%s_(.*%s)"%(histname0,shift)
          histnames    = findHistogramsInTDir(dir,histpattern,regex=True)
          nShifts      = len(histnames)
          #print ">>>     %s: %s"%(histname0,histnames)
          for histname in histnames:
            shiftnames = re.findall(shiftpattern,histname)
            shiftkey   = shiftnames[0]
            if shiftkey not in shift_histname_dict:
              shift_histname_dict[shiftkey] = { }
            elif histkey in shift_histname_dict[shiftkey]:
              warning('sumHistogramsInDir: found more than one instance of "%s" shift on "%s"'%(shiftkey,histkey))
            shift_histname_dict[shiftkey][histkey] = histname
      for shiftkey in shift_histname_dict:
        for histkey in histnames_dict:
          if histkey not in shift_histname_dict[shiftkey]:
            histname = histnames_dict[histkey][0]
            print '>>>     using "%s" for "%s" shift'%(histname,shiftkey)
            shift_histname_dict[shiftkey][histkey] = histname
        
    # SUM
    sumhist = None
    checkExistingHistogram(dir,sumhistname,delete=forceEdit)
    for histkey in histnames_dict:
      histname = histnames_dict[histkey][0]
      print '>>>     "%s"'%(histname),
      hist     = dir.Get(histname)
      if sumhist:
        print 'adding  to "%s"'%(sumhistname)
        sumhist.Add(hist)
      else:
        print 'cloning to "%s"'%(sumhistname)
        sumhist = hist.Clone(sumhistname)
    sumhist.Write(sumhistname,TFile.kOverwrite)
    
    # SUM systematics
    for shiftkey in shift_histname_dict:
      print '>>>     shift "%s"'%(shiftkey)
      sumhist = None
      shifthistname = "%s_%s"%(sumhistname,shiftkey)
      checkExistingHistogram(dir,shifthistname,delete=forceEdit)
      for histkey in shift_histname_dict[shiftkey]:
        histname = shift_histname_dict[shiftkey][histkey]
        print '>>>       "%s"'%(histname),
        hist     = dir.Get(histname)
        if sumhist:
          print 'adding  to "%s"'%(shifthistname)
          sumhist.Add(hist)
        else:
          print 'cloning to "%s"'%(shifthistname)
          sumhist = hist.Clone(shifthistname)
      sumhist.Write(shifthistname,TFile.kOverwrite)
    


# PRINT contents of files
def printTFileContents(filename,**kwargs):
    """Print recursively of the tree/hierarchy of directories in a given filename."""
    
    file = ensureTFile(filename)
    print ">>> contents of %s"%(filename)
    printTDirContents(file,**kwargs)
    print ">>> "
    
# PRINT contents of dirs
def printTDirContents(dir,**kwargs):
    """Print recursively of the tree/hierarchy of a given directory."""
    space    = kwargs.get('space',"  ")
    contents = kwargs.get('contents',False)
    
    if contents:
      keylist = dir.GetListOfKeys()
      for key in keylist:
        objclass = gROOT.GetClass(key.GetClassName())
        if not objclass.InheritsFrom("TDirectory"):
          print ">>> %s%s"%(space,key.GetName())
    
    subdirnames = findTDirs(dir)
    for subdirname in subdirnames:
        print ">>> %s%s"%(space,subdirname)
        subdir = dir.Get(subdirname)
        printTDirContents(subdir,space=space+'  ',contents=True)
    


# FIND object in file
def findTDirs(directory,**kwargs):
    """Find all directories in a given TDirectory object."""
    return findObjectsOfClass("TDirectory",directory,**kwargs)

# FIND object in file
def findObjectsOfClass(classname,directory,**kwargs):
    """Find all objects that inherited from a given classname in a given TDirectory object."""
    objlist = [ ]
    keylist = directory.GetListOfKeys()
    for key in keylist:
        keyname  = key.GetName()
        if gROOT.GetClass(key.GetClassName()).InheritsFrom(classname):
          objlist.append(keyname)
    return objlist
    
# FIND histograms in TDirectory
def findHistogramsInTDir(dir,histnames,**kwargs):
    """Help function to find histograms in given TDirectory."""
    
    doRegex   = kwargs.get( 'regex',     False )
    recursive = kwargs.get( 'recursive', False )
    unique    = kwargs.get( 'unique',    False )
    result    = [ ]
    if not (isinstance(histnames,list) or isinstance(histnames,tuple)):
      histnames = [histnames]
    
    if doRegex:
      patterns  = histnames[:]
      for key in dir.GetListOfKeys():
        if gROOT.GetClass(key.GetClassName()).InheritsFrom('TH1'):
          histname = key.GetName()
          for pattern in patterns:
            if re.findall(pattern,histname):
              result.append( histname )
              if unique: break
        #elif gROOT.GetClass(key.GetClassName()).InheritsFrom('TDirectory'):
    else:
      for histname in histnames:
        hist = dir.Get(histname)
        if not hist:
          warning('Did not find "%s"'%(histname),pre="    ")
          continue
        if not hist.InheritsFrom('TH1'): #isinstance(oldhist,TH1):
          warning('Object "%s" is not a TH1 object!'%(histname),pre="    ")
          continue
        result.append(histname)
    
    #if not result: print ">>>     no matches found"
    return result
    
# CHECK existence of histogram:
def checkExistingHistogram(dir,histname,delete=False):
    hist = dir.Get(histname)
    if hist and hist.InheritsFrom('TH1'): #isinstance(sumhist,TH1):
      if delete:
        warning('Histogram "%s" already exists! Overwriting...'%(histname),pre="    ")
        dir.Delete("%s;*"%histname)
      else:
        warning('Histogram "%s" already exists! Use the -f flag if you are certain you want to overwrite this histogram.'%(histname),pre="    ")
        return

def green(string,**kwargs): return "\x1b[0;32;40m%s\033[0m"%string

def error(string,**kwargs):
  print ">>> \033[1m\033[91m%sERROR! %s\033[0m"%(kwargs.get('pre',""),string)
  exit(1)
  
def warning(string,**kwargs):
  print ">>> \033[1m\033[93m%sWarning!\033[0m\033[93m %s\033[0m"%(kwargs.get('pre',""),string)

def ensureTFile(filename,option='READ'):
  """Open TFile and make sure if that it exists."""
  file = TFile(filename,option)
  if 'read' in option.lower() and not os.path.exists(filename):
      error('ensureTFile: File "%s" does not exists!'%(filename))
  if not file:
    print '>>> Warning! getTFile: Could not open file "%s"!'%(filename)
  return file
  


# MAIN
def main():
    print ""
    
    #filenames = [
    #    "ttbar_mt_tid_pfmt_1.inputs-13TeV.root",
    #    "ttbar_mt_tid_m_vis.inputs-13TeV.root",
    #    "ttbar_mt_tid_pfmt_1.inputs-13TeV_mtlt100.root",
    #    "ttbar_em_tid_m_vis.inputs-13TeV.root",
    #    "ttbar_em_tid_pfmt_1.inputs-13TeV.root",
    #    "ttbar_em_tid_pfmt_1.inputs-13TeV_mtlt100.root",
    #]
    #filenames = glob.glob('%s/xtt*.root'%IN_DIR)
    
    #backgrounds = [ 'TT',  'TTT', 'TTJ', 'TTL',
    #                'DY',  'ZTT', 'ZJ',  'ZL',
    #                'QCD', 'WJ',  'W',   'ST',
    #                'VV',  'WW',  'WZ',  'ZZ', ]
    #for filename in filenames:
      #filename = "%s/%s"%(IN_DIR,filename)
      #makeAsimovDataSet(filename,backgrounds,dirs=dirnames,force=force)
    
    # RENAME
    #patterns = [ ("jer_mt", "jer"), ("jes_mt", "jes"), ("jer_em", "jer"), ("jes_em", "jes") ]
    #for filename in filenames:
    #  filename = "input/%s"%(filename)
    #  renameHistograms(filename,patterns,force=force,regex=True)
    #  printTFileContents(filename,contents=True)
    
    # SUM
    filenames = [
      #"ztt_mt_tes_m_2.inputs-13TeV_ZTTregion.root",
      #"ztt_mt_tes_m_2.inputs-13TeV_ZTTregion2.root",
      #"ztt_mt_tes_m_2.inputs-13TeV_ZTTregion3.root",
      #"ztt_mt_tes_m_vis.inputs-13TeV_ZTTregion.root",
      #"ztt_mt_tes_m_vis.inputs-13TeV_ZTTregion2.root",
      #"ztt_mt_tes_m_vis.inputs-13TeV_ZTTregion3.root",
      "ztt_mt_tes_m_vis.inputs-13TeV_restr2.root",
    ]

    for filename in filenames:
      filename = "input/%s"%(filename)
      sumHistograms(filename,'ST',['STT','STJ'],force=force,systematics=True)
      sumHistograms(filename,'TT',['TTT','TTJ'],force=force,systematics=True)


if __name__ == '__main__':
    main()
    print ">>>\n>>> done\n"
    

