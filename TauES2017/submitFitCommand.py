#! /usr/bin/env python
# 
# Multicore jobs:
#   to submit multicore job:    qsub -pe smp 8 ...
#   in mg_configuration.txt:    run_mode=2 # multicore
#                               nb_core=8
#   note it might wait longer in queue
# 
# https://wiki.chipp.ch/twiki/bin/view/CmsTier3/Tier3Policies#Batch_system_policies
# 

import os, sys
import subprocess
import time
from math import floor
from argparse import ArgumentParser
print

argv = sys.argv
usage = """This script will submit jobs running combineTool.py."""
parser = ArgumentParser(prog="submitToys",description=usage,epilog="Succes!")
parser.add_argument('-q', "--queue",        dest="queue", type=str, choices=["short.q","all.q","long.q"], default="all.q", action='store',
                    metavar="QUEUE",        help="queue for batch submission" )
parser.add_argument( '-m', "--mock-submit", dest="submit", default=True, action='store_false',
                                            help="do not submit job to batch (mock submit)")
parser.add_argument(       "--ncores",      dest="ncores", type=int, default=1, action='store',
                                            help="number of core in each job")
parser.add_argument( '-N', "--ntoys",       dest="ntoys", default=100, action='store',
                                            help="number of event to be generated in each job")
parser.add_argument( '-s', "--seeds",       dest="seeds", type=int, nargs='+', default=[ ], action='store',
                                            help="random seeds for toy generation")
parser.add_argument( '-i', "--index",       dest="indices", type=int, nargs='+', default=[ ], action='store',
                     metavar="INDEX",       help="indices to run over" )
parser.add_argument( '-t', "--tag",         dest="tags", type=str, nargs='+', default=[ ], action='store',
                     metavar="TAGS",        help="tag for a file names" )
parser.add_argument( '-d', "--decayMode",   dest="DMs", type=str, nargs='+', default=[ ], action='store',
                     metavar="DECAYMODE",   help="decay mode" )
parser.add_argument( '-e', "--extra-tag",   dest="extratag", type=str, default="", action='store',
                     metavar="TAG",         help="extra tag for output files" )
parser.add_argument( '-c', "--checkPoints", dest="checkPoints", type=str, nargs='+', default=[ ], action='store',
                     metavar="POINTS",      help="check tes points (for post-fit and bias test)" )
parser.add_argument( '-o', "--observable",  dest="observables", type=str, nargs='+', default=[ ], action='store',
                     metavar="VARIABLE",    help="name of observable for TES measurement" )
parser.add_argument( '-B', "--biasTest",    dest="doBiasTest", default=False, action='store_true',
                                            help="perform bias test")
parser.add_argument( '-p', "--postfit",     dest="doPostFit", default=False, action='store_true',
                                            help="perform postfit")
parser.add_argument( '-M', "--multiDimFit", dest="multiDimFit",  default=False, action='store_true',
                                            help="run simultaneous fit between each DM in MultiDimFit" )
parser.add_argument( '-P', "--npoints",     dest="nPointsPerJob", type=int, default=1000, action='store',
                     metavar="NPOINTS",     help="number of points per job")
parser.add_argument( '-n', "--noNomRun",    dest="noNomRun", default=False, action='store_true',
                                            help='do not run "nominal" fit')
parser.add_argument( '-H', "--harvester",   dest="noHarvester", default=True, action='store_false',
                                            help="run harvester")
args = parser.parse_args()

#WORKPATH    = "/shome/ineuteli/analysis/CMSSW_8_1_0/src/CombineHarvester/LowMassTauTau"
queue       = args.queue            # all.q (10h), short.q (90 min.)
observables = args.observables      # observables
DMs         = args.DMs              # decay modes
tags        = args.tags             # tag for file
checkPoints = args.checkPoints      # points to run postfit or bias test over
ncores      = args.ncores           # "nb_core" in input/mg5_configuration.txt should be the same number!
ntoys       = args.ntoys            # number of events to be generated
seeds       = args.seeds            # random seed
doBiasTest  = args.doBiasTest       # run bias test
multiDimFit = args.multiDimFit      # run simultaneous fit with multiDimFit
noNomRun    = args.noNomRun         # do not run nominal fit
noHarvester = args.noHarvester      # do not run harvester
first_index = 1                     # first index of a sample
last_index  = 2                     # last index of a sample
indices     = range( first_index, last_index + 1 )
if args.indices: indices = args.indices
if not tags:  tags  = [ "" ]
if not seeds: seeds = [ "" ] 
if not DMs:   DMs   = [ 'DM0', 'DM1', 'DM10', 'DM11' ]
if not observables: observables = [ 'm_2', 'm_vis' ]
nsubmitted    = 0
nPointsPOI    = 61
nPointsPerJob = args.nPointsPerJob

# ensure directory
REPORTDIR = "submitFitCommand"
if not os.path.exists(REPORTDIR):
  os.makedirs(REPORTDIR)
  print ">>> made directory %s\n>>>"%(REPORTDIR)



def main():
    global observables, DMs, tags, seeds, ntoys, doBiasTest, checkPoints, noNomRun, noHarvester, multiDimFit
    
    if multiDimFit:
      DMs = [ 'MDF' ]
    
    ijob = 0
    for seed in seeds:
      for tag in tags:
        for obs in observables:
          if obs=="m_vis" and "0p" in tag: continue
          if obs=="m_2" and "restr" in tag: continue
          for DM in DMs:
            if obs=="m_2" and DM=="DM0": continue
            if 'newDM' in tag and DM=="DM11": continue
            options = "-o %s"%(obs)
            jobname = "fit_TES_%s_%s"%(obs,DM)
            if DM!='MDF':   options += " -d %s"%(DM)
            if tag:         options += " -t %s"%(tag);   jobname += "%s"%(tag)
            if seed:        options += " -s %s"%(seed);
            if ntoys!=0:    options += " -N %s"%(ntoys)
            if doBiasTest:  options += " -B"
            if noNomRun:    options += " -n"
            if noHarvester: options += " -h"
            if multiDimFit:
              options += " -M -F %d -L %d"
              nDMs       = 2
              if 'newDM' in tag: nDMs += 1
              if 'm_vis' in obs: nDMs += 1
              nPointsMDF = nPointsPOI**nDMs
              nJobs      = floor(nPointsMDF/nPointsPerJob)
              points     = [nPointsPerJob*i for i in range(0,int(nJobs+1))]
              if nPointsMDF not in points: points.append(nPointsMDF)
              for i,first in enumerate(points[:-1]):
                ijob += 1
                last = points[i+1]
                if last!=nPointsMDF: last -= 1
                jobnamep = "%s_%d"%(jobname,ijob)
                if "-h" not in options and i>0: options+=" -h"
                submitSample(jobnamep,options%(first,last))
                if i==0 and '-h' not in options and args.submit:
                  print ">>> wait 30 seconds so the first job can run the harvester and text2workspace..."
                  time.sleep(30)
            elif checkPoints:
              options += " -c %s"
              for i,checkpoint in enumerate(checkPoints):
                ijob += 1
                jobnamep = "%s_%d"%(jobname,ijob)
                if "-n" not in options and i>0: options+=" -n -h"
                submitSample(jobnamep,options%checkpoint)
                if i==0 and "-n" not in options and args.submit:
                  print ">>> wait 30 seconds so the first job can run the harvester and text2workspace..."
                  time.sleep(30)
            else:
              ijob += 1
              jobname += "_%d"%(ijob)
              submitSample(jobname,options)
    

def submitSample(jobname,options):
    global nsubmitted 
    command = "qsub -q %s -N %s submitFitCommand.sh %s"%(queue,jobname,options)
    print ">>> %s"%(command.replace(jobname,"\033[;1m%s\033[0;0m"%jobname,1))
    nsubmitted += 1
    if not args.submit: return
    sys.stdout.write(">>> ")
    sys.stdout.flush()
    os.system(command)
    print ">>> "
    


if __name__ == '__main__':
    print "\n>>> "
    main()
    print ">>> done, submitted %d job(s)\n"%(nsubmitted)


