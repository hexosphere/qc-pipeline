#!/usr/bin/env python3

################################################################################################################################################
##                                                             Results Treatment                                                              ##
##                                                                                                                                            ##
##                               This script scans one or more molecule folders containing all the information                                ##
##                    obtained through CHAINS, ORCA, QCHEM and QOCT-RA and generates the corresponding tables and graphs.                     ##
##                                                                                                                                            ##
##   /!\ In order to run, this script requires Python 3.5+ as well as YAML and Jinja2. Ask your cluster(s) administrator(s) if needed. /!\    ##
################################################################################################################################################

import argparse
import fnmatch
import os
import re
import shutil
import sys
from collections import OrderedDict
from inspect import getsourcefile

import jinja2  # Only needed in the renderer subscript, it is loaded here to check if your python installation does support jinja2
import yaml

import errors

# ===================================================================
# ===================================================================
# Command line arguments
# ===================================================================
# ===================================================================

# Define the arguments needed for the script (here they are defined as named arguments rather than positional arguments, check https://stackoverflow.com/questions/24180527/argparse-required-arguments-listed-under-optional-arguments for more info).

parser = argparse.ArgumentParser(add_help=False, description="For one or more molecule folders, this script reads the results files and generates the corresponding tables and graphs.")

required = parser.add_argument_group('Required arguments')
required.add_argument("-o","--out_dir", type=str, help="Path to the directory where you want to store the graphs and tables.", required=True)

mol_inp = parser.add_mutually_exclusive_group(required=True)
mol_inp.add_argument("-s","--single", type=str, help="Molecule folder containing the results files that need to be processed.")
mol_inp.add_argument("-m","--multiple", type=str, help="Folder containing multiple molecule folders.")

optional = parser.add_argument_group('Optional arguments')
optional.add_argument('-h','--help',action='help',default=argparse.SUPPRESS,help='Show this help message and exit')
optional.add_argument("-ow","--overwrite",action="store_true",help="Overwrite files if they already exists")

args = parser.parse_args()

# Define the variables corresponding to those arguments

out_dir = args.out_dir                   # Folder where all jobs subfolders will be created

single_mol = args.single                 # Molecule folder containing the results files that need to be processed.
multiple_mol = args.multiple             # Folder containing multiple molecule folders.

overwrite = args.overwrite               # Flag for overwriting the files

# ===================================================================
# ===================================================================
#                           PREPARATION STEP
# ===================================================================
# ===================================================================

# Save a reference to the original standard output as it will be modified later on (see https://stackabuse.com/writing-to-a-file-with-pythons-print-function/ for reference)

original_stdout = sys.stdout

# Get the size of the terminal in order to have a prettier output, if you need something more robust, go check http://granitosaurus.rocks/getting-terminal-size.html

columns, rows = shutil.get_terminal_size()

# Output Header

print("".center(columns,"*"))
print("")
print("EXECUTION OF THE RESULTS TREATMENT BEGINS NOW".center(columns))
print("")
print("".center(columns,"*"))

# =========================================================
# Define codes directory
# =========================================================

# Codes directory (determined by getting the path to the directory where this script is)
code_dir = os.path.dirname(os.path.realpath(os.path.abspath(getsourcefile(lambda:0))))
print ("{:<40} {:<100}".format('\nCodes directory:',code_dir))

# =========================================================
# Check molecule folder(s)
# =========================================================

if multiple_mol:
  multiple_mol = errors.check_abspath(multiple_mol,"folder")
  mol_inp_path = multiple_mol
  # We need to look for folder in the multiple_mol folder (see https://stackoverflow.com/questions/800197/how-to-get-all-of-the-immediate-subdirectories-in-python for reference).
  print("{:<40} {:<100}".format("\nLooking for every molecule folder in", mol_inp_path + " ..."), end="")
  mol_inp_list = [folder.name for folder in os.scandir(mol_inp_path) if folder.is_dir()]
  if mol_inp_list == []:
    print("\nERROR: Can't find any folder in %s" % mol_inp_path)
    exit(1)
  print('%12s' % "[ DONE ]")

else:
  single_mol = errors.check_abspath(single_mol,"folder")
  print ("{:<40} {:<100}".format('\nMolecule folder:',single_mol))
  mol_inp_path = os.path.dirname(single_mol)
  mol_inp_folder = os.path.basename(single_mol)
  mol_inp_list = [mol_inp_folder]
 
# =========================================================
# Check other arguments
# =========================================================

out_dir = errors.check_abspath(out_dir,"folder")
print ("{:<40} {:<100}".format('\nFigures main directory:',out_dir))

# =========================================================
# Check jinja templates
# =========================================================

# Get the path to jinja templates folder (a folder named "Templates" in the same folder as this script)
path_tpl_dir = os.path.join(code_dir,"Templates")

#TODO

# =========================================================
# Check gnuplot scripts
# =========================================================

#TODO

# ===================================================================
# ===================================================================
#                   FILES MANIPULATION & GENERATION
# ===================================================================
# ===================================================================

for mol_inp_folder in mol_inp_list:

  # For more informations on try/except structures, see https://www.tutorialsteacher.com/python/exception-handling-in-python
  try:
    
    mol_name = mol_inp_folder

    console_message = "Start procedure for the molecule " + mol_name
    print("")
    print(''.center(len(console_message)+11, '*'))
    print(console_message.center(len(console_message)+10))
    print(''.center(len(console_message)+11, '*'))

    # =========================================================
    # Create log file
    # =========================================================

    # Create a output log file containing all the information about the molecule results treatment
    mol_log_name = mol_name + ".log"
    mol_log = open(os.path.join(out_dir,mol_log_name), 'w', encoding='utf-8')

    # Redirect standard output to the mol_log file (see https://stackabuse.com/writing-to-a-file-with-pythons-print-function/ for reference)
    sys.stdout = mol_log

    # =========================================================
    # Load config file
    # =========================================================

    config_file = os.path.join(mol_inp_path,mol_inp_folder,mol_name + ".yml")
    config_file = errors.check_abspath(config_file,"file")
    print ("{:<40} {:<100}".format('\nLoading the configuration file',config_file + " ..."), end="")
    with open(config_file, 'r') as f_config:
      config = yaml.load(f_config, Loader=yaml.FullLoader)
    print('%12s' % "[ DONE ]")

    #TODO: Check arborescence

  except errors.ResultsError as error:
    sys.stdout = original_stdout                       # Reset the standard output to its original value
    print(error)
    print("Skipping %s molecule" % mol_name)
    os.remove(os.path.join(out_dir,mol_log_name))      # Remove the log file since there was a problem
    continue