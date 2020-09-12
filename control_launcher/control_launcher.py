#!/usr/bin/env python3
# coding: utf8

########################################################################################################################################################
##                                                        QOCT-RA Input Builder & Job Launcher                                                        ##
##                                                                                                                                                    ##
##                                    This script prepares the input files needed to run the QOCT-RA program by extracting                            ##
##                                  information from a given source file and launches the corresponding jobs on the cluster.                          ##
##                                                                                                                                                    ##
## /!\ In order to run, this script requires Python 3.5+ as well as NumPy 1.14+, YAML and Jinja2. Ask your cluster(s) administrator(s) if needed. /!\ ##
########################################################################################################################################################

import argparse
import importlib
import os
import shutil
import sys
from collections import OrderedDict
from inspect import getsourcefile

import jinja2
import numpy as np
import yaml

# ===================================================================
# ===================================================================
# Function definitions
# ===================================================================
# ===================================================================

def check_abspath(path,type="either"):
    """Checks if a path towards a file or folder exists and makes sure it's absolute.

    Parameters
    ----------
    path : str
        The path towards the file or directory you want to test
    type : str (optional)
        The type of element for which you would like to test the path (file, folder or either)
        By default, checks if the path leads to either a file or a folder (type = either)
    
    Returns
    -------
    abspath : str
        Normalized absolutized version of the path
    """

    if type not in ["file","folder","either"]:
      # Not in try/except structure because the full error message will be need in this case
      raise ValueError ("The specified type for which the check_abspath function has been called is not one of 'file', 'folder or 'either'")

    # For more informations on try/except structures, see https://www.tutorialsteacher.com/python/exception-handling-in-python
    try:
      if not os.path.exists(path):
        raise IOError ("ERROR: The argument %s does not seem to exist." % path)
      elif type == "file":
        if not os.path.isfile(path):
          raise ValueError ("ERROR: The argument %s is not a file" % path)
      elif type == "folder":
        if not os.path.isdir(path):
          raise ValueError ("ERROR: The argument %s is not a directory" % path)
      elif type == "either":
        if not os.path.isdir(path) and not os.path.isfile(path):
          raise ValueError ("ERROR: The argument %s is neither a file nor a directory" % path)
    except Exception as error:
      print(error)
      exit(1)

    # If everything went well, get the normalized absolutized version of the path
    abspath = os.path.abspath(path)

    return abspath

def jinja_render(path_tpl_dir, tpl, render_vars):
    """Renders a file based on its jinja template.

    Parameters
    ----------
    path_tpl_dir : str
        The path towards the directory where the jinja template is located
    tpl : str
        The name of the jinja template file
    render_vars : dict
        Dictionary containing the definitions of all the variables present in the jinja template

    Returns
    -------
    output_text : str
        Content of the rendered file
    """
   
    environment = jinja2.Environment(loader=jinja2.FileSystemLoader(path_tpl_dir))
    output_text = environment.get_template(tpl).render(render_vars)
    
    return output_text

# ===================================================================
# ===================================================================
# Command line arguments
# ===================================================================
# ===================================================================

# Define the arguments needed for the script (here they are defined as named arguments rather than positional arguments, check https://stackoverflow.com/questions/24180527/argparse-required-arguments-listed-under-optional-arguments for more info).

parser = argparse.ArgumentParser(add_help=False, description="This script prepares the input files needed to run the QOCT-RA program by extracting information from a given source file and launches the corresponding jobs on the cluster.")

required = parser.add_argument_group('Required arguments')
required.add_argument("-i","--source", type=str, help="Path to the source file that contains all the necessary informations that need to be processed", required=True)
required.add_argument("-o","--out_dir", type=str, help="Path to the directory where you want to create the subdirectories for each job", required=True)
required.add_argument('-cfg', '--config', type=str, help="Path to the YAML config file", required=True)

optional = parser.add_argument_group('Optional arguments')
optional.add_argument('-h','--help',action='help',default=argparse.SUPPRESS,help='Show this help message and exit')
optional.add_argument("-ow","--overwrite",action="store_true",help="Overwrite files if they already exists")
optional.add_argument("-k","--keep",action="store_true",help="Do not archive the treated source file and leave it where it is")
optional.add_argument('-cl', '--clusters', type=str, help="Path to the YAML clusters file, default is abin_launcher/clusters.yml")

args = parser.parse_args()

# Define the variables corresponding to those arguments

source = args.source                     # Source file containing all the necessary informations
out_dir = args.out_dir                   # Folder where all jobs subfolders will be created
config_file = args.config                # Main configuration file

overwrite = args.overwrite               # Flag for overwriting the files
keep = args.keep                         # Flag for keeping the source file where it is
clusters_file = args.clusters            # YAML file containing all informations about the clusters

# Other important variable

prog = "qoct-ra"                         # Name of the blocks that appear in the clusters and config YAML files

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

section_title = "0. Preparation step"

print("")
print("")
print(''.center(len(section_title)+10, '*'))
print(section_title.center(len(section_title)+10))
print(''.center(len(section_title)+10, '*'))

# =========================================================
# Define the cluster
# =========================================================

cluster_name = os.environ['CLUSTER_NAME']
print("\nThis script is running on the %s cluster" % cluster_name.upper())

# =========================================================
# Define codes directory
# =========================================================

# Codes directory (determined by getting the path to the directory where this script is)
code_dir = os.path.dirname(os.path.realpath(os.path.abspath(getsourcefile(lambda:0))))
print ("{:<40} {:<100}".format('\nCodes directory:',code_dir))

# =========================================================
# Check arguments
# =========================================================

source = check_abspath(source,"file")
print ("{:<40} {:<100}".format('\nSource file:',source))

out_dir = check_abspath(out_dir,"folder")
print ("{:<40} {:<100}".format('\nJobs main directory:',out_dir))

config_file = check_abspath(config_file,"file")

if clusters_file: 
  clusters_file = check_abspath(clusters_file,"file")
else:
  # If no value has been provided through the command line, take the clusters.yml file in the abin_launcher directory of CHAINS
  chains_dir = os.path.dirname(code_dir) 
  clusters_file = os.path.join(chains_dir,"abin_launcher","clusters.yml")

# =========================================================
# Important files and folders
# =========================================================

# Get the name of the source file and the name of the folder where the source file is
source_path = os.path.dirname(source)
source_filename = os.path.basename(source)

# Check if a folder already exists for that molecule
mol_name = str(source_filename.split('.')[0]) # Getting rid of the format extension to get the name of the molecule
if os.path.exists(os.path.join(out_dir,mol_name)) and not overwrite:
  print("\n\nERROR: A folder for the %s molecule already exists in %s !" % (mol_name, out_dir))
  print("Aborting ...")
  exit(4)

# =========================================================
# Load YAML files
# =========================================================

# Loading the config_file for the information about the molecule

print ("{:<40} {:<100}".format('\nLoading the main configuration file',config_file + " ..."), end="")
#print("\nLoading the main configuration file  %s ..." % config_file, end="")
with open(config_file, 'r') as f_config:
  config = yaml.load(f_config, Loader=yaml.FullLoader)
print('%12s' % "[ DONE ]")

# Loading the clusters_file for the information about the clusters

print ("{:<40} {:<100}".format('\nLoading the clusters file',clusters_file + " ..."), end="")
#print("\nLoading the clusters file            %s ..." % clusters_file, end="")
with open(clusters_file, 'r') as f_clusters:
  clusters_cfg = yaml.load(f_clusters, Loader=yaml.FullLoader)
print('%12s' % "[ DONE ]")

# =========================================================
# Establishing the different job scales
# =========================================================

# Check if the relevant informations about QOCT-RA have been provided in the YAML config and clusters files

if prog not in config:
  print("\nERROR: No information provided for %s in the YAML config file. Please add informations for %s before attempting to run this script." % (prog,prog))
  print("Aborting...")
  exit(3)

if prog not in clusters_cfg[cluster_name]["progs"]:
  print("\nERROR: There is no information about %s on this cluster, please add informations to the YAML cluster file." % prog)
  print("Aborting...")
  exit(3) 

# Gather all the different job scales from the clusters configuration file in a temporary dictionary

job_scales_tmp = clusters_cfg[cluster_name]['progs'][prog]['job_scales']

# Initialize the final dictionary where the job scales will be sorted by their upper limit

job_scales = {}

# Sort the different job scales by their upper limit and store them in the job_scales dictionary

for scale in job_scales_tmp:
  scale_limit = scale['scale_limit']
  del scale['scale_limit']
  job_scales[int(scale_limit)] = scale

print("\nJob scales for %s on %s:" % (prog,cluster_name.upper()))
job_scales = OrderedDict(sorted(job_scales.items()))

print("")
print(''.center(95, '-'))
print ("{:<15} {:<20} {:<20} {:<20} {:<20}".format('Scale Limit','Label','Partition Name','Time','Mem per CPU (MB)'))
print(''.center(95, '-'))
for scale_limit, scale in job_scales.items():
  print ("{:<15} {:<20} {:<20} {:<20} {:<20}".format(scale_limit, scale['label'], scale['partition_name'], scale['time'], scale['mem_per_cpu']))
print(''.center(95, '-'))

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

# Define and import the parser module that will be used to parse the source file

parser_file = config[prog]['parser_script']
print("\nParser script file: ", parser_file)

try:
  # The source_parser must be named as the "parser_script" provided in the config YAML file + ".py"
  source_parser = importlib.import_module(parser_file)
except ModuleNotFoundError:
  print("ERROR: Unable to find the %s.py file in %s" % (parser_file, code_dir))
  exit(1)
# For more informations on try/except structures, see https://www.tutorialsteacher.com/python/exception-handling-in-python

# =========================================================
# Reading the file
# =========================================================

print ("{:<60}".format('\nScanning %s file ... ' % source_filename), end="")
with open(source, 'r') as source_file:
  source_content = source_file.read().splitlines()
print('%12s' % "[ DONE ]")

# Cleaning up the source file from surrounding spaces and blank lines

source_content = list(map(str.strip, source_content))   # removes leading & trailing blank/spaces
source_content = list(filter(None, source_content))     # removes blank lines/no char

# =========================================================
# Get the list of states
# =========================================================

print ("{:<60}".format('\nExtracting the list of states ... '), end="")
states_list = source_parser.get_states_list(source_content)
print('%12s' % "[ DONE ]")

#! The states_list variable is a list of tuples of the form [[0, Multiplicity, Energy, Label], [1, Multiplicity, Energy, Label], [2, Multiplicity, Energy, Label], ...]
#! The first element of each tuple is the state number, starting at 0
#! Multipliciy corresponds to the multiplicity of the state
#! Energy is the energy of the state, in cm-1
#! Label is the label of the state, in the form of first letter of multiplicity + number of that state of this multiplicity (ex: T1 for the first triplet, S3 for the third singlet)

print("")
print(''.center(50, '-'))
print('States List'.center(50, ' '))
print(''.center(50, '-'))
print("{:<10} {:<15} {:<15} {:<10}".format('Number','Multiplicity','Energy (cm-1)','Label'))
print(''.center(50, '-'))
for state in states_list:
  print("{:<10} {:<15} {:<15.3f} {:<10}".format(state[0],state[1],state[2],state[3]))
print(''.center(50, '-'))

# =========================================================
# Get the list of coupling values
# =========================================================

print ("{:<60}".format('\nExtracting the list of states couplings ... '), end="")
coupling_list = source_parser.get_coupling_list(source_content)
print('%12s' % "[ DONE ]")

#! The coupling_list variable is a list of tuples of the form [[State0, State1, Coupling0-1], [State0, State2, Coupling0-2], [State1, State2, Coupling1-2], ...]
#! The first two elements of each tuple are the number of the two states and the third one is the value of the coupling linking them (in cm-1)

# =========================================================
# Get the list of transition dipole moments
# =========================================================

print ("{:<60}".format('\nExtracting the list of transition dipole moments ... '), end="")
momdip_list = source_parser.get_momdip_list(source_content)
print('%12s' % "[ DONE ]")

#! The momdip_list variable is a list of tuples of the form [[State0, State1, MomDip0-1], [State0, State2, MomDip0-2], [State1, State2, MomDip1-2], ...]
#! The first two elements of each tuple are the number of the two states and the third one is the value of the transition dipole moment associated with the transition between them (in atomic units)

print("\nThe source file has been succesfully parsed.")

# ===================================================================
# ===================================================================
#                     CALCULATION REQUIREMENTS
# ===================================================================
# ===================================================================

section_title = "2. Calculation requirements"

print("")
print("")
print(''.center(len(section_title)+10, '*'))
print(section_title.center(len(section_title)+10))
print(''.center(len(section_title)+10, '*'))

# Use the number of states to determine the job scale

scale_index = len(states_list)

# Job scale category definition

jobscale = None

for scale_limit in job_scales:
  if scale_index > scale_limit:
    continue
  else:
    jobscale = job_scales[scale_limit]
    jobscale_limit = scale_limit
    break

if not jobscale:
  print("\n\nERROR: The number of states is too big for this cluster (%s). Please change cluster." % cluster_name.upper())
  exit(4)

# Obtaining the information associated to our job scale

job_partition = jobscale['partition_name']
job_walltime = jobscale['time']
job_mem_per_cpu = jobscale['mem_per_cpu']

print("")
print(''.center(50, '-'))
print("{:<20} {:<30}".format("Number of states: ", scale_index))
print(''.center(50, '-'))
print("{:<20} {:<30}".format("Cluster: ", cluster_name))
print("{:<20} {:<30}".format("Job scale: ", jobscale["label"]))
print("{:<20} {:<30}".format("Job scale limit: ", jobscale_limit))
print(''.center(50, '-'))
print("{:<20} {:<30}".format("Job partition: ", job_partition))
print("{:<20} {:<30}".format("Job walltime: ", job_walltime))
print("{:<20} {:<30}".format("Mem per CPU (MB): ", job_mem_per_cpu))
print(''.center(50, '-'))

# ===================================================================
# ===================================================================
#                       MIME DIAGONALIZATION
# ===================================================================
# ===================================================================

section_title = "3. MIME diagonalization"

print("")
print("")
print(''.center(len(section_title)+10, '*'))
print(section_title.center(len(section_title)+10))
print(''.center(len(section_title)+10, '*'))

# =========================================================
# Creation of the MIME containing the coupling elements
# =========================================================

print("\nBuilding the MIME ...     ", end="")   

mime = np.zeros((len(states_list), len(states_list)))  # Quick init of a zero-filled matrix

# Add energies (in cm-1) to the tuple list (those will be placed on the diagonal of the MIME)
for state in states_list:
  # Reminder : state[0] is the state number and state[2] is the state energy
  tpl = (state[0], state[0], state[2])
  coupling_list.append(tpl)

# Creation of the MIME
for coupling in coupling_list:
  k1 = coupling[0]
  k2 = coupling[1]
  val = coupling[2]
  mime[k1][k2] = val
  mime[k2][k1] = val    # For symetry purposes

print('%20s' % "[ DONE ]")

print("\nMIME (cm-1)")
print('')
for row in mime:
  for val in row:
    print(np.format_float_scientific(val,precision=5,unique=False,pad_left=2), end = " ")
  print('')

# =========================================================
# MIME diagonalization
# =========================================================

print("\nDiagonalizing the MIME ...", end="")
# Using NumPy to diagonalize the matrix (see https://numpy.org/doc/stable/reference/generated/numpy.linalg.eig.html for reference)   
diag_mime = np.linalg.eig(mime)
print('%20s' % "[ DONE ]")

# =========================================================
# Eigenvalues
# =========================================================

eigenvalues = diag_mime[0]

# Converting the eigenvalues from cm-1 to ua, nm and eV
eigenvalues_ua = eigenvalues / 219474.6313705
eigenvalues_nm = 10000000 / eigenvalues
eigenvalues_ev = eigenvalues / 8065.6

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

eigenvectors = diag_mime[1]

print("\nEigenvectors matrix")
print('')
for vector in eigenvectors:
  for val in vector:
    print(np.format_float_scientific(val,precision=5,unique=False,pad_left=2), end = " ")
  print('')

# =========================================================
# Eigenvectors transpose matrix
# =========================================================

# Using NumPy to transpose the eigenvectors matrix (see https://numpy.org/doc/stable/reference/generated/numpy.transpose.html for reference)
transpose = np.transpose(eigenvectors)

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

section_title = "4. Dipole moments matrix"

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
  momdip_mtx[k2][k1] = val    # For symetry purposes

print("\nDipole moments matrix in the zero order basis set (ua)")
print('')
for row in momdip_mtx:
  for val in row:
    print(np.format_float_scientific(val,precision=5,unique=False,pad_left=2), end = " ")
  print('')

# =========================================================
# Conversion in the eigenstates basis set
# =========================================================

momdip_es_mtx = np.dot(transpose,momdip_mtx) #! TODO: check if it's correct

for row in range(len(momdip_es_mtx)):
  for val in range(row):
    momdip_es_mtx[val,row] = momdip_es_mtx[row,val] #!: Why?
		
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

section_title = "5. Data files creation"

print("")
print("")
print(''.center(len(section_title)+10, '*'))
print(section_title.center(len(section_title)+10))
print(''.center(len(section_title)+10, '*'))

# =========================================================
# Creating the molecule folder and the data subfolder
# =========================================================

mol_dir = os.path.join(out_dir,mol_name)

if os.path.exists(mol_dir): # Overwrite was already checked previously, no need to check it again
  shutil.rmtree(mol_dir)

os.makedirs(mol_dir)

# Creating the data subfolder where all the files describing the molecule will be stored
data_dir = os.path.join(mol_dir,"data")
os.makedirs(data_dir)

print("\nThe data subfolder has been created at %s" % data_dir)

# =========================================================
# Writing already calculated values to files
# =========================================================

# MIME

mime_file = config[prog]['created_files']['mime_file']
print("{:<60}".format('\nCreating %s file ... ' % mime_file), end="")
np.savetxt(os.path.join(data_dir,mime_file),mime,fmt='% 18.10e')
print('%12s' % "[ DONE ]")

# States List (not neeeded for QOCT-RA but useful to know) in CSV format

states_file = config[prog]['created_files']['states_file']
print("{:<60}".format('\nCreating %s file ... ' % states_file), end="")
with open(os.path.join(data_dir, states_file), "w") as f:
  print("Number;Multiplicity;Energy (cm-1);Label", file = f)
  for state in states_list:
    # Print every item in state, separated by ";"
    print(";".join(map(str,state)), file = f)
print('%12s' % "[ DONE ]")

# Energies

energies_file = config[prog]['created_files']['energies_file']
print("{:<60}".format('\nCreating %s file ... ' % energies_file), end="")
np.savetxt(os.path.join(data_dir,energies_file + '_cm-1'),eigenvalues,fmt='%1.10e')
#np.savetxt(os.path.join(data_dir,energies_file + '_ua'),eigenvalues_ua,fmt='%1.10e',footer='comment',comments='#')
np.savetxt(os.path.join(data_dir,energies_file + '_ua'),eigenvalues_ua,fmt='%1.10e')
np.savetxt(os.path.join(data_dir,energies_file + '_nm'),eigenvalues_nm,fmt='%1.10e')
np.savetxt(os.path.join(data_dir,energies_file + '_ev'),eigenvalues_ev,fmt='%1.10e')
print('%12s' % "[ DONE ]")

# Eigenvectors matrix and eigenvectors transpose matrix

mat_et0 = config[prog]['created_files']['mat_et0']
print("{:<60}".format('\nCreating %s file ... ' % mat_et0), end="")
np.savetxt(os.path.join(data_dir,mat_et0),eigenvectors,fmt='% 18.10e')
print('%12s' % "[ DONE ]")

mat_0te = config[prog]['created_files']['mat_0te']
print ("{:<60}".format('\nCreating %s file ... ' % mat_0te), end="")
np.savetxt(os.path.join(data_dir,mat_0te),transpose,fmt='% 18.10e')
print('%12s' % "[ DONE ]")

# Dipole moments matrix

momdip_0 = config[prog]['created_files']['momdip_zero']
print("{:<60}".format('\nCreating %s file ... ' % momdip_0), end="")
np.savetxt(os.path.join(data_dir,momdip_0),momdip_mtx,fmt='% 18.10e')
print('%12s' % "[ DONE ]")

momdip_e = config[prog]['created_files']['momdip_eigen']
print("{:<60}".format('\nCreating %s file ... ' % momdip_e), end="")
np.savetxt(os.path.join(data_dir,momdip_e),momdip_es_mtx,fmt='% 18.10e')	
print('%12s' % "[ DONE ]")

# =========================================================
# Density matrices
# =========================================================

# Initial population

init_file = config[prog]['created_files']['init_pop']
print("{:<60}".format("\nCreating %s file ..." % init_file), end="") 

init_pop = np.zeros((len(states_list), len(states_list)),dtype=complex)  # Quick init of a zero-filled matrix
init_pop[0,0] = 1+0j # All the population is in the ground state at the beginning

with open(os.path.join(data_dir, init_file + "_1"), "w") as f:
  for line in init_pop:
    for val in line:
      print('( {0.real:.2f} , {0.imag:.2f} )'.format(val), end = " ", file = f)
    print('', file = f)

print('%12s' % "[ DONE ]")

# Final population (dummy file but still needed by QOCT-RA)

final_file = config[prog]['created_files']['final_pop']
print("{:<60}".format("\nCreating %s file ..." % final_file), end="") 

final_pop = np.zeros((len(states_list), len(states_list)),dtype=complex)  # Quick init of a zero-filled matrix
final_pop[0,0] = 0+0j # Unrealistic population

with open(os.path.join(data_dir, final_file + "_1"), "w") as f:
  for line in final_pop:
    for val in line:
      print('( {0.real:.2f} , {0.imag:.2f} )'.format(val), end = " ", file = f)
    print('', file = f)

print('%12s' % "[ DONE ]")

# Projectors

print('')
proj_file = config[prog]['created_files']['projectors']
target_state = config[prog]['target_state'] # The type of states that will be targeted by the control

for state in states_list:
  if state[1] == target_state:
    print("{:<59}".format("Creating %s file ..." % (proj_file + state[3])), end="")
    proj = np.zeros((len(states_list),len(states_list)),dtype=complex)
    proj[state[0],state[0]] = 1+0j
    with open(os.path.join(data_dir, proj_file + state[3] + "_1"), "w") as f:
      for line in proj:
        for val in line:
          print('( {0.real:.2f} , {0.imag:.2f} )'.format(val), end = " ", file = f)
        print('', file = f)
    print('%12s' % "[ DONE ]")

# ===================================================================
# ===================================================================
#         RENDERING OF THE PARAMETERS FILE AND JOBS LAUNCHING
# ===================================================================
# ===================================================================

section_title = "6. Rendering of the parameters file and jobs launching"

print("")
print("")
print(''.center(len(section_title)+10, '*'))
print(section_title.center(len(section_title)+10))
print(''.center(len(section_title)+10, '*'))

# =========================================================
# Defining the jinja templates
# =========================================================

print("{:<81}".format("\nDefining and preparing the jinja templates ..."), end="") 

# Define the names of the template and rendered files, given in the YAML files.

tpl_param = config[prog]['jinja_templates']['parameters_file']                           # Jinja template file for the parameters file

tpl_manifest = clusters_cfg[cluster_name]['progs'][prog]['manifest_template']            # Jinja template file for the job manifest (job submitting script)
rnd_manifest = clusters_cfg[cluster_name]['progs'][prog]['manifest_render']              # Name of the rendered job manifest file

# Determine the central frequency of the guess pulse in cm-1 (here defined as the average of the eigenvalues)

central_frequency = np.mean(eigenvalues)

# Define here the number of iterations for QOCT-RA, as it will be used multiple times later on

niter = config[prog]['param_nml']['control']['niter']

# Definition of the variables present in the jinja template for the parameters file (except the target state)

param_render_vars = {
  "mol_name" : mol_name,
  "energies_file_path" : os.path.join(data_dir,energies_file + '_ua'),
  "momdip_e_path" : os.path.join(data_dir,momdip_e),
  "init_file_path" : os.path.join(data_dir,init_file),
  "final_file_path" : os.path.join(data_dir,final_file),
  "proj_file_path" : os.path.join(data_dir,proj_file),
  "nstep" : config[prog]['param_nml']['control']['nstep'],
  "dt" : config[prog]['param_nml']['control']['dt'],
  "niter" : niter,
  "threshold" : config[prog]['param_nml']['control']['threshold'],
  "alpha0" : config[prog]['param_nml']['control']['alpha0'],
  "ndump" : config[prog]['param_nml']['control']['ndump'],
  "ndump2" : config[prog]['param_nml']['post-control']['ndump2'],
  "mat_et0_path" : os.path.join(data_dir,mat_et0),
  "numericincrements" : config[prog]['param_nml']['guess_pulse']['numericincrements'],
  "numberofpixels" : config[prog]['param_nml']['guess_pulse']['numberofpixels'],
  "inputenergy" : config[prog]['param_nml']['guess_pulse']['inputenergy'],
  "widthhalfmax" : config[prog]['param_nml']['guess_pulse']['widthhalfmax'],
  "omegazero" : central_frequency
}

# Definition of the variables present in the jinja template for the job manifest (except the target state and the name of the rendered parameters file)

manifest_render_vars = {
  "mol_name" : mol_name,
  "user_email" : config['general']['user-email'],
  "mail_type" : config['general']['mail-type'],
  "job_walltime" : job_walltime,
  "job_mem_per_cpu" : job_mem_per_cpu, # in MB
  "partition" : job_partition,     
  "set_env" : clusters_cfg[cluster_name]['progs'][prog]['set_env'],       
  "command" : clusters_cfg[cluster_name]['progs'][prog]['command'],
  "output_folder" : config[prog]['output-folder'],
  "results_folder" : config['general']['results-folder'],
  "data_dir" : data_dir,
  "job_manifest" : rnd_manifest,
  "niter" : niter
}

print('%12s' % "[ DONE ]")

# =========================================================
# Rendering the templates and launching the jobs
# =========================================================

# For each projector, render the parameters file and run the corresponding job

for state in states_list:
  if state[1] == target_state:
    target = state[3]
    print("\nPreparing to launch job with %s as the target state ..." % target)

    # Create the job folder for that specific target
    job_dirname = proj_file + target
    job_dir = os.path.join(mol_dir,job_dirname)
    os.makedirs(job_dir)
    print("    The %s job folder has been created in %s" % (job_dirname,mol_dir))

    # Create the OPM parameters file for that specific target
    rnd_param = "param" + "_" + target + ".nml"                                                              # Name of the rendered parameters file
    print("{:<80}".format("    Rendering the jinja template to create the %s file ..." % rnd_param), end ="")
    param_render_vars["target"] = target
    param_render_vars["processus"] = "OPM"
    param_render_vars["source"] = " "
    param_content = jinja_render(os.path.join(code_dir,"Templates"), tpl_param, param_render_vars)           # Render the jinja template of the parameters file
    with open(os.path.join(job_dir, rnd_param), "w", encoding='utf-8') as param_file:
      param_file.write(param_content)
    print('%12s' % "[ DONE ]")

    # Create the PCP parameters file for that specific target
    rnd_param_PCP = "param" + "_" + target + "_PCP.nml"                                                      # Name of the rendered parameters file
    print("{:<80}".format("    Rendering the jinja template to create the %s file ..." % rnd_param_PCP), end ="")
    param_render_vars["processus"] = "PCP"
    param_render_vars["source"] = "../Pulse/Pulse_iter" + str(niter)
    param_content = jinja_render(os.path.join(code_dir,"Templates"), tpl_param, param_render_vars)           # Render the jinja template of the parameters file
    with open(os.path.join(job_dir, rnd_param_PCP), "w", encoding='utf-8') as param_file:
      param_file.write(param_content)
    print('%12s' % "[ DONE ]")

    # Create the job manifest for that specific target
    print("{:<80}".format("    Rendering the jinja template to create the %s file ..." % rnd_manifest), end ="")
    manifest_render_vars["target"] = target
    manifest_render_vars["rnd_param"] = rnd_param
    manifest_render_vars["rnd_param_PCP"] = rnd_param_PCP
    manifest_render_vars["job_dirname"] = job_dirname
    manifest_content = jinja_render(os.path.join(code_dir,"Templates"), tpl_manifest, manifest_render_vars)  # Render the jinja template of the job manifest
    with open(os.path.join(job_dir, rnd_manifest), "w", encoding='utf-8') as manifest_file:
      manifest_file.write(manifest_content)
    print('%12s' % "[ DONE ]")
    
    # Launch the job
    print("{:<80}".format("    Launching the job ..."), end="")
    os.chdir(job_dir)
    launch_command = clusters_cfg[cluster_name]['subcommand'] + " " + rnd_manifest
    retcode = os.system(launch_command)
    if retcode != 0 :
      print("ALERT: Job submit encountered an issue")
      print("Aborting ...")
      exit(1)
    print('%12s' % "[ DONE ]")
    
# Archive the source file in launched_dir if keep has not been set
    
if not keep:
  launched_dir = os.path.join(source_path,"Launched")                             # Folder where the source file will be put after having been treated by this script, path is relative to the directory of the source file.
  os.makedirs(launched_dir, exist_ok=True)
  if os.path.exists(os.path.join(launched_dir,source_filename)):
    os.remove(os.path.join(launched_dir,source_filename))
  shutil.move(os.path.join(source_path,source_filename), launched_dir)
  print("\nOriginal source file archived to %s" % launched_dir)

print("")
print("".center(columns,"*"))
print("")
print("END OF EXECUTION".center(columns))
print("")
print("".center(columns,"*"))