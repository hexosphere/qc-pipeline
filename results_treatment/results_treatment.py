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
import csv
import fnmatch
import os
import re
import shutil
import sys
from inspect import getsourcefile

import jinja2  # Only needed in the renderer subscript, it is loaded here to check if your python installation does support jinja2
import yaml

import errors

# ===================================================================
# ===================================================================
# Function definitions
# ===================================================================
# ===================================================================

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

def import_path(fullpath:str):
    """ 
    Imports a file with full path specification. Allows one to import from anywhere, something __import__ does not do. Taken from https://stackoverflow.com/questions/72852/how-to-do-relative-imports-in-python

    Parameters
    ----------
    fullpath : str
        Full path towards the file you want to import

    Returns
    -------
    module
        The loaded file
    """

    # Split the path and filename (and remove extension of the filename)
    path, filename = os.path.split(fullpath)
    filename = os.path.splitext(filename)[0]

    # Add path to sys.path in order to be able to load the module, then remove it
    sys.path.insert(0, path)
    module = __import__(filename)
    del sys.path[0]

    return module

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
  multiple_mol = errors.check_abspath(multiple_mol,"Command line argument -m / --multiple","folder")
  mol_inp_path = multiple_mol
  # We need to look for folder in the multiple_mol folder (see https://stackoverflow.com/questions/800197/how-to-get-all-of-the-immediate-subdirectories-in-python for reference).
  print("{:<40} {:<100}".format("\nLooking for every molecule folder in", mol_inp_path + " ..."), end="")
  mol_inp_list = [dir.name for dir in os.scandir(mol_inp_path) if dir.is_dir()]
  if mol_inp_list == []:
    print("\nERROR: Can't find any folder in %s" % mol_inp_path)
    exit(1)
  print('%12s' % "[ DONE ]")

else:
  single_mol = errors.check_abspath(single_mol,"Command line argument -s / --single","folder")
  print ("{:<40} {:<100}".format('\nMolecule folder:',single_mol))
  mol_inp_path = os.path.dirname(single_mol)
  mol_name = os.path.basename(single_mol)
  mol_inp_list = [mol_name]
 
# =========================================================
# Check other arguments
# =========================================================

out_dir = errors.check_abspath(out_dir,"Command line argument -o / --out_dir","folder")
print ("{:<40} {:<100}".format('\nFigures directory:',out_dir))

# =========================================================
# Check jinja templates
# =========================================================

# Get the path to jinja templates folder (a folder named "Templates" in the same folder as this script)
path_tpl_dir = os.path.join(code_dir,"Templates")

# Define the names of the jinja templates

jinja_tpl = {
"states_list_tpl" : "states_list.tek.jinja"
}

# Check if all the files specified in the jinja_tpl dictionary exists in the Templates folder of results_treatment.

for filename in jinja_tpl.values():
  errors.check_abspath(os.path.join(path_tpl_dir,filename),"file")

# =========================================================
# Check gnuplot scripts
# =========================================================

#TODO

# ===================================================================
# ===================================================================
#                   FILES MANIPULATION & GENERATION
# ===================================================================
# ===================================================================

for mol_name in mol_inp_list:

  # For more informations on try/except structures, see https://www.tutorialsteacher.com/python/exception-handling-in-python
  try:
    
    mol_dir = os.path.join(mol_inp_path, mol_name)

    console_message = "Start procedure for the molecule " + mol_name
    print("")
    print(''.center(len(console_message)+11, '*'))
    print(console_message.center(len(console_message)+10))
    print(''.center(len(console_message)+11, '*'))

    # =========================================================
    # Load config file
    # =========================================================

    config_file = os.path.join(mol_dir, mol_name + ".yml")
    config_file = errors.check_abspath(config_file,"file")
    print ("{:<40} {:<100}".format('\nLoading the configuration file',config_file + " ..."), end="")
    with open(config_file, 'r') as f_config:
      config = yaml.load(f_config, Loader=yaml.FullLoader)
    print('%12s' % "[ DONE ]")

    # =========================================================
    # Check if all the necessary files are present
    # =========================================================

    # Optimized geometry

    orca_dir = os.path.join(mol_dir, config['results']['orca']['folder_name'])
    opt_geom_file = errors.check_abspath(os.path.join(orca_dir, mol_name + ".xyz"),"Optimized geometry file","file",False)

    # Data extracted from the qchem output by control_launcher and the diagonalization of the MIME

    qoctra_dir = os.path.join(mol_dir, config['results']['qoctra']['folder_name'])
    data_dir = errors.check_abspath(os.path.join(qoctra_dir, "data"),"Data folder created by control_launcher.py","folder",False)

    states_file = config['qoctra']['created_files']['states_file']
    states_file = errors.check_abspath(os.path.join(data_dir, states_file),"List of excited states","file",False)

    mime_file = config['qoctra']['created_files']['mime_file']
    mime_file = errors.check_abspath(os.path.join(data_dir, mime_file),"MIME file","file",False)

    momdip_0 = config['qoctra']['created_files']['momdip_zero']
    momdip_0 = errors.check_abspath(os.path.join(data_dir, momdip_0),"Transition dipole moments matrix (in atomic units)","file",False)

    mat_et0 = config['qoctra']['created_files']['mat_et0']
    mat_et0 = errors.check_abspath(os.path.join(data_dir, mat_et0),"Eigenvectors matrix (mat_et0)","file",False)

    energies_file = config['qoctra']['created_files']['energies_file']
    energies_file = errors.check_abspath(os.path.join(data_dir, energies_file + "_cm-1"),"List of eigenstates energies in cm-1 (eigenvalues from the diagonalization of the MIME)","file",False)

    # Projectors files and folders

    proj_generic_name = config['qoctra']['created_files']['projectors']
    # Get the list of projector folders
    proj_dirs = [dir.name for dir in os.scandir(qoctra_dir) if dir.is_dir() and dir.name.startswith(proj_generic_name)]
    # Get the list of projector files (all the files in data_dir which begins by "proj_generic_name") minus the "_1" part
    proj_files = [proj.rpartition('_')[0] for proj in os.listdir(data_dir) if os.path.isfile(os.path.join(data_dir,proj)) and proj.startswith(proj_generic_name)] 

    if sorted(proj_files) != sorted(proj_dirs):
      raise errors.ResultsError ("The projector files ({}) do not match the projector directories ({}).".format(proj_files,proj_dirs))

    # QOCT-RA results (pulses and populations)

    for proj_dir in proj_dirs:

      proj_path = os.path.join(qoctra_dir,proj_dir)

      fidelity = os.path.join(proj_path,config['results']['qoctra']['fidelity'])
      fidelity = errors.check_abspath(fidelity,"Fidelity file for the %s of %s" % (proj_dir,mol_name),"file",False)

      # Pulse folder

      pulse_dir = os.path.join(proj_path,config['results']['qoctra']['pulse_folder']['folder_name'])
      pulse_dir = errors.check_abspath(pulse_dir,"Folder containing the pulses for the %s of %s" % (proj_dir,mol_name),"folder",False)

      guess_pulse = config['results']['qoctra']['pulse_folder']['guess_pulse']
      guess_pulse = errors.check_abspath(os.path.join(pulse_dir, guess_pulse),"Guess pulse file for the %s of %s" % (proj_dir,mol_name),"file",False)

      guess_pulse_param = config['results']['qoctra']['pulse_folder']['guess_pulse_param']
      guess_pulse_param = errors.check_abspath(os.path.join(pulse_dir, guess_pulse_param),"Guess pulse parameters file for the %s of %s" % (proj_dir,mol_name),"file",False)

      final_pulse = config['results']['qoctra']['pulse_folder']['final_pulse']
      final_pulse = errors.check_abspath(os.path.join(pulse_dir, final_pulse),"Final pulse file for the %s of %s" % (proj_dir,mol_name),"file",False)

      final_pulse_param = config['results']['qoctra']['pulse_folder']['final_pulse_param']
      final_pulse_param = errors.check_abspath(os.path.join(pulse_dir, final_pulse_param),"Final pulse parameters file for the %s of %s" % (proj_dir,mol_name),"file",False)

      final_pulse_heat = config['results']['qoctra']['pulse_folder']['final_pulse_heat']
      final_pulse_heat = errors.check_abspath(os.path.join(pulse_dir, final_pulse_heat),"Final pulse pixel heat file for the %s of %s" % (proj_dir,mol_name),"file",False)

      # Post-control with pulse (PCP) folder

      pcp_dir = os.path.join(proj_path,config['results']['qoctra']['pcp_folder']['folder_name'])
      pcp_dir = errors.check_abspath(pcp_dir,"Folder containing the PCP populations for the %s of %s" % (proj_dir,mol_name),"folder",False)

      pop_zero = config['results']['qoctra']['pcp_folder']['pop_zero']
      pop_zero = errors.check_abspath(os.path.join(pcp_dir, pop_zero),"PCP population file for the %s of %s" % (proj_dir,mol_name),"file",False)

    # =========================================================
    # Check if the fidelity is high enough
    # =========================================================

    #TODO

    # =========================================================
    # Create log file
    # =========================================================

    # Create a output log file containing all the information about the molecule results treatment
    mol_log_name = mol_name + ".log"
    mol_log = open(os.path.join(out_dir, mol_log_name), 'w', encoding='utf-8')

    # Redirect standard output to the mol_log file (see https://stackabuse.com/writing-to-a-file-with-pythons-print-function/ for reference)
    #sys.stdout = mol_log

    # =========================================================
    # =========================================================
    #                    TABLES GENERATION
    # =========================================================
    # =========================================================

    # Initialize the dictionary that will contain all the text of the rendered files

    rendered_content = {}  

    # =========================================================
    # List of excited states
    # =========================================================

    # Load states_file

    print("\nScanning states file {} ... ".format(states_file))
    with open(states_file, 'r', newline='') as f_states:
      states_content = csv.DictReader(f_states, delimiter=';')
      states_list = list(states_content)
      states_header = states_content.fieldnames
      print("    Detected CSV header in states file : {}".format(states_header))

    # Converting the energies from cm-1 to nm and eV

    for state in states_list:
      print (state['Energy (cm-1)'])
      if float(state['Energy (cm-1)']) == 0: # Ground state
        state['Energy (cm-1)'] = "-"
        state['Energy (ev)'] = "-"
        state['Energy (nm)'] = "-"
      else:
        state['Energy (ev)'] = float(state['Energy (cm-1)']) / 8065.6
        state['Energy (nm)'] = 10000000 / float(state['Energy (cm-1)'])
    
    # Rendering the jinja template for the states list

    tpl_states = jinja_tpl["states_list_tpl"] # Name of the template file
    rnd_states = mol_name + "_states.tek"     # Name of the rendered file

    print("\nRendering the jinja template for the states list ...", end="")
  
    render_vars = {
        "states_list" : states_list
        }

    rendered_content[rnd_states] = jinja_render(path_tpl_dir, tpl_states, render_vars)

    print('%12s' % "[ DONE ]")

    print(rendered_content[rnd_states])

  except errors.ResultsError as error:
    sys.stdout = original_stdout                       # Reset the standard output to its original value
    print(error)
    print("Skipping %s molecule" % mol_name)
    os.remove(os.path.join(out_dir,mol_log_name))      # Remove the log file since there was a problem
    continue
