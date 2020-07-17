#!/usr/bin/env python3

################################################################################################################################################
##                                                 Ab Initio Input Builder & Job Launcher                                                     ##
##                                                                                                                                            ##
##                             For one or more molecule files and a given ab initio program, this script prepares                             ##
##                       the input files needed for each calculation and launches the corresponding jobs on the cluster.                      ##
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

import mol_scan
import renderer
import scaling_fcts

"""
# SERVERHOME for repl.it
_ROOT_ = os.getcwd()
print("ROOT dir = " + os.getcwd())
"""
# ===================================================================
# ===================================================================
# Command line arguments
# ===================================================================
# ===================================================================

# Define the arguments needed for the script (here they are defined as named arguments rather than positional arguments, check https://stackoverflow.com/questions/24180527/argparse-required-arguments-listed-under-optional-arguments for more info).

parser = argparse.ArgumentParser(add_help=False, description="For one or more molecule files and a given ab initio program, this script prepares the input files needed for each calculation and launches the corresponding job on the cluster.")

required = parser.add_argument_group('Required arguments')
required.add_argument("-p","--program", type=str, help="Program you wish to run jobs with, must be the same as the name mentioned in the clusters and configuration YAML files", required=True)
required.add_argument("-i","--mol_inp", type=str, help="Path to either a molecule file or a directory containing multiple molecule files", required=True)
required.add_argument("-o","--out_dir", type=str, help="Path to the directory where you want to create the subdirectories for each job", required=True)

optional = parser.add_argument_group('Optional arguments')
optional.add_argument('-h','--help',action='help',default=argparse.SUPPRESS,help='Show this help message and exit')
optional.add_argument("-ow","--overwrite",action="store_true",help="Overwrite files if they already exists")
optional.add_argument("-k","--keep",action="store_true",help="Do not archive launched molecule files and leave them where they are")
optional.add_argument('-cfg', '--config', type=str, help="Path to the YAML config file, default is this_script_directory/config.yml.")
optional.add_argument('-cl', '--clusters', type=str, help="Path to the YAML clusters file, default is this_script_directory/clusters.yml.")

args = parser.parse_args()

# Define the variables corresponding to those arguments

prog = args.program                      # Name of the program for which files need to be created
mol_inp = args.mol_inp                   # Molecule file or folder containing the molecule files
out_dir = args.out_dir                   # Folder where all jobs subfolders will be created

overwrite = args.overwrite               # Flag for overwriting the files
keep = args.keep                         # Flag for keeping the molecule files where they are
config_file = args.config                # Main configuration file
clusters_file = args.clusters            # YAML file containing all informations about the clusters

# Other important variables that could become arguments if the need arises

mol_fmt = "xyz"                                 # Format of the molecule files we want to treat
mol_ext = "." + mol_fmt                         # Extension of the molecule files we're looking for

""" 
prog = "ORCA"
mol_inp = _ROOT_+"/INIT"
out_dir = _ROOT_+"/ORCA"
"""

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
print("EXECUTION OF THE AB INITIO INPUT BUILDER & JOB LAUNCHER BEGINS NOW".center(columns))
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

if config_file:
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
else:
  config_file = os.path.join(code_dir,"config.yml")

config_filename = os.path.basename(config_file)          # Store only the name of the config_file for later use

print("\nLoading the main configuration file %s ..." % config_file, end="")
with open(config_file, 'r') as f_config:
  config = yaml.load(f_config, Loader=yaml.FullLoader)
print('%12s' % "[ DONE ]")

# Loading the clusters_file for the informations about the clusters

if clusters_file:
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
else:
  clusters_file = os.path.join(code_dir,"clusters.yml")

print("\nLoading the clusters file %s ..." % clusters_file, end="")
with open(clusters_file, 'r') as f_clusters:
  clusters_cfg = yaml.load(f_clusters, Loader=yaml.FullLoader)
print('%20s' % "[ DONE ]")

# Loading AlexGustafsson's Mendeleev Table (found at https://github.com/AlexGustafsson/molecular-data) which will be used for the scaling functions.

print("\nLoading AlexGustafsson's Mendeleev Table ...", end="")
with open(os.path.join(code_dir,'elements.yml'), 'r') as f_elements:
  elements = yaml.load(f_elements, Loader=yaml.FullLoader)
print('%18s' % "[ DONE ]")

# =========================================================
# Define the name of our subfunctions
# =========================================================

# Name of the scanning function that will extract informations about the molecule from the molecule file (depends on the file format) - defined in mol_scan.py
scan_fct = mol_fmt + "_scan"

# Name of the scaling function that will determine the scale_index of the molecule (necessary for determining the job scale) - defined in scaling_fcts.py
scaling_fct = config[prog]["scaling_function"]

# Name of the render function that will render the job manifest and the input file (depends on the program)  - defined in renderer.py
render_fct = prog + "_render"

# =========================================================
# Check arguments
# =========================================================

# Check if the program exists in our databases. 
 
""" cluster_name = "dragon2" """
cluster_name = os.environ['CLUSTER_NAME']
print("\nThis script is running on the %s cluster" % cluster_name)

if prog not in config:
  print("\nERROR: No information provided for this program in the YAML config file. Please add informations for this program before attempting to run this script.")
  print("Aborting...")
  exit(3)

if prog not in clusters_cfg[cluster_name]["progs"]:
  print("\nERROR: Program unknown on this cluster. Possible program(s) include" , ', '.join(program for program in clusters_cfg[cluster_name]["progs"].keys()))
  print("Please use one of those, change cluster or add informations for this program to the YAML cluster file.")
  print("Aborting...")
  exit(3) 

if (render_fct) not in dir(renderer) or not callable(getattr(renderer, render_fct)):
  print("\nERROR: There is no function defined for the %s program in renderer.py." % prog)
  print("Aborting...")
  exit(3) 

# TODO: case insensitive program name?

# Check if the path to the working directory exists and make sure it's absolute.

if not os.path.exists(out_dir):
  print(out_dir)
  print("  ^ ERROR: The path to the folder where you want to run the jobs does not seem to exist.")
  print("Aborting ...")
  exit(4)

if not os.path.isdir(out_dir):
  print(out_dir)
  print("  ^ ERROR: This is not a directory.")
  print("Aborting ...")
  exit(4)

out_dir = os.path.abspath(out_dir)
print("\nJobs main directory: ", out_dir)

# Check if the path to the molecule file or the folder containing the molecule files exists and make sure it's absolute.

if not os.path.exists(mol_inp):
  print(mol_inp)
  print("  ^ ERROR: The path to the molecule file or the folder containing the molecule files does not seem to exist.")
  print("Aborting ...")
  exit(4)

if not os.path.isdir(mol_inp) and not os.path.isfile(mol_inp):
  print(mol_inp)
  print("  ^ ERROR: This is neither a file nor a directory.")
  print("Aborting ...")
  exit(4)

if os.path.isfile(mol_inp) and os.path.splitext(mol_inp)[-1].lower() != (mol_ext):
  print("  ^ ERROR: This is not an %s file." % mol_fmt)

mol_inp = os.path.abspath(mol_inp)

# Check if a scanning function has been defined for the given format of the molecule file(s)

if (scan_fct) not in dir(mol_scan) or not callable(getattr(mol_scan, scan_fct)):
  print("\nERROR: There is no function defined for the %s format in mol_scan.py." % mol_fmt)
  print("Aborting...")
  exit(3) 

# Check if the chosen scaling function has been defined in scaling_fcts.py

if (scaling_fct) not in dir(scaling_fcts) or not callable(getattr(scaling_fcts, scaling_fct)):
  print("\nERROR: There is no scaling function named %s defined in scaling_fcts.py." % scaling_fct)
  print("Aborting...")
  exit(3) 

# =========================================================
# Establishing the different job scales
# =========================================================

# Gather all the different job scales from the clusters configuration file in a temporary dictionary

job_scales_tmp = clusters_cfg[cluster_name]['progs'][prog]['job_scales']

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

# =========================================================
# Looking for the molecule files
# =========================================================

# If the argument mol_inp is a folder, we need to look for every molecule file with the given format in that folder.
if os.path.isdir(mol_inp):
  print("\nLooking for every %s molecule file in %s ..." % (mol_ext,mol_inp))
  mol_inp_path = mol_inp
  # Define which type of file we are looking for in a case-insensitive way (see https://gist.github.com/techtonik/5694830)
  rule = re.compile(fnmatch.translate("*." + mol_fmt), re.IGNORECASE)
  # Find all matching files in mol_inp folder
  mol_inp_list = [mol for mol in os.listdir(mol_inp) if rule.match(mol)]
  if mol_inp_list == []:
    print("\nERROR: Can't find any molecule of the %s format in %s" % (mol_ext,mol_inp_path))
else:
  mol_inp_path = os.path.dirname(mol_inp)
  mol_inp_file = os.path.basename(mol_inp)
  mol_inp_list = [mol_inp_file]

# ===================================================================
# ===================================================================
#                   FILES MANIPULATION & GENERATION
# ===================================================================
# ===================================================================

for mol_filename in mol_inp_list:

  #print("Treating %s file ..." % mol_filename, end="")
  #TODO: Create an output log file for each molecule

  # =========================================================
  # Molecule file treatment
  # =========================================================
  
  # Getting rid of the format extension to get the name of the molecule
  
  mol_name = str(mol_filename.split('.')[0])

  print("")
  print("".center(80,"-"))
  print("Molecule %s".center(80) % mol_name)
  print("".center(80,"-"))
 
  if os.path.exists(os.path.join(out_dir,mol_name)) and not overwrite:
      print("\n\nERROR: A folder for the %s molecule already exists in %s !" % (mol_name, out_dir))
      print("Skipping this molecule...")
      continue

  # Reading the content of the molecule file
  
  print("\nScanning %s file ..." % mol_filename, end="")
  with open(os.path.join(mol_inp_path,mol_filename), 'r') as mol_file:
    mol_content = mol_file.read().splitlines()

  # Scanning the content of the file and extracting the relevant informations

  model_file_data = {'nb_atoms': 0, 'chemical_formula':{}, 'atomic_coordinates':[]}  # The data extracted from the molecule file through the "mol_fmt"_scan function must follow this pattern as it will be used later on by the other subscripts.

  file_data = eval("mol_scan." + scan_fct)(mol_content,model_file_data)

  if not file_data:
    continue

  print('%20s' % "[ DONE ]")
   
  # =========================================================
  # Determining the scale_index
  # =========================================================
  
  section_title = "1. Scale index determination"

  print("")
  print("")
  print(''.center(len(section_title)+10, '*'))
  print(section_title.center(len(section_title)+10))
  print(''.center(len(section_title)+10, '*'))
  
  # scale_index determination
  
  scale_index = eval("scaling_fcts." + scaling_fct)(elements, file_data)

  print("\nScale index: ", scale_index)
  
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
    print("\n\nERROR: This molecule job scale is too big for this cluster (%s). Please change cluster." % cluster_name)
    print("Skipping this molecule...")
    continue
  
  # =========================================================
  # Determining the ressources needed for the job
  # =========================================================
  
  section_title = "2. Calculation requirements"

  print("")
  print("")
  print(''.center(len(section_title)+10, '*'))
  print(section_title.center(len(section_title)+10))
  print(''.center(len(section_title)+10, '*'))
  
  # Determining which cluster we're running on and obtaining the related informations
  
  job_partition = jobscale['partition_name']
  job_walltime = jobscale['time']
  job_cores = jobscale['cores']
  job_mem_per_cpu = jobscale['mem_per_cpu']

  print("")
  print(''.center(50, '-'))
  print("{:<20} {:<30}".format("Scale index: ", scale_index))
  print(''.center(50, '-'))
  print("{:<20} {:<30}".format("Cluster: ", cluster_name))
  print("{:<20} {:<30}".format("Job scale: ", jobscale["label"]))
  print("{:<20} {:<30}".format("Job scale limit: ", jobscale_limit))
  print(''.center(50, '-'))
  print("{:<20} {:<30}".format("Job partition: ", job_partition))
  print("{:<20} {:<30}".format("Job walltime: ", job_walltime))
  print("{:<20} {:<30}".format("Number of cores: ", job_cores))
  print("{:<20} {:<30}".format("Mem per CPU (MB): ", job_mem_per_cpu))

  # =========================================================
  # Rendering the needed input files
  # =========================================================

  section_title = "3. Generation of the job manifest and input files"

  print("")
  print("")
  print(''.center(len(section_title)+10, '*'))
  print(section_title.center(len(section_title)+10))
  print(''.center(len(section_title)+10, '*'))
  
  # Get the path to jinja templates folder (a folder named "Templates" in the samed folder as this script)

  path_tpl_dir = os.path.join(code_dir,"Templates")

  # Dynamically call the inputs render function for the given program

  rendered_content = eval("renderer." + render_fct)(locals())  # Dictionary containing the text of all the rendered files in the form of <filename>: <rendered_content>
  
  # =========================================================
  # The end step
  # =========================================================

  section_title = "4. The end step"

  print("")
  print("")
  print(''.center(len(section_title)+10, '*'))
  print(section_title.center(len(section_title)+10))
  print(''.center(len(section_title)+10, '*'))

  # Creating the molecule subfolder where the job will be launched and creating all the relevant files in it.
 
  mol_dir = os.path.join(out_dir,mol_name)

  if os.path.exists(mol_dir):
    shutil.rmtree(mol_dir)

  os.makedirs(mol_dir)

  print("\nThe %s subfolder has been created at %s" % (mol_name, out_dir))
  
  # Copying the config file and the molecule file into the molecule subfolder
  
  shutil.copy(os.path.join(mol_inp_path,mol_filename), mol_dir)
  shutil.copy(config_file, mol_dir)

  print("\nThe files %s and %s have been successfully copied into the subfolder." % (config_filename, mol_filename))
  print("")

  # Writing the content of each rendered file into its own file with the corresponding filename

  for filename, file_content in rendered_content.items():
    rendered_file_path = os.path.join(mol_dir, filename)
    with open(rendered_file_path, "w") as result_file:
      result_file.write(file_content)
    print("The %s file has been created into the subfolder" % filename)

  # Launch the job
  
  print("\nLaunching the job ...")
  os.chdir(mol_dir)
  subcommand = clusters_cfg[cluster_name]['subcommand']
  delay_command = str(jobscale["delay_command"] or '')
  manifest = config[prog]['rendered_files']['manifest']
  launch_command = subcommand + " " + delay_command + " " + manifest
  retcode = os.system(launch_command)
  if retcode != 0 :
    print("Job submit encountered an issue")
    print("Aborting ...")
    exit(5)

  # Archive the molecule file in launched_dir if keep has not been set
  
  if not keep:
    launched_dir = os.path.join(mol_inp_path,"Launched")                             # Folder where the molecule files will be put after having been treated by this script, path is relative to the directory where are all the molecule files.
    os.makedirs(launched_dir, exist_ok=True)
    if os.path.exists(os.path.join(launched_dir,mol_filename)):
      os.remove(os.path.join(launched_dir,mol_filename))
    shutil.move(os.path.join(mol_inp_path,mol_filename), launched_dir)
    print("\nMolecule original structure file archived to %s" % launched_dir)

  print("\nEnd of procedure for the molecule %s" % mol_name)
  
  #print('%20s' % "[ DONE ]")

print("")
print("".center(columns,"*"))
print("")
print("END OF EXECUTION".center(columns))
print("")
print("".center(columns,"*"))