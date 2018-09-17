#!/usr/bin/env python

import sys, os, re
import time
from argparse import ArgumentParser
import YutaPlotTools.CMS_lumi as CMS_lumi
import YutaPlotTools.tdrstyle as tdrstyle
from array import array
import ROOT
from ROOT import gPad, gROOT, gStyle, TFile, TVectorD, Double,\
                 TCanvas, TLegend, TLatex, TText,\
                 TH1F, TH2F, THStack, TF1, TGraph, TGraphErrors, TGraphAsymmErrors,\
                 kBlack, kRed, kBlue, kAzure, kGreen, kGreen, kYellow, kOrange, kMagenta, kViolet,\
                 kSolid, kDashed, kDotted, kDashDotted
from math import log, floor, ceil
ROOT.gROOT.SetBatch(ROOT.kTRUE)
gStyle.SetOptStat(0)

argv = sys.argv
description = """This script runs combine on data cards, extracts limits from the output and plot them."""
parser = ArgumentParser(prog="plotLimits",description=description,epilog="Succes!")
#parser.add_argument( "filename", nargs='*', type=str, action='store',
#                     metavar="LOGFILE", help="log file to plot" )
parser.add_argument( "-t", "--tag",         dest="tag", type=str, default="", action='store',
                     metavar="TAG",         help="tag for a file" )
parser.add_argument( "-w", "--isoWP",     dest="isoWPs", type=str, nargs='*', default="", action='store',
                     metavar="TAU_ISO_ID_WP", help="working point for the tau MVA iso ID" )
parser.add_argument( "-o", "--obs",       dest="observables", nargs='*', type=str, default="", action='store',
                     metavar="MASS",      help="name of mass observable" )
parser.add_argument( "-c", "--use-CR",    dest="useCR1",  default=False, action='store_true',
                                          help="use emu control region" )
parser.add_argument( "--use-CR-pass",     dest="useCR2",  default=False, action='store_true',
                                          help="use emu control region with pass region" )
parser.add_argument( "--use-CR-pass-fail", dest="useCR3",  default=False, action='store_true',
                                          help="use emu control region with pass/fail region" )
parser.add_argument( "-v", "--verbose",   dest="verbose",  default=False, action='store_true',
                                          help="set verbose" )
args = parser.parse_args()

# PLOT OPTIONS
LOG_DIR     = "./log"
PLOTS_DIR   = "./plots"
verbosity   = 1
emuCR       = 1 if args.useCR1 else 2 if args.useCR2 else 3 if args.useCR3 else 0

# CMS style
lumi = 41.86
CMS_lumi.cmsText = "CMS"
CMS_lumi.extraText = "Preliminary"
CMS_lumi.cmsTextSize  = 0.65
CMS_lumi.lumiTextSize = 0.60
CMS_lumi.relPosX = 0.11
CMS_lumi.outOfFrame = True
CMS_lumi.lumi_13TeV = "%s fb^{-1}" % lumi
tdrstyle.setTDRStyle()

colors = [ kBlack,
           kRed+2, kAzure+5, kOrange-5, kGreen+2, kMagenta+2, kYellow+2,
           kRed-7, kAzure-4, kOrange+6, kGreen-2, kMagenta-3, kYellow-2 ] #kViolet
styles = [ kSolid, kDashed, kDashDotted, ] #kDotted



# GET signal SFs from log files
def getSignalSFAndError(filename,**kwargs):
    """Get signal SF and errors from log file."""
    
    with open(filename) as file: # Best fit SF: 0.696849 -0.0958027/+0.129344 (68% CL)
      for line in file:
        line = line.rstrip('\n')
        if not "Best fit SF" in line: continue
        #print '>>> searching "%s"'%(line)
        matches = re.findall("(\d+\.?\d*)\ +(-\d+\.?\d*e?[-+]?\d*)/(\+\d+\.?\d*)",line)
        if len(matches)==0:
          warning("getSignalSFAndError: Did not find SFs with errors in line!")
          exit(1)
        results = [float(x) for x in matches[0]]
        #print '>>> getSignalSFAndError(%s): found'%(filename),
        #for match in results: print "%5.4f"%(match),
        #print
        return results
        

# GET SFs from log files
def getProcessSFs(filename,**kwargs):
    """Get SF for each process in each region from log file."""
    
    start   = False
    SF_dict = { }
    
    with open(filename) as file:
      for line in file:
        line = line.rstrip('\n')
        if start:
            if re.search(r"\-{20,}",line): continue
            matches = re.findall("([a-z0-9\-_]+)\ +([a-z]+)\ +(\d+\.?\d*)",line,re.IGNORECASE)
            if len(matches)==0: break
            if len(matches[0])!=3: break
            (region,process,SF) = matches[0]
            if region  not in SF_dict:
              SF_dict[region] = { process:SF }
              continue
            elif process not in SF_dict[region]:
              SF_dict[region][process] = SF
              continue
            print warning('>>> getSFs: Could not fill SF dictionairy for "%s" with "%s": SF_dict = %s'%(region,process,SF_dict))
        elif re.search(r"Bin\ +Process\ +Scale factor",line):
            print line
            start = True
    
    if len(SF_dict)==0:
        print warning("getSFs: Did not find SFs with errors in line!")
        exit(1)
    
    print "SF_dict = ",SF_dict
    
    return SF_dict
    

# PLOT SFs
def plotSignalSFs(filenames,ID,plotname,**kwargs):
    """Plot expected upperlimits as boxes."""
    print magenta("plotSignalSFs()",pre=">>>\n>>> ")
    
    results   = TGraphAsymmErrors()
    filenames = filenames[::-1] # reverse order: top to bottom
    width     = 0.2
    
    #(xmin,xmax) = (99999,0)
    (xmin,xmax) = (0.6,1.2)
    lines       = [ ] # for txt file
    for i, filename in enumerate(filenames):
        (SF,eDown,eUp) = [ abs(x) for x in getSignalSFAndError(filename)]
        line = "   %7s:  %4.2f -%.2f/+%.2f"%(getWPFromString(filename),SF,eDown,eUp)
        lines.append(line)
        print ">>> "+line
        results.SetPoint(i, SF, i+0.5)
        results.SetPointError(i, eDown, eUp, width, width) # -/+ 1 sigma
        #if SF+eUp > xmax:   xmax = SF+eUp
        #if SF-eDown < xmin: xmin = SF-eDown
    #(xmin,xmax)   = (xmin*0.90,xmax*1.10)
        
    N       = len(filenames)
    H       = 100*N
    canvas  = TCanvas("canvas","canvas",100,100,800,H)
    canvas.SetTopMargin(0.08)
    canvas.SetBottomMargin(0.12)
    canvas.SetLeftMargin(0.16)
    canvas.SetRightMargin(0.04)
    #canvas.SetTickx(0)
    #canvas.SetTicky(0)
    canvas.SetGrid(1,0)
    canvas.cd()
    
    xtitle = "%s scale factor"%(ID)
    frame = canvas.DrawFrame(xmin,0,xmax,N)
    frame.GetXaxis().SetTitleSize(0.05)
    frame.GetYaxis().SetLabelSize(0.0)
    frame.GetXaxis().SetLabelSize(0.045)
    frame.GetXaxis().SetTitleOffset(1.14)
    frame.GetYaxis().SetNdivisions(N,0,0,False) # ndiv = N1 + 100*N2 + 10000*N3
    frame.GetXaxis().SetTitle(xtitle)
    results.SetLineWidth(2)
    
    #frame.Draw("AXIS")
    results.Draw("P")
    
    labelfontsize = 0.048
    text = TLatex()
    text.SetTextSize(labelfontsize)
    text.SetTextAlign(22)
    text.SetTextFont(62)
    
    xtext = marginCenter(canvas,frame.GetXaxis()) # automatic
    for i, filename in enumerate(filenames):
        ytext = i+0.5
        WP = getWPFromString(filename)
        #print ">>> WP %-8s (x,y)=(%s,%s)"%(WP,xtext,ytext)
        text.DrawLatex(xtext,ytext,WP)
    
    CMS_lumi.CMS_lumi(canvas,13,0)
    #canvas.Modified()
    frame.Draw('SAME AXIS')
    #gPad.RedrawAxis()
    
    canvas.SaveAs(plotname+".png")
    canvas.SaveAs(plotname+".pdf")
    canvas.Close()
    
    with open(plotname+".txt",'w+') as file:
      print ">>>   created txt file %s"%(plotname+".txt")
      startdate = time.strftime("%a %d/%m/%Y %H:%M:%S",time.gmtime())
      file.write("%s\n"%(startdate))
      for line in lines:
        file.write(line+'\n')
    
    

# PLOT SFs
def plotProcessSFs(filenames,ID,plotname,**kwargs):
    """Plot expected upperlimits as boxes."""
    print magenta("plotProcessSFs()",pre=">>>\n>>> ")
    
    #results   = TGraphAsymmErrors()
    #filenames = filenames[::-1] # reverse order: top to bottom
    #width     = 0.2
    #
    #(xmin,xmax)   = (99999,0)
    #for i, filename in enumerate(filenames):
    #    (SF,eDown,eUp) = [ abs(float(x)) for x in getProcessSFs(filename)]
    #    results.SetPoint(i, SF, i+0.5)
    #    results.SetPointError(i, eDown, eUp, width, width) # -/+ 1 sigma
    #    if SF+eUp > xmax:   xmax = SF+eUp
    #    if SF-eDown < xmin: xmin = SF-eDown
    #
    #N       = len(filenames)
    #H       = 110*N
    #canvas  = TCanvas("canvas","canvas",100,100,800,H)
    #canvas.SetTopMargin(0.08)
    #canvas.SetBottomMargin(0.12)
    #canvas.SetLeftMargin(0.16)
    #canvas.SetRightMargin(0.04)
    #canvas.SetGrid(1,0)
    #results.SetLineWidth(2)
    #
    #frame = canvas.DrawFrame(xmin*0.90,0,xmax*1.10,N)
    #frame.GetXaxis().SetTitleSize(0.05)
    #frame.GetYaxis().SetLabelSize(0.0)
    #frame.GetXaxis().SetLabelSize(0.045)
    #frame.GetXaxis().SetTitleOffset(1.14)
    #frame.GetYaxis().SetNdivisions(N,0,0,False) # ndiv = N1 + 100*N2 + 10000*N3
    #xtitle = "tau %s scale factor"%(ID)
    #frame.GetXaxis().SetTitle(xtitle)
    #
    #frame.Draw("AXIS")
    #results.Draw("P")
    #
    #labelfontsize = 0.048
    #text = TLatex()
    #text.SetTextSize(labelfontsize)
    #text.SetTextAlign(22)
    #text.SetTextFont(62)
    #
    #xtext = marginCenter(canvas,frame.GetXaxis()) # automatic
    #for i, filename in enumerate(filenames):
    #    ytext = i+0.5
    #    WP = getWPFromString(filename)
    #    print ">>> WP %-8s (x,y)=(%s,%s)"%(WP,xtext,ytext)
    #    text.DrawLatex(xtext,ytext,WP)
    #
    #CMS_lumi.CMS_lumi(canvas,13,0)
    #
    #print " "
    #canvas.SaveAs(plotname+".png")
    ##canvas.SaveAs(plotname+".png")
    #canvas.Close()
    

# GET WP
def getWPFromString(string):
    """Find WP from string."""
    WPs = re.findall(r"(v*loose|medium|v*tight)",string,re.IGNORECASE)
    if len(WPs)==0:
      error("Did not find WP in %s"%(string))
      exit(1)
    if len(WPs)>1:
      warning("Found WP in %s"%(string))
    WP = capitalizeWP(WPs[0])
    return WP
    
# CAPITALIZE WP
def capitalizeWP(WP):
    """Find WP from string."""
    WP = WP.replace('v','V').replace('lo','Lo').replace('me','Me').replace('ti','Ti')
    return WP
    
# GET string width
def stringWidth(*strings0):
    """Make educated guess on the maximum length of a string."""
    strings = list(strings0)
    for string in strings0:
      matches = re.search(r"#splitline\{(.*?)\}\{(.*?)\}",string) # check splitline
      if matches:
        while string in strings: strings.pop(strings.index(string))
        strings.extend([matches.group(1),matches.group(2)])
      matches = re.search(r"[_^]\{(.*?)\}",string) # check subscript/superscript
      if matches:
        while string in strings: strings.pop(strings.index(string))
        strings.append(matches.group(1)+matches.group(2))
      string = string.replace('#','')
    return max([len(s) for s in strings])
    
# CALCULATE the center of the margin
def marginCenter(canvas,axis,side='left',shift=0):
    """Calculate the center of the right margin in units of a given axis"""
    range    = axis.GetXmax() - axis.GetXmin()
    rangeNDC = 1 - canvas.GetRightMargin() - canvas.GetLeftMargin()
    center   = axis.GetXmin() - canvas.GetLeftMargin()*range/2/rangeNDC
    if side == "right":
      center = axis.GetXmin() - canvas.GetRightMargin()*range/2/rangeNDC
    if shift:
        if center>0: center*=(1+shift/100.0)
        else:        center*=(1-shift/100.0)
    return center
    
# ENSURE dir
def ensureDirectory(dir):
    """Make directory if it does not exist."""
    if not os.path.exists(dir):
        os.makedirs(dir)
        print ">>> made directory %s" % dir


def green(string,**kwargs): return "%s\x1b[0;32;40m%s\033[0m"%(kwargs.get('pre',""),string)
def magenta(string,**kwargs): return "%s\x1b[0;36;40m%s\033[0m"%(kwargs.get('pre',""),string)
def error(string,**kwargs): print ">>> \033[1m\033[91m%sERROR! %s\033[0m"%(kwargs.get('pre',""),string)
def warning(string,**kwargs): print ">>> \033[1m\033[93m%sWarning!\033[0m\033[93m %s\033[0m"%(kwargs.get('pre',""),string)




def main():
    print ""
    
    ensureDirectory(PLOTS_DIR)
    
    analysis = "ttbar"
    channels = [ "mt" ]
    observables = args.observables if args.observables else [
        "pfmt_1",
        "m_vis",
    ]
    isoWPs = args.isoWPs if args.isoWPs else [
        "vloose",
        "loose",
        "medium",
        "tight",
        "vtight",
        "vvtight",
    ]
    if emuCR>0:
      tag = "_withEmu%sCR"%("Pass" if emuCR==2 else "PassFail" if emuCR==3 else "") + args.tag
    
    for channel in channels:
      for obs in observables:
        ID        = "byIsolationMVArun2v1DBoldDMwLT"
        plotname  = "%s/SFs_%s_%s%s"%(PLOTS_DIR,obs,channel,tag)
        filenames = [ ]
        for WP in isoWPs:
          filename = "%s/%s_%s_%s-%s%s-13TeV.log"%(LOG_DIR,analysis,channel,obs,WP,tag)
          print ">>> %s"%(green(filename))
          filenames.append(filename)
        plotSignalSFs(filenames,ID,plotname)
    
    #for channel in channels:
    #  for obs in observables:
    #    ID        = "byIsolationMVArun2v1DBoldDMwLTraw"
    #    plotname  = "%s/SFs_%s_%s%s"%(PLOTS_DIR,obs,channel,tag)
    #    filenames = [ ]
    #    for WP in isoWPs:
    #      filename = "%s/%s_%s_%s-%s%s.log"%(LOG_DIR,analysis,channel,obs,WP,tag)
    #      print ">>> %s"%(green(filename))
    #      filenames.append(filename)
    #    plotSignalSFs(filenames,ID,plotname)
    
    



if __name__ == '__main__':
    main()
    print ">>>\n>>> done\n"

