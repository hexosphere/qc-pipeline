##########################################
# Command line arguments
##########################################

# This script needs five positional command line arguments:
#   - the input file (ARG1)
#   - the output file (ARG2) 
#   - the number of lines (ARG3)
#   - the number of points in the graph (ARG4)
#   - the time exponent (ARG5)

##########################################
# Set parameters
##########################################

# Determine the frequency of the plotting (how much data is skipped between two points)
skip = ARG3/ARG4
if (skip < 1) skip = 1 ; else skip = floor(skip)

# Set a LaTeX terminal to let LaTex process all the text parts
set terminal cairolatex pdf
set output ARG2

# Name of the axes
set xlabel 'Temps ($10\up{' . ARG5 . '}$ s)'
set ylabel 'Amplitude'

# No legend
unset key

# Grid
set grid

##########################################
# Plot values
##########################################

ua_to_sec = 2.4188843265857e-17

plot ARG1 using ($1*ua_to_sec/(10**ARG5)):2 every skip with lines

##########################################
# Close everything before leaving
##########################################

set output
set terminal pop