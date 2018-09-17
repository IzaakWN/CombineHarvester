#! /usr/bin/env python

import os, sys, re
#sys.path.append('../plots')
from argparse import ArgumentParser
import PlotTools.PlotTools
from PlotTools.SampleTools import sample_dict
from PlotTools.SettingTools import isList
from PlotTools.PlotTools import Plot, ceilToSignificantDigit, groupHistsInList, getHist
import PlotTools.CMS_lumi as CMS_lumi, PlotTools.tdrstyle as tdrstyle
from PlotTools.PrintTools import color, warning, error
import ROOT
from ROOT import TFile, TTree
ROOT.gROOT.SetBatch(ROOT.kTRUE)

argv = sys.argv
description = '''This script makes shape variations from input root files for datacards.'''
parser = ArgumentParser(prog="checkshapes_TID",description=description,epilog="Succes!")
parser.add_argument( "filename",            type=str, nargs='+', action='store',
                     metavar="FILENAME",    help="file with shapes" ),
parser.add_argument( "-t", "--tag",         dest="tags", type=str, nargs='+', default=[ "" ], action='store',
                     metavar="TAGS",        help="tags for the input file" )
parser.add_argument( "-w", "--wp",          dest="WPs", type=str, nargs='*', default="", action='store',
                     metavar="TAU_ISO_ID_WP", help="working point for the tau MVA iso ID" )
parser.add_argument( "-o", "--obs",         dest="observables", nargs='*', type=str, default="", action='store',
                     metavar="MASS",        help="name of mass observable" )
parser.add_argument( "--dirnames",          dest="dirnames", type=str, nargs='*', default=[ ], action='store',
                     metavar="DIRNAMES",    help="list of dirnames for given file" )
parser.add_argument( "-p", "--postfit",     dest="postfit", default=False, action='store_true',
                                            help="do pre-/post-fit" )
parser.add_argument( "--out-dir",           dest="outdirname", type=str, default="", action='store',
                     metavar="DIRNAME",     help="name of output directory" )
parser.add_argument( "--pdf",               dest="pdf", default=False, action='store_true',
                                            help="save plot as pdf as well" )
parser.add_argument( "-v", "--verbose",     dest="verbose",  default=False, action='store_true',
                                            help="set verbose" )
args = parser.parse_args()

IN_DIR  = "output"
OUT_DIR = "shapes"
category_dict  = {
    'MVAOldV2':  "MVA Old MC_V2",
    'MVANewV2':  "MVA New MC_V2",
    'cut':       "cut-based",
}
variable_dict  = {
    'm_2':    "tau mass m_{tau}",
    'pfmt_1': "transverse mass m_{T}(mu,MET) [GeV]",
    'm_vis':  "visible mass m_{vis} [GeV]",
}
PlotTools.PlotTools.luminosity = 41.4
PlotTools.PlotTools.era = 2017



def drawStacks(filename,dirname,samples,shifts=[ "" ],**kwargs):
  """Compare shapes."""
  print '>>>\n>>> drawStacks("%s","%s")'%(filename,dirname)
  
  file    = TFile(filename,'READ')
  dir     = file.Get(dirname)
  channel = kwargs.get('channel', ""             )
  tag     = kwargs.get('tag',     ""             )
  xmin    = kwargs.get('xmin',    None           )
  xmax    = kwargs.get('xmax',    None           )
  outdir  = kwargs.get('outdir',  "controlPlots" )
  blind   = kwargs.get('blind',   [ ]            )
  group   = kwargs.get('group',   [ ]            )
  ensureDirectory(outdir)
  if not isList(samples): samples = [samples]
  if not dir: print warning('drawStacks: did not find dir "%s"'%(dirname),pre=">>>   ")
  if channel: channel += '-'
  
  for shift in shifts:
    variations = [ "Up", "Down" ] if shift else [""]
    for variation in variations:
      histsB   = [ ]
      histsD   = [ ]
      samplesS = [ ]
      nShifted = 0
      for sample in reversed(samples):
        hist = None
        if shift: # SHIFTED
          sample1 = "%s_%s%s"%(sample,shift,variation)
          hist    = dir.Get(sample1)
          nShifted+=1
          if not hist:
            hist = dir.Get(sample)
        else: # NOMINAL
          hist = dir.Get(sample)
        if not hist:
          print warning('drawStacks: could not find "%s" template in directory "%s"'%(sample,dir.GetName()),pre=">>>   ")
          continue
        hist.SetName(hist.GetName().replace('_ttbar','').replace('_ztt',''))
        hist.SetTitle(sample_dict[sample])
        if "data_obs" in sample:
          histsD.append(hist)
          hist.SetLineColor(1)
          if blind:
            for bin in range(hist.FindBin(blind[0]),hist.FindBin(blind[1]+2)):
              hist.SetBinContent(bin,0)
        else:
          histsB.append(hist)
      
      if len(histsB)==0 or (shift and nShifted==0):
        print warning('drawStacks: could not find any "%s" templates in directory "%s"'%(shift,dir.GetName()),pre=">>>   ")
        continue
      
      for groupargs in group:
        histsB = groupHistsInList(histsB,*groupargs)
      
      var      = histsB[0].GetXaxis().GetTitle()
      varname  = formatVariable(var)
      vartitle = variable_dict.get(var,var)
      tshift   = shift.replace("CMS_","").replace("ttbar_","").replace("ztt_","").replace("_13TeV","")
      nshift   = ('_'+tshift+variation) if tshift else ""
      title    = formatCategory(dirname,tshift,variation)
      canvasname = "%s/%s_%s%s%s%s.png"%(outdir,varname,channel,dirname,tag,nshift)
      exts       = ['pdf','png'] if args.pdf else ['png']
      
      plot = Plot(histsD,histsB,stack=True)
      plot.plot(vartitle,title=title,ratio=True,staterror=True,xmin=xmin,xmax=xmax)
      plot.saveAs(canvasname,ext=exts)
      plot.close()
  
  file.Close()
  


def drawPrePostFit(filename,dirname,samples,**kwargs):
    """Create pre- and post-fit plots from histograms and data."""
    print '>>>\n>>> drawPrePostFit("%s","%s")'%(filename,dirname)
    
    titleu      = kwargs.get('title',       None     )
    ratio       = kwargs.get('ratio',       True     )
    tag         = kwargs.get('tag',         ""       )
    xmin        = kwargs.get('xmin',        None     )
    xmax        = kwargs.get('xmax',        None     )
    dirnametag  = kwargs.get('dirnametag',  dirname  )
    outdir      = kwargs.get('outdir',      "plots"  )
    group       = kwargs.get('group',       [ ]      )
    signals     = kwargs.get('signals',     [ ]      )
    signaltags  = kwargs.get('signaltags',  [ ]      )
    upscale     = kwargs.get('upscale',     -1.0     )
    append_dict = kwargs.get('apptitle',    { }      )
    ymax        = None
    signalPostScale = 1.0
    ensureDirectory(outdir)
    fits        = ['prefit','postfit']
    file        = TFile(filename)
    if not file:
      print error('drawPrePostFit: did not find file "%s"'%(filename),pre=">>>   ")
      exit(1)
    
    for fit in fits:
      fitdirname = "%s_%s"%(dirname,fit)
      dir = file.Get(fitdirname)
      if not dir:
        print warning('drawPrePostFit: did not find dir "%s"'%(fitdirname),pre=">>>   ")
        return
      histsD = [ ]
      histsB = [ ]
      histsS = [ ]
      for sample in reversed(signals+samples):
        histname = "%s/%s"%(fitdirname,sample)
        stitle   = sample_dict[sample]+append_dict.get(sample,"")
        hist     = file.Get(histname)
        if not hist:
          print warning('drawPrePostFit: could not find "%s" template in directory "%s_%s"'%(sample,dirname,fit),pre=">>>   ")
          continue
        if "data_obs" in sample:
          histsD.append(hist)
          hist.SetLineColor(1)
          ymax = hist.GetMaximum()*1.18
        elif sample in signals:
          if 'post' in fit: signalPostScale = 1./hist.Integral()
          if signals.index(sample)<len(signaltags):
            stitle += ", %s"%(signaltags[signals.index(sample)])
          if upscale>0.0:
            if 'post' in fit:
              upscale = roundToSignificantDigit(upscale*signalPostScale,multiplier=5)
            hist.Scale(upscale)
            stitle += ", %d pb"%(upscale)
          else:
            upscale2 = roundToSignificantDigit(ymax/4.0/hist.GetMaximum(),multiplier=5)
            hist.Scale(upscale2)
            stitle += ", %d pb"%(upscale2)
          if 'pre' in fit: signalPostScale = hist.Integral()
          histsS.append(hist)
        else:
          histsB.append(hist)
        hist.SetTitle(stitle)
      
      if len(histsB)==0:
        print warning('drawPrePostFit: could not find any templates in directory "%s"'%(dirname),pre=">>>   ")
        continue
      if len(histsD)==0:
        print warning('drawPrePostFit: could not find a data template in directory "%s"'%(dirname),pre=">>>   ")
        continue
      
      for groupargs in group:
        histsB = groupHistsInList(histsB,*groupargs)
      
      var        = histsB[0].GetXaxis().GetTitle()
      varname    = formatVariable(var)
      vartitle   = variable_dict.get(var,var)
      title      = formatCategory(dirname) if titleu==None else titleu
      errortitle = "pre-fit stat. + syst. unc." if 'pre' in fit else "post-fit unc."
      canvasname = "%s/%s_%s%s_%s.png"%(outdir,varname,dirnametag,tag,fit)
      exts       = ['pdf','png'] if args.pdf else ['png']
      
      plot = Plot(histsD,histsB,histsS,stack=True)
      plot.plot(vartitle,title=title,ratio=ratio,staterror=True,errortitle=errortitle,xmin=xmin,xmax=xmax,ymax=ymax)
      plot.saveAs(canvasname,ext=exts)
      plot.close()
  


def drawVariations(filename,dirname,samples,variations,**kwargs):
  """Compare variations, e.g. sample ZTT with variations ['TES0.97','TES1.03']."""
  print '>>>\n>>> drawVariations("%s","%s")'%(filename,dirname)
  
  file   = TFile(filename,'READ')
  dir    = file.Get(dirname)
  tag    = kwargs.get('tag',    ""      )
  xmin   = kwargs.get('xmin',   None    )
  xmax   = kwargs.get('xmax',   None    )
  rmin   = kwargs.get('rmin',   None    )
  rmax   = kwargs.get('rmax',   None    )
  outdir = kwargs.get('outdir', OUT_DIR )
  ensureDirectory(outdir)
  if not isList(samples): samples = [samples]
  if not dir: print warning('drawVariations: did not find dir "%s"'%(dirname))
  ratio = True
  
  for sample in samples:
    hists = [ ]
    ratio  = int(len(variations)/2)
    for i, variation in enumerate(variations):
      #print '>>>   sample "%s" for shift "%s"'%(sample, shift)
      name = "%s_%s"%(sample,variation.lstrip('_'))
      hist = dir.Get(name)
      if not hist:
        print warning('drawVariations: did not find "%s" in directory "%s"'%(name,dir.GetName()),pre=">>>   ")
        continue
      sampletitle = sample
      if variation in variation_dict:
        sampletitle += variation_dict[variation]
      else:
        sampletitle += getShiftTitle(variation)
      hist.SetTitle(sampletitle)
      if sample==sampletitle or "nom" in sampletitle.lower(): ratio = i+1
      hists.append(hist)
    
    if len(hists)!=len(variations):
      print warning('drawVariations: number of hists (%d) != number variations (%d)'%(len(hists),len(variations)),pre=">>>   ")
    
    var      = hists[0].GetXaxis().GetTitle()
    varname  = formatVariable(var)
    vartitle = variable_dict.get(var,var)
    shift0   = formatFilename(variations[0])
    shift1   = formatFilename(variations[-1])
    shift    = ""; i=0
    for i, letter in enumerate(shift0):
      if i>=len(shift1): break
      if letter==shift1[i]: shift+=shift0[i]
      else: break
    nshift = "_%s-%s"%(shift0,shift1.replace(shift,""))
    title  = formatCategory(dirname,shift)
    canvasname = "%s/%s_%s_%s%s%s.png"%(outdir,sample,varname,dirname,tag,nshift.replace('.','p'))
    exts       = ['pdf','png'] if args.pdf else ['png']
    
    plot = Plot(hists)
    plot.plot(vartitle,title=title,ratio=ratio,linestyle=False,xmin=xmin,xmax=xmax,rmin=rmin,rmax=rmax)
    plot.saveAs(canvasname,ext=exts)
    plot.close()
  
  file.Close()
  


def drawUpDownVariation(filename,dirname,samples,shifts,**kwargs):
  """Compare up/down variations of systematics, e.g. sample ZTT with it up and down variations for 'TES0.97'.
  One can add several backgrounds with the same systematics into one by passing e.g. 'ZTT+ZJ+ZL=DY'."""
  print '>>>\n>>> drawUpDownVariation("%s","%s")'%(filename,dirname)
  
  file   = TFile(filename,'READ')
  dir    = file.Get(dirname)
  tag    = kwargs.get('tag',    ""      )
  xmin   = kwargs.get('xmin',   None    )
  xmax   = kwargs.get('xmax',   None    )
  outdir = kwargs.get('outdir', OUT_DIR )
  ensureDirectory(outdir)
  if not isList(samples): samples = [samples]
  if not dir: print warning('drawUpDownVariation: did not find dir "%s"'%(dirname))
  
  for sample in samples:
    for shift in shifts:
      if not shift: continue
      print '>>>   sample "%s" for shift "%s"'%(sample, shift)
      
      skip = False
      matches = re.findall(r"(.+\+.+)=(.*)",sample) # e.g. "ZTT+ZJ+ZL=DY"
      if len(matches)==0:
        sampleUp = "%s_%sUp"%(sample,shift)
        sampleDn = "%s_%sDown"%(sample,shift)
        hist   = dir.Get(sample)
        histUp = dir.Get(sampleUp)
        histDn = dir.Get(sampleDn)
        names  = [ sample, sampleUp, sampleDn]
        hists  = [ histUp, hist, histDn ]
        for hist1, name in zip(hists,names):
          if not hist1:
            print warning('drawUpDownVariation: did not find "%s" in directory "%s"'%(name,dir.GetName()),pre=">>>   ")
            skip = True; break
      else: # add samples
        hist, histUp, histDn = None, None, None
        sample = matches[0][1]
        for subsample in matches[0][0].split('+'):
          print '>>>     adding subsample "%s"'%(subsample)
          subsampleUp = "%s_%sUp"%(subsample,shift)
          subsampleDn = "%s_%sDown"%(subsample,shift)
          subhist     = dir.Get(subsample)
          subhistUp   = dir.Get(subsampleUp)
          subhistDn   = dir.Get(subsampleDn)
          subhists    = [ subhistUp, subhist, subhistDn ]
          subnames    = [ subsampleUp, subsample, subsampleDn ]
          for hist1, name in zip(subhists,subnames):
            if not hist1:
              print warning('drawUpDownVariation: did not find "%s" in directory "%s"'%(name,dir.GetName()),pre=">>>   ")
              skip = True; break
          if skip: break
          if hist:   hist.Add(subhist)
          else:      hist = subhist
          if histUp: histUp.Add(subhistUp)
          else:      histUp = subhistUp
          if histDn: histDn.Add(subhistDn)
          else:      histDn = subhistDn
        hist.SetTitle(sample)
        histUp.SetTitle("%s_%sUp"%(sample,shift))
        histDn.SetTitle("%s_%sDown"%(sample,shift))
        hists  = [ histUp, hist, histDn ]
      if skip: continue
      
      var      = hist.GetXaxis().GetTitle()
      varname  = formatVariable(var)
      vartitle = variable_dict.get(var,var)
      tshift   = formatFilename(shift)
      nshift   = ('_'+tshift) if tshift else ""
      title    = formatCategory(sample,tshift)
      hist.SetTitle("nominal")
      histUp.SetTitle("up variation")
      histDn.SetTitle("down variation")
      canvasname = "%s/%s_%s_%s%s%s.png"%(outdir,sample,varname,dirname,tag,nshift)
      exts       = ['pdf','png'] if args.pdf else ['png']
      
      plot = Plot(hists)
      plot.plot(title=title,ratio=2,linestyle=False,xmin=xmin,xmax=xmax,errorbars=True)
      plot.saveAs(canvasname,ext=exts)
      plot.close()
  
  file.Close()

def formatFilename(filename):
    """Help function to format filename."""
    filename = filename.replace("CMS_","").replace("ttbar_","").replace("_13TeV","")
    return filename

def formatCategory(category,shift="",var=""):
    """Help function to format category."""
    if category in category_dict:
      category = category_dict[category]
    else:
      for key in category_dict:
        if key in category:
          category = re.sub(key,category_dict[key],category)
    string = category.replace('-',' ')
    string = re.sub("(?:v*l(?=oose)|m(?=edium)|v*t(?=ight))",lambda x: x.group(0).upper(), string)
    if 'emuCR' in category:
      string = "e#mu: "+string.replace("emuCR","")
    else:
      string = "#mu#tau: "+string
    if shift:
      string += " - %s"%formatFilename(shift).replace('_',' ').replace(" et"," e#tau").replace(" mt"," #mu#tau")
    if var:
      string += " %s"%(var)
    string = '{%s}'%(string)
    return string

def formatVariable(variable,shift=""):
    """Help function to format category."""
    if 'Up' in variable:
      variable = re.sub("_[^_-]+Up","",variable)
    elif 'Down' in variable:
      variable = re.sub("_[^_-]+Down","",variable)
    return variable
    
def getShiftTitle(string):
    """Help function to format title, e.g. '_TES0p970' -> '-3% TES'."""
    matches = re.findall(r"([a-zA-Z]+)(\d+[p\.]\d+)",string)
    if not matches: return ""
    param, shift = matches[0]
    shift = float(shift.replace('p','.'))-1.
    if not shift: return ""
    title = " %s%% %s"%(("%+.2f"%(100.0*shift)).rstrip('0').rstrip('.'),param)
    return title

def ensureDirectory(dirname):
    """Make directory if it does not exist."""
    if not os.path.exists(dirname):
        os.makedirs(dirname)
        print ">>> made directory " + dirname
    return dirname
  
def ensureTFile(filename,**kwargs):
  """Open TFile and make sure if that it exists."""
  if not os.path.exists(filename):
    os.makedirs(filename)
    print '>>> Warning! getTFile: File "%s" does not exist!'%(filename)
  file = TFile(filename)
  if not file:
    print '>>> Warning! getTFile: Could not open file "%s"!'%(filename)
  return file
    
def xlimits(var,DM):
    xmin, xmax = None, None
    if "m_2" in var:
      xmin = 0.78 if '10' in DM else 0.20
      xmax = 1.60 if '10' in DM else 1.50
    return xmin, xmax
    

        
def main():
    print ""
    
    ensureDirectory(OUT_DIR)
    
    tags     = args.tags
    era      = '13TeV'
    analysis = 'ttbar'
    channels = [ 'mt' ]
    vars     = [ 'pfmt_1', 'm_vis' ]
    WPs      = args.WPs if args.WPs else [ 'vloose','loose','medium','tight','vtight','vvtight' ]
    shapesamples  = [
      'TTT', 'TTJ', 'STT', 'STJ', 'ZTT', 'ZL', 'ZJ', 'W',
    ]
    stacksamples  = [
      'ZTT', 'ZL', 'ZJ', 'TTT', 'TTJ', 'W', 'STT', 'STJ', 'VV', 'QCD', 'data_obs',
    ]
    shifts   = [
      "CMS_ttbar_shape_t_mt_13TeV",
      "CMS_ttbar_shape_e_em_13TeV",
      "CMS_ttbar_shape_jetTauFake_13TeV",
      "CMS_ttbar_shape_jes_13TeV",
      "CMS_ttbar_shape_jer_13TeV",
      "CMS_ttbar_shape_uncEn_13TeV",
    ]
    
    if args.postfit and args.filename and args.dirnames:
      tag = tags[0]
      for dirname in args.dirnames:
        xmin, xmax = xlimits(args.filename,dirname)
        app_dict   = {'ZTT':getShiftTitle(tag)}
        outdirname = args.outdirname if args.outdirname else "postfit"
        drawPrePostFit(args.filename,dirname,stacksamples2,xmin=xmin,xmax=xmax,apptitle=app_dict,tag=tag,outdir=outdirname)
    else:
      for tag in tags:
        for channel in channels:
          for var in vars:
            for WP in WPs:
              filename = "%s/%s_%s_%s-%s.input-%s%s.root"%(IN_DIR,analysis,channel,var,WP,era,tag)
              dirnames = [ "pass-%s"%(WP), "pass-%s-emuCR"%(WP) ]
              for dirname in dirnames:
                drawUpDownVariation(filename,dirname,shapesamples,shifts)
                drawStacks(filename,dirname,stacksamples,shifts)
    
    print ">>>\n>>> done\n"
    
    
    
    
    
if __name__ == '__main__':
    main()




