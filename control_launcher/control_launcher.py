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
  k1 = soc[0] - 1
  k2 = soc[1] - 1
  val = soc[2]
  mime[k1][k2] = val

print("\nMIME (cm-1)")
print('')
for row in mime:
  for val in row:
    print(np.format_float_scientific(val,precision=7,unique=False,pad_left=2), end = " ")
  print('')

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

print("")
print(''.center(40, '-'))
print('Eigenvalues'.center(40, ' '))
print(''.center(40, '-'))
print("{:<10} {:<10} {:<10} {:<10}".format('cm-1','ua','eV','nm'))
print(''.center(40, '-'))
for val in range(len(eigenvalues)):
  print("{:<9.2f} {:<1.4e} {:<8.4f} {:<8.4f}".format(eigenvalues[val],eigenvalues_ua[val],eigenvalues_ev[val],eigenvalues_nm[val]))
print(''.center(40, '-'))

# =========================================================
# Eigenvectors matrix
# =========================================================

print("\nEigenvectors matrix")
print('')
for vector in eigenvectors:
  for val in vector:
    print(np.format_float_scientific(val,precision=5,unique=False,pad_left=2), end = " ")
  print('')

# =========================================================
# Eigenvectors transpose matrix
# =========================================================

print("\nEigenvectors transpose matrix")
print('')
for vector in transpose:
  for val in vector:
    print(np.format_float_scientific(val,precision=5,unique=False,pad_left=2), end = " ")
  print('')

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
    print(np.format_float_scientific(val,precision=5,unique=False,pad_left=2), end = " ")
  print('')

# =========================================================
# Conversion in the eigenstates basis set
# =========================================================

momdip_es_mtx = np.dot(transpose,momdip_mtx)

for row in range(len(momdip_es_mtx)):
	for val in range(row):
		momdip_es_mtx[val,row] = momdip_es_mtx[row,val] #TODO: Why?
		
print("\nDipole moments matrix in the eigenstates basis set (ua)")
print('')
for row in momdip_es_mtx:
  for val in row:
    print(np.format_float_scientific(val,precision=5,unique=False,pad_left=2), end = " ")
  print('')

# ===================================================================
# ===================================================================
#                       FILES CREATION
# ===================================================================
# ===================================================================

section_title = "3. Files creation"

print("")
print("")
print(''.center(len(section_title)+10, '*'))
print(section_title.center(len(section_title)+10))
print(''.center(len(section_title)+10, '*'))

# =========================================================
# Creating the subfolder in the "Dat" folder of QOCT-RA
# =========================================================

mol_dir = os.path.join(qoct_ra_dir,"Dat",mol_name)

if os.path.exists(mol_dir):
  shutil.rmtree(mol_dir)

os.makedirs(mol_dir)

print("\nThe %s subfolder has been created at %s" % (mol_name, os.path.join(qoct_ra_dir,"Dat")))

# =========================================================
# Writing already calculated values to files
# =========================================================

print("\nWriting already calculated values to files (states list, mime, eigenvalues, eigenvectors, dipole moments matrix) ...", end="") 

# MIME

np.savetxt(os.path.join(mol_dir,"mime"),mime,fmt='% 18.10e')

# States List

basis_dir = os.path.join(mol_dir,"Basis")

os.makedirs(basis_dir)

states_file = open(os.path.join(basis_dir,"states"),"w")

for state in states_list:
  print("%d %s" % (state[0], state[1]), file=states_file)
print("#comment", file = states_file)
#TODO : Save the whole states_list with np.savetxt ? Will it still works with QOCT-RA ?

states_file.close()

# Energies

energies_dir = os.path.join(mol_dir,"Energies")

os.makedirs(energies_dir)

np.savetxt(os.path.join(energies_dir,'energies_cm-1'),eigenvalues,fmt='%1.10e')
np.savetxt(os.path.join(energies_dir,'energies_ua'),eigenvalues_ua,fmt='%1.10e',footer='comment',comments='#')
np.savetxt(os.path.join(energies_dir,'energies_nm'),eigenvalues_nm,fmt='%1.10e')
np.savetxt(os.path.join(energies_dir,'energies_ev'),eigenvalues_ev,fmt='%1.10e')

# Eigenvectors matrix and eigenvectors transpose matrix

mat_dir = os.path.join(mol_dir,"Mat_cb")

os.makedirs(mat_dir)

np.savetxt(os.path.join(mat_dir,'mat_pto'),eigenvectors,fmt='% 18.10e')
np.savetxt(os.path.join(mat_dir,'mat_otp'),transpose,fmt='% 18.10e')

# Dipole moments matrix

mom_dir = os.path.join(mol_dir,"MomDip")

os.makedirs(mom_dir)

np.savetxt(os.path.join(mom_dir,'momdip_0'),momdip_mtx,fmt='% 18.10e')
np.savetxt(os.path.join(mom_dir,'momdip_p'),momdip_es_mtx,fmt='% 18.10e')	

print('%20s' % "[ DONE ]")

# =========================================================
# Density matrices
# =========================================================

md_dir = os.path.join(mol_dir,"Md")

os.makedirs(md_dir)

# Initial population

print("\nCreating initial population file (ground state in the eigenstates basis set) ...", end="") 

init_pop = np.zeros((len(states_list), len(states_list)),dtype=complex)  # Quick init of a zero-filled matrix
init_pop[0,0] = 1+0j # All the population is in the ground state at the beginning

pop_file = open(os.path.join(md_dir,"fondamental_1"),"w")
for line in init_pop:
  for val in line:
    print('( {0.real:.2f} , {0.imag:.2f} )'.format(val), end = " ", file = pop_file)
  print('', file = pop_file)
pop_file.close()

print('%20s' % "[ DONE ]")

# Final population (dummy file but still needed by QOCT-RA)

print("\nCreating dummy final population file (copy of the initial population file) ...", end="") 

shutil.copy(os.path.join(md_dir,"fondamental_1"), os.path.join(md_dir,"final_1"))

print('%20s' % "[ DONE ]")

# Projectors

print("\nCreating the projectors files ...")
print('')

for state in states_list:
  if state[1] == "T":
    print("Creating the projector file for state %s ..." % state[3])
    proj = np.zeros((len(states_list),len(states_list)),dtype=complex)
    proj[state[0]-1,state[0]-1] = 1+0j
    proj_file = open(os.path.join(md_dir,"projector" + state[3] + "_1"),"w")
    for line in proj:
      for val in line:
        print('( {0.real:.2f} , {0.imag:.2f} )'.format(val), end = " ", file = proj_file)
      print('', file = proj_file)
    proj_file.close()
    print('%20s' % "[ DONE ]")

print("\nAll the projectors files have been created")

# =========================================================
# Shaped Pulses
# =========================================================

pulse_dir = os.path.join(mol_dir,"Shaped_pulse")

os.makedirs(pulse_dir)

print("\nCreating shaped pulse file ...")

