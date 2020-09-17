# This script needs five positional command line arguments:
#   - the input file (ARG1)
#   - the output file (ARG2) 
#   - the number of lines (ARG3)
#   - the number of points in the graph (ARG4)
#   - the number of states (columns) needing to be plotted (ARG5)

# Determine the frequency of the plotting (how much data is skipped between two points)
skip = ARG3/ARG4
if (skip < 1) skip = 1 ; else skip = floor(skip)

# Set a LaTeX terminal to let LaTex process all the text parts
set terminal cairolatex pdf
set output ARG2

# Name of the axes
set xlabel "Temps"
set ylabel "Population"

# No legend
# unset key

# Grid
set grid

# Y axis range and labels
set yrange [0:1]
set ytic 0,0.1,1

# X axis range
#set xrange [0:ARG3]

# Plot values
plot for [i=2:ARG5+1] ARG1 using 1:i every skip with linespoints

# Close everything before leaving
set output
set terminal pop