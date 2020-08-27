#!/usr/bin/env python3

##################################################################################################################################################
##                                                     QOCT-RA Input Builder & Job Launcher                                                     ##
##                                                                                                                                              ##
##                                 This script prepares the input files needed to run the QOCT-RA program by extracting                         ##
##                               information from a given source file and launches the corresponding jobs on the cluster.                       ##
##                                                                                                                                              ##
## /!\ In order to run, this script requires Python 3.5+ as well as NumPy, YAML and Jinja2. Ask your cluster(s) administrator(s) if needed. /!\ ##
##################################################################################################################################################

import argparse
import importlib
import os
import shutil
import sys
from collections import OrderedDict
from inspect import getsourcefile

import jinja2  # Only needed in the renderer subscript, it is loaded here to check if your python installation does support jinja2
import numpy as np
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

# Define and import the parser module that wil be used to parse the source file

print("\nSource file format: ", config['qoct-ra']['source_file_format'])
source_parser = importlib.import_module(config['qoct-ra']['source_file_format'] + "_parser")

# =========================================================
# Reading the file
# =========================================================

print("\nScanning %s file ..." % source_filename, end="")
with open(source, 'r') as source_file:
  source_content = source_file.read().splitlines()
print('%20s' % "[ DONE ]")

# Cleaning up the source file from surrounding spaces and blank lines

source_content = list(map(str.strip, source_content))   # removes leading & trailing blank/spaces
source_content = list(filter(None, source_content))     # removes blank lines/no char

# =========================================================
# Get the list of states and their multiplicity
# =========================================================

print("\nExtracting the list of states and their multiplicity ...", end="")
states_list = source_parser.get_states_list(source_content)
#TODO : define get_states_list in qchem_parser.py
print('%20s' % "[ DONE ]")

# =========================================================
# Get the list of spin-orbit couplings (SOC)
# =========================================================

print("\nExtracting the list of spin-orbit couplings ...", end="")
soc_list = source_parser.get_soc_list(source_content, states_list)
#TODO : define get_soc_list in qchem_parser.py
print('%20s' % "[ DONE ]")

# =========================================================
# Get the list of transition dipole moments
# =========================================================

print("\nExtracting the list of transition dipole moments ...", end="")
momdip_list = source_parser.get_momdip_list(source_content)
#TODO : define get_momdip_list in qchem_parser.py
print('%20s' % "[ DONE ]")

print("\nThe source file has been succesfully parsed.")

# ===================================================================
# ===================================================================
#                       MIME DIAGONALIZATION
# ===================================================================
# ===================================================================

section_title = "2. MIME diagonalization"

print("")
print("")
print(''.center(len(section_title)+10, '*'))
print(section_title.center(len(section_title)+10))
print(''.center(len(section_title)+10, '*'))

# =========================================================
# Creation of the MIME matrix containing the SOC
# =========================================================
   
mime = np.zeros((len(states_list), len(states_list)))  # Quick init of a zero-filled matrix

for soc in soc_list:
  k1 = soc[0] - 1 #TODO: Apply that minus 1 in the get_soc_list function instead (since it's specific to Q-CHEM)
  k2 = soc[1] - 1 #TODO: Apply that minus 1 in the get_soc_list function instead (since it's specific to Q-CHEM)
  val = soc[2]
  mime[k1][k2] = val

print("\nMIME (cm-1)")
print('')
for row in mime:
  for val in row:
    print (np.format_float_scientific(val,precision=7,unique=False,pad_left=2), end = " ")
  print ('')

# =========================================================
# MIME diagonalization
# =========================================================

print("\nDiagonalizing the MIME ...", end="")   
diag_mime = np.linalg.eig(mime)
print('%20s' % "[ DONE ]")

eigenvalues = diag_mime[0]
eigenvectors = diag_mime[1]
transpose = np.transpose(eigenvectors)

# =========================================================
# Eigenvalues
# =========================================================

# Converting the eigenvalues from cm-1 to ua, nm and eV
eigenvalues_ua=eigenvalues/219474.6313705
eigenvalues_nm=10000000/eigenvalues
eigenvalues_ev=eigenvalues/8065.6

print("\nEigenvalues (cm-1 | ua | eV | nm)")
for val in range(len(eigenvalues)):
	print ("% 12.5f || % 1.8e || % 10.6f || % 8.7f" % (eigenvalues[val],eigenvalues_ua[val],eigenvalues_ev[val],eigenvalues_nm[val]))

np.savetxt('energies_cm-1',eigenvalues,fmt='%1.10e')
np.savetxt('energies_ua',eigenvalues_ua,fmt='%1.10e',footer='comment',comments='#')
np.savetxt('energies_nm',eigenvalues_nm,fmt='%1.10e')
np.savetxt('energies_ev',eigenvalues_ev,fmt='%1.10e')

# =========================================================
# Eigenvectors matrix
# =========================================================

print("\nEigenvectors matrix")
print ('')
for vector in eigenvectors:
  for val in vector:
    print (np.format_float_scientific(val,precision=7,unique=False,pad_left=2), end = " ")
  print ('')
np.savetxt('mat_pto',eigenvectors,fmt='% 18.10e')

# =========================================================
# Eigenvectors transpose
# =========================================================

print("\nEigenvectors transpose")
print ('')
for vector in transpose:
  for val in vector:
    print (np.format_float_scientific(val,precision=10,unique=False,pad_left=2), end = " ")
  print ('')
np.savetxt('mat_otp',transpose,fmt='% 18.10e')

# ===================================================================
# ===================================================================
#                       DIPOLE MOMENTS MATRIX
# ===================================================================
# ===================================================================

section_title = "3. Dipole moments matrix"

print("")
print("")
print(''.center(len(section_title)+10, '*'))
print(section_title.center(len(section_title)+10))
print(''.center(len(section_title)+10, '*'))

# =========================================================
# Creation of the dipole moments matrix
# =========================================================
   
momdip_mtx = np.zeros((len(states_list), len(states_list)), dtype=float)  # Quick init of a zero-filled matrix

for momdip in momdip_list:
  k1 = int(momdip[0])
  k2 = int(momdip[1])
  val = float(momdip[2])
  momdip_mtx[k1][k2] = val

print("\nDipole moments matrix in the zero order basis set (ua)")
print('')
for row in momdip_mtx:
  for val in row:
    print (np.format_float_scientific(val,precision=7,unique=False,pad_left=2), end = " ")
  print ('')
np.savetxt('momdip_0',momdip_mtx,fmt='% 18.10e')

# =========================================================
# Conversion in the eigenstates basis set
# =========================================================

momdip_ev_mtx = np.dot(transpose,momdip_mtx)

for row in range(len(momdip_ev_mtx)):
	for val in range(row):
		momdip_ev_mtx[val,row] = momdip_ev_mtx[row,val]
		
print("\nDipole moments matrix in the eigenstates basis set (ua)")
print('')
for row in momdip_ev_mtx:
  for val in row:
    print (np.format_float_scientific(val,precision=10,unique=False,pad_left=2), end = " ")
  print ('')
np.savetxt('momdip_p',momdip_ev_mtx,fmt='% 18.10e')	

# ===================================================================
# ===================================================================
#                       DENSITY MATRICES
# ===================================================================
# ===================================================================

section_title = "3. Density matrices"

print("")
print("")
print(''.center(len(section_title)+10, '*'))
print(section_title.center(len(section_title)+10))
print(''.center(len(section_title)+10, '*'))

# =========================================================
# Initial density matrix
# =========================================================

print("\nCreating starting population file (ground state, eigenstates basis set)")

dim = len(eigenvalues_ua)
init_pop = np.zeros((dim,dim),dtype=complex)
init_pop[0,0] = 1+0j

f = open("fondamental_1","w+")
for line in init_pop:
  for val in line:
    print ('( {0.real:.2f} , {0.imag:.2f} )'.format(val), end = " ", file = f)
  print ('', file = f)
f.close()

# =========================================================
# Projectors
# =========================================================

#TODO: This section needs to be reworked to not depend on external files

print("\nCreating the projectors files")
print ('')
with open('etats') as file:
  tcount = 0
  for line in file:
    parts = line.split()
    if parts[1] == 'T':
      state = int(parts[0])
      print ("The ", state, " state is a triplet. The corresponding projector will be prepared.") 
      P = np.zeros((dim,dim),dtype=complex)
      P[state-1,state-1]=1+0j
      tcount = tcount + 1
      name = "projectorT" + str(tcount) + "_1"
      g = open(name,"w+")
      for i in P:
        for j in i:
          print ('( {0.real:.2f} , {0.imag:.2f} )'.format(j), end = " ", file = g)
        print ('', file = g)
      g.close()
print(' ')
print("All the projectors files have been created")

