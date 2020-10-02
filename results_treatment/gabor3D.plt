##########################################
# Command line arguments
##########################################

# This script needs four positional command line arguments:
#   - the input file (ARG1)
#   - the output file (ARG2) 
#   - the time exponent (ARG3)
#   - the frequency exponent (ARG4)

##########################################
# Set the 3D plotting parameters
##########################################

set pm3d at ss
set view 45,45

##########################################
# Set parameters
##########################################

set terminal cairolatex pdf
set output ARG2

unset key
set ticslevel 0
set xlabel 'Time ($10\\up{ARG3}$ s)'
set ylabel "Frequency ($10\\up{ARG4}$ Hz)"
set zlabel "Gabor transform (arbitrary units)" rotate parallel

set xtics 0,2,18 nomirror
set ytics 2,0.2,3.2 nomirror

##########################################
# Plot values
##########################################

time_conv = 2.4188843265857e-17
freq_conv = 1 / time_conv

splot ARG1 using ($1*time_conv/(10**ARG3)):(3.6):5 with lines, \
ARG1 using (-4):($2*freq_conv/(10**ARG4)):5 with lines, \
ARG1 using ($1*time_conv/(10**ARG3)):($2*freq_conv/(10**ARG4)):5 with pm3d

##########################################
# Close everything before leaving
##########################################

set output
set terminal pop
