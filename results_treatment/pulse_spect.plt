##########################################
# Command line arguments
##########################################

# This script needs five positional command line arguments:
#   - the input file (ARG1)
#   - the output file (ARG2) 
#   - the frequency exponent (ARG3)
#   - the minimum frequency (ARG4)
#   - the maximum frequency (ARG5)

##########################################
# Set parameters
##########################################

# Important variables
ua_to_cm = 219474.6313705

# Set a LaTeX terminal to let LaTex process all the text parts
set terminal cairolatex pdf
set output ARG2

# Name of the axes
set xlabel "Nombre d'onde ($10\\up{" . ARG3 . "}$ cm$\\up{-1}$)"
set ylabel 'Intensité'

# No legend
unset key

# Grid
set grid

# Define wave number range
# xmin = ARG4 * ua_to_cm / (10**ARG3)
# xmax = ARG5 * ua_to_cm / (10**ARG3)
# set xrange[xmin:xmax]

##########################################
# Plot values
##########################################

plot ARG1 using ($1*ua_to_cm/(10**ARG3)):2 with lines

##########################################
# Close everything before leaving
##########################################

set output
set terminal pop