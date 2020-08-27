#!/usr/bin/env python3

################################################################################################################################################
##                                                    QOCT-RA Input Builder & Job Launcher                                                    ##
##                                                                                                                                            ##
##                                This script prepares the input files needed to run the QOCT-RA program by extracting                        ##
##                              information from a given source file and launches the corresponding jobs on the cluster.                      ##
##                                                                                                                                            ##
##   /!\ In order to run, this script requires Python 3.5+ as well as YAML and Jinja2. Ask your cluster(s) administrator(s) if needed. /!\    ##
################################################################################################################################################

import argparse
import os
import shutil
import sys
from collections import OrderedDict
from inspect import getsourcefile

import jinja2  # Only needed in the renderer subscript, it is loaded here to check if your python installation does support jinja2
import yaml

# ===================================================================
# ===================================================================
# Command line arguments
# ===================================================================
# ===================================================================

# Define the arguments needed for the script (here they are defined as named arguments rather than positional arguments, check https://stackoverflow.com/questions/24180527/argparse-required-arguments-listed-under-optional-arguments for more info).

parser = argparse.ArgumentParser(add_help=False, description="This script prepares the input files needed to run the QOCT-RA program by extracting information from a given source file and launches the corresponding jobs on the cluster.")

required = parser.add_argument_group('Required arguments')
required.add_argument("-i","--source", type=str, help="Path to the source file that contains all the necessary informations that need to be processed", required=True)
required.add_argument("-d","--qoct_ra_dir", type=str, help="Path to the directory where QOCT-RA is located", required=True)
required.add_argument('-cfg', '--config', type=str, help="Path to the YAML config file", required=True)
required.add_argument('-cl', '--clusters', type=str, help="Path to the YAML clusters file", required=True)

optional = parser.add_argument_group('Optional arguments')
optional.add_argument('-h','--help',action='help',default=argparse.SUPPRESS,help='Show this help message and exit')
optional.add_argument("-ow","--overwrite",action="store_true",help="Overwrite files if they already exists")
optional.add_argument("-k","--keep",action="store_true",help="Do not archive the treated source file and leave it where it is")

args = parser.parse_args()

# Define the variables corresponding to those arguments

source = args.source                     # Source file containing all the necessary informations
qoct_ra_dir = args.qoct_ra_dir           # Path to the directory where QOCT-RA is located
config_file = args.config                # Main configuration file
clusters_file = args.clusters            # YAML file containing all informations about the clusters

overwrite = args.overwrite               # Flag for overwriting the files
keep = args.keep                         # Flag for keeping the source file where it is

# ===================================================================
# ===================================================================
#                           PREPARATION STEP
# ===================================================================
# ===================================================================

# Get the size of the terminal in order to have a prettier output, if you need something more robust, go check http://granitosaurus.rocks/getting-terminal-size.html

columns, rows = shutil.get_terminal_size()

# Output Header

print("".center(columns,"*"))
print("")
print("EXECUTION OF THE QOCT-RA INPUT BUILDER & JOB LAUNCHER BEGINS NOW".center(columns))
print("")
print("".center(columns,"*"))

# =========================================================
# Important folders
# =========================================================

# Codes directory (determined by getting the path to the directory where this script is)

code_dir = os.path.dirname(os.path.realpath(os.path.abspath(getsourcefile(lambda:0))))
print("\nCodes directory:   ", code_dir)

# =========================================================
# Load YAML files
# =========================================================

# Loading the config_file

if not os.path.exists(config_file):
  print(config_file)
  print("  ^ ERROR: The path to the YAML main configuration file does not seem to exist.")
  print("Aborting ...")
  exit(4)
elif not os.path.isfile(config_file):
  print(config_file)
  print("  ^ ERROR: This is not a file.")
  print("Aborting ...")
  exit(4)
else:
  config_file = os.path.abspath(config_file)

print("\nLoading the main configuration file %s ..." % config_file, end="")
with open(config_file, 'r') as f_config:
  config = yaml.load(f_config, Loader=yaml.FullLoader)
print('%12s' % "[ DONE ]")

# Loading the clusters_file for the informations about the clusters

if not os.path.exists(clusters_file):
  print(clusters_file)
  print("  ^ ERROR: The path to the YAML clusters configuration file does not seem to exist.")
  print("Aborting ...")
  exit(4)
elif not os.path.isfile(clusters_file):
  print(clusters_file)
  print("  ^ ERROR: This is not a file.")
  print("Aborting ...")
  exit(4)
else:
  clusters_file = os.path.abspath(clusters_file)

print("\nLoading the clusters file %s ..." % clusters_file, end="")
with open(clusters_file, 'r') as f_clusters:
  clusters_cfg = yaml.load(f_clusters, Loader=yaml.FullLoader)
print('%20s' % "[ DONE ]")

# =========================================================
# Check arguments
# =========================================================

cluster_name = os.environ['CLUSTER_NAME']
print("\nThis script is running on the %s cluster" % cluster_name)

# Check if the path to the QOCT-RA directory exists and make sure it's absolute.

if not os.path.exists(qoct_ra_dir):
  print(qoct_ra_dir)
  print("  ^ ERROR: The path to the QOCT-RA folder does not seem to exist.")
  print("Aborting ...")
  exit(4)

if not os.path.isdir(qoct_ra_dir):
  print(qoct_ra_dir)
  print("  ^ ERROR: This is not a directory.")
  print("Aborting ...")
  exit(4)

qoct_ra_dir = os.path.abspath(qoct_ra_dir)
print("\nQOCT-RA directory: ", qoct_ra_dir)

# Check if the path to the source file exists and make sure it's absolute.

if not os.path.exists(source):
  print(source)
  print("  ^ ERROR: The path to the ab initio program output file does not seem to exist.")
  print("Aborting ...")
  exit(4)

if not os.path.isfile(source):
  print(source)
  print("  ^ ERROR: This is not a file.")
  print("Aborting ...")
  exit(4)

source = os.path.abspath(source)
print("\nSource file: ", source)

source_path = os.path.dirname(source)
source_filename = os.path.basename(source)

# Check if a folder already exists for that molecule

mol_name = str(source_filename.split('.')[0]) # Getting rid of the format extension to get the name of the molecule

if os.path.exists(os.path.join(qoct_ra_dir,"Dat",mol_name)) and not overwrite:
  print("\n\nERROR: A folder for the %s molecule already exists in %s !" % (mol_name, os.path.join(qoct_ra_dir,"Dat")))
  print("Aborting ...")
  exit(4)

# =========================================================
# Establishing the different job scales
# =========================================================

# Gather all the different job scales from the clusters configuration file in a temporary dictionary

job_scales_tmp = clusters_cfg[cluster_name]['progs']['qoct-ra']['job_scales']

# Initialize the final dictionary where the job scales will be sorted by their upper limit

job_scales = {}

# Sort the different job scales by their upper limit and store them in the job_scales dictionary

for scale in job_scales_tmp:
  scale_limit = scale['scale_limit']
  del scale['scale_limit']
  job_scales[float(scale_limit)] = scale

print("\nJob scales for %s:" % cluster_name)
job_scales = OrderedDict(sorted(job_scales.items()))

print("")
print(''.center(85, '-'))
print ("{:<15} {:<20} {:<20} {:<20} {:<10}".format('scale_limit','Label','Partition_name','Time','Cores'))
print(''.center(85, '-'))
for scale_limit, scale in job_scales.items():
  print ("{:<15} {:<20} {:<20} {:<20} {:<10}".format(scale_limit, scale['label'], scale['partition_name'], scale['time'], scale['cores']))
print(''.center(85, '-'))

# ===================================================================
# ===================================================================
#                       PARSING THE SOURCE FILE
# ===================================================================
# ===================================================================

section_title = "1. Parsing the source file"

print("")
print("")
print(''.center(len(section_title)+10, '*'))
print(section_title.center(len(section_title)+10))
print(''.center(len(section_title)+10, '*'))

# =========================================================
# Reading the file
# =========================================================

print("\nScanning %s file ..." % source_filename, end="")
with open(source, 'r') as source_file:
  source_content = source_file.read().splitlines()
print('%20s' % "[ DONE ]")

