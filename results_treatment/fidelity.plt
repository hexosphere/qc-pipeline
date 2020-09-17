# This script needs four positional command line arguments:
#   - the input file (ARG1)
#   - the output file (ARG2) 
#   - the number of lines (ARG3)
#   - the number of points in the graph (ARG4)

# Determine the frequency of the plotting (how much data is skipped between two points)
skip = ARG3/ARG4
if (skip < 1) skip = 1 ; else skip = floor(skip)

# Set a LaTeX terminal to let LaTex process all the text parts
set terminal cairolatex pdf
set output ARG2

# Name of the axes
set xlabel "Nombre d'itérations"
set ylabel "Fidélité"

# No legend
unset key

# Grid
set grid

# Y axis range and labels
set yrange [0:1]
set ytic 0,0.1,1

# X axis range
set xrange [0:ARG3]

# Plot values
plot ARG1 using 1:24 every skip with linespoints

# Close everything before leaving
set output
set terminal pop