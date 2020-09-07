#!/usr/bin/env python3

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
    """Checks if a path towards a file or folder exists and make sure it's absolute

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
      raise ValueError ("The specified type for which check_path function has been called is not one of 'file', 'folder or 'either'")
    elif not os.path.exists(path):
      raise IOError ("%s does not seem to exist." % path)
    elif type == "file":
      if not os.path.isfile(path):
        raise ValueError ("%s is not a file" % path)
    elif type == "folder":
      if not os.path.isdir(path):
        raise ValueError ("%s is not a directory" % path)
    elif type =="either":
      if not os.path.isdir(path) and not os.path.isfile(path):
        raise ValueError ("%s is neither a file nor a directory" % path)
    
    abspath = os.path.abspath(path)

    return abspath

def jinja_render(path_tpl_dir, tpl, render_vars):
    """Renders a file based on its jinja template

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

section_title = "0. Preparation step"

print("")
print("")
print(''.center(len(section_title)+10, '*'))
print(section_title.center(len(section_title)+10))
print(''.center(len(section_title)+10, '*'))

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

config_file = check_abspath(config_file,"file")

print("\nLoading the main configuration file %s ..." % config_file, end="")
with open(config_file, 'r') as f_config:
  config = yaml.load(f_config, Loader=yaml.FullLoader)
print('%12s' % "[ DONE ]")

# Loading the clusters_file for the informations about the clusters

clusters_file = check_abspath(clusters_file,"file")

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

qoct_ra_dir = check_abspath(qoct_ra_dir,"folder")

print("\nQOCT-RA directory: ", qoct_ra_dir)

# Check if the path to the source file exists and make sure it's absolute.

source = check_abspath(source,"file")

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

if "qoct-ra" not in config:
  print("\nERROR: No information provided for qoct-ra in the YAML config file. Please add informations for qoct-ra before attempting to run this script.")
  print("Aborting...")
  exit(3)

if "qoct-ra" not in clusters_cfg[cluster_name]["progs"]:
  print("\nERROR: There is no information about qoct-ra on this cluster, please add informations to the YAML cluster file.")
  print("Aborting...")
  exit(3) 

# Gather all the different job scales from the clusters configuration file in a temporary dictionary

job_scales_tmp = clusters_cfg[cluster_name]['progs']['qoct-ra']['job_scales']

# Initialize the final dictionary where the job scales will be sorted by their upper limit

job_scales = {}

# Sort the different job scales by their upper limit and store them in the job_scales dictionary

for scale in job_scales_tmp:
  scale_limit = scale['scale_limit']
  del scale['scale_limit']
  job_scales[int(scale_limit)] = scale

print("\nJob scales for %s:" % cluster_name)
job_scales = OrderedDict(sorted(job_scales.items()))

print("")
print(''.center(95, '-'))
print ("{:<15} {:<20} {:<20} {:<20} {:<20}".format('scale_limit','Label','Partition_name','Time','Mem per CPU (MB)'))
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

print("\nSource file format: ", config['qoct-ra']['source_file_format'])

try:
  source_parser = importlib.import_module(config['qoct-ra']['source_file_format'] + "_parser")
except ModuleNotFoundError:
  print("Unable to find the %s.py file in %s" % (source_parser, code_dir))
  exit(1)
# For more informations on try/except structures, see https://www.tutorialsteacher.com/python/exception-handling-in-python

# =========================================================
# Reading the file
# =========================================================

print("\nScanning %s file ... " % source_filename, end="")
with open(source, 'r') as source_file:
  source_content = source_file.read().splitlines()
print('%20s' % "[ DONE ]")

# Cleaning up the source file from surrounding spaces and blank lines

source_content = list(map(str.strip, source_content))   # removes leading & trailing blank/spaces
source_content = list(filter(None, source_content))     # removes blank lines/no char

# =========================================================
# Get the list of states
# =========================================================

print("\nExtracting the list of states ...                   ", end="")
states_list = source_parser.get_states_list(source_content)
print('%20s' % "[ DONE ]")

#! The states_list variable is a list of lists of the form [[0, Multiplicity, Energy, Label], [1, Multiplicity, Energy, Label], [2, Multiplicity, Energy, Label], ...]
#! The first element of each sublist is the state number, starting at 0
#! Multipliciy corresponds to the first letter of the multiplicity of the state (ex : S for a singlet, T for a triplet)
#! Energy is the energy of the state, in cm-1
#! Label is the label of the state, in the form of multiplicity + number of that state of this multiplicity (ex : T1 for the first triplet, S3 for the third singlet)

# =========================================================
# Get the list of coupling values
# =========================================================

print("\nExtracting the list of states couplings ...         ", end="")
coupling_list = source_parser.get_coupling_list(source_content)
print('%20s' % "[ DONE ]")

#! The coupling_list variable is a list of tuples of the form [[State0, State1, Coupling0-1], [State0, State2, Coupling0-2], [State1, State2, Coupling1-2], ...]
#! The first two elements of each tuple are the number of the two states and the third one is the value of the coupling linking them (in cm-1)

# =========================================================
# Get the list of transition dipole moments
# =========================================================

print("\nExtracting the list of transition dipole moments ...", end="")
momdip_list = source_parser.get_momdip_list(source_content)
print('%20s' % "[ DONE ]")

#! The coupling_list variable is a list of tuples of the form [[State0, State1, MomDip0-1], [State0, State2, MomDip0-2], [State1, State2, MomDip1-2], ...]
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
  print("\n\nERROR: The number of states is too big for this cluster (%s). Please change cluster." % cluster_name)
  exit(4)

# Obtaining the informations associated to our job scale

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
  tpl = (state[0], state[0], state[2])
  # Reminder : state[0] is the state number and state[2] is the state energy
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

mime_file = config['qoct-ra']['created_files']['mime_file']
np.savetxt(os.path.join(mol_dir,mime_file),mime,fmt='% 18.10e')

# States List

basis_dir = os.path.join(mol_dir,"Basis")
os.makedirs(basis_dir)

states_file = config['qoct-ra']['created_files']['basis_folder']['states_file']

with open(os.path.join(basis_dir, states_file), "w") as f:
  for state in states_list:
    f.write("%d %s" % (state[0], state[1]))
  f.write("#comment")

#TODO : Save the whole states_list with np.savetxt ? Will it still works with QOCT-RA ?

# Energies

energies_dir = os.path.join(mol_dir,"Energies")
os.makedirs(energies_dir)

energies_file = config['qoct-ra']['created_files']['energies_folder']['energies_file']

np.savetxt(os.path.join(energies_dir,energies_file + '_cm-1'),eigenvalues,fmt='%1.10e')
np.savetxt(os.path.join(energies_dir,energies_file + '_ua'),eigenvalues_ua,fmt='%1.10e',footer='comment',comments='#')
np.savetxt(os.path.join(energies_dir,energies_file + '_nm'),eigenvalues_nm,fmt='%1.10e')
np.savetxt(os.path.join(energies_dir,energies_file + '_ev'),eigenvalues_ev,fmt='%1.10e')

# Eigenvectors matrix and eigenvectors transpose matrix

mat_dir = os.path.join(mol_dir,"Mat_cb")
os.makedirs(mat_dir)

mat_et0 = config['qoct-ra']['created_files']['mat_cb_folder']['eigen_to_zero']
np.savetxt(os.path.join(mat_dir,mat_et0),eigenvectors,fmt='% 18.10e')

mat_0te = config['qoct-ra']['created_files']['mat_cb_folder']['zero_to_eigen']
np.savetxt(os.path.join(mat_dir,mat_0te),transpose,fmt='% 18.10e')

# Dipole moments matrix

mom_dir = os.path.join(mol_dir,"MomDip")
os.makedirs(mom_dir)

momdip_0 = config['qoct-ra']['created_files']['momdip_folder']['momdip_zero']
np.savetxt(os.path.join(mom_dir,momdip_0),momdip_mtx,fmt='% 18.10e')

momdip_e = config['qoct-ra']['created_files']['momdip_folder']['momdip_eigen']
np.savetxt(os.path.join(mom_dir,momdip_e),momdip_es_mtx,fmt='% 18.10e')	

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

init_file = config['qoct-ra']['created_files']['md_folder']['initial'] + "_1"

with open(os.path.join(md_dir, init_file), "w") as f:
  for line in init_pop:
    for val in line:
      print('( {0.real:.2f} , {0.imag:.2f} )'.format(val), end = " ", file = f)
    print('', file = f)

print('%20s' % "[ DONE ]")

# Final population (dummy file but still needed by QOCT-RA)

print("\nCreating dummy final population file (copy of the initial population file) ...", end="") 

final_file = config['qoct-ra']['created_files']['md_folder']['final'] + "_1"
shutil.copy(os.path.join(md_dir,init_file), os.path.join(md_dir,final_file))

print('%20s' % "[ DONE ]")

# Projectors

print('')

for state in states_list:
  if state[1] == "T":
    print("Creating the projector file for state %s ..." % state[3], end="")
    proj = np.zeros((len(states_list),len(states_list)),dtype=complex)
    proj[state[0]-1,state[0]-1] = 1+0j
    proj_file = config['qoct-ra']['created_files']['md_folder']['projectors'] + state[3] + "_1"
    with open(os.path.join(md_dir, proj_file), "w") as f:
      for line in proj:
        for val in line:
          print('( {0.real:.2f} , {0.imag:.2f} )'.format(val), end = " ", file = f)
        print('', file = f)
    print('%20s' % "[ DONE ]")

# =========================================================
# Shaped Pulse
# =========================================================

pulse_dir = os.path.join(mol_dir,"Shaped_pulse")
os.makedirs(pulse_dir)

print("\nRendering the jinja template for the shaped pulse file ...", end="")

# Define the names of the template and rendered file, given in the main configuration YAML file.

tpl_pulse = config['qoct-ra']['jinja_templates']['shaped_pulse']                           # Jinja template file for the shaped pulse file
rnd_pulse = config['qoct-ra']['created_files']['shaped_pulse_folder']['pulse_file']        # Name of the rendered shaped pulse file

# Determine the central frequency of the pulse in cm-1 (here defined as the average of the eigenvalues)

central_frequency = np.mean(eigenvalues)

# Definition of the variables present in the jinja template

render_vars = {
  "basis" : config['qoct-ra']['created_files']['basis_folder']['states_file'],
  "shape" : config['qoct-ra']['pulse_parameters']['shape'],
  "nb_pixels" : config['qoct-ra']['pulse_parameters']['nb_pixels'],
  "energy" : config['qoct-ra']['pulse_parameters']['energy'],
  "fwhm" : config['qoct-ra']['pulse_parameters']['fwhm'],
  "frequency" : central_frequency
}

# Rendering the jinja template

pulse_content = jinja_render(os.path.join(code_dir,"Templates"), tpl_pulse, render_vars)

with open(os.path.join(pulse_dir, rnd_pulse), "w") as pulse_file:
  pulse_file.write(pulse_content)

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

# Define the names of the template and rendered file, given in the main configuration YAML file.

tpl_param = config['qoct-ra']['jinja_templates']['parameters_file']                           # Jinja template file for the parameters file
rnd_param = config['qoct-ra']['rendered_files']['parameters_file']                            # Name of the rendered parameters file

# Definition of the variables present in the jinja template

render_vars = {
  "mol_name" : mol_name,
  "basis" : config['qoct-ra']['created_files']['basis_folder']['states_file'],
  "energies_ua" : energies_file + '_ua',
  "momdip_e" : momdip_e,
  "initial" : init_file,
  "final" : final_file,
  "projector" : config['qoct-ra']['created_files']['md_folder']['projectors'],
  "nstep" : config['qoct-ra']['main_parameters']['nstep'],
  "dt" : config['qoct-ra']['main_parameters']['dt'],
  "niter" : config['qoct-ra']['main_parameters']['niter'],
  "threshold" : config['qoct-ra']['main_parameters']['threshold'],
  "alpha0" : config['qoct-ra']['main_parameters']['alpha0'],
  "pulse" : rnd_pulse,
  "mat_et0" : mat_et0
}

# For each projector, render the parameters file and run the corresponding job

print("\nRendering the jinja template for the param.dat file ...")

for state in states_list:
  if state[1] == "T":
    render_vars["target"] = state[3]
    param_content = jinja_render(os.path.join(code_dir,"Templates"), tpl_param, render_vars)
    with open(os.path.join(qoct_ra_dir, rnd_param), "w") as param_file:   #! join(qoct_ra_dir, "QOCTRA", rnd_param)   before modification
      param_file.write(param_content)
    #TODO: Run the job

