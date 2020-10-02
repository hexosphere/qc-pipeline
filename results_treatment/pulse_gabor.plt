##########################################
# Command line arguments
##########################################

# This script needs four positional command line arguments:
#   - the input file (ARG1)
#   - the output file (ARG2) 
#   - the time exponent (ARG3)
#   - the frequency exponent (ARG4)

##########################################
# Set parameters
##########################################

# Important variables
ua_to_cm = 219474.6313705
ua_to_sec = 2.4188843265857e-17

# Set a LaTeX terminal to let LaTex process all the text parts
set terminal cairolatex pdf
set output ARG2
set palette defined (0.00 "white", 55.0 "navy")

# No legend
unset key

# Name of the axes
set xlabel 'Temps ($10\up{' . ARG3 . '}$ s)'
set ylabel "Nombre d'onde ($10\\up{" . ARG4 . "}$ cm$\\up{-1}$)"
set zlabel 'Intensité (unités arbitraires)'

##########################################
# Plot values
##########################################

plot ARG1 using ($1*ua_to_sec/(10**ARG3)):($2*ua_to_cm/(10**ARG4)):5 with image

##########################################
# Close everything before leaving
##########################################

set output
set terminal pop
