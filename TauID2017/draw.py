import os, numpy, math, copy, math
from array import array
from argparse import ArgumentParser
from ROOT import gStyle, TCanvas, TLegend, TH1F
from YutaPlotTools.officialStyle import officialStyle
from YutaPlotTools.DisplayManager import DisplayManager
from YutaPlotTools.DataMCPlot import *
import sys

argv = sys.argv
description = '''This script draws pre- and postfit plots.'''
parser = ArgumentParser(prog="Draw pre-/post fits",description=description,epilog="Succes!")
parser.add_argument( "filename", type=str, action='store',
                     metavar="FILENAME",  help="filename with pre- and postfit shapes" ),
parser.add_argument( "-w", "--isoWP", dest="isoWP", type=str, default="", action='store',
                     metavar="TAU_ISO_ID_WP", help="working point for the tau MVA iso ID" )
parser.add_argument( "-t", "--tag",         dest="tag", type=str, default="", action='store',
                     metavar="TAG",         help="tag for a file" )
parser.add_argument( "-c", "--use-CR",    dest="useCR1",  default=False, action='store_true',
                                          help="use emu control region" )
parser.add_argument( "--use-CR-pass",     dest="useCR2",  default=False, action='store_true',
                                          help="use emu control region with pass region" )
parser.add_argument( "--use-CR-pass-fail", dest="useCR3",  default=False, action='store_true',
                                          help="use emu control region with pass/fail region" )
parser.add_argument( "-v", "--verbose",   dest="verbose",  default=False, action='store_true',
                                          help="set verbose" )
args = parser.parse_args()


filename    = args.filename
tag         = args.tag
isoWP       = args.isoWP
emuCR       = 1 if args.useCR1 else 2 if args.useCR2 else 3 if args.useCR3 else 0
var_dict    = { "pfmt_1": "transverse mass m_{T}(l,MET) [GeV]",
                "m_vis": "visible mass m_{vis} [GeV]",
                "m_2": "m_{#tau_{h}} [GeV]", }

gROOT.SetBatch(True)
#gROOT.SetBatch(False)
officialStyle(gStyle)
gStyle.SetOptTitle(0)
lumi = 41.86



def comparisonPlots(hist_, pname='sync.pdf', isRatio=True, ymax=None):

    display = DisplayManager(pname, isRatio, lumi, pullRange=0.35) #, 0.42, 0.65) #
    display.Draw(hist_,ymax)



def main():
    
    global filename, tag, isoWP, emuCR
    #filename = "output/ttbar_mt_pfmt_1-pass-%s.output-13TeV.root"%isoWP
    #if doCR:
    #  filename = "output/ttbar_mt_pfmt_1-pass-%s.output-13TeV.root"%(isoWP+"_withCR")
    filedict = {
        'pass':{'filename':filename},
        #'fail':{'filename':filename},
        #'pass-emuCR':{'filename':filename},
    }
    if emuCR==1: filedict['emuCR']      = {'filename':filename}
    if emuCR>=2: filedict['pass-emuCR'] = {'filename':filename}
    if emuCR==3: filedict['fail-emuCR'] = {'filename':filename}
    
    process = {
        #'TotalSig':{'name':'TotalSig', 'isSignal':1, 'order':1001},
        'QCD': {'name':'QCD', 'isSignal':0, 'order':8},
        'TTT': {'name':'TTT', 'isSignal':0, 'order':1},
        'TTJ': {'name':'TTJ', 'isSignal':0, 'order':2},
        #'TTL': {'name':'TTL', 'isSignal':0, 'order':1},
        #'ST':  {'name':'ST',  'isSignal':0, 'order':4},
        'STT': {'name':'STT', 'isSignal':0, 'order':4},
        'STJ': {'name':'STJ', 'isSignal':0, 'order':4},
        'VV':  {'name':'VV',  'isSignal':0, 'order':5},
        'W':   {'name':'W',   'isSignal':0, 'order':6},
        'ZJ':  {'name':'ZJ',  'isSignal':0, 'order':7},
        'ZL':  {'name':'ZL',  'isSignal':0, 'order':7},
        'ZTT': {'name':'ZTT', 'isSignal':0, 'order':7},
        'data':{'name':'data_obs', 'isSignal':0, 'order':2999},
    }
    
    ymax = None
    
    for region, ifile in filedict.iteritems():
      filename = ifile['filename']
      file = TFile(filename)
      for fittype in ['prefit','postfit']:
        #region = key.replace("pass","pass-"+isoWP).replace("fail","fail-"+isoWP)
        print "\n>>> " + green("%s - %s"%(region,fittype))
        
        hist0 = DataMCPlot("h_mass_%s_%s"%(fittype,region))        
        hist0.legendBorders = 0.55, 0.55, 0.88, 0.88
        
        var   = ""
        hists = [ ]
        rhist = None
        DYs = [ ]
        
        for ii, val in process.iteritems():
            histname = "%s_%s/%s"%(region,fittype,val['name'])
            hist = file.Get(histname)
            if not hist:
              print ">>> Warning! Could not find histogram \"%s\" in %s"%(histname,filename)
              continue
            elif "Z" in val['name']:
              DYs.append(val['name'])
            print ">>> %s:%s"%(filename,histname)
            
            var = hist.GetXaxis().GetTitle()
            hist.GetXaxis().SetTitle(var_dict[var])
            hist.SetName(val['name'])
            hist.GetXaxis().SetLabelColor(1)
            hist.GetXaxis().SetLabelSize(0.0)
            #hist.Sumw2()
            
            hist0.AddHistogram(hist.GetName(), hist, val['order'])
            
            if val['name'] in ['data_obs']:
              hist0.Hist(hist.GetName()).stack = False
              hists.append(hist)
            else:
              if rhist==None:
                rhist = copy.deepcopy(hist)
                rhist.GetXaxis().SetLabelSize(0.05)
                rhist.GetXaxis().SetLabelColor(1)
              else:
                rhist.Add(hist)
        
        if rhist==None or len(hists)==0:
          print ">>> Warning! no histograms!"
          break
          #exit(1)
        
        #hist0.Group('TT', ['TTT', 'TTJ', 'TTL'])
        if len(DYs)>1:
          hist0.Group('DY', DYs)
        #hist0.Group('DY', ["ZTT","ZJ","ZL"])
        #hist0.Group('electroweak', ['W', 'ZL', 'ZJ', 'VV'])
        hists.insert(0, rhist)
        
        canvas = TCanvas()
        #print ">>> DrawStack"
        hist0.DrawStack('HIST', None, None, None, None, 1.9)
        if 'prefit' in fittype: ymax = hist0.ymax
        #print ">>> hist0.ymax = ",hist0.ymax
        
        
        #print hist0
        labelCR  = ""
        if emuCR>0:
          labelCR = "_withEmu%sCR"%("Pass" if emuCR==2 else "PassFail" if emuCR==3 else "")
        regionWP = region.replace("pass","pass-"+isoWP).replace("fail","fail-"+isoWP)
        plotname = "plots/%s_%s%s_%s%s.pdf"%(var,regionWP,labelCR,fittype,tag)
        #print ">>> comparisonPlots"
        comparisonPlots(hist0, plotname, True, ymax=ymax)
        


def green(string,**kwargs):
    return "\x1b[0;32;40m%s\033[0m"%string
    


if __name__ == '__main__':
    main()
    print ">>>\n>>> done\n"
