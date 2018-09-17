#! /usr/bin/env python
# Author: Izaak Neutelings (January 2018)

import os, sys, re, glob
import numpy, copy
from array import array
from argparse import ArgumentParser
from plotParabola_TES import measureTES, plotMeasurements, writeMeasurement, readMeasurement
from ROOT import gROOT, gDirectory, gPad, gStyle, Double, TFile, TCanvas, TLegend, TLatex, TH1F, TH2F, TF1, TGraph, TGraphErrors, TLine,\
                 kBlack, kBlue, kRed, kGreen, kYellow, kOrange, kMagenta, kTeal, kAzure
from ROOT import RooRealVar, RooArgSet, RooGaussian
from ROOT.RooFit import LineColor, Title, Binning
import CMS_lumi as CMS_lumi
import tdrstyle as tdrstyle
from math import sqrt, log, ceil, floor
gROOT.SetBatch(True)
#gROOT.SetBatch(False)
gStyle.SetOptTitle(0)
gStyle.SetLineStyleString(11,"50 100")

argv = sys.argv
description = '''This script makes plots for a bias test with toy and Asimov datasets.'''
parser = ArgumentParser(prog="plot bias test",description=description,epilog="Succes!")
parser.add_argument( "-t", "--tag",         dest="tags", type=str, nargs='+', default=[ '' ], action='store',
                     metavar="TAG",         help="tags for a file" )
parser.add_argument( "-d", "--decayMode",   dest="DMs", type=str, nargs='+', default=[ ], action='store',
                     metavar="DECAY",       help="decay mode" )
parser.add_argument( "-m", "-o", "--observable",  dest="observables", type=str, nargs='*', default=[ ], action='store',
                     metavar="VARIABLE",    help="name of observable for TES measurement" )
parser.add_argument( "-r", "--shift-range", dest="shiftRange", type=str, default="0.940,1.060", action='store',
                     metavar="RANGE",       help="range of TES shifts" )
parser.add_argument( "-c", "--checkPoints", dest="checkPoints", type=float, nargs='+', default=[ ], action='store',
                     metavar="POINTS",      help="check tes points (for post-fit and bias test)" )
parser.add_argument( "-N", "--maxToys",     dest="maxToys", type=int, default=-1, action='store',
                     metavar="NTOYS",       help="maximal number of toys (per file) to run over" )
parser.add_argument( "-p", "--pdf",         dest="pdf", default=True, action='store_true',
                                            help="save plot as pdf as well" )
parser.add_argument( "-v", "--verbose",     dest="verbose",  default=False, action='store_true',
                                            help="set verbose" )
args = parser.parse_args()

DIR         = "./toys"
PLOTS_DIR   = "./biastest"
verbosity   = args.verbose
observables = [o for o in args.observables if '#' not in o]

# CMS style
year = 2017
lumi = 41.4
CMS_lumi.cmsText      = "CMS"
CMS_lumi.extraText    = "Preliminary"
CMS_lumi.cmsTextSize  = 0.75
CMS_lumi.lumiTextSize = 0.70
CMS_lumi.relPosX      = 0.12
CMS_lumi.outOfFrame   = True
CMS_lumi.lumi_13TeV   = "%s, %s fb^{-1}"%(year,lumi)
tdrstyle.setTDRStyle()
colors  = [ kBlack, kBlue, kRed, kGreen, kMagenta, kOrange, kTeal, kAzure+1, kYellow-3 ]

bin_dict    = { 1: 'DM0', 2: 'DM1', 3: 'DM10', 4: 'all', }
varlabel    = { 'm_2':   "m_{#tau}", #_{h}
                'm_vis': "m_{vis}",
                'DM0':   "h^{#pm}",
                'DM1':   "h^{#pm}#pi^{0}",
                'DM10':  "h^{#pm}h^{#mp}h^{#pm}", }
vartitle    = { 'm_2':   "tau mass m_{#tau}", #_{h}
                'm_vis': "visible mass m_{vis}", }
varshorttitle = { 'm_2':   "m_{#tau}",
                  'm_vis': "m_{vis}", }



def plotBiasTest(filenames,**kwargs):
    """Plot bias of TES measurement in toys and Asimov:
       - histograms of measured tes in toy datasets
       - 2D histgrams of measured tes in toy datasets
       - bias + 1 s.d. band 
    """
    print green('\n>>> plot bias test for "%s"'%(kwargs.get('tag',"")))
    
    title         = kwargs.get('title',      ""           )
    text          = kwargs.get('text',       ""           )
    tag           = kwargs.get('tag',        ""           )
    plottag       = kwargs.get('plottag',    ""           )
    data          = kwargs.get('data',       ""           ) # real data filename
    maxToys       = kwargs.get('maxToys',    args.maxToys )
    xmin, xmax    = 0.96, 1.05
    nxbins        = int((xmax-xmin)/0.002)
    nxbins2D      = int(100.0*(xmax-xmin))
    yminErr       = -1.5
    ymaxErr       = +2.0
    datates, datatesErrD, datatesErrU, dataline = None, None, None, None
    #print nxbins, nxbins2D
    
    if not isinstance(filenames,list) and not isinstance(filenames,tuple):
      filenames   = [ filenames ]
    filenamesToys = [f for f in filenames if "_toys" in f.lower()]
    filenamesAsim = [f for f in filenames if "_asim" in f.lower()]
    freqToys      = any("freq" in f.lower() for f in filenamesToys)
    
    # GET TOYS HISTS
    tespointsToys, hist2D, hists, graphErr = getToysHists(filenamesToys,nxbins,nxbins2D,xmin,xmax,maxToys=maxToys)
    
    # GET ASIMOV GRAPHS
    graphs = getAsimovGraphs(filenamesAsim)
    
    # PROJECT ERRORS
    extrema  = findTGraphExtrema(graphErr)
    errlines = [ (xmin,extrema[1],extrema[0],extrema[1]), (xmin,extrema[3],extrema[2],extrema[3]) ]
    
    # GET DATA
    if data:
      datates, datatesErrD, datatesErrU = measureTES(data, unc=True)
    tesDown, tesUp = -extrema[1]*datates/100.0, extrema[2]*datates/100.0
    print datates, tesDown, tesUp
    
    # DRAW HISTOGRAMS
    ymin, ymax = 0, max([h.GetMaximum() for h in hists])*1.32
    xtitle     = "measured tau energy scale"
    ytitle     = "frequentist toys" if freqToys else "toys"
    xtitle2D   = "tau energy scale"
    ytitle2D   = xtitle
    ztitle2D   = ytitle
    xtitleErr  = "tau energy scale"
    ytitleErr  = "( measured tes - tes ) / tes [%]"
    doLog      = ymin and ymax/ymin>12
    
    # DRAW 2D & scatter
    if freqToys: tag = "-freq"+tag
    lentry          = "tes_{obs.} = tes" #_{real}
    lentryErr       = "tes = %5.3f_{-%5.3f}^{+%5.3f} (real data)"%(datates,datatesErrD,datatesErrU)
    canvasname      = "%s/biastest%s%s"%(PLOTS_DIR,tag,plottag)
    canvasname2D    = canvasname+"_2D"
    canvasnameScat  = canvasname+"_scatter"
    canvasnameErr   = canvasname+"_error"
    positionErr     = "left" if datates and datates>1.0 else "right"
    plotHist2D(hist2D,title=title,position="left",canvas=canvasname2D,xtitle=xtitle2D,ytitle=ytitle2D,ztitle=ztitle2D,option="COLZ",
              line=(xmin,xmin,xmax-0.005,xmax-0.005),lentry=lentry,graph=graphs)
    #plotScatter(tespointsToys,canvas=canvasnameScat,xtitle=xtitle2D,ytitle=ytitle2D,xmin=xmin,xmax=xmax,ymin=xmin,ymax=xmax,line=(xmin,xmin,xmax,xmax))
    plotErrorBand(graphErr,title=title,canvas=canvasnameErr,xtitle=xtitleErr,ytitle=ytitleErr,xmin=xmin,xmax=xmax-0.01,ymin=yminErr,ymax=ymaxErr,entry="bias in toys",
                  line=errlines)
                  #line=(datates,-errband,datates,errband),entry="bias (toys)",lentry=lentryErr,position=positionErr)
    ymin -= 0.01
    
    canvas = TCanvas("canvas","canvas",100,100,800,600)
    canvas.SetFillColor(0)
    canvas.SetBorderMode(0)
    canvas.SetFrameFillStyle(0)
    canvas.SetFrameBorderMode(0)
    canvas.SetTopMargin(  0.08 ); canvas.SetBottomMargin( 0.14 )
    canvas.SetLeftMargin( 0.13 ); canvas.SetRightMargin(  0.04 )
    canvas.SetTickx(0)
    canvas.SetTicky(0)
    canvas.SetGrid()
    canvas.cd()
    #if doLog:
    #  ymin = 10**(floor(log(ymin,10)))
    #  ymax = 10**(ceil(log(ymax,10)))
    #  canvas.SetLogy()
    
    textsize   = 0.042
    if len(hists)>6:
      x1, width  = 0.16, 0.76
      y1, height = 0.88, textsize*1.10*ceil(len([o for o in hists+[text] if o])/4.0)
    else:
      x1, width  = 0.16, 0.25
      y1, height = 0.88, textsize*1.10*len([o for o in hists+[text] if o])
    if title: height += textsize*1.10
    histsleg = columnize(hists,4) if len(hists)>6 else hists
    legend = TLegend(x1,y1,x1+width,y1-height)
    legend.SetTextSize(textsize)
    legend.SetBorderSize(0)
    legend.SetFillStyle(0)
    legend.SetFillColor(0)
    if title:
      legend.SetTextFont(62)
      legend.SetHeader(title)
    if len(hists)>6:
      legend.SetNColumns(4)
      legend.SetColumnSeparation(0.05)
    legend.SetTextFont(42)
    
    frame = canvas.DrawFrame(xmin,ymin,xmax,ymax)
    frame.GetYaxis().SetTitleSize(0.060)
    frame.GetXaxis().SetTitleSize(0.060)
    frame.GetXaxis().SetLabelSize(0.050)
    frame.GetYaxis().SetLabelSize(0.048)
    frame.GetXaxis().SetLabelOffset(0.010)
    frame.GetXaxis().SetTitleOffset(1.00)
    frame.GetYaxis().SetTitleOffset(1.08)
    frame.GetXaxis().SetNdivisions(508)
    frame.GetYaxis().SetTitle(ytitle)
    frame.GetXaxis().SetTitle(xtitle)
    
    for i,hist in enumerate(hists):
      color = colors[i%len(colors)]
      hist.SetLineColor(color)
      hist.SetLineWidth(2)
      hist.SetLineStyle(1)
      hist.Draw('HISTSAME')
    
    if data:      
      dataline = TLine(datates,ymin,datates,ymax)
      dataline.SetLineStyle(7)
      dataline.Draw("SAME")
      latex = TLatex()
      latex.SetTextSize(textsize*0.78)
      latex.SetTextAlign(13)
      latex.SetTextFont(42)
      latex.DrawLatex(datates+0.01*(xmax-xmin),ymax-0.025*(ymax-ymin),"%5.3f^{-%5.3f}_{+%5.3f} (real data)"%(datates,datatesErrD,datatesErrU))
    
    for hist in histsleg:
      legend.AddEntry(hist,hist.GetTitle(),'l')
    #if dataline:
    #  legend.AddEntry(dataline,"tes_{data} = %5.3f^{-%5.3f}_{+%5.3f}"%(datates,datatesErrD,datatesErrU),'l')  
    if text:
      legend.AddEntry(0,text,'')  
    legend.Draw()
    
    CMS_lumi.relPosX = 0.12
    CMS_lumi.CMS_lumi(canvas,13,0)
    gPad.SetTicks(1,1)
    gPad.Modified()
    frame.Draw('SAMEAXIS')
    
    canvas.SaveAs(canvasname+".png")
    if args.pdf: canvas.SaveAs(canvasname+".pdf")
    canvas.Close()
    for hist in hists+[hist2D]:
      gDirectory.Delete(hist.GetName())
    
    return datates, tesDown, tesUp
    


def plotParabola(filenames,**kwargs):
    """Plot parabola for toys and asimov."""
    print green('\n>>> plot parabola for "%s"'%(kwargs.get('tag',"")))
    
    title         = kwargs.get('title',      ""           )
    text          = kwargs.get('text',       ""           )
    tag           = kwargs.get('tag',        ""           )
    plottag       = kwargs.get('plottag',    ""           )
    maxToys       = kwargs.get('maxToys',    args.maxToys )
    canvasname    = "%s/biastest%s%s_parabola"%(PLOTS_DIR,tag,plottag)
    xtitle        = "tau energy scale"
    ytitle        = "-2#Deltaln(L)"
    xmin, xmax    = 0.94, 1.05
    ymin, ymax    = 0, 12
    
    if not isinstance(filenames,list) and not isinstance(filenames,tuple):
      filenames   = [ filenames ]
    filenamesToys = [f for f in filenames if "_toys" in f.lower()]
    filenamesAsim = [f for f in filenames if "_asim" in f.lower()]
    filenamesData = [f for f in filenames if f not in filenamesToys and f not in filenamesAsim ]
    
    # GET Parabola
    graphs = [ ]
    for filename in filenamesData:
      graphs += getParabolas(filename,toy=0)
    for filename in filenamesAsim:
      graphs += getParabolas(filename,toy=-1)
    for filename in filenamesToys:
      graphs += getParabolas(filename,toy=range(1,7))
    
    # DRAW
    canvas = TCanvas("canvas","canvas",100,100,800,600)
    canvas.SetFillColor(0)
    canvas.SetBorderMode(0)
    canvas.SetFrameFillStyle(0)
    canvas.SetFrameBorderMode(0)
    canvas.SetTopMargin(  0.08 ); canvas.SetBottomMargin( 0.14 )
    canvas.SetLeftMargin( 0.13 ); canvas.SetRightMargin(  0.04 )
    canvas.SetTickx(0)
    canvas.SetTicky(0)
    canvas.SetGrid()
    canvas.cd()
    
    textsize   = 0.042
    x1, width  = 0.16, 0.25
    y1, height = 0.88, textsize*1.08*len([o for o in graphs+[title,text] if o])
    legend = TLegend(x1,y1,x1+width,y1-height)
    legend.SetTextSize(textsize)
    legend.SetBorderSize(0)
    legend.SetFillStyle(0)
    legend.SetFillColor(0)
    if title:
      legend.SetTextFont(62)
      legend.SetHeader(title) 
    legend.SetTextFont(42)
    legend.SetTextSize(textsize*0.90)
    
    frame = canvas.DrawFrame(xmin,ymin,xmax,ymax)
    frame.GetYaxis().SetTitleSize(0.060)
    frame.GetXaxis().SetTitleSize(0.060)
    frame.GetXaxis().SetLabelSize(0.050)
    frame.GetYaxis().SetLabelSize(0.048)
    frame.GetXaxis().SetLabelOffset(0.010)
    frame.GetXaxis().SetTitleOffset(1.00)
    frame.GetYaxis().SetTitleOffset(1.08)
    frame.GetXaxis().SetNdivisions(508)
    frame.GetXaxis().SetTitle(xtitle)
    frame.GetYaxis().SetTitle(ytitle)
    
    for i, graph in enumerate(graphs):
      color = colors[i%len(colors)]
      graph.SetLineColor(color)
      graph.SetMarkerColor(color)
      graph.SetLineWidth(2)
      graph.SetMarkerSize(0.8)
      graph.SetLineStyle(1)
      graph.SetMarkerStyle(20)
      graph.Draw('LPSAME')
      legend.AddEntry(graph, graph.GetTitle(), 'lp')
    
    latex = TLatex()
    lines = [ ]
    for i,y in [(1,1),(2,4)]:
      line = TLine(xmin, y, xmax, y)
      line.SetLineWidth(1)
      line.SetLineStyle(7)
      line.Draw("SAME")
      latex.SetTextSize(0.050)
      latex.SetTextAlign(11)
      latex.SetTextFont(42)
      #latex.SetTextColor(kRed)
      #latex.SetNDC(True)
      latex.DrawLatex(xmin+0.025*(xmax-xmin),y+0.02*(ymax-ymin),"%d#sigma"%i)
      lines.append(line)
    
    if text:
      legend.AddEntry(0,text,'')  
    legend.Draw()
    
    CMS_lumi.relPosX = 0.12
    CMS_lumi.CMS_lumi(canvas,13,0)
    gPad.SetTicks(1,1)
    gPad.Modified()
    frame.Draw('SAMEAXIS')
    
    canvas.SaveAs(canvasname+".png")
    if args.pdf: canvas.SaveAs(canvasname+".pdf")
    canvas.Close()
    for graph in graphs:
      gDirectory.Delete(graph.GetName())
    


def getParabolas(filename, **kwargs):
    """Read all file and return graphs of measured vs. real TES for toy and Asimov datasets.
    Differentiate between with or without frequentist in the filename (for comparisons)."""
    toys       = kwargs.get('toy',      [0]  ) # -1 Asimov, 0 real data, >0 toy
    saveMin    = kwargs.get('saveMin',  True ) # save minimum in title
    graphs     = [ ]
    title0     = kwargs.get('title',    ""   )
    
    if not isinstance(toys,list) and not isinstance(toys,tuple):
      toys     = [ toys ]
    
    print '>>>   file "%s"'%(filename)
    file       = ensureTFile(filename)
    tree       = file.Get('limit')
    
    graphs = [ ]
    for toy in sorted(toys):
      title = title0
      if not title:
        if toy>0:   title = "toy %d"%(toy)
        elif toy<0: title = "Asimov"
        else:       title = "data"
      if "freq" in filename.lower() and "freq" not in title:
          title += " (freq.)"
      
      # GET DeltaNLL
      found    = False
      tes, nll = [ ], [ ]
      for event in tree:
        #print tree.iToy, tree.tes, tree.deltaNLL, tree.quantileExpected
        #if tree.iToy>10: exit(1)
        if tree.iToy!=toy:
          if found: break
          else:     continue
        found = True
        if tree.quantileExpected<0: continue
        tes.append(tree.tes)
        nll.append(2*tree.deltaNLL)
      #file.Close()
    
      # GET MINIMUM
      if not nll:
        print ">>> getParabola: ERROR! nll is empty!"
        exit(1)
      nllmin = min(nll)
      dnll   = map(lambda x: x-nllmin, nll) # DeltaNLL
      tesmin = tes[nll.index(nllmin)]
      if saveMin:
        title += ", %.3f"%(tesmin)
    
      graph = TGraph(len(tes),array('d',tes),array('d',dnll))
      graph.SetTitle(title)
      graphs.append(graph)
      
    file.Close()
    return graphs


def getToysHists(filenamesToys,nxbins,nxbins2D,xmin,xmax,**kwargs):
    """Read all files and return measured vs. real TES points as list and 2D histogram, plus 1D histograms for each real TES point."""
    maxToys   = kwargs.get('maxToys',    args.maxToys )
    hists     = [ ]
    tespoints = [ ]
    graphErr  = TGraphErrors()
    graphErr.SetTitle("error")
    hist2D    = TH2F("tes2D","tes",nxbins2D,xmin-0.005,xmax-0.005,nxbins,xmin,xmax)
    #print ">>> nxbins = %s, xmin = %.3f, xmax = %.3f"%(nxbins,xmin,xmax)
    for i, filename in enumerate(filenamesToys):
      print '>>>   file "%s",'%(filename),
      file    = ensureTFile(filename)
      tree    = file.Get('limit')
      realtes = getTES(filename)
      meantes = [ ]
      htitle  = "tes"
      ntoys   = 0
      if realtes!=None:
        htitle = "tes = %.2f"%(realtes)
      
      # GET DeltaNLL
      tesmap     = { }
      nllmap     = { }
      for event in tree:
        if tree.quantileExpected<0: continue
        if tree.deltaNLL==0: continue
        ktoy     = "%s-%s"%(tree.iToy,tree.iSeed) # key for toy
        #print tree.iToy, tree.tes, 2*tree.deltaNLL
        if ktoy not in tesmap:
          if ntoys>=maxToys>0: break
          tesmap[ktoy] = [ ]
          nllmap[ktoy] = [ ]
          ntoys += 1
        #print "tes = %s, rounded = %.3f"%(tree.tes,roundToDecimals(tree.tes,decimals=3))
        tesmap[ktoy].append(roundToDecimals(tree.tes,decimals=3))
        nllmap[ktoy].append(2*tree.deltaNLL)
      file.Close()
      print "ntoys=%d,"%(ntoys),
      
      # GET TES minimum
      hist      = TH1F("tes_%s"%i,htitle,nxbins,xmin,xmax)
      for ktoy in tesmap:
        nllmin  = min(nllmap[ktoy])
        tes     = tesmap[ktoy][nllmap[ktoy].index(nllmin)]
        tespoints.append((realtes,tes))
        meantes.append(tes)
        hist.Fill(tes)
        hist2D.Fill(realtes,tes)
      hists.append(hist)
      
      # GET MEAN & ERROR
      tmean = mean(meantes)
      tsd   = standardDeviation(meantes)
      graphErr.SetPoint(i,realtes,(tmean-realtes)/realtes*100.0)
      graphErr.SetPointError(i,0.0,tsd/realtes*100.0)
      print "mean = %.5f, +/- %.5f"%(tmean,tsd)
      
    return tespoints, hist2D, hists, graphErr
    


def getAsimovGraphs(filenames, **kwargs):
    """Read all files and return graphs of measured vs. real TES from Asimov datasets.
    Differentiate between with or without frequentist in the filename (for comparisons)."""
    
    graph      = None
    graph_Freq = None
    if any(["freq" in f.lower() for f in filenames]):
      graph_Freq = TGraph()
      graph_Freq.SetTitle("Asimov (freq.)")
    if any(["freq" not in f.lower() for f in filenames]):
      graph = TGraph()
      graph.SetTitle("Asimov")
    
    ifile      = 0
    ifile_Freq = 0
    for i, filename in enumerate(filenames):
      print '>>>   file "%s"'%(filename)
      file       = ensureTFile(filename)
      tree       = file.Get('limit')
      realtes    = getTES(filename)
      
      # GET DeltaNLL
      tes, nll   = [ ], [ ]
      for event in tree:
        itoy     = tree.iToy
        if itoy!=-1: print "Warning! iToy = %s != -1"%(itoy)
        if tree.quantileExpected<0: continue
        if tree.deltaNLL==0: continue
        tes.append(roundToDecimals(tree.tes,decimals=3))
        nll.append(2*tree.deltaNLL)
      file.Close()
      
      # GET TES minimum
      ###print realtes, tes; print nll 
      nllmin  = min(nll)
      tes     = tes[nll.index(nllmin)]
      if "freq" in filename.lower():
        graph_Freq.SetPoint(ifile_Freq,realtes,tes)
        ifile_Freq += 1
      else:
        graph.SetPoint(ifile,realtes,tes)
        ifile += 1
        
    graphs = [g for g in [graph,graph_Freq] if g]
    return graphs
    


def plotErrorBand(graph,**kwargs):
    """Make a scatter plot."""
        
    title      = kwargs.get('title',      ""                     )
    entry      = kwargs.get('entry',      ""                     )
    bentry     = kwargs.get('bentry',     "#pm 1 std. deviation" )
    lentries   = kwargs.get('lentry',     [ ]                    )
    lwidth     = kwargs.get('lwidth',     2                      )
    text       = kwargs.get('text',       ""                     )
    position   = kwargs.get('position',   ""                     ).lower()
    plottag    = kwargs.get('tag',        ""                     )
    xtitle     = kwargs.get('xtitle',     ""                     )
    ytitle     = kwargs.get('ytitle',     ""                     )
    xmin       = kwargs.get('xmin',       None                   )
    xmax       = kwargs.get('xmax',       None                   )
    ymin       = kwargs.get('ymin',       None                   )
    ymax       = kwargs.get('ymax',       None                   )
    color      = kwargs.get('color',      kGreen+1               )
    lines      = kwargs.get('line',       [ ]                    )
    canvasname = kwargs.get('canvas',     ""                     )
    #if not re.search("\.(png|pdf|gif|tiff|root|C)$",canvasname,re.IGNORECASE):
    #  canvasname += ".png"
    if not isinstance(lines,list) and not isinstance(lines,tuple):
      lines    = [ lines ]
    if not isinstance(lentries,list) and not isinstance(lentries,tuple):
      lentries = [ lentries ]
    
    # MAKE plot
    doLog  = ymin and ymax/ymin>12
    canvas = TCanvas("canvas","canvas",100,100,800,600)
    canvas.SetFillColor(0)
    canvas.SetBorderMode(0)
    canvas.SetFrameFillStyle(0)
    canvas.SetFrameBorderMode(0)
    canvas.SetTopMargin(  0.08 ); canvas.SetBottomMargin( 0.14 )
    canvas.SetLeftMargin( 0.13 ); canvas.SetRightMargin(  0.04 )
    canvas.SetTickx(0)
    canvas.SetTicky(0)
    canvas.SetGrid()
    canvas.cd()
    if doLog:
      ymin = 10**(floor(log(ymin,10)))
      ymax = 10**(ceil(log(ymax,10)))
      canvas.SetLogy()
    textsize = 0.042
    width    = 0.25
    height   = textsize*1.11*len([o for o in [title,text,entry]+zip(lines,lentries) if o])
    if entry and bentry: height += textsize*1.11
    if 'left' in position:   x1 = 0.17; x2 = x1+width
    else:                    x1 = 0.88; x2 = x1-width 
    if 'bottom' in position: y1 = 0.21; y2 = y1+height
    else:                    y1 = 0.88; y2 = y1-height
    legend = TLegend(x1,y1,x2,y2)
    legend.SetTextSize(textsize)
    legend.SetBorderSize(0)
    legend.SetFillStyle(0)
    legend.SetFillColor(0)
    if title:
      legend.SetTextFont(62)
      legend.SetHeader(title)
    legend.SetTextFont(42)
    
    frame = canvas.DrawFrame(xmin,ymin,xmax,ymax)
    frame.GetYaxis().SetTitleSize(0.060)
    frame.GetXaxis().SetTitleSize(0.060)
    frame.GetXaxis().SetLabelSize(0.050)
    frame.GetYaxis().SetLabelSize(0.048)
    frame.GetXaxis().SetLabelOffset(0.010)
    frame.GetXaxis().SetTitleOffset(1.00)
    frame.GetYaxis().SetTitleOffset(1.06)
    frame.GetXaxis().SetNdivisions(508)
    frame.GetYaxis().SetTitle(ytitle)
    frame.GetXaxis().SetTitle(xtitle)
    
    graph.SetFillColor(color)
    graph.SetLineColor(kBlack)
    graph.SetLineStyle(1)
    graph.SetLineWidth(2)
    bgraph = graph.Clone()
    bgraph.SetLineWidth(0)
    bgraph.Draw('E3SAME')
    graph.Draw('LXSAME')
    
    for i, line in enumerate(lines[:]):
      line = TLine(*line)
      line.SetLineColor(kBlack)
      line.SetLineWidth(lwidth)
      line.SetLineStyle(7)
      line.Draw('SAME')
      lines[i] = line
    
    if entry:
      legend.AddEntry(graph,entry,'l')
      if bentry:
        legend.AddEntry(bgraph,bentry,'f')
    for line, lentry in zip(lines,lentries):
      legend.AddEntry(line,lentry,'l')
    if text:
      legend.AddEntry(0,text,'')
    if entry or lentry:
      legend.Draw()
    
    CMS_lumi.relPosX = 0.12
    CMS_lumi.CMS_lumi(canvas,13,0)
    gPad.SetTicks(1,1)
    gPad.Modified()
    frame.Draw('SAMEAXIS')
    
    canvas.SaveAs(canvasname+".png")
    if args.pdf: canvas.SaveAs(canvasname+".pdf")
    canvas.Close()



def plotScatter(*points,**kwargs):
    """Make a scatter plot."""
    
    xvals, yvals = [ ], [ ]
    if len(points)>1 and isinstance(points[0],list) and isinstance(points[1],list):
      if len(points[0])!=len(points[1]): print ">>> Warning! plotScatter: len(xval)=%d vs. len(yvals)=%d is not the same!"%(len(points[0]),len(points[1]))
      nmin   = min(len(points[0]),len(points[1]))
      xvals  = points[0][:nmin]
      yvals  = points[1][:nmin]
      points = zip(points[0],points[1])
    elif isinstance(points[0],list) and not any(len(p)!=2 for p in points[0]):
      points = points[0]
      for x,y in points:
        xvals.append(x)
        yvals.append(y)
    else:
      print '>>> ERROR! plotScatter: Did not get valid input "%s"'%(points)
      exit(1)
    
    npoints    = len(points)
    title      = kwargs.get('title',      ""              )
    entry      = kwargs.get('entry',      ""              )
    text       = kwargs.get('text',       ""              )
    plottag    = kwargs.get('tag',        ""              )
    xtitle     = kwargs.get('xtitle',     ""              )
    ytitle     = kwargs.get('ytitle',     ""              )
    xmin       = kwargs.get('xmin',       min(xvals)      )
    xmax       = kwargs.get('xmax',       max(xvals)      )
    ymin       = kwargs.get('ymin',       min(yvals)      )
    ymax       = kwargs.get('ymax',       max(yvals)*1.16 )
    line       = kwargs.get('line',       None            )
    canvasname = kwargs.get('canvas',     ""              )
    #if not re.search("\.(png|pdf|gif|tiff|root|C)$",canvasname,re.IGNORECASE):
    #  canvasname += ".png"
    
    # MAKE graph
    graph = TGraph(npoints,array('d',xvals),array('d',yvals))
    
    # MAKE plot
    doLog  = ymin and ymax/ymin>12
    canvas = TCanvas("canvas","canvas",100,100,800,600)
    canvas.SetFillColor(0)
    canvas.SetBorderMode(0)
    canvas.SetFrameFillStyle(0)
    canvas.SetFrameBorderMode(0)
    canvas.SetTopMargin(  0.08 ); canvas.SetBottomMargin( 0.14 )
    canvas.SetLeftMargin( 0.13 ); canvas.SetRightMargin(  0.04 )
    canvas.SetTickx(0)
    canvas.SetTicky(0)
    canvas.SetGrid()
    canvas.cd()
    if doLog:
      ymin = 10**(floor(log(ymin,10)))
      ymax = 10**(ceil(log(ymax,10)))
      canvas.SetLogy()
    
    frame = canvas.DrawFrame(xmin,ymin,xmax,ymax)
    frame.GetYaxis().SetTitleSize(0.060)
    frame.GetXaxis().SetTitleSize(0.060)
    frame.GetXaxis().SetLabelSize(0.048)
    frame.GetYaxis().SetLabelSize(0.048)
    frame.GetXaxis().SetLabelOffset(0.010)
    frame.GetXaxis().SetTitleOffset(1.00)
    frame.GetYaxis().SetTitleOffset(1.08)
    frame.GetXaxis().SetNdivisions(508)
    frame.GetYaxis().SetTitle(ytitle)
    frame.GetXaxis().SetTitle(xtitle)
    
    #color = colors[i%len(colors)]
    color = kAzure-1
    #graph.SetLineColor(color)
    #graph.SetLineWidth(2)
    #graph.SetLineStyle(1)
    graph.SetMarkerColor(color)
    graph.SetMarkerStyle(20)
    graph.SetMarkerSize(0.4)
    graph.Draw('PSAME')
    
    if line:
      line = TLine(*line)
      line.SetLineColor(kBlack)
      line.SetLineWidth(2)
      line.SetLineStyle(7)
      line.Draw('SAME')
    
    #if entry:
    #  legend.AddEntry(0,entry,'')
    #if text:
    #  legend.AddEntry(0,text,'')
    #legend.Draw()
    
    CMS_lumi.relPosX = 0.12
    CMS_lumi.CMS_lumi(canvas,13,0)
    gPad.SetTicks(1,1)
    gPad.Modified()
    frame.Draw('SAMEAXIS')
    
    canvas.SaveAs(canvasname+".png")
    if args.pdf: canvas.SaveAs(canvasname+".pdf")
    canvas.Close()
    


def plotHist2D(hist,**kwargs):
    """Draw 2D histogram on canvas."""
      
    title      = kwargs.get('title',      ""                         )
    xtitle     = kwargs.get('xtitle',     hist.GetXaxis().GetTitle() )
    ytitle     = kwargs.get('ytitle',     hist.GetYaxis().GetTitle() )
    ztitle     = kwargs.get('ztitle',     ""                         )
    xmin       = kwargs.get('xmin',       None                       )
    xmax       = kwargs.get('xmax',       None                       )
    ymin       = kwargs.get('ymin',       None                       )
    ymax       = kwargs.get('ymax',       None                       )
    zmin       = kwargs.get('zmin',       None                       )
    zmax       = kwargs.get('zmax',       None                       )
    legend     = kwargs.get('legend',     True                       )
    position   = kwargs.get('position',   ""                         )
    text       = kwargs.get('text',       ""                         )
    plottag    = kwargs.get('tag',        ""                         )
    line       = kwargs.get('line',       None                       )
    lentry     = kwargs.get('lentry',     None                       )
    graphs     = kwargs.get('graph',      [ ]                        )
    gentries   = kwargs.get('gentry',     [ ]                        )
    canvasname = kwargs.get('canvas',     "hist2D.png"               )
    option     = kwargs.get('option',     "COLZTEXT44"               )
    #if not re.search("\.(png|pdf|gif|tiff|root|C)$",canvasname,re.IGNORECASE):
    #  canvasname += ".png"
    lmargin    = 0.13
    rmargin    = 0.19 if ztitle else 0.12
    if zmin: hist.SetMinimum(zmin)
    if zmax: hist.SetMaximum(zmax)
    if not isinstance(graphs,list) and not isinstance(graphs,tuple):
      graphs = [ graphs ]
    if not isinstance(gentries,list) and not isinstance(gentries,tuple):
      gentries = [ gentries ]
    colors2D = [ kOrange+7, kMagenta-4 ] # kOrange-3,
    
    canvas = TCanvas("canvas","canvas",100,100,800,700)
    canvas.SetFillColor(0)
    canvas.SetBorderMode(0)
    canvas.SetFrameFillStyle(0)
    canvas.SetFrameBorderMode(0)
    canvas.SetTopMargin(    0.07  ); canvas.SetBottomMargin(  0.14  )
    canvas.SetLeftMargin( lmargin ); canvas.SetRightMargin( rmargin )
    canvas.SetTickx(0); canvas.SetTicky(0)
    canvas.SetGrid()
    canvas.cd()
    
    if legend:
      textsize   = 0.041
      lineheight = 0.050
      width      = 0.25
      height     = textsize*1.10*len([o for o in graphs+[title,text,lentry] if o])
      if 'left' in position.lower():   x1 = 0.17; x2 = x1+width
      else:                            x1 = 0.78; x2 = x1-width 
      if 'bottom' in position.lower(): y1 = 0.20; y2 = y1+height
      else:                            y1 = 0.90; y2 = y1-height
      legend = TLegend(x1,y1,x2,y2)
      legend.SetTextSize(textsize)
      legend.SetBorderSize(0)
      legend.SetFillStyle(0)
      legend.SetFillColor(0)
      if title:
        legend.SetTextFont(62)
        legend.SetHeader(title) 
      legend.SetTextFont(42)
    
    hist.GetXaxis().SetTitleSize(0.058)
    hist.GetYaxis().SetTitleSize(0.058)
    hist.GetZaxis().SetTitleSize(0.056)
    hist.GetXaxis().SetLabelSize(0.048)
    hist.GetYaxis().SetLabelSize(0.048)
    hist.GetZaxis().SetLabelSize(0.044)
    hist.GetXaxis().SetLabelOffset(0.010)
    hist.GetXaxis().SetTitleOffset(1.04)
    hist.GetYaxis().SetTitleOffset(1.12)
    hist.GetZaxis().SetTitleOffset(1.25)
    hist.GetZaxis().CenterTitle(True)
    hist.GetXaxis().SetTitle(xtitle)
    hist.GetYaxis().SetTitle(ytitle)
    hist.GetZaxis().SetTitle(ztitle)
    hist.SetMarkerColor(kRed);
    hist.Draw(option)
    
    for i, graph in enumerate(graphs):
      if not graph: continue
      color = colors2D[i%len(colors2D)]
      graph.SetLineColor(color)
      graph.SetMarkerColor(color)
      graph.SetLineWidth(3)
      graph.SetMarkerSize(3)
      graph.SetLineStyle(1)
      graph.SetMarkerStyle(3)
      graph.Draw('LPSAME')
      if legend:
        gtitle = gentries[i] if i<len(gentries) else graph.GetTitle()
        legend.AddEntry(graph, graph.GetTitle(), 'lp')
    
    if line:
      line = TLine(*line[:4])
      line.SetLineColor(kBlack)
      line.SetLineStyle(7)
      line.SetLineWidth(2)
      line.Draw('SAME')
      if lentry and legend:
        legend.AddEntry(line, lentry, 'l')
    
    if text:
      if legend:
        legend.AddEntry(0,text,'')
      else:
        if 'left' in position.lower():   align = 10; x = 0.17
        else:                            align = 30; x = 0.78
        if 'bottom' in position.lower(): align += 1; y = 0.20
        else:                            align += 3; y = 0.90
        latex = TLatex()
        latex.SetTextSize(0.050)
        latex.SetTextAlign(align)
        latex.SetTextFont(42)
        #latex.SetTextColor(kRed)
        latex.SetNDC(True)
        latex.DrawLatex(x,y,text)
    if legend:
      legend.Draw()
      
    
    CMS_lumi.relPosX = 0.15
    CMS_lumi.CMS_lumi(canvas,13,0)
    canvas.SaveAs(canvasname+".png")
    if args.pdf: canvas.SaveAs(canvasname+".pdf")
    canvas.Close()
    


def plotToys(channel,var,DM,**kwargs):
    """Plot toy dataset."""
    if DM=='DM0' and 'm_2' in var: return
    print green("\n>>> plot toys for %s, %s"%(DM, var))
    
    title      = kwargs.get('title',      ""          )
    tag        = kwargs.get('tag',        ""          )
    plottag    = kwargs.get('plottag',    ""          )
    seed       = kwargs.get('seed',       "123456"    )
    indices    = kwargs.get('indices',    range(1,5)  )
    filename   = kwargs.get('filename',   ""          )
    xmin       = kwargs.get('xmin',         0         )
    xmax       = kwargs.get('xmax',       100         )
    nbins      = kwargs.get('nbins',      100         )
    if not filename:
      filename   = '%s/higgsCombine.%s_%s-%s%s-13TeV_toys.GenerateOnly.mH90.%s.root'%(DIR,channel,var,DM,tag,seed)
    
    print '>>>   file "%s"'%(filename)
    file       = ensureTFile(filename)
    #tree       = file.Get('limit')
    
    xvar       = RooRealVar("CMS_th1x","CMS_th1x",xmin,xmax)
    
    for i in indices:
      toykey     = "toy_%s"%i
      toyname    = "asimov" if "asimov" in i else toyname
      canvasname = "%s/%s-%s_%s%s%s"%(PLOTS_DIR,toyname,var,DM,tag,plottag)
      xframe     = xvar.frame(Title("Pseudo dataset"))
      data       = file.Get('toys/%s'%toykey)
      #data2     = gauss.generate(RooArgSet(x),10000) # RooDataSet
      #data.plotOn(frame)
      data.plotOn(xframe,Binning(nbins))
      
      canvas = TCanvas("canvas","canvas",100,100,800,600)
      gPad.SetLeftMargin(0.15); gPad.SetRightMargin(0.02)
      xframe.GetYaxis().SetLabelOffset(0.008)
      xframe.GetYaxis().SetTitleOffset(1.6)
      xframe.GetYaxis().SetTitleSize(0.045)
      xframe.GetXaxis().SetTitleSize(0.045)
      xframe.Draw()
      canvas.SaveAs(canvasname+".png")
      canvas.Close()
    





def plotMorph(filenames,graphname,**kwargs):
    """Plot interpolated DY yields morphed ZTT shape."""
    print green('\n>>> plot morph for "%s"'%(kwargs.get('tag',"")))
    
    title         = kwargs.get('title',      ""                       )
    text          = kwargs.get('text',       ""                       )
    entries       = kwargs.get('entries',    ""                       )
    tag           = kwargs.get('tag',        ""                       )
    plottag       = kwargs.get('plottag',    ""                       )
    ytitle        = kwargs.get('ytitle',     ""                       )
    xtitle        = kwargs.get('xtitle',     ""                       )
    legend        = kwargs.get('legend',     entries or title or text )
    DIR           = kwargs.get('dir',        PLOTS_DIR                )
    canvasname    = "%s/%s%s%s"%(DIR,graphname,tag,plottag)
    xmin, xmax    = 0.94, 1.06
    ymin, ymax    = None, None
    
    # GET GRAPHS
    graphs = [ ]
    for filename in filenames:
      file  = TFile(filename)
      graph = file.Get(graphname)
      graphs.append(graph)
      dum, ymin, dum, ymax  = findTGraphExtrema(graph,ymin=ymin,ymax=ymax)
    print ymin, ymax
    ymin *= 0.98
    ymax *= 1.06
    print ymin, ymax
    
    # DRAW
    canvas = TCanvas("canvas","canvas",100,100,900,600)
    canvas.SetFillColor(0)
    canvas.SetBorderMode(0)
    canvas.SetFrameFillStyle(0)
    canvas.SetFrameBorderMode(0)
    canvas.SetTopMargin(  0.08 ); canvas.SetBottomMargin( 0.13 )
    canvas.SetLeftMargin( 0.15 ); canvas.SetRightMargin(  0.04 )
    canvas.SetTickx(0)
    canvas.SetTicky(0)
    canvas.SetGrid()
    canvas.cd()
    
    if legend:
      textsize   = 0.050
      x1, width  = 0.18, 0.25
      y1, height = 0.88, textsize*1.08*len([o for o in zip(entries,graphs)+[title,text] if o])
      legend = TLegend(x1,y1,x1+width,y1-height)
      legend.SetTextSize(textsize)
      legend.SetBorderSize(0)
      legend.SetFillStyle(0)
      legend.SetFillColor(0)
      if title:
        legend.SetTextFont(62)
        legend.SetHeader(title) 
      legend.SetTextFont(42)
      legend.SetTextSize(textsize*0.90)
    
    frame = canvas.DrawFrame(xmin,ymin,xmax,ymax)
    frame.GetYaxis().SetTitleSize(0.060)
    frame.GetXaxis().SetTitleSize(0.060)
    frame.GetXaxis().SetLabelSize(0.050)
    frame.GetYaxis().SetLabelSize(0.048)
    frame.GetXaxis().SetLabelOffset(0.010)
    frame.GetXaxis().SetTitleOffset(1.00)
    frame.GetYaxis().SetTitleOffset(1.27)
    frame.GetXaxis().SetNdivisions(508)
    frame.GetXaxis().SetTitle(xtitle)
    frame.GetYaxis().SetTitle(ytitle)
    
    for i, graph in enumerate(graphs):
      color = colors[i%len(colors)]
      graph.SetLineColor(color)
      graph.SetMarkerColor(color)
      graph.SetLineWidth(2)
      graph.SetMarkerSize(0.75)
      graph.SetLineStyle(1)
      graph.SetMarkerStyle(20)
      graph.Draw('LEPSAME')
      if legend and i<len(entries):
        legend.AddEntry(graph, entries[i], 'lp')
    
    if legend:
      if text:
        legend.AddEntry(0,text,'')
      legend.Draw()
    
    CMS_lumi.relPosX = 0.12
    CMS_lumi.CMS_lumi(canvas,13,0)
    gPad.SetTicks(1,1)
    gPad.Modified()
    frame.Draw('SAMEAXIS')
    
    canvas.SaveAs(canvasname+".png")
    if args.pdf: canvas.SaveAs(canvasname+".pdf")
    canvas.Close()
    for graph in graphs:
      gDirectory.Delete(graph.GetName())
    


def findTGraphExtrema(graphs,ymin=None,ymax=None):
    """Get full y-range of a given TGraph object."""
    xmin, xmax = None, None
    if not isinstance(graphs,list) and not isinstance(graphs,tuple):
      graphs = [ graphs ]
    for graph in graphs:
      N = graph.GetN()
      x, y = Double(), Double()
      for i in xrange(0,N):
        graph.GetPoint(i,x,y)
        yup  = y+graph.GetErrorYhigh(i)
        ylow = y-graph.GetErrorYlow(i)
        if ymin==None or ylow<ymin:  xmin = float(x); ymin = ylow
        if ymax==None or yup >ymax:  xmax = float(x); ymax = yup
    return (xmin,ymin,xmax,ymax)
    
def columnize(list,ncol=2):
    """Transpose into n columns"""
    parts   = partition(list,ncol)
    collist = [ ]
    row     = 0
    while len(collist)<len(list):
      for part in parts:
        if row<len(part): collist.append(part[row])
      row += 1
    return collist
    
def partition(list,nparts):
    """Partion list into n chunks, as evenly sized as possible."""
    nleft    = len(list)
    divider  = float(nparts)
    parts    = [ ]
    findex   = 0
    for i in range(0,nparts): # partition recursively
      nnew   = int(ceil(nleft/divider))
      lindex = findex + nnew
      parts.append(list[findex:lindex])
      nleft   -= nnew
      divider -= 1
      findex   = lindex
      #print nnew
    return parts
    
def green(string,**kwargs):
  return kwargs.get('pre',"")+"\x1b[0;32;40m%s\033[0m"%string
  
def ensureDirectory(dirname):
  """Make directory if it does not exist."""
  if not os.path.exists(dirname):
      os.makedirs(dirname)
      print ">>> made directory %s"%dirname
  
def ensureTFile(filename,**kwargs):
  """Open TFile and make sure if that it exists."""
  if not os.path.exists(filename):
    print '>>> Warning! getTFile: File "%s" does not exist!'%(filename)
  file = TFile(filename)
  if not file:
    print '>>> Warning! getTFile: Could not open file "%s"!'%(filename)
  return file
  
def getTES(string):
    matches = re.findall("_TES(\dp\d*)",string)
    if not matches:
      print 'Error! getTES: Did not find valid patttern to extract TES from "%s"'%(string)
      return None
    return float(matches[0].replace('p','.'))
    
def roundToDecimals(x,decimals=2):
    """Round TES value to two decimals."""
    return round(x*10.0**decimals)/10.0**decimals

def mean(xvals): return sum(xvals) / len(xvals)
    
def standardDeviation(xvals):
    xmean = mean(xvals)
    xvar  = sum((x-xmean)**2 for x in xvals)/(len(xvals)-1)
    xsd   = sqrt(xvar)
    return xsd

def getShiftTitle(string):
    """Help function to format title, e.g. '_TES0p970' -> '-3% TES'."""
    matches = re.findall(r"([a-zA-Z]+)(\d+[p\.]\d+)",string)
    if not matches: return ""
    param, shift = matches[0]
    shift = float(shift.replace('p','.'))-1.
    if not shift: return ""
    title = " %s%% %s"%(("%+.2f"%(100.0*shift)).rstrip('0').rstrip('.'),param)
    return title
    


def main():
    
    ensureDirectory(PLOTS_DIR)
    channels  = [ 'mt', ]
    vars      = [ 'm_2', 'm_vis' ]
    DMs       = [ 'DM0', 'DM1', 'DM10' ]
    tags      = args.tags
    seed      = "all" #"123456"
    if args.DMs: DMs = args.DMs
    if args.observables: vars = observables
    
    cats    = [varlabel[d] for d in DMs]
    entries = [varlabel[v] for v in vars]
    
    (minshift,maxshift,steps) = ( -0.04, 0.04, 0.01 )
    tesshifts = [ s*steps for s in xrange(int(minshift/steps),int(maxshift/steps)+1) ]
    if args.checkPoints: tesshifts = args.checkPoints
    testags   = [ ]
    for tes in tesshifts:
      nametag  = "_TES%.3f"%(1+tes)
      #shifttag = getShiftTitle(nametag)
      #variation_dict[nametag.replace('_','')] = shifttag
      if (tes*100)%1==0: testags.append(nametag.replace('.','p'))
    
#     for tag in tags:
#       for channel in channels:
#         points = [ ]
#         for DM in DMs:
#           pointsDM = [ ]
#           for var in vars:
#             if "_0p"    in tag and var=='m_vis': continue
#             if "_85"    in tag and var=='m_2':   continue
#             if "_restr" in tag and var=='m_2':   continue
#             if DM=='DM0' and 'm_2' in var:
#               pointsDM.append(None)
#               continue
#             
#             title   = "%s, %s"%(varlabel[var],varlabel[DM])
#             plottag = "-%s_%s%s"%(var,DM,tag)
#             datafilename = 'output/higgsCombine.%s_%s-%s%s-13TeV.MultiDimFit.mH90.root'%(channel,var,DM,tag)
#             
#             # BIAS TEST
#             #filenames  = [ '%s/higgsCombine.%s_%s-%s%s-13TeV%s_toysFreq.MultiDimFit.mH90.%s.root'%(DIR,channel,var,DM,tag,t,seed) for t in testags ]
#             filenames  = [ '%s/higgsCombine.%s_%s-%s%s-13TeV%s_toys.MultiDimFit.mH90.%s.root'%(DIR,channel,var,DM,tag,t,seed) for t in testags ]
#             filenames += [ '%s/higgsCombine.%s_%s-%s%s-13TeV%s_asimov.MultiDimFit.mH90.root'%(DIR,channel,var,DM,tag,t)       for t in testags ]
#             #filenames += [ '%s/higgsCombine.%s_%s-%s%s-13TeV%s_asimovFreq.MultiDimFit.mH90.root'%(DIR,channel,var,DM,tag,t)   for t in testags ]
#             tes, tesDown, tesUp = plotBiasTest(filenames,title=title,tag=plottag,data=datafilename)
#             
#             # MEASUREMENTS
#             pointsDM.append((tes,tesDown,tesUp))
#             
#             # PARABOLA
#             filenamesSets = [ (t,['output/higgsCombine.%s_%s-%s%s-13TeV.MultiDimFit.mH90.root'%(channel,var,DM,tag),
#                                   '%s/higgsCombine.%s_%s-%s%s-13TeV%s_asimov.MultiDimFit.mH90.root'%(DIR,channel,var,DM,tag,t),
#                                   '%s/higgsCombine.%s_%s-%s%s-13TeV%s_toys.MultiDimFit.mH90.%s.root'%(DIR,channel,var,DM,tag,t,seed)]) for t in ['_TES0p990','_TES1p000','_TES1p010','_TES1p020'] ]
#             for testag, filenamesP in filenamesSets:
#               plottestag = plottag+testag
#               tesvalue   = getTES(testag)
#               testitle   = "%s, tes = %s"%(title,tesvalue) if testag else tesvalue
#               plotParabola(filenamesP,title=testitle,tag=plottestag)
#             
#             #### TOY DATASET
#             ###seed = "123456"
#             ###indices  = [ 'asimov' ] #range(1,5)
#             ###filename = '%s/higgsCombine.%s_%s-%s%s-13TeV_toys.GenerateOnly.mH90.%s.root'%(DIR,channel,var,DM,tag,seed)
#             ###for atag in [ "_TES1p020_asimov", "_TES1p020_asimov_noFreq" ]:
#             ###  #filename = '%s/higgsCombine.%s.GenerateOnly.mH90.%s.root'%(DIR,tag,seed)
#             ###  filename = '%s/higgsCombine.%s_%s-%s%s-13TeV%s.GenerateOnly.mH90.%s.root'%(DIR,channel,var,DM,tag,atag,seed)
#             ###  plotToys(var,DM,tag=tag+atag,indices=indices,filename=filename,xmax=10,nbins=10)
#             ####plotToys(var,DM,tag=tag,indices=indices) #,filename=filename)
#           
#           points.append(pointsDM)
#         
#         filename = "%s/measurement_tes_%s%s_toys"%("plots",channel,tag)
#         writeMeasurement(filename,DMs,points)
    
    for tag in tags:
      for channel in channels:
        if len(vars)==2 and len(DMs)>=3:
          canvas  = "%s/measurement_tes_%s%s_toys"%("plots",channel,tag)
          measurements = readMeasurement(canvas)
          if "_0p" in tag: # add m_vis from measurement tagged without "_0p05"
            canvas2 = re.sub(r"_0p\d+","",canvas)
            measurements2 = readMeasurement(canvas2)
            for points,points2 in zip(measurements,measurements2):
              points.append(points2[1])
          if "_restr" in tag: # add m_2 from measurement tagged with "_0p05"
            canvas2 = canvas.replace("_restr","_0p05")
            measurements2 = readMeasurement(canvas2)
            for points, points2 in zip(measurements,measurements2):
              points = points.insert(0,points2[0])
          print measurements
          plotMeasurements(cats,measurements,xtitle="tau energy scale",xmin=0.97,xmax=1.04,L=0.20,position="out",entries=entries,canvas=canvas)
    
    if len(vars)==2 and len(DMs)>=3:
      channel = "mt"
      canvas  = "%s/measurement_tes_%s%s"%("plots",channel,"_differentCuts_toys")
      canvas1 = "%s/measurement_tes_%s%s"%("plots",channel,"_mtlt50_0p05_toys")
      canvas2 = "%s/measurement_tes_%s%s"%("plots",channel,"_ZTTregion2_toys")
      measurements1 = readMeasurement(canvas1) # m_2
      measurements2 = readMeasurement(canvas2) # m_vis
      for points1, points2 in zip(measurements1,measurements2):
        points1 = points1.append(points2[1])
      writeMeasurement(canvas,DMs,measurements1)
      plotMeasurements(cats,measurements1,xtitle="tau energy scale",xmin=0.97,xmax=1.04,L=0.20,position="out",entries=entries,canvas=canvas)
    
    ###for var in vars:
    ###  tag = "_m_2_ZTTregion2_0p05"
    ###  filenames  = ["debug/morph_debug_mt_m_2_ZTTregion2_0p05_old.root", "debug/morph_debug_mt_m_2_ZTTregion2_0p05_oldJobFix.root", "debug/morph_debug_mt_m_2_ZTTregion2_0p05.root"]
    ###  if var=="m_vis":
    ###    tag = "_m_vis_ZTTregion2"
    ###    filenames = [f.replace("_0p05","").replace("_m_2_","_m_vis_") for f in filenames]
    ###  for DM in DMs:
    ###    if var=="m_2" and DM=="DM0": continue
    ###    graphname = "interp_rate_%s_ZTT"%(DM)
    ###    title = "%s, %s"%(varlabel[var],varlabel[DM])
    ###    plotMorph(filenames,graphname,tag=tag,title=title,entries=["randomly failing jobs","without failing jobs","without failing jobs + extensions"],xtitle="tau energy scale",ytitle="interpolated DY yield",dir="./plots")


if __name__ == '__main__':
    main()
    print ">>>\n>>> done\n"
    


