#! /usr/bin/env python
# Author: Izaak Neutelings (January 2018)

import os, sys, re, glob, time
import numpy, copy
from array import array
from argparse import ArgumentParser
from ROOT import gROOT, gPad, gStyle, Double, TFile, TCanvas, TLegend, TLatex, TF1, TGraph, TGraph2D, TPolyMarker3D, TGraphAsymmErrors, TLine,\
                 kBlack, kBlue, kRed, kGreen, kYellow, kOrange, kMagenta, kTeal, kAzure, TMath
import CMS_lumi as CMS_lumi
import tdrstyle as tdrstyle
from itertools import combinations
from math import sqrt, log, ceil, floor

gROOT.SetBatch(True)
#gROOT.SetBatch(False)
gStyle.SetOptTitle(0)

# CMS style
year = 2017
lumi = 41.4
CMS_lumi.cmsText      = "CMS"
CMS_lumi.extraText    = "Preliminary"
CMS_lumi.cmsTextSize  = 0.85
CMS_lumi.lumiTextSize = 0.80
CMS_lumi.relPosX      = 0.13
CMS_lumi.outOfFrame   = True
CMS_lumi.lumi_13TeV   = "%s, %s fb^{-1}"%(year,lumi)
tdrstyle.setTDRStyle()

DIR         = "./output"
PLOTS_DIR   = "./plots"
DM_label    = { 'DM0':      "h^{#pm} decay mode",
                'DM1':      "h^{#pm}#pi^{0} decay mode",
                'DM10':     "h^{#pm}h^{#mp}h^{#pm} decay mode",
                'DM11':     "h^{#pm}h^{#mp}h^{#pm}#pi^{0} decay mode",
                'all':      "all old decay modes",
                'combined': "combined", }
bin_dict    = { 1: 'DM0', 2: 'DM1', 3: 'DM10', 4: 'all', }
varlabel    = { 'm_2':   "m_{#tau}",
                'm_vis': "m_{vis}",
                'DM0':   "h^{#pm}",
                'DM1':   "h^{#pm}#pi^{0}",
                'DM10':  "h^{#pm}h^{#mp}h^{#pm}",
                'DM11':  "h^{#pm}h^{#mp}h^{#pm}#pi^{0}", }
vartitle    = { 'm_2':   "tau mass m_{#tau}",
                'm_vis': "visible mass m_{vis}", }
varshorttitle = { 'm_2':   "m_{#tau}",
                  'm_vis': "m_{vis}", }



def plotParabola(channel,var,DM,**kwargs):
    if DM=='DM0' and 'm_2' in var: return
    print green("\n>>> plot parabola for %s, %s"%(DM, var))
    
    tag       = kwargs.get('tag',       ""        )
    plotlabel = kwargs.get('plotlabel', ""        )
    MDFslices = kwargs.get('MDFslices', None      )
    breakdown = kwargs.get('breakdown', False     )
    fit       = kwargs.get('fit',       args.fit  ) and not breakdown
    
    results      = [ ]
    results_up   = [ ]
    results_down = [ ]
    
    filename      = '%s/higgsCombine.%s_%s-%s%s-13TeV.MultiDimFit.mH90.root'%(DIR,channel,var,'MDF' if MDFslices else DM,tag)
    filename_bbb  = '%s/higgsCombine.bin-%s_%s-%s%s-13TeV.MultiDimFit.mH90.root'%(DIR,channel,var,'MDF' if MDFslices else DM,tag)
    filename_stat = '%s/higgsCombine.stat-%s_%s-%s%s-13TeV.MultiDimFit.mH90.root'%(DIR,channel,var,'MDF' if MDFslices else DM,tag)
    print '>>>   file "%s"'%(filename)
    file = ensureTFile(filename)
    tree = file.Get('limit')
    
    # GET DeltaNLL
    list_nll = [ ]
    list_tes = [ ]
    if MDFslices:
      tes = "tes_%s"%DM
      MDFslices = { t:v for t,v in MDFslices.iteritems() if t!=tes }
      for event in tree:
        if tree.quantileExpected<0: continue
        if tree.deltaNLL == 0: continue
        if any(getattr(tree,t)!=v for t,v in MDFslices.iteritems()): continue
        list_tes.append(getattr(tree,tes))
        list_nll.append(2*tree.deltaNLL)
    else:
      for event in tree:
        if tree.quantileExpected<0: continue
        if tree.deltaNLL == 0: continue
        #if tree.tes < 0.97: continue
        list_tes.append(tree.tes)
        list_nll.append(2*tree.deltaNLL)
    file.Close()
    nllmin    = min(list_nll)
    list_dnll = map(lambda n: n-nllmin, list_nll) # DeltaNLL
    
    # MINIMUM
    dnllmin         = min(list_dnll) # should be 0.0 by definition
    min_index       = list_dnll.index(dnllmin)
    list_dnll_left  = list_dnll[:min_index]
    list_tes_left   = list_tes[:min_index]
    list_dnll_right = list_dnll[min_index:]
    list_tes_right  = list_tes[min_index:]
    if len(list_dnll_left)==0 or len(list_dnll_right)==0 : 
      print "ERROR! Parabola does not have minimum within given range !!!"
      exit(1)
    tmin_left = -1
    tmin_right = -1
    
    # FIND crossings of 1 sigma line
    # |-----<---min---------|
    for i, val in reversed(list(enumerate(list_dnll_left))):
      if val > (dnllmin+1):
          tmin_left = list_tes_left[i]
          break
    # |---------min--->-----|
    for i, val in enumerate(list_dnll_right):
      if val > (dnllmin+1):
          tmin_right = list_tes_right[i]
          break
    
    tes         = round(list_tes[min_index],4)
    tes_errDown = round((tes-tmin_left)*10000)/10000
    tes_errUp   = round((tmin_right-tes)*10000)/10000
    shift       = (list_tes[min_index]-1)*100
    
    # GRAPHS
    graph       = createParabolaFromLists(list_tes,list_dnll,fit=fit)
    graph_bbb, graph_stat = None, None
    tes_bbb, tes_stat = -1., -1.
    if breakdown:
      graph_bbb,  tes_bbb  = createParabola(filename_bbb)
      graph_stat, tes_stat = createParabola(filename_stat)
      graph_stat.SetMarkerColor(kRed)
      for graphe, color in [ (graph_stat,kRed), (graph_bbb,kBlue)]:
        graphe.SetMarkerColor(color)
        graphe.SetLineColor(color)
        graphe.SetLineWidth(2)
        graphe.SetLineStyle(1)
        graphe.SetMarkerStyle(20)
        graphe.SetMarkerSize(0.8)
      graph.SetLineWidth(2)
      #graph_bbb.SetLineStyle(2)
      graph_bbb.SetTitle("b.b.b. incl.")
      graph_stat.SetTitle("stat. only")
    
    # DRAW
    canvas = TCanvas("canvas","canvas",100,100,700,600)
    canvas.SetFillColor(0)
    canvas.SetBorderMode(0)
    canvas.SetFrameFillStyle(0)
    canvas.SetFrameBorderMode(0)
    canvas.SetTopMargin(  0.07 ); canvas.SetBottomMargin( 0.12 )
    canvas.SetLeftMargin( 0.12 ); canvas.SetRightMargin(  0.04 )
    canvas.cd()
    
    xmin, xmax   = 0.89, 1.14
    ymin, ymax   = 0.0,  16.
    fontsize     = 0.044
    lineheight   = 0.05
    xtext, ytext = 0.91, 0.38
    frame = canvas.DrawFrame(xmin,ymin,xmax,ymax)
    frame.GetYaxis().SetTitleSize(0.055)
    frame.GetXaxis().SetTitleSize(0.055)
    frame.GetXaxis().SetLabelSize(0.050)
    frame.GetYaxis().SetLabelSize(0.050)
    frame.GetXaxis().SetLabelOffset(0.010)
    frame.GetXaxis().SetTitleOffset(1.04)
    frame.GetYaxis().SetTitleOffset(1.02)
    frame.GetXaxis().SetTitle('tau energy scale')
    frame.GetYaxis().SetTitle('-2#Deltaln(L)')
    
    # GRAPH
    graph.SetMarkerStyle(20)
    graph.SetMarkerSize(0.8 if breakdown else 0.4)
    graph.Draw("PLXSAME")
    
    # FIT
    para, graph_clone, tesf, tes_errDown2, tes_errUp2 = None, None, None, None, None
    if fit:
      para = fitParabola(xmin,xmax,tes,list_tes_left,list_dnll_left,list_tes_right,list_dnll_right)
      fit = graph.Fit("fit",'R0')
      para.SetRange(xmin,xmax)
      #print para.GetXmin(),para.GetXmax()
      #fit = graph.Fit("fit",'R0','',para.GetXmin(),para.GetXmax())
      #para = para.Clone("fit_clone")
      para.Draw("SAME")
      gStyle.SetOptFit(0)
      tesf         = para.GetParameter(1)
      tes_errUp2   = round( sqrt( 1./(1000.*para.GetParameter(0)) )*10000)/10000 # TODO: propagate fit uncertainties with GetParError(i) !
      tes_errDown2 = round( sqrt( 1./(1000.*para.GetParameter(0)) )*10000)/10000
    
    latex = TLatex()
    lines = [ ]
    for i,y in [(1,1),(2,4)]:
      line = TLine(xmin, dnllmin+y, xmax, dnllmin+y)
      #line.SetLineWidth(1)
      line.SetLineStyle(7)
      line.Draw("SAME")
      latex.SetTextSize(0.050)
      latex.SetTextAlign(11)
      latex.SetTextFont(42)
      latex.DrawLatex(xmin+0.04*(xmax-xmin),y+0.02*(ymax-ymin),"%d#sigma"%i)
      lines.append(line)
    
    for tmin in [tmin_left,tmin_right]:
      line = TLine(tmin, dnllmin, tmin, dnllmin+1)
      line.SetLineStyle(2)
      line.Draw("SAME")
      lines.append(line)
    
    legend = None
    if breakdown:
      height = 3*fontsize
      x1, y1 = 0.94, 0.85
      legend = TLegend(x1,y1,x1-0.22,y1-height)
      legend.SetFillStyle(0)
      legend.SetBorderSize(0)
      legend.SetTextSize(fontsize)
      legend.SetTextFont(42)
      for graphf in [graph_stat,graph_bbb]:
        graphf.Draw("PLSAME")
        legend.AddEntry(graphf,graphf.GetTitle(),'lp')
      legend.AddEntry(graph,"syst. incl.",'lp')
      legend.Draw()
    
    print ">>> tes SF %7.3f - %-5.3f + %-5.3f"%(tes,tes_errDown,tes_errUp)
    print ">>> shift  %7.3f - %-5.2f + %-5.2f %%"%(shift,tes_errDown*100,tes_errUp*100)
    if fit:
      print ">>> tes SF %7.3f - %-5.3f + %-5.3f   (parabola)"%(tesf,tes_errDown2,tes_errUp2)
      print ">>> shift  %7.3f - %-5.2f + %-5.2f %% (parabola)"%(tesf-1,tes_errDown2*100,tes_errUp2*100)
    
    text = TLatex()
    text.SetTextSize(fontsize)
    text.SetTextAlign(31)
    text.SetTextFont(42)
    text.SetNDC(True)
    text.DrawLatex(xtext,ytext,                varlabel[var])
    text.DrawLatex(xtext,ytext-lineheight,     "%s"%DM_label[DM])
    
    text.DrawLatex(xtext,ytext-2.2*lineheight, "%7.3f_{-%5.3f}^{+%5.3f}"%(tes,tes_errDown,tes_errUp))
    if fit:
      text.SetTextColor(kRed)
      text.DrawLatex(xtext,ytext-3.5*lineheight, "%7.3f_{-%5.3f}^{+%5.3f}"%(tesf,tes_errDown2,tes_errUp2))
    if breakdown:
      text.SetTextColor(kRed)
      text.DrawLatex(xtext,ytext-3.5*lineheight, "%7.3f"%(tes_stat))
      text.SetTextColor(kBlue)
      text.DrawLatex(xtext,ytext-4.5*lineheight, "%7.3f"%(tes_bbb))
    
    CMS_lumi.relPosX = 0.13
    CMS_lumi.CMS_lumi(canvas,13,0)
    #canvas.SetTicks(1,1)
    canvas.Modified()
    canvas.Update()
    
    if breakdown: tag += "_breakdown"
    if MDFslices: tag += "_MDF"
    if fit:       tag += "_fit"
    canvasname = "%s/parabola_tes_%s_%s-%s%s"%(PLOTS_DIR,channel,var,DM,tag)
    canvas.SaveAs(canvasname+".png")
    canvas.SaveAs(canvasname+".pdf")
    canvas.Close()
    
    return tes, tes_errDown, tes_errUp, tesf, tes_errDown2, tes_errUp2
    

def createParabolaFromLists(list_tes,list_dnll,fit=False):
    """Create TGraph of DeltaNLL parabola vs. tes from lists."""
    npoints = len(list_dnll)
    if not fit: return TGraph(npoints, array('d',list_tes), array('d',list_dnll))
    graph  = TGraphAsymmErrors()
    for i, (tes,dnll) in enumerate(zip(list_tes,list_dnll)):
      error = 1.0
      if dnll<6 and i>0 and i+1<npoints:
        left, right = list_dnll[i-1], list_dnll[i+1]
        error       = max(0.1,(abs(dnll-left)+abs(right-dnll))/2)
      graph.SetPoint(i,tes,dnll)
      graph.SetPointError(i,0.0,0.0,error,error)
    return graph
    
def createParabola(filename):
    """Create TGraph of DeltaNLL parabola vs. tes from MultiDimFit file."""
    file = ensureTFile(filename)
    tree = file.Get('limit')
    tes, nll = [ ], [ ]
    for event in tree:
      tes.append(tree.tes)
      nll.append(2*tree.deltaNLL)
    file.Close()
    minnll = min(nll)
    mintes = tes[nll.index(minnll)]
    dnll   = map(lambda x: x-minnll, nll) # DeltaNLL
    graph  = TGraph(len(tes), array('d',tes), array('d',dnll))
    return graph, mintes

def findMultiDimSlices(channel,var,**kwargs):
    """Find minimum of multidimensional parabola in MultiDimFit file and return
    dictionary of the corresponding values of POI's."""
    tag      = kwargs.get('tag', "" )
    filename = '%s/higgsCombine.%s_%s-%s%s-13TeV.MultiDimFit.mH90.root'%(DIR,channel,var,'MDF',tag)
    file     = ensureTFile(filename)
    tree     = file.Get('limit')
    pois     = [b.GetName() for b in tree.GetListOfBranches() if 'tes_DM' in b.GetName()]
    slices   = { }
    nnlmin   = 10e10
    for event in tree:
      nnl = 2*event.deltaNLL
      if nnl<nnlmin:
        nnlmin = nnl
        for poi in pois:
          slices[poi] = getattr(event,poi)
        #print nnlmin, slices
    file.Close()
    #print nnlmin, slices
    return nnlmin, slices
    
def plotParabola2D(channel,var,**kwargs):
    """Plot 2D parabola."""
    tag        = kwargs.get('tag',        ""  )
    nnlmin     = kwargs.get('nnlmin',     0   )
    MDFslices  = kwargs.get('MDFslices', { }  )
    canvasname = "%s/parabola_tes_%s_%s-%s%s"%(PLOTS_DIR,channel,var,"MDF",tag)
    filename   = '%s/higgsCombine.%s_%s-%s%s-13TeV.MultiDimFit.mH90.root'%(DIR,channel,var,'MDF',tag)
    file       = ensureTFile(filename)
    tree       = file.Get('limit')
    ztitle     = "-2#Deltaln(L)"
    pois       = [b.GetName() for b in tree.GetListOfBranches() if 'tes_DM' in b.GetName()]
    pmin, pmax = 0.97, 1.03
    
    for poi1, poi2 in combinations(pois,2):
      
      if len(pois)>2:
        canvasname = "%s/parabola_tes_%s_%s-%s_%s-%s%s"%(PLOTS_DIR,channel,var,"MDF",poi1,poi2,tag)
        canvasname = canvasname.replace('tes_DM','DM')
      
      graph = TGraph2D()
      graph.SetTitle(ztitle)
      #tree.Draw("%s:%s:deltaNLL >> graph"%(poi1,poi2),"","COLZ")
      for i, event in enumerate(tree):
        nnl  = 2*event.deltaNLL-nnlmin
        xpoi = getattr(event,poi1)
        ypoi = getattr(event,poi2)
        graph.SetPoint(i,xpoi,ypoi,nnl)
    
      latex = TLatex()
      latex.SetTextSize(0.040)
      latex.SetTextFont(42)
      lines = [ ]
      if poi1 in MDFslices:
        line = TLine(MDFslices[poi1],pmin,MDFslices[poi1],pmax)
        x, y = MDFslices[poi1]+0.001, pmax-0.003
        lines.append((line,"%s = %.3f"%(poi1,MDFslices[poi1]),x,y,13))
      if poi2 in MDFslices:
        line = TLine(pmin,MDFslices[poi2],pmax,MDFslices[poi2])
        x, y = pmin+0.003, MDFslices[poi2]+0.001
        lines.append((line,"%s = %.3f"%(poi2,MDFslices[poi2]),x,y,11))
    
      canvas = TCanvas("canvas","canvas",100,100,800,600)
      canvas.SetFillColor(0)
      canvas.SetBorderMode(0)
      canvas.SetFrameFillStyle(0)
      canvas.SetFrameBorderMode(0)
      canvas.SetTopMargin(  0.07 ); canvas.SetBottomMargin( 0.13 )
      canvas.SetLeftMargin( 0.14 ); canvas.SetRightMargin(  0.18 )
      canvas.cd()
      canvas.SetLogz()
      #canvas.SetTheta(90.); pad.SetPhi(0.001)
    
      frame = canvas.DrawFrame(pmin,pmin,pmax,pmax)
      frame.GetXaxis().SetTitle(re.sub(r"_(DM\d+)",r"_{\1}",poi1))
      frame.GetYaxis().SetTitle(re.sub(r"_(DM\d+)",r"_{\1}",poi2))
      frame.GetZaxis().SetTitle(ztitle)
      frame.GetYaxis().SetTitleSize(0.055)
      frame.GetXaxis().SetTitleSize(0.055)
      frame.GetZaxis().SetTitleSize(0.055)
      frame.GetXaxis().SetLabelSize(0.050)
      frame.GetYaxis().SetLabelSize(0.050)
      frame.GetXaxis().SetLabelOffset(0.010)
      frame.GetXaxis().SetTitleOffset(1.05)
      frame.GetYaxis().SetTitleOffset(1.14)
      graph.GetZaxis().SetTitle(ztitle)
      graph.GetZaxis().SetTitleOffset(0.1)
      frame.GetZaxis().SetTitleOffset(0.1)
      frame.GetZaxis().SetNdivisions(5)
      #if nnlmin:
        #print "here"
        #levels = [0.01,1,10,100,1000]
        #frame.SetContour(len(levels),array('d',levels))
    
      graph.SetMinimum(0.5)
      graph.SetMaximum(100)
      graph.Draw('COLZ SAME')
    
      for line,poi,x,y,align in lines:
        line.SetLineStyle(2)
        line.Draw('SAME')
        latex.SetTextAlign(align)
        latex.DrawLatex(x,y,re.sub(r"_(DM\d+)",r"_{\1}",poi))
    
      latex.SetTextAlign(33)
      latex.SetTextSize(0.055)
      latex.SetTextAngle(90)
      latex.DrawLatex(pmax+0.19*(pmax-pmin),pmax,ztitle)
    
      CMS_lumi.relPosX = 0.14
      CMS_lumi.CMS_lumi(canvas,13,0)
      gPad.Modified()
      gPad.Update()
      gPad.RedrawAxis()
    
      canvas.SaveAs(canvasname+'.png')
      canvas.SaveAs(canvasname+'.pdf')
    
    


def fitParabola(xmin,xmax,tes,list_tes_left,list_dnll_left,list_tes_right,list_dnll_right):
    
    # FIT X RANGE (<ymax)
    xmin_fit = xmin
    xmax_fit = xmax
    ymax_fit = 6
    ymax_left  = min(ymax_fit,max(list_dnll_left))
    ymax_right = min(ymax_fit,max(list_dnll_right))
    # |-->---|----min----|------|
    for i, val in enumerate(list_dnll_left):
      if val <= (ymax_left):
        xmin_fit = round(list_tes_left[i],4)
        print ">>> xmin_fit = %.3f (%2d,%.1f) is below NLL %.1f"%(xmin_fit,val,i,ymax_left)
        break
    # |------|----min----|---<--|
    for i, val in reversed(list(enumerate(list_dnll_right))):
      if val <= (ymax_right):
        xmax_fit = round(list_tes_right[i],4)
        print ">>> xmax_fit = %.3f (%2d,%.1f) is below NLL %.1f"%(xmax_fit,val,i,ymax_right)
        break
    
    # FIT MAX WIDTH
    bmid     = (xmax_fit+xmin_fit)/2.
    dtmin    = max(tes-xmin_fit,0.004)
    dtmax    = max(xmax_fit-tes,0.004)
    tmin_fit = tes-abs(dtmin)*0.26
    tmax_fit = tes+abs(dtmax)*0.26
    wmin_fit, wmax_fit = sorted([ymax_left/(1000.*(dtmin**2)),ymax_right/(1000.*(dtmax**2))])
    print ">>> tes=%.3f, tmin_fit=%.3f, tmin_fit=%.3f, bmid=xmin_fit+(xmax_fit-xmin_fit)/2=%.3f"%(tes,tmin_fit,tmax_fit,bmid)
    print ">>> wmin_fit=%.3f, wmax_fit=%.3f"%(wmin_fit,wmax_fit)
    
    # FIT Y RANGE (<ymax)
    #ymax_fit = 0.5
    
    # FIT PARAMETERS
    wmin, wval, wmax = wmin_fit*0.99, wmin_fit, wmax_fit*1.50
    bmin, bval, bmax = tmin_fit, tes, tmax_fit
    cmin, cval, cmax = -0.0001, 0.0, 0.5 #max(min(ymax_fit,3),0.001)
    
    if bmin<xmin_fit: print ">>> Warning! setting bmin=%.3f -> %.3f=xmin_fit"%(bmin,xmin_fit); bmin = xmin_fit
    if bmax>xmax_fit: print ">>> Warning! setting bmin=%.3f -> %.3f=xmin_fit"%(bmax,xmax_fit); bmax = xmax_fit
    if bval<bmin or bmax<bval: print ">>> Warning! setting bval=%.3f -> %.3f=bmin+(bmin-bmax)/2"%(bval,(bmax+bmin)/2.); bval = (bmax+bmin)/2.
    if cval<cmin or cmax<cval: print ">>> Warning! setting cval=%.3f -> %.3f=cmin+(cmin-cmax)/2"%(cval,(cmax+cmin)/2.); cval = (cmax+cmin)/2.
    print ">>> width   = %5s [%5s, %5s]"%(wval, wmin, wmax)
    print ">>> tes     = %5s [%5s, %5s]"%(bval, bmin, bmax)
    print ">>> voffset = %5s [%5s, %5s]"%(cval, cmin, cmax)
    
    # FIT FUNCTION
    #xmin_fit, xmax_fit = 0.91, 1.05
    para = TF1("fit","[0]*1000*(x-[1])**2+[2]",xmin_fit,xmax_fit)
    print xmin_fit, para.GetXmin()
    print xmax_fit, para.GetXmax()
    para.SetParName(0,"width")
    para.SetParName(1,"tes")
    para.SetParName(2,"voffset")
    #para.FixParameter(0,0)
    #para.FixParameter(2,0)
    para.SetParameters(wval,bval,0)
    para.SetParLimits(0,wmin,wmax)
    para.SetParLimits(1,bmin,bmax)
    para.SetParLimits(2,cmin,cmax)
    
    return para


def measureTES(filename, unc=False):
    """Create TGraph of DeltaNLL parabola vs. tes from MultiDimFit file."""
    file = ensureTFile(filename)
    tree = file.Get('limit')
    tes, nll = [ ], [ ]
    for event in tree:
      tes.append(tree.tes)
      nll.append(2*tree.deltaNLL)
    file.Close()
    nllmin = min(nll)
    imin   = nll.index(nllmin)
    tesmin = tes[imin]
    
    if unc:
      nll_left  = nll[:imin]
      tes_left  = tes[:imin]
      nll_right = nll[imin:]
      tes_right = tes[imin:]
      if len(nll_left)==0 or len(nll_right)==0 : 
        print "ERROR! measureTES: Parabola does not have a minimum within given range!"
        exit(1)
      tmin_left = -1
      tmin_right = -1
      
      # FIND crossings of 1 sigma line
      # |-----<---min---------|
      for i, val in reversed(list(enumerate(nll_left))):
        if val > (nllmin+1):
          tmin_left = tes_left[i]
          break
      # |---------min--->-----|
      for i, val in enumerate(nll_right):
        if val > (nllmin+1):
          tmin_right = tes_right[i]
          break
      
      tes_errDown = tesmin-tmin_left
      tes_errUp   = tmin_right-tesmin
      return tesmin, tes_errDown, tes_errUp
    
    return tesmin
    


def plotMeasurements(categories,measurements,**kwargs):
    """Plot measurements."""
    print green("plotMeasurements()",pre=">>>\n>>> ")
    
    npoints      = len(measurements)
    categories   = categories[::-1]
    measurements = measurements[::-1]
    minB         = 0.13
    title        = kwargs.get('title',      ""                   )
    text         = kwargs.get('text',       ""                   )
    entries      = kwargs.get('entries',    ""                   )
    plottag      = kwargs.get('tag',        ""                   )
    xtitle       = kwargs.get('xtitle',     ""                   )
    xminu        = kwargs.get('xmin',       None                 )
    xmaxu        = kwargs.get('xmax',       None                 )
    position     = kwargs.get('position',   ""                   ).lower() # legend
    align        = kwargs.get('align',      "center"             ).lower() # category labels
    canvasH      = kwargs.get('H',          min(400,120+90*npoints) )
    canvasL      = kwargs.get('L',          0.20                 )
    canvasB      = kwargs.get('B',          minB                 )
    canvasname   = kwargs.get('canvas',     "measurements"       )
    xmin, xmax   = None, None
    maxpoints    = 0
    colors       = [ kBlack, kBlue, kRed, kOrange, kGreen, kMagenta ]
    
    # MAKE GRAPH
    errwidth     = 0.1
    graphs       = [ ]
    for i, points in enumerate(measurements): #(name, points)
      if not isinstance(points,list):
        points = [ points ]
      offset = 1./(len(points)+1)
      while len(points)>maxpoints:
        maxpoints += 1
        graphs.append(TGraphAsymmErrors())
      for j, point in enumerate(points):
        if point==None: continue
        (x,xErrLow,xErrUp) = point
        graph = graphs[j]
        graph.SetPoint(i,x,1+i-(j+1)*offset)
        graph.SetPointError(i,xErrLow,xErrUp,errwidth,errwidth) # -/+ 1 sigma
        if xmin==None or x-xErrLow < xmin: xmin = x-xErrLow
        if xmax==None or x+xErrUp  > xmax: xmax = x+xErrUp
    if xminu or xmaxu:
      if xminu: xmin = xminu
      if xmaxu: xmax = xmaxu
    else:
      range = xmax - xmin
      xmin -= 0.18*range
      xmax += 0.18*range
    
    # DRAW
    canvasB  = min(canvasB,minB)
    canvasH  = int(canvasH/(1.-minB+canvasB))
    scale    = 600./canvasH
    canvasB  = minB*(scale-1)+canvasB
    canvas   = TCanvas("canvas","canvas",100,100,800,canvasH)
    canvas.SetTopMargin( 0.07*scale ); canvas.SetBottomMargin( canvasB )
    canvas.SetLeftMargin(  canvasL  ); canvas.SetRightMargin(  0.04 )
    canvas.SetGrid(1,0)
    canvas.cd()
    
    legend = None
    if entries:
      legtextsize = 0.052*scale
      width       = 0.25
      height      = legtextsize*1.08*len([o for o in [title,text]+zip(graphs,entries) if o])
      if 'out' in position:
        x1 = 0.01; x2 = x1+width
        y1 = 0.03; y2 = y1+height
      else:
        if 'left' in position:   x1 = canvasL+0.04;    x2 = x1+width
        else:                    x1 = 0.88;            x2 = x1-width 
        if 'bottom' in position: y1 = 0.04+0.13*scale; y2 = y1+height
        else:                    y1 = 0.96-0.07*scale; y2 = y1-height
      legend = TLegend(x1,y1,x2,y2)
      legend.SetTextSize(legtextsize)
      legend.SetBorderSize(0)
      legend.SetFillStyle(0)
      legend.SetFillColor(0)
      if title:
        legend.SetTextFont(62)
        legend.SetHeader(title)
      legend.SetTextFont(42)
    
    frame  = canvas.DrawFrame(xmin,0.0,xmax,float(npoints))
    frame.GetYaxis().SetLabelSize(0.0)
    frame.GetXaxis().SetLabelSize(0.052*scale)
    frame.GetXaxis().SetTitleSize(0.060*scale)
    frame.GetXaxis().SetTitleOffset(0.98)
    frame.GetYaxis().SetNdivisions(npoints,0,0,False)
    frame.GetXaxis().SetTitle(xtitle)
    
    for i, graph in enumerate(graphs):
      color = colors[i%len(colors)]
      graph.SetLineColor(color)
      graph.SetMarkerColor(color)
      graph.SetLineStyle(1)
      graph.SetMarkerStyle(20)
      graph.SetLineWidth(2)
      graph.SetMarkerSize(1)
      graph.Draw("PSAME")
      if legend and i<len(entries):
        legend.AddEntry(graph,entries[i],'lep')
    if legend:
      if text:
        legend.AddEntry(graph,entries[i],'lep')
      legend.Draw()
    
    labelfontsize = 0.050*scale
    latex = TLatex()
    latex.SetTextSize(labelfontsize)
    latex.SetTextFont(62)
    if align=="center":
      latex.SetTextAlign(22)
      margin = 0.02+ stringWidth(*categories)*labelfontsize/2 # width strings
      #print stringWidth(*categories)
      #print margin
      xtext  = marginCenter(canvas,frame.GetXaxis(),margin=margin) # automatic
    else:
      latex.SetTextAlign(32)
      xtext  = xmin-0.02*(xmax-xmin)
    for i, name in enumerate(categories):
      ytext = i+0.5
      latex.DrawLatex(xtext,ytext,name)
    
    CMS_lumi.relPosX = 0.13
    CMS_lumi.CMS_lumi(canvas,13,0)
    
    canvas.SaveAs(canvasname+".png")
    canvas.SaveAs(canvasname+".pdf")
    canvas.Close()
    
def combineMeasurements(measurements):
  """Average measurement (x,errDown,errUp), weighted by their uncertainty."""
  if not isinstance(measurements,list) and isinstance(measurements,ntuple):
    return measurement
  sumxvar2 = sum([ x/em**2 for x,em,ep in measurements])
  sumvar2  = sum([ 1./em**2 for x,em,ep in measurements])
  average  = sumxvar2/sumvar2
  stddev   = sqrt(1./sumvar2)
  return (average,stddev,stddev)

def combineMeasurementsAsymm(measurements):
  """Average measurement (x,errDown,errUp), weighted by their uncertainty."""
  # https://arxiv.org/pdf/physics/0406120v1.pdf (21-25)
  if not isinstance(measurements,list) and isinstance(measurements,ntuple):
    return measurement
  sumxvar2 = sum([ x/em**2 for x,em,ep in measurements])
  sumvar2  = sum([ 1./em**2 for x,em,ep in measurements])
  average  = sumxvar2/sumvar2
  stddev   = sqrt(1./sumvar2)
  return (average,stddev,stddev)

#def weightAsymm(sigmaP,sigmaM):
#  sigmaA = 2*sigmaP*sigmaLow/(sigmaP+sigmaM)
#  sigmaB = (sigmaM-sigmaP)/(sigmaP+sigmaM)
#  weight = sigmaA/(sigmaA+sigmaB)**3
#def sigma(sigmaM,sigmaP):      return 2*sigmaP*sigmaLow/(sigmaP+sigmaM)
#def sigmaPrime(sigmaM,sigmaP): return (sigmaM-sigmaP)/(sigmaP+sigmaM)

def writeMeasurement(filename,categories,measurements,**kwargs):
    """Write measurements to file."""
    if ".txt" not in filename[-4]: filename += ".txt"
    mformat = kwargs.get('format'," %10.4f %10.4f %10.4f") #" %10.6g %10.6g %10.6g"
    sformat = re.sub(r"%(\d*).?\d*[a-z]",r"%\1s",mformat)
    with open(filename,'w+') as file:
      print ">>>   created txt file %s"%(filename)
      startdate = time.strftime("%a %d/%m/%Y %H:%M:%S",time.gmtime())
      file.write("%s\n"%(startdate))
      for category, points in zip(categories,measurements):
        file.write("%-10s"%category)
        for point in points:
          if point:
            file.write(mformat%point)
          else:
            file.write(sformat%("-","-","-"))
        file.write('\n')

def readMeasurement(filename,**kwargs):
    """Read measurements from file."""
    if ".txt" not in filename[-4]: filename += ".txt"
    categories   = [ ]
    measurements = [ ]
    with open(filename,'r') as file:
      print ">>>   reading txt file %s"%(filename)
      startdate = time.strftime("%a %d/%m/%Y %H:%M:%S",time.gmtime())
      file.next()
      for line in file:
        points  = [ ]
        columns = line.split()
        categories.append(columns[0])
        i = 1
        while len(columns[i:])>=3:
          try:
            points.append((float(columns[i]),float(columns[i+1]),float(columns[i+2])))
          except ValueError:
            points.append(None)
          i += 3
        measurements.append(points)
    return measurements
    
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
        strings.append(matches.group(1))
      string = string.replace('#','')
    return max([len(s) for s in strings])
    
def marginCenter(canvas,axis,side='left',shift=0,margin=None):
    """Calculate the center of the right margin in units of a given axis"""
    range    = axis.GetXmax() - axis.GetXmin()
    rangeNDC = 1 - canvas.GetRightMargin() - canvas.GetLeftMargin()
    if side=="right":
      if margin==None: margin = canvas.GetRightMargin()
      center = axis.GetXmax() + margin*range/rangeNDC/2.0
    else:
      if margin==None: margin = canvas.GetLeftMargin()
      center = axis.GetXmin() - margin*range/rangeNDC/2.0
    if shift:
        if center>0: center*=(1+shift/100.0)
        else:        center*=(1-shift/100.0)
    return center
  
def green(string,**kwargs):
  return kwargs.get('pre',"")+"\x1b[0;32;40m%s\033[0m"%(string)
  
def warning(string,**kwargs):
  print ">>> \x1b[1;33;40m%sWarning!\x1b[0;33;40m %s\033[0m"%(kwargs.get('pre',""),string)
    
def error(string,**kwargs):
  print ">>> \x1b[1;31;40m%sERROR!\x1b[0;31;40m %s\033[0m"%(kwargs.get('pre',""),string)
  exit(1)
  
def ensureDirectory(dirname):
  """Make directory if it does not exist."""
  if not os.path.exists(dirname):
      os.makedirs(dirname)
      print ">>> made directory %s"%dirname
  
def ensureTFile(filename,**kwargs):
  """Open TFile and make sure if that it exists."""
  if not os.path.exists(filename):
    warning('getTFile: File "%s" does not exist!'%(filename))
  file = TFile(filename)
  if not file:
    warning('getTFile: Could not open file "%s"!'%(filename))
  return file

def ensureFile(filename):
  if not os.path.isfile(filename):
    error('File "%s" does not exist!'%(filename))
  return filename



def main(args):
    
    verbosity   = args.verbose
    ensureDirectory(PLOTS_DIR)
    channels    = [ 'mt', ] #'et' ]
    vars        = [ 'm_2', 'm_vis' ]
    DMs         = [ 'DM0', 'DM1', 'DM10' ] #3 ]
    tags        = args.tags
    breakdown   = args.breakdown
    multiDimFit = args.multiDimFit
    if args.DMs: DMs = args.DMs
    if args.observables: vars = [o for o in args.observables if '#' not in o]
    
    cats    = [varlabel[d] for d in DMs]
    entries = [varlabel[v] for v in vars]
    
    # LOOP over tags, channels, variables
    for tag in tags:
      for channel in channels:
        points, points_fit = [[ ],[ ]], [[ ],[ ]]
        for i, var in enumerate(vars):
          
          # MULTIDIMFIT
          slices = { }
          if multiDimFit:
            nnlmin, slices = findMultiDimSlices(channel,var,tag=tag)
            plotParabola2D(channel,var,nnlmin=nnlmin,MDFslices=slices,tag=tag)
          
          # LOOP over DMs
          for DM in DMs:
            if "_0p" in tag and var=='m_vis':  continue
            if "_85" in tag and var=='m_2':    continue
            if "_restr" in tag and var=='m_2': continue
            if DM=='DM11' and "newDM" not in tag:  continue
            if DM=="DM0" and var=='m_2':
              points[i].append(None); points_fit[i].append(None)
              continue
            #title = "%s, %s"%(varshorttitle[var],DM_label[DM].replace("decay mode",''))
            
            # PARABOLA
            tes,tesDown,tesUp,tesf,tesfDown,tesfUp = plotParabola(channel,var,DM,tag=tag,breakdown=breakdown,MDFslices=slices)
            
            # SAVE points
            points[i].append((tes,tesDown,tesUp))
            points_fit[i].append((tesf,tesfDown,tesfUp))
        
        filename = "%s/measurement_tes_%s%s"%(PLOTS_DIR,channel,tag)
        writeMeasurement(filename,DMs,points)
        if args.fit: writeMeasurement(filename+"_fit",DMs,points_fit)
    
#     for tag in tags:
#       if 'newDM' in tag: continue
#       for channel in channels:
#         if len(vars)==2 and len(DMs)>=3:
#           tags2 = [ tag, tag+"_fit"  ] if args.fit else [ tag ]
#           for tag2 in tags2:
#             canvas  = "%s/measurement_tes_%s%s"%(PLOTS_DIR,channel,tag2)
#             measurements = readMeasurement(canvas)
#             if "_0p" in tag: # add m_vis from measurement tagged without "_0p05"
#               canvas2 = re.sub(r"_0p\d+","",canvas)
#               measurements2 = readMeasurement(canvas2)
#               for points,points2 in zip(measurements,measurements2):
#                 points.append(points2[1])
#             if "_restr" in tag: # add m_2 from measurement tagged with "_0p05"
#               canvas2 = canvas.replace("_restr","_0p05")
#               measurements2 = readMeasurement(canvas2)
#               for points, points2 in zip(measurements,measurements2):
#                 points = points.insert(0,points2[0])
#             plotMeasurements(cats,measurements,xtitle="tau energy scale",xmin=0.97,xmax=1.04,L=0.20,position="out",entries=entries,canvas=canvas)
#     
#     if args.customSummary and len(vars)==2 and len(DMs)>=3:
#       channel = "mt"
#       tags2   = [ "", "_fit"  ] if args.fit else [ "" ]
#       for tag2 in tags2:
#         canvas  = "%s/measurement_tes_%s%s"%(PLOTS_DIR,channel,"_differentCuts"+tag2)
#         canvas1 = "%s/measurement_tes_%s%s"%(PLOTS_DIR,channel,"_mtlt50_0p05"+tag2)
#         canvas2 = "%s/measurement_tes_%s%s"%(PLOTS_DIR,channel,"_ZTTregion2"+tag2)
#         ensureFile(canvas+'.txt')
#         ensureFile(canvas1+'.txt')
#         ensureFile(canvas2+'.txt')
#         measurements1 = readMeasurement(canvas1) # m_2
#         measurements2 = readMeasurement(canvas2) # m_vis
#         for points1, points2 in zip(measurements1,measurements2):
#           points1 = points1.append(points2[1])
#         writeMeasurement(canvas,DMs,measurements1)
#         plotMeasurements(cats,measurements1,xtitle="tau energy scale",xmin=0.97,xmax=1.04,L=0.20,position="out",entries=entries,canvas=canvas)
    
    #meas_old = [[ None,              (0.976,0.004,0.004)],
    #            [(0.996,0.004,0.002),(0.982,0.006,0.002)],
    #            [(1.010,0.010,0.004),(0.992,0.002,0.008)]]
    #meas_FR  = [[ None,              (0.986,0.002,0.002)],
    #            [(0.980,0.002,0.002),(0.988,0.002,0.002)],
    #            [(0.986,0.004,0.006),(0.980,0.002,0.002)]]
    #meas_new = [[ None,              (1.018,0.002,0.002)],
    #            [(0.988,0.002,0.002),(0.986,0.002,0.004)],
    #            [(1.012,0.002,0.002),(0.988,0.002,0.002)]]
    #meas = [[ None,              (1.018,0.011,0.012)],
    #        [(0.988,0.003,0.003),(0.986,0.007,0.005)],
    #        [(1.012,0.004,0.006),(0.988,0.005,0.005)]]
    #entries = ["m_{#tau}","m_{vis}"]
    #canvasname = "measurement%s"%(tag)
    #plotMeasurements(cats,meas,    xtitle="tau energy scale",xmin=0.97,xmax=1.04,L=0.18,position="out",entries=entries,canvas=canvasname)
    #plotMeasurements(cats,meas_old,xtitle="tau energy scale",xmin=0.97,xmax=1.04,L=0.18,position="out",entries=entries,canvas=canvasname+"_old",H=380)
    #plotMeasurements(cats,meas_FR, xtitle="tau energy scale",xmin=0.97,xmax=1.04,L=0.18,position="out",entries=entries,canvas=canvasname+"_FR", H=380)
    #plotMeasurements(cats,meas_new,xtitle="tau energy scale",xmin=0.97,xmax=1.04,L=0.18,position="out",entries=entries,canvas=canvasname+"_new",H=380)
    


if __name__ == '__main__':
    print 
    
    argv = sys.argv
    description = '''This script makes datacards with CombineHarvester.'''
    parser = ArgumentParser(prog="plot Parabola",description=description,epilog="Succes!")
    parser.add_argument( '-t', "--tag",         dest="tags", type=str, nargs='+', default=[ '' ], action='store',
                         metavar="TAGS",        help="tags for the input file" )
    parser.add_argument( '-d', "--decayMode",   dest="DMs", type=str, nargs='+', default=[ ], action='store',
                         metavar="DECAY",       help="decay mode" )
    parser.add_argument( '-o', '-m', "--observable",  dest="observables", type=str, nargs='+', default=[ ], action='store',
                         metavar="VARIABLE",    help="name of observable for TES measurement" )
    parser.add_argument( '-r', "--shift-range", dest="shiftRange", type=str, default="0.940,1.060", action='store',
                         metavar="RANGE",       help="range of TES shifts" )
    parser.add_argument( '-f', "--fit",         dest="fit",  default=True, action='store_true',
                                                help="fit NLL profile with parametrized parabola" )
    parser.add_argument( '-b', "--breakdown",   dest="breakdown",  default=False, action='store_true',
                                                help="plot breakdown of NLL profile" )
    parser.add_argument( '-M', "--multiDimFit", dest="multiDimFit",  default=False, action='store_true',
                                                help="assume multidimensional fit with a POI for each DM" )
    parser.add_argument( '-c', "--custom",      dest="customSummary",  default=False, action='store_true',
                                                help="make custom summary of measurements" )
    parser.add_argument( '-v', "--verbose",     dest="verbose",  default=False, action='store_true',
                                                help="set verbose" )
    args = parser.parse_args()
    
    main(args)
    print ">>>\n>>> done\n"
    

