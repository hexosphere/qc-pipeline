#!/usr/bin/env python3

################################################################################################################################################
##                                                             Results Treatment                                                              ##
##                                                                                                                                            ##
##                               This script scans one or more molecule folders containing all the information                                ##
##                    obtained through CHAINS, ORCA, QCHEM and QOCT-RA and generates the corresponding tables and graphs.                     ##
##                                                                                                                                            ##
##                    /!\ In order to run, this script requires Python 3.5+ as well as YAML, Jinja2 and GNUplot 5+. /!\                       ##
##                                          /!\ Ask your cluster(s) administrator(s) if needed. /!\                                           ##
################################################################################################################################################

import argparse
import csv
import fnmatch
import os
import re
import shutil
import sys
from inspect import getsourcefile
import math

import jinja2 
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
optional.add_argument('-cf', '--config', type=str, help="Path to the YAML configuration file, default is this_script_directory/results_config.yml")

args = parser.parse_args()

# Define the variables corresponding to those arguments

out_dir = args.out_dir                   # Folder where all jobs subfolders will be created

single_mol = args.single                 # Molecule folder containing the results files that need to be processed.
multiple_mol = args.multiple             # Folder containing multiple molecule folders.

config_file = args.config                # YAML configuration file

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
# Check other arguments
# =========================================================

out_dir = errors.check_abspath(out_dir,"Command line argument -o / --out_dir","folder")
print ("{:<40} {:<100}".format('\nFigures directory:',out_dir))

# =========================================================
# Load config file
# =========================================================

if config_file: 
  config_file = errors.check_abspath(config_file,"Command line argument -cf / --config","file")
else:
  # If no value has been provided through the command line, take the results_config.yml file in the same directory as this script 
  config_file = os.path.join(code_dir, "results_config.yml")

print ("{:<40} {:<99}".format('\nLoading the configuration file',config_file + " ..."), end="")
with open(config_file, 'r') as f_config:
  config = yaml.load(f_config, Loader=yaml.FullLoader)
print('%12s' % "[ DONE ]")

# =========================================================
# Check jinja templates
# =========================================================

# Get the path to jinja templates folder (a folder named "Templates" in the same folder as this script)
path_tpl_dir = os.path.join(code_dir,"Templates")

# Check if all the files specified in the config file exist in the Templates folder of results_treatment.
for filename in config["jinja_templates"].values():
  errors.check_abspath(os.path.join(path_tpl_dir,filename),"Jinja template","file")

# =========================================================
# Check gnuplot scripts
# =========================================================

# Check if all the files specified in the config file exist in the same folder as this script.
for filename in config["gnuplot_scripts"].values():
  errors.check_abspath(os.path.join(code_dir,filename),"Gnuplot script","file")

# =========================================================
# Determine other important variables
# =========================================================

quality_treshold = float(config["other"]["quality_treshold"])
nb_points = int(config["other"]["nb_points"])                                     
gabor = errors.check_abspath(config["other"]["gabor"],"Gabor transform calculating script","file")    # Location of the xfrog script, necessary to obtain the gabor transform of our pulses
fft = errors.check_abspath(config["other"]["fft"],"FFT calculating script","file")                    # Location of the FFT script, necessary to obtain the Fourier transform of our pulses
created_files = []                                                                                    # Create a list to keep track of the files we've been creating (in order to remove them more easily if a problem occurs)

# =========================================================
# Conversion factors
# =========================================================

ua_to_sec = 2.4188843265857e-17
ua_to_cm = 219474.6313705                                                       # cm stands for cm-1
cm_to_ua = 1 / ua_to_cm                                                         # cm stands for cm-1

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
    # Load molecule config file
    # =========================================================

    mol_config_file = os.path.join(mol_dir, "config.yml")
    mol_config_file = errors.check_abspath(mol_config_file,"Molecule configuration file","file", True)
    print ("{:<40} {:<99}".format('\nLoading the configuration file',mol_config_file + " ..."), end="")
    with open(mol_config_file, 'r') as f_config:
      mol_config = yaml.load(f_config, Loader=yaml.FullLoader)
    print('%12s' % "[ DONE ]")

    # =========================================================
    # Check if all the necessary files are present
    # =========================================================

    print ("{:<140}".format('\nChecking if all the necessary files are present ...'), end="")

    # Optimized geometry

    orca_dir = os.path.join(mol_dir, mol_config['results']['orca']['folder_name'])
    opt_geom_file = errors.check_abspath(os.path.join(orca_dir, mol_name + ".xyz"),"Optimized geometry file","file",True)

    # Data extracted from the qchem output by control_launcher and the diagonalization of the MIME

    qoctra_dir = os.path.join(mol_dir, mol_config['results']['qoctra']['folder_name'])
    data_dir = errors.check_abspath(os.path.join(qoctra_dir, "data"),"Data folder created by control_launcher.py","folder",True)

    states_file = "states.csv"
    states_file = errors.check_abspath(os.path.join(data_dir, states_file),"List of excited states","file",True)

    coupling_file = "coupling_list.csv"
    coupling_file = errors.check_abspath(os.path.join(data_dir, coupling_file),"List of spin-orbit couplings (cm-1)","file",True)

    momdip_file = "momdip_list.csv"
    momdip_file = errors.check_abspath(os.path.join(data_dir, momdip_file),"List of transition dipole moments (in atomic units)","file",True)

    mime_file = mol_config['qoctra']['created_files']['mime_file']
    mime_file = errors.check_abspath(os.path.join(data_dir, mime_file),"MIME file","file",True)

    momdip_0 = mol_config['qoctra']['created_files']['momdip_zero']
    momdip_0 = errors.check_abspath(os.path.join(data_dir, momdip_0),"Transition dipole moments matrix (in atomic units)","file",True)

    mat_et0 = mol_config['qoctra']['created_files']['mat_et0']
    mat_et0 = errors.check_abspath(os.path.join(data_dir, mat_et0),"Eigenvectors matrix (mat_et0)","file",True)

    energies_file = mol_config['qoctra']['created_files']['energies_file']
    energies_file = errors.check_abspath(os.path.join(data_dir, energies_file + "_cm-1"),"List of eigenstates energies in cm-1 (eigenvalues from the diagonalization of the MIME)","file",True)

    # Projectors files and folders

    proj_generic_name = mol_config['qoctra']['created_files']['projectors']
    # Get the list of projector folders
    proj_dirs = [dir.name for dir in os.scandir(qoctra_dir) if dir.is_dir() and dir.name.startswith(proj_generic_name)]
    # Get the list of projector files (all the files in data_dir which begins by "proj_generic_name") minus the "_1" part
    proj_files = [proj.rpartition('_')[0] for proj in os.listdir(data_dir) if os.path.isfile(os.path.join(data_dir,proj)) and proj.startswith(proj_generic_name)] 

    if sorted(proj_files) != sorted(proj_dirs):
      raise errors.ResultsError ("ERROR: The projector files ({}) do not match the projector directories ({}).".format(proj_files,proj_dirs))

    # QOCT-RA results (pulses and populations)

    proj_info = [] # Initialize a list that will host the dictionaries containing all the information related to each projector 

    for proj_dir in proj_dirs:

      proj_dict = {} # Intialize a dictionary that will contain all the information related to the projector

      proj_path = os.path.join(qoctra_dir,proj_dir)
      proj_dict["main_path"] = proj_path

      # Get the target state from the projector name (e.g. projectorT1 => T1)

      target = proj_dir.partition(proj_generic_name)[2] 
      proj_dict["target"] = target

      # Get the path to the iterations file and its content

      iter_file = os.path.join(proj_path,mol_config['results']['qoctra']['fidelity'])
      iter_file = errors.check_abspath(iter_file,"Fidelity file for the %s of %s" % (proj_dir,mol_name),"file",True)
      proj_dict["iter_file"] = iter_file

      # Replace all occurrences of D by E (from Fortran's float format to Python's)
      command = "sed -i 's/D/E/g' " + iter_file
      retcode = os.system(command)
      if retcode != 0:
        raise errors.ResultsError ("ERROR: Unable to edit %s to replace all occurrences of D by E" % iter_file)

      # Go straight to the last line of the iterations file (see https://stackoverflow.com/questions/46258499/read-the-last-line-of-a-file-in-python for reference)
      with open(iter_file, 'rb') as f:
        f.seek(-2, os.SEEK_END)
        while f.read(1) != b'\n':
            f.seek(-2, os.SEEK_CUR)
        last_line = f.readline().decode()

      # Define how the lines of the iterations file must look like, here it is for example "    300     2  2sec |Proba_moy  0.000000E+00 |Fidelity(U)  0.000000E+00 |Chp  0.123802E+00 -0.119953E+00 |Aire  0.140871E-03 |Fluence  0.530022E+01 |Recou(i)  0.000000E+00 |Tr_dist(i) -0.500000E+00 |Tr(rho)(i)  0.100000E+01 |Tr(rho^2)(i)  0.100000E+01 |Projector  0.479527E-13"
      template_iter_file = re.compile(r"^\s+(?P<niter>\d+)\s+\d+\s+\d+sec\s\|Proba_moy\s+\d\.\d+E[+-]\d+\s\|Fidelity\(U\)\s+\d\.\d+E[+-]\d+\s\|Chp\s+\d\.\d+E[+-]\d+\s+-?\d\.\d+E[+-]\d+\s\|Aire\s+-?\d\.\d+E[+-]\d+\s\|Fluence\s+\d\.\d+E[+-]\d+\s\|Recou\(i\)\s+\d\.\d+E[+-]\d+\s\|Tr_dist\(i\)\s+-?\d\.\d+E[+-]\d+\s\|Tr\(rho\)\(i\)\s+\d\.\d+E[+-]\d+\s\|Tr\(rho\^2\)\(i\)\s+\d\.\d+E[+-]\d+\s\|Projector\s+(?P<projector>\d\.\d+E[+-]\d+)")

      # Get the number of iterations and the last fidelity from the last line
      content = template_iter_file.match(last_line)
      if content is not None:
        proj_dict["niter"] = int(content.group("niter"))
        proj_dict["fidelity"] = float(content.group("projector"))
      else:
        raise errors.ResultsError ("ERROR: Unable to get information from the last line of %s" % iter_file) 

      # Pulse folder

      pulse_dir = os.path.join(proj_path,mol_config['results']['qoctra']['pulse_folder']['folder_name'])
      pulse_dir = errors.check_abspath(pulse_dir,"Folder containing the pulses for the %s of %s" % (proj_dir,mol_name),"folder",True)
      proj_dict["pulse_dir"] = pulse_dir

      guess_pulse = mol_config['results']['qoctra']['pulse_folder']['guess_pulse']
      guess_pulse = errors.check_abspath(os.path.join(pulse_dir, guess_pulse),"Guess pulse file for the %s of %s" % (proj_dir,mol_name),"file",True)
      proj_dict["guess_pulse"] = guess_pulse

      guess_pulse_param = mol_config['results']['qoctra']['pulse_folder']['guess_pulse_param']
      guess_pulse_param = errors.check_abspath(os.path.join(pulse_dir, guess_pulse_param),"Guess pulse parameters file for the %s of %s" % (proj_dir,mol_name),"file",True)
      proj_dict["guess_pulse_param"] = guess_pulse_param

      final_pulse = mol_config['results']['qoctra']['pulse_folder']['final_pulse']
      final_pulse = errors.check_abspath(os.path.join(pulse_dir, final_pulse),"Final pulse file for the %s of %s" % (proj_dir,mol_name),"file",True)
      proj_dict["final_pulse"] = final_pulse

      final_pulse_param = mol_config['results']['qoctra']['pulse_folder']['final_pulse_param']
      final_pulse_param = errors.check_abspath(os.path.join(pulse_dir, final_pulse_param),"Final pulse parameters file for the %s of %s" % (proj_dir,mol_name),"file",True)
      proj_dict["final_pulse_param"] = final_pulse_param

      final_pulse_heat = mol_config['results']['qoctra']['pulse_folder']['final_pulse_heat']
      final_pulse_heat = errors.check_abspath(os.path.join(pulse_dir, final_pulse_heat),"Final pulse pixel heat file for the %s of %s" % (proj_dir,mol_name),"file",True)
      proj_dict["final_pulse_heat"] = final_pulse_heat

      # Post-control with pulse (PCP) folder

      pcp_dir = os.path.join(proj_path,mol_config['results']['qoctra']['pcp_folder']['folder_name'])
      pcp_dir = errors.check_abspath(pcp_dir,"Folder containing the PCP populations for the %s of %s" % (proj_dir,mol_name),"folder",True)
      proj_dict["pcp_dir"] = pcp_dir

      pop_zero = mol_config['results']['qoctra']['pcp_folder']['pop_zero']
      pop_zero = errors.check_abspath(os.path.join(pcp_dir, pop_zero),"PCP population file for the %s of %s" % (proj_dir,mol_name),"file",True)
      proj_dict["pop_zero"] = pop_zero

      # Save the dictionary to the proj_info list

      proj_info.append(proj_dict)

    print('%12s' % "[ DONE ]")

    # =========================================================
    # Check if the fidelity is high enough
    # =========================================================

    print("{:<40} {:<99}".format("\nQuality threshold",quality_treshold))
    to_remove = [] # List of the projectors that will be removed due to not meeting the quality threshold
    fidelities = {} # Dictionary of the form <target>:<fidelity> 

    print("")
    print(''.center(45, '-'))
    print("{:<15} {:<15} {:<15}".format('Target State','Fidelity','Good ?'))
    print(''.center(45, '-'))
    for projector in proj_info:
      target = projector["target"]
      fidelity = projector["fidelity"]
      good = "Yes" if fidelity >= quality_treshold else "No"
      print("{:<15} {:<15} {:<15}".format(target, fidelity, good))
      if fidelity < quality_treshold:
        to_remove.append(os.path.basename(projector["main_path"]))
      fidelities[target] = fidelity
    print(''.center(45, '-'))

    if to_remove != []:
      print('')
      print("The fidelity of the following projectors are too low, graphs will not be generated for those datas:")
      for projector in to_remove:  
        print("    -",projector)
      proj_info = [projector for projector in proj_info if os.path.basename(projector["main_path"]) not in to_remove] # Reconstruct proj_info omitting all projectors mentionned in to_remove

    if proj_info == []:
      raise errors.ResultsError ("None of the pulses associated with %s have a high enough fidelity. Graphs and tables will not be generated for this molecule." % mol_name)

    # =========================================================
    # =========================================================
    #                    TABLES GENERATION
    # =========================================================
    # =========================================================

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
      if float(state['Energy (cm-1)']) == 0: # Ground state
        state['Energy (cm-1)'] = None
        state['Energy (ev)'] = None
        state['Energy (nm)'] = None
        state['Fidelity'] = None
      else:
        state['Energy (cm-1)'] = float(state['Energy (cm-1)'])
        state['Energy (ev)'] = state['Energy (cm-1)'] / 8065.6
        state['Energy (nm)'] = 10000000 / state['Energy (cm-1)']
        if state['Label'] in fidelities.keys():
          state['Fidelity'] = "{:e}".format(float(fidelities[state['Label']])) 
        else:
          state['Fidelity'] = None
    
    # Rendering the jinja template for the states list

    tpl_states = config["jinja_templates"]["states_list"] # Name of the template file
    rnd_states = mol_name + "_states.tex"     # Name of the rendered file

    print("{:140}".format("\nCreating the states list %s file ... " % rnd_states), end="")
  
    render_vars = {
        "states_list" : states_list
        }

    rendered_file_path = os.path.join(out_dir, rnd_states)
    with open(rendered_file_path, "w", encoding='utf-8') as result_file:
      result_file.write(jinja_render(path_tpl_dir, tpl_states, render_vars))

    created_files.append(rnd_states)

    print('%12s' % "[ DONE ]")

    # =========================================================
    # List of spin-orbit couplings
    # =========================================================    

    # Load coupling_file

    print("\nScanning coupling file {} ... ".format(coupling_file))
    with open(coupling_file, 'r', newline='') as f_coupling:
      coupling_content = csv.DictReader(f_coupling, delimiter=';')
      coupling_list = list(coupling_content)
      coupling_header = coupling_content.fieldnames
      print("    Detected CSV header in coupling file : {}".format(coupling_header))

    # Translating state numbers into state labels

    for coupling in coupling_list:
      coupling['State 1'] = states_list[int(coupling['State 1'])]["Label"]
      coupling['State 2'] = states_list[int(coupling['State 2'])]["Label"]
      coupling['Energy (cm-1)'] = float(coupling['Energy (cm-1)'])

     # Rendering the jinja template for the states list

    tpl_coupling = config["jinja_templates"]["coupling_list"] # Name of the template file
    rnd_coupling = mol_name + "_soc.tex"          # Name of the rendered file

    print("{:140}".format("\nCreating the coupling list %s file ... " % rnd_coupling), end="")
  
    render_vars = {
        "coupling_list" : coupling_list
        }

    rendered_file_path = os.path.join(out_dir, rnd_coupling)
    with open(rendered_file_path, "w", encoding='utf-8') as result_file:
      result_file.write(jinja_render(path_tpl_dir, tpl_coupling, render_vars))

    created_files.append(rnd_coupling)

    print('%12s' % "[ DONE ]")
   
    # =========================================================
    # List of transition dipole moment
    # =========================================================    

    # Load momdip_file

    print("\nScanning momdip file {} ... ".format(momdip_file))
    with open(momdip_file, 'r', newline='') as f_momdip:
      momdip_content = csv.DictReader(f_momdip, delimiter=';')
      momdip_list = list(momdip_content)
      momdip_header = momdip_content.fieldnames
      print("    Detected CSV header in momdip file : {}".format(momdip_header))

    # Translating state numbers into state labels

    for momdip in momdip_list:
      momdip['State 1'] = states_list[int(momdip['State 1'])]["Label"]
      momdip['State 2'] = states_list[int(momdip['State 2'])]["Label"]
      momdip['Dipole (a.u.)'] = "{:e}".format(float(momdip['Dipole (a.u.)']))

     # Rendering the jinja template for the states list

    tpl_momdip = config["jinja_templates"]["momdip_list"]      # Name of the template file
    rnd_momdip = mol_name + "_momdip.tex"          # Name of the rendered file

    print("{:140}".format("\nCreating the momdip list %s file ... " % rnd_momdip), end="")
  
    render_vars = {
        "momdip_list" : momdip_list
        }

    rendered_file_path = os.path.join(out_dir, rnd_momdip)
    with open(rendered_file_path, "w", encoding='utf-8') as result_file:
      result_file.write(jinja_render(path_tpl_dir, tpl_momdip, render_vars))

    created_files.append(rnd_momdip)

    print('%12s' % "[ DONE ]")

    # =========================================================
    # =========================================================
    #                    GRAPHS GENERATION
    # =========================================================
    # =========================================================   
   
    for projector in proj_info:

      print("\nTreating the %s projector ..." % projector["target"])

      # =========================================================
      # Evolution of fidelity over the iterations
      # =========================================================      

      fidelity_script = os.path.join(code_dir,config["gnuplot_scripts"]["fidelity"])
      fidelity_graph = mol_name + "_" + projector["target"] + "_fidelity.tex"
      print("{:139}".format("    Creating the graph presenting the evolution of fidelity over the iterations (%s) ... " % fidelity_graph), end="")

      os.chdir(out_dir)
      command = "gnuplot -c {} {} {} {} {}".format(fidelity_script,projector["iter_file"],fidelity_graph,projector["niter"],nb_points)
      retcode = os.system(command)
      if retcode != 0 :
        raise errors.ResultsError ("ERROR: The %s gnuplot script encountered an issue" % fidelity_script)

      created_files.append(fidelity_graph)

      print('%12s' % "[ DONE ]")
  
      # =========================================================
      # Evolution of the states population over time
      # =========================================================      

      pop_file = projector["pop_zero"]
      pop_graph = mol_name + "_" + projector["target"] + "_pop.tex"
      print("{:139}".format("    Creating the graph presenting the evolution of the states population over time (%s) ... " % pop_graph), end="")

      # Count the number of lines in the population file
      #TODO: Use wccount (https://stackoverflow.com/questions/845058/how-to-get-line-count-of-a-large-file-cheaply-in-python/850962#850962)
      with open(pop_file) as f:
          for i, l in enumerate(f):
              pass
      nb_lines = i + 1

      # Go straight to the last line of the populations file (see https://stackoverflow.com/questions/46258499/read-the-last-line-of-a-file-in-python for reference)

      with open(pop_file, 'rb') as f:
        f.seek(-2, os.SEEK_END)
        while f.read(1) != b'\n':
            f.seek(-2, os.SEEK_CUR)
        last_line = f.readline().decode()

      # Extract the exponent from the time scale

      template_pop_file = re.compile(r"^\s+(?P<last_time>\d\.\d+E[+-]\d+)(\s+\d\.\d+E[+-]\d+){3,}$")
      content = template_pop_file.match(last_line)
      if content is not None:
        last_time = content.group("last_time")
      else:
        raise errors.ResultsError ("ERROR: Unable to get information from the last line of %s" % pop_file) 

      last_time_sec = float(last_time) * ua_to_sec                                     # Convert from u.a. to seconds
      time_exponent = re.split(r'[Ee]', str(last_time_sec))[1]                         # Get the exponent only from the scientific notation

      # Rendering the jinja template for the gnuplot script

      tpl_pop = config["jinja_templates"]["pop_gnuplot"]      # Name of the template file
      pop_script = "pop.plt"                                  # Name of the rendered file
  
      render_vars = {
          "input_file" : pop_file,
          "output_file" : pop_graph,
          "nb_lines" : nb_lines,
          "nb_points" : nb_points,
          "exponent" : time_exponent,
          "states_list" : states_list,
          "time_conv" : ua_to_sec
          }

      rendered_file_path = os.path.join(out_dir, pop_script)
      with open(rendered_file_path, "w", encoding='utf-8') as result_file:
        result_file.write(jinja_render(path_tpl_dir, tpl_pop, render_vars))

      created_files.append(pop_script)

      # Executing the newly created gnuplot script

      os.chdir(out_dir)
      command = "gnuplot " + pop_script
      retcode = os.system(command)
      if retcode != 0 :
        raise errors.ResultsError ("ERROR: The %s gnuplot script rendered through the %s jinja template encountered an issue" % (pop_script,tpl_pop))

      created_files.append(pop_graph)

      print('%12s' % "[ DONE ]")

      # Removing the newly created gnuplot script since it has done its job

      os.remove(os.path.join(out_dir, pop_script))
      created_files.remove(pop_script)

      # =========================================================
      # Gabor transform of the final pulse
      # =========================================================   

      print("{:139}".format("    Calculating the Gabor transform of the final pulse ... "), end="")

      # Get the central frequency of the pulse
      #TODO: see if we can get omegazero without recalculating it
      with open(energies_file,'r') as energies:
        energies_cm = energies.read().splitlines()
      
      energies_ua = [(float(energy) * cm_to_ua) for energy in energies_cm]
      ozero = sum(energies_ua) / (len(energies_ua) - 1) # Just like in control_launcher, -1 because the ground state doesn't count

      # Get the full width in frequency

      fwhm = float(mol_config['qoctra']['param_nml']['guess_pulse']['widthhalfmax']) * cm_to_ua
      full_width = fwhm / 2.355 * 6

      # Obtain the gabor transform through xfrog

      gabor_file = mol_name + "_" + projector["target"] + ".xfg"
      gabor_file_path = os.path.join(out_dir, gabor_file)
      freq_max = ozero + (full_width / 2)
      freq_min = ozero - (full_width / 2)
      # command = gabor + " -o " + gabor_file_path + " -fd " + str(freq_min) + " " + str(freq_max) + " " + os.path.relpath(projector["final_pulse"])
      # retcode = os.system(command)
      # if retcode != 0 :
      #   raise errors.ResultsError ("ERROR: The %s gabor script encountered an issue" % gabor)      
      # created_files.append(gabor_file)

      print('%12s' % "[ DONE ]")

      # Get the frequency exponent

      freq_max_cm = freq_max * ua_to_cm
      freq_exponent = re.split(r'[Ee]', "{:e}".format(freq_max_cm))[1]                         # Get the exponent only from the scientific notation

      # =========================================================
      # Temporal representation of the final pulse
      # =========================================================   

      time_script = os.path.join(code_dir,config["gnuplot_scripts"]["pulse_time"])
      time_graph = mol_name + "_" + projector["target"] + "_time.tex"
      print("{:139}".format("    Creating the graph presenting the temporal representation of the final pulse (%s) ... " % time_graph), end="")

      os.chdir(out_dir)
      command = "gnuplot -c {} {} {} {} {} {}".format(time_script,projector["final_pulse"],time_graph,int(mol_config['qoctra']['param_nml']['control']['nstep']),nb_points,time_exponent)
      retcode = os.system(command)
      if retcode != 0 :
        raise errors.ResultsError ("ERROR: The %s gnuplot script encountered an issue" % time_script)

      created_files.append(time_graph)

      print('%12s' % "[ DONE ]")

      # =========================================================
      # Spectral representation of the final pulse
      # =========================================================   

      # Obtain the FFT of the final pulse

      print("{:139}".format("    Calculating the FFT transform of the final pulse ... "), end="")

      command = fft + " 1 " + projector["final_pulse"]      # The 1 is an argument of the FFT script, to indicate that we want the FFT mode of that script
      retcode = os.system(command)
      if retcode != 0 :
        raise errors.ResultsError ("ERROR: The %s fft script encountered an issue" % fft)

      fft_file = projector["final_pulse"] + "_TF"

      print('%12s' % "[ DONE ]")

      # Plot the data

      spect_script = os.path.join(code_dir,config["gnuplot_scripts"]["pulse_spect"])
      spect_graph = mol_name + "_" + projector["target"] + "_spect.tex"
      print("{:139}".format("    Creating the graph presenting the spectral representation of the final pulse (%s) ... " % spect_graph), end="")

      os.chdir(out_dir)
      command = "gnuplot -c {} {} {} {} {} {}".format(spect_script,fft_file,spect_graph,int(freq_exponent),freq_min,freq_max)
      retcode = os.system(command)
      if retcode != 0 :
        os.remove(fft_file)
        raise errors.ResultsError ("ERROR: The %s gnuplot script encountered an issue" % spect_script)

      created_files.append(spect_graph)

      print('%12s' % "[ DONE ]")
  
      # Remove the newly created FFT file since it has done its job

      os.remove(fft_file)

  except errors.ResultsError as error:
    print("\n",error)
    if created_files != []:
      print("Removing the files that have been created so far ...")
      for filename in created_files:
        os.remove(os.path.join(out_dir,filename))
        print("    Removing %s file" % filename)
      print("[ DONE ]")
    print("Skipping %s molecule" % mol_name)
    continue

  console_message = "End of procedure for the molecule " + mol_name
  print("")
  print(''.center(len(console_message)+10, '*'))
  print(console_message.center(len(console_message)+10))
  print(''.center(len(console_message)+10, '*'))

print("")
print("".center(columns,"*"))
print("")
print("END OF EXECUTION".center(columns))
print("")
print("".center(columns,"*"))