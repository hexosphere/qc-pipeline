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
from inspect import getsourcefile

import jinja2
import yaml

import get_bigindex
import inputs_render

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
optional.add_argument('-cfg', '--config', type=str, help="Path to the YAML config file, default is this_script_directory/config.yml.")
optional.add_argument('-cl', '--clusters', type=str, help="Path to the YAML clusters file, default is this_script_directory/clusters.yml.")

args = parser.parse_args()

# Define the variables corresponding to those arguments

prog = args.program                      # Name of the program for which files need to be created
mol_inp = args.mol_inp                   # Molecule file or folder containing the molecule files
out_dir = args.out_dir                   # Folder where all jobs subfolders will be created

overwrite = args.overwrite               # Flag for overwriting the files
config_file = args.config                # Main configuration file
clusters_file = args.clusters            # YAML file containing all informations about the clusters

# Other important variables that could become arguments

mol_fmt = "xyz"                          # Format of the molecule files we want to treat
mol_ext = ".xyz"                         # Extension of the molecule files we're looking for

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

# Define the function that will render our files, based on the jinja templates

def jinja_render(path_tpl_dir, tpl, path_rnd_dir, rnd, var):
  template_file_path = os.path.join(path_tpl_dir, tpl)
  print("  Template path:  ",template_file_path)
  
  rendered_file_path = os.path.join(path_rnd_dir, rnd)
  print("  Output path:    ",rendered_file_path)
  
  environment = jinja2.Environment(loader=jinja2.FileSystemLoader(path_tpl_dir))
  output_text = environment.get_template(tpl).render(var)
  
  with open(rendered_file_path, "w") as result_file:
      result_file.write(output_text)

# Define the function that will scan our xyz files to interpret the data

def xyz_scan(mol_content:list,model_file_data:dict):

  file_data = model_file_data
  
  # Scanning the content of the XYZ file to determine the chemical formula of the molecule
  
  file_data['#atoms'] = mol_content[0]
    
  lines_rx = {
      # Pattern for finding lines looking like 'Si        -0.31438        1.89081        0.00000' (this is a regex, for more information, see https://docs.python.org/3/library/re.html)
      'atomLine': re.compile(
          r'^\s{0,4}(?P<atomSymbol>[a-zA-Z]{0,3})\s+[-]?\d+\.\d+\s+[-]?\d+\.\d+\s+[-]?\d+\.\d+$')
  }
  
  checksum_nlines = 0                                        # This variable will be used to check if the number of coordinate lines matches the number of atoms of the molecule 
  
  for line in mol_content[2:]:                               # We only start at the 3rd line because the first two won't contain any coordinates
    m = lines_rx['atomLine'].match(line)
    if m is not None:                                        # We only care if the line looks like an atom coordinates
      checksum_nlines += 1
      file_data['atom_coordinates'].append(line)             # All coordinates will be stored in this variable to be rendered in the input file later on
      if m.group("atomSymbol") not in file_data['elm_list']:
        file_data['elm_list'][m.group("atomSymbol")] = 1
      else:
        file_data['elm_list'][m.group("atomSymbol")] += 1
              
  # Check if the number of lines matches the number of atoms defined in the first line of the .xyz file
  
  if checksum_nlines != int(file_data['#atoms']):
    print("\n\nERROR: Number of atoms lines (%s) doesn't match the number of atoms mentioned in the first line of the .xyz file (%s) !" % (checksum_nlines, int(file_data['#atoms'])))
    print("Skipping this molecule...")
    file_data = None

  return file_data

# Get the size of the terminal in order to have a prettier output, if you need something more robust, go check http://granitosaurus.rocks/getting-terminal-size.html

columns, rows = shutil.get_terminal_size()

# Output Header

print("".center(columns,"*"))
print("")
print("EXECUTION OF THE AB INITIO INPUT BUILDER & JOB LAUNCHER BEGINS NOW".center(columns))
print("")
print("".center(columns,"*"))

# =========================================================
# TO BE REMOVED WHEN RENDER IS READY
# =========================================================

# Jinja templates
# TODO: create prog_jinja_render.py and just look for that file?
# => Name them in the YAML config file

""" if prog == "orca":
  tpl_inp = "orca.inp.jinja"                             # Jinja template file for the orca input
  tpl_manifest = "orca_job.sh.jinja"                     # Jinja template file for the orca job manifest (slurm script)
  rnd_manifest = "orca_job.sh"                           # Name of the orca job manifest that will be created by this script

elif prog == "qchem":
  tpl_inp = "qchem.in.jinja"                           # Jinja template file for the q-chem input
  tpl_manifest = "qchem_job.sh.jinja"                   # Jinja template file for the q-chem job manifest (slurm script)
  rnd_manifest = "qchem_job.sh"                         # Name of the q-chem job manifest that will be created by this script """

# Associated scripts
# TODO: just check for prog_check.py? => or better, just leave those names in the jina, there's no need for them to be variables

if prog == "orca": 
  check_script = "orca_check.py"                           # Python script used to check if the ORCA job ended normally

elif prog == "qchem": 
  check_script = "qchem_check.py"                         # Python script used to check if the Q-CHEM job ended normally

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

if (prog + "_render") not in dir(inputs_render) or not callable(inputs_render, prog + "_render"):
  print("\nERROR: There is no function defined for the %s program in inputs_render.py." % prog)
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
print("\nWorking directory: ", out_dir)

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

if os.path.isfile(mol_inp) and os.path.splitext(mol_inp)[-1].lower() != ("." + mol_fmt):
  print("  ^ ERROR: This is not an %s file." % mol_fmt)

mol_inp = os.path.abspath(mol_inp)

# =========================================================
# Looking for the molecule files
# =========================================================

# If the argument mol_inp is a folder, we need to look for every molecule file with the given format in that folder.
if os.path.isdir(mol_inp):
  print("\nLooking for every %s molecule file in %s ..." % ("." + mol_fmt,mol_inp))
  mol_inp_path = mol_inp
  # Define which type of file we are looking for in a case-insensitive way (see https://gist.github.com/techtonik/5694830)
  rule = re.compile(fnmatch.translate("*." + mol_fmt), re.IGNORECASE)
  # Find all matching files in mol_inp folder
  mol_inp_list = [mol for mol in os.listdir(mol_inp) if rule.match(mol)]
  if mol_inp_list == []:
    print("\nERROR: Can't find any molecule of the %s format in %s" % ("." + mol_fmt,mol_inp_path))
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
  print("".center(columns,"-"))
  print("Molecule %s".center(columns) % mol_name)
  print("".center(columns,"-"))

  if os.path.exists(os.path.join(out_dir,mol_name)) and not overwrite:
      print("\n\nERROR: A folder for the %s molecule already exists in %s !" % (mol_name, out_dir))
      print("Skipping this molecule...")
      continue
  
  # Reading the content of the molecule file
  
  print("\nScanning %s file ..." % mol_filename, end="")
  with open(os.path.join(mol_inp_path,mol_filename), 'r') as mol_file:
    mol_content = mol_file.read().splitlines()

  model_file_data = {'#atoms': 0, 'elm_list':{}, 'atom_coordinates':[]}

  file_data = xyz_scan(mol_content,model_file_data)

  if not file_data:
    continue

  print('%20s' % "[ DONE ]")
   
  # =========================================================
  # Determining the jobscale category (through bigindex)
  # =========================================================
  
  section_title = "1. Job scale determination"

  print("")
  print("")
  print(''.center(len(section_title)+10, '-'))
  print(section_title.center(len(section_title)+10))
  print(''.center(len(section_title)+10, '-'))
  
  # Big Index determination
  
  bigindex = get_bigindex.total_nb_elec(code_dir,file_data)

  print("\nBigindex: ", bigindex)
  
  # Job scale category definition

  #TODO: Make this part dynamic (what if the user made more partitions like very small, small, medium, big, very big, giant...)
  if bigindex < clusters_cfg['dummy']['partition']['tiny']['bigindex_limit']:
    jobscale = "tiny"
  elif bigindex >= clusters_cfg['dummy']['partition']['tiny']['bigindex_limit'] \
    and bigindex < clusters_cfg[cluster_name]['progs'][prog]['partition']['medium']['bigindex_limit']:
    jobscale = "small"
  elif bigindex >= clusters_cfg[cluster_name]['progs'][prog]['partition']['medium']['bigindex_limit'] \
    and bigindex < clusters_cfg[cluster_name]['progs'][prog]['partition']['big']['bigindex_limit']:
    jobscale = "medium"
  elif bigindex >= bigindex < clusters_cfg[cluster_name]['progs'][prog]['partition']['big']['bigindex_limit']:
    jobscale = "big"

  print("    => Job scale category: ", jobscale)
  
  # =========================================================
  # Determining the ressources needed for the job
  # =========================================================
  
  section_title = "2. Calculation requirements"

  print("")
  print("")
  print(''.center(len(section_title)+10, '-'))
  print(section_title.center(len(section_title)+10))
  print(''.center(len(section_title)+10, '-'))
  
  # Determining which cluster we're running on and obtaining the related informations
  
  print("\nThis script is running on the %s cluster." % cluster_name)
  
  if jobscale == "tiny":
    job_time = clusters_cfg['dummy']['partition'][jobscale]['time']
    job_cores = clusters_cfg['dummy']['partition'][jobscale]['cores']
    job_partition = "default"
  elif jobscale not in clusters_cfg[cluster_name]['progs'][prog]['partition']:
    print("\n\nERROR: Requested job scale (%s) is too big for this cluster (%s). Please change cluster." % (jobscale, cluster_name))
    print("Skipping this molecule...")
    #TODO : either get rid of the newly created mol_name folder, or do all files and folders writing at the end of the loop
    continue
  else:
    job_time = clusters_cfg[cluster_name]['progs'][prog]['partition'][jobscale]['time']
    job_cores = clusters_cfg[cluster_name]['progs'][prog]['partition'][jobscale]['cores']
    job_partition = clusters_cfg[cluster_name]['progs'][prog]['partition'][jobscale]['name']
  
  print("    => Job partition:   ", job_partition)
  print("    => Number of cores: ", job_cores)
  print("    => Job duration:    ", job_time)
    
  # Creating the molecule subfolder where the job will be run
  
  mol_dir = os.path.join(out_dir,mol_name)

  if os.path.exists(mol_dir):
    shutil.rmtree(mol_dir)

  os.makedirs(mol_dir)

  print("The %s subfolder has been created at %s" % (mol_name, out_dir))
  
  # Copying the config file and the molecule file into the molecule subfolder
  
  shutil.copy(os.path.join(mol_inp_path,mol_filename), mol_dir)
  shutil.copy(config_file, mol_dir)

  print("The files %s and %s have been successfully copied into the subfolder." % (config_filename, mol_filename))

  # =========================================================
  # Creating the orca job manifest and orca input files
  # =========================================================

  section_title = "3. Generation of the job manifest and input files"

  print("")
  print("")
  print(''.center(len(section_title)+10, '-'))
  print(section_title.center(len(section_title)+10))
  print(''.center(len(section_title)+10, '-'))
  
  # Get the path to jinja templates folder

  path_tpl_dir = os.path.join(code_dir,"Templates")

  # Dynamically call the inputs render function for the given program

  #prog_rnd_fct = prog + "_render"
  inputs_content = eval("inputs_render." + prog + "_render")(locals()) 

  for filename, file_content in inputs_content:
    rendered_file_path = os.path.join(mol_dir, filename)
    with open(rendered_file_path, "w") as result_file:
      result_file.write(file_content)
   
  """ if prog == "orca":
  
    # Rendering the jinja template for the ORCA job manifest
  
    print("\nRendering the jinja template for the ORCA job manifest")
  
    render_vars = {
        "mol_name" : mol_name,
        "user_email" : config['general']['user-email'],
        "mail_type" : config['general']['mail-type'],
        "job_duration" : job_time,
        "job_cores" : job_cores,
        "partition" : job_partition,
        "set_env" : clusters_cfg[cluster_name]['progs'][prog]['set_env'],
        "command" : clusters_cfg[cluster_name]['progs'][prog]['command'],
        "output_folder" : config['orca']['output-folder'],
        "results_folder" : config['general']['results-folder'],
        "codes_folder" : code_dir,
        "check_script" : check_script,
        "job_manifest" : rnd_manifest,
        "config_file" : config_filename
        }
    
    jinja_render(path_tpl_dir, tpl_manifest, mol_dir, rnd_manifest, render_vars)
   
    # Rendering the jinja template for the ORCA input file
  
    print("\nRendering the jinja template for the ORCA input file")
    
    render_vars = {
        "method" : config[prog]['method'],
        "basis_set" : config[prog]['basis-set'],
        "aux_basis_set" : config[prog]['aux-basis-set'],
        "job_type" : config[prog]['job-type'],
        "other" : config[prog]['other'],
        "job_cores" : job_cores,
        "charge" : config['general']['charge'],
        "multiplicity" : config['general']['multiplicity'],
        "coordinates" : file_data['atom_coordinates']
        }
    
    rnd_input = mol_name + ".inp"
  
    jinja_render(path_tpl_dir, tpl_inp, mol_dir, rnd_input, render_vars)
  
  elif prog == "qchem":
  
    # Rendering the jinja template for the Q-CHEM job manifest
  
    print("\nRendering the jinja template for the Q-CHEM job manifest")
  
    render_vars = {
        "mol_name" : mol_name,
        "user_email" : config['general']['user-email'],
        "mail_type" : clusters_cfg[cluster_name]['mail-type'],
        "job_duration" : job_time,
        "job_cores" : job_cores,
        "set_env" : clusters_cfg[cluster_name]['progs'][prog]['set_env'],
        "command" : clusters_cfg[cluster_name]['progs'][prog]['command'],
        "output_folder" : config['qchem']['output-folder'],
        "results_folder" : config['general']['results-folder'],
        "codes_folder" : code_dir,
        "check_script" : check_script
        }
    
    jinja_render(path_tpl_dir, tpl_manifest, mol_dir, rnd_manifest, render_vars)
   
    # Rendering the jinja template for the Q-CHEM input file
  
    print("\nRendering the jinja template for the Q-CHEM input file")
    
    render_vars = {
        "job_type" : config[prog]['job-type'],
        "exchange" : config[prog]['exchange'],
        "basis_set" : config[prog]['basis-set'],
        "cis_n_roots" : config[prog]['cis-n-roots'],
        "charge" : config['general']['charge'],
        "multiplicity" : config['general']['multiplicity'],
        "coordinates" : file_data['atom_coordinates']
        }
    
    rnd_input = mol_name + ".in"
  
    jinja_render(path_tpl_dir, tpl_inp, mol_dir, rnd_input, render_vars) """
      
  # =========================================================
  # The end step
  # =========================================================

  section_title = "4. The end step"

  print("")
  print("")
  print(''.center(len(section_title)+10, '-'))
  print(section_title.center(len(section_title)+10))
  print(''.center(len(section_title)+10, '-'))

  # Launch the job
  
  print("\nLaunching the job ...", end='')
  os.chdir(mol_dir)
  subcommand = clusters_cfg[cluster_name]['subcommand']
  launch_command = subcommand + " " + rnd_manifest
  retcode = os.system(launch_command)
  if retcode != 0 :
    print("Job submit encountered an issue")
    print("Aborting ...")
    exit(5)
    #TODO: quoi faire en cas de submit fail ??

  print('%20s' % "[ DONE ]")

  # Archive the molecule file in launched_dir
  
  launched_dir = os.path.join(mol_inp_path,"Launched")                             # Folder where the molecule files will be put after having been treated by this script, path is relative to the directory where are all the molecule files.
  os.makedirs(launched_dir, exist_ok=True)
  if os.path.exists(os.path.join(launched_dir,mol_filename)):
    os.remove(os.path.join(launched_dir,mol_filename))
  shutil.move(os.path.join(mol_inp_path,mol_filename), launched_dir)
  print("\nMolecule file archived to %s" % launched_dir)
  
  #print('%20s' % "[ DONE ]")
