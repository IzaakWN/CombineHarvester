#! /bin/bash

SEEDS1="111111 120194 123456 300518 472012 567890 654321 765432 888888 901234"
SEEDS2="111111 120194 123456 137125 222222 251252 297463 300518 345678 472012 445566 562018 567890 621337 654321 765432" #789012 888888 901234"
SEEDS3="251252 297463 651337"
COMMON="-t _ZTTregion2 _ZTTregion2_0p05 _mtlt50_0p05 -c 0.960 0.970 0.980 0.990 1.000 1.010 1.020 1.030 1.040"
#COMMON2="-t _mtlt50 -c 0.960 0.970 0.980 0.990 1.000 1.010 1.020 1.030 1.040"
#COMMON3="-t _ZTTregion2 _ZTTregion2_0p05 _mtlt50_0p05 -c 0.960 0.970 0.980 0.990 1.000 1.010 1.020 1.030 1.040"

./submitFitCommand.py $COMMON -B -n -N 1000 -s $SEEDS1 -o m_2 m_vis -d DM0 DM10
./submitFitCommand.py $COMMON -B -n -N 1000 -s $SEEDS1 -o m_vis -d DM1
./submitFitCommand.py $COMMON -B -n -N 500 -s $SEEDS2 -o m_2 -d DM1

# SEEDS4="111111 120194 123456 137125 222222 251252"
# SEEDS5="297463 300518 345678 472012 445566"
# SEEDS6="562018 567890 621337 654321 765432"
#./submitFitCommand.py $COMMON2 -B -n -N 800 -s $SEEDS6 -o m_2 m_vis -d DM0 #DM10
#./submitFitCommand.py $COMMON2 -B -n -N 800 -s $SEEDS6 -o m_vis -d DM1
# ./submitFitCommand.py $COMMON2 -B -n -N 500 -s $SEEDS5 -o m_2 -d DM1

#./submitFitCommand.py $COMMON3 -B -n -N 500 -s $SEEDS3 -o m_2 -d DM1

# ASIMOV:
#$ ./doFit_TES.sh -B -n -N -1 -t _ZTTregion2

# MULTIDIMENSION FIT:
# ./submitFitCommand.py -q short.q -t _mtlt50_0p05 _mtlt50 -M -o m_2 -H 
# ./submitFitCommand.py -q short.q -t _ZTTregion2 -M -o m_vis -P 3000
# ./haddMDF.sh -t _mtlt50_0p05
# ./haddMDF.sh -t _ZTTregion2 -m m_vis
# ./plotParabola_TES.py -t _mtlt50_0p05 -M -o m_2