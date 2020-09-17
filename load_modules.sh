#!/bin/bash
# vim:ts=4:sw=4

module --force purge

# Load python, jinja2 and yaml in order to run the scripts. The modules we need to load depend on the cluster the scripts are running on.
# Current requirements:
#	- jinja2	2 and later		(in case of required upgrade, load python 3 module then issue in cmdline: python -m pip install --user -U Jinja2)
#	- yaml		5.1 and later	(in case of required upgrade, load python 3 module then issue in cmdline: python -m pip install --user -U pyyaml)

# Specifically for control_launcher
#   - numpy     1.14 and later  (in case of required upgrade, load python 3 module then issue in cmdline: python -m pip install --user -U numpy)

# Specifically for results_treatment
#   - gnuplot   5 .0 and later    

if   [ "$CLUSTER_NAME" = "dragon1" ]; then
    module load python/3.5.4-GCC-4.9.2
	
elif [ "$CLUSTER_NAME" = "dragon2" ]; then
    module load releases/2019a
    module load PyYAML/5.1-GCCcore-8.2.0

elif [ "$CLUSTER_NAME" = "vega" ]; then
    module load Python/3.7.4-GCCcore-8.3.0
    module load PyYAML/5.1.2-GCCcore-8.3.0
    module load gnuplot/5.0.3-intel-2016a

elif [ "$CLUSTER_NAME" = "lemaitre3" ]; then
	module load releases/2018b
	module load Python/3.6.6-foss-2018b
    module load gnuplot/5.2.5-foss-2018b

elif [ "$CLUSTER_NAME" = "hercules" ]; then
    module load Python/3.5.2-foss-2016b

elif [ "$CLUSTER_NAME" = "" ] && [ `hostname` = "login2.cerberus.os" ]; then
    module load PyYAML/5.1.2-GCCcore-8.3.0
    export CLUSTER_NAME="hydra"

elif [ "$CLUSTER_NAME" = "hydra" ]; then
    module load PyYAML/5.1.2-GCCcore-8.3.0

else
    echo "ERROR: Unknown cluster. Corresponding modules can't be loaded. Please add the cluster module informations to load_modules.sh."

fi
