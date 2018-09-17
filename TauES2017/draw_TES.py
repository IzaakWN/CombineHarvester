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
parser = ArgumentParser(prog="LowMassDiTau_Harvester",description=description,epilog="Succes!")
parser.add_argument( "filename", type=str,  action='store',
                     metavar="FILENAME",    help="filename with pre- and postfit shapes" )
parser.add_argument( "-t", "--tag",         dest="tag", type=str, default="", action='store',
                     metavar="TAG",         help="tag for a file" )
parser.add_argument( "-d", "--decayMode",   dest="DM", type=str, default="DM1", action='store',
                     metavar="DECAY",       help="decay mode" )
parser.add_argument( "-o", "--observable",  dest="observables", type=str, nargs='*', default=[ ], action='store',
                     metavar="VARIABLE",    help="name of observable for TES measurement" )
parser.add_argument( "-r", "--shift-range", dest="shiftRange", type=str, default="0.940,1.060", action='store',
                     metavar="RANGE",       help="range of TES shifts" )

args = parser.parse_args()


filename    = args.filename
tag         = args.tag
DM          = args.DM
#var         = args.observables
var_dict    = { "pfmt_1": "transverse mass m_{T}(l,MET) [GeV]",
                "m_vis":  "visible mass m_{vis} [GeV]",
                "m_2":    "m_{#tau_{h}} [GeV]", }

gROOT.SetBatch(True)
officialStyle(gStyle)
gStyle.SetOptTitle(0)
lumi = 41.86



def comparisonPlots(hist_, pname='sync.pdf', isRatio=True, ymax=None):

    display = DisplayManager(pname, isRatio, lumi, pullRange=0.35)
    display.Draw(hist_,ymax)



def main():
    
    global filename, tag, DM
    
    process = {
        'QCD': {'name':'QCD', 'isSignal':0, 'order':8},
        'TTT': {'name':'TTT', 'isSignal':0, 'order':1},
        'TTJ': {'name':'TTJ', 'isSignal':0, 'order':2},
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
    
    file = TFile(filename)
    for fittype in ['prefit','postfit']:
      print "\n>>> " + green("%s - %s"%(DM,fittype))
      
      hist0 = DataMCPlot("h_mass_%s_%s"%(fittype,DM))        
      hist0.legendBorders = 0.55, 0.55, 0.88, 0.88
      
      hists = [ ]
      rhist = None
      
      for ii, val in process.iteritems():
          histname = "%s_%s/%s"%(DM,fittype,val['name'])
          hist = file.Get(histname)
          if not hist:
            print ">>> Warning! Could not find histogram \"%s\" in %s"%(histname,filename)
            continue
          print ">>> %s:%s"%(filename,histname)
          
          var = hist.GetXaxis().GetTitle()
          hist.GetXaxis().SetTitle(var_dict[var])
          hist.SetName(val['name'])
          hist.GetXaxis().SetLabelColor(1)
          hist.GetXaxis().SetLabelSize(0.0)
          
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
      
      hist0.Group('TT', ['TTT', 'TTJ'])
      #hist0.Group('DY', ["ZTT","ZJ","ZL"])
      #hist0.Group('electroweak', ['W', 'ZL', 'ZJ', 'VV'])
      hists.insert(0, rhist)
      
      canvas = TCanvas()
      hist0.DrawStack('HIST', None, None, None, None, 1.9)
      if 'prefit' in fittype: ymax = hist0.ymax
      #print ">>> hist0.ymax = ",hist0.ymax
      
      plotname = "plots/%s_%s_%s%s.pdf"%(var,DM,fittype,tag)
      comparisonPlots(hist0, plotname, True, ymax=ymax)
        


def green(string,**kwargs):
    return "\x1b[0;32;40m%s\033[0m"%string
    


if __name__ == '__main__':
    main()
    print ">>>\n>>> done\n"
