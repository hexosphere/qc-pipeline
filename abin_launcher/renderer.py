################################################################################################################################################
##                                                                The Renderer                                                                ##
##                                                                                                                                            ##
##         This script contains the rendering functions for the different job manifest and input files corresponding to each program          ##
################################################################################################################################################

import os
import jinja2

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

#! ATTENTION: All the functions defined below need to:
#! - be called prog_render, where prog is the name of the program as it appears in the YAML files (and as it will be given in the command line) 
#! - receive six dictionaries from abin_launcher.py as arguments: mendeleev, clusters_cfg, config, file_data, job_specs and misc
#! - return a dictionary (rendered_content) containing the text of all the rendered files in the form of <filename>: <rendered_content>
#! Otherwise, you will need to modify abin_launcher.py accordingly.

def orca_render(mendeleev:dict, clusters_cfg:dict, config:dict, file_data:dict, job_specs:dict, misc:dict):
    """Renders the job manifest and the input file associated with the program orca

    Parameters
    ----------
    mendeleev : dict
        Content of AlexGustafsson's Mendeleev Table YAML file (found at https://github.com/AlexGustafsson/molecular-data).
        Unused in this function.
    clusters_cfg : dict
        Content of the YAML clusters file
    config : dict
        Content of the YAML configuration file
    file_data : dict
        The extracted informations of the molecule file (see mol_scan.py for more details)
    job_specs : dict
        Contains all information related to the job (see abin_launcher.py for more details)
    misc : dict
        Contains all the additional variables that did not pertain to the other arguments (see abin_launcher.py for more details)

    Returns
    -------
    rendered_content : dict
        Dictionary containing the text of all the rendered files in the form of <filename>: <rendered_content>
    
    Advice
    -------
    Pay a particular attention to the render_vars dictionary, it contains all the definitions of the variables appearing in your jinja template and should be modified accordingly.
    """

    # Define the names of all the template and rendered files, given in the YAML cluster file.

    tpl_inp = clusters_cfg[job_specs['cluster_name']]['progs'][job_specs['prog']]['jinja']['templates']['input']                     # Jinja template file for the orca input
    tpl_manifest = clusters_cfg[job_specs['cluster_name']]['progs'][job_specs['prog']]['jinja']['templates']['job_manifest']         # Jinja template file for the orca job manifest (job submitting script)

    rnd_input = misc['mol_name'] + ".inp"                                                                                            # Name of the rendered input file (automatically named after the molecule and not defined in the clusters file)
    rnd_manifest = clusters_cfg[job_specs['cluster_name']]['progs'][job_specs['prog']]['jinja']['renders']['job_manifest']           # Name of the rendered job manifest file

    # Initialize our dictionary that will contain all the text of the rendered files

    rendered_content = {}

    # Get the path to the chains folder and the check_scripts folder because the job manifest needs to execute check_orca.py and source load_modules.sh

    chains_path = os.path.dirname(misc['code_dir'])                      # Get the parent folder from the codes_dir (which is the abin_launcher folder)                         
    check_script_path = os.path.join(chains_path,"check_scripts")

    # Rendering the jinja template for the orca job manifest
  
    print("\nRendering the jinja template for the orca job manifest ...", end="")

    render_vars = {  
        "mol_name" : misc['mol_name'],
        "user_email" : config['general']['user-email'],
        "mail_type" : config['general']['mail-type'],
        "job_walltime" : job_specs['walltime'],
        "job_cores" : job_specs['cores'],
        "job_mem_per_cpu" : job_specs['mem_per_cpu'], # in MB
        "partition" : job_specs['partition'],     
        "set_env" : clusters_cfg[job_specs['cluster_name']]['progs'][job_specs['prog']]['set_env'],       
        "command" : clusters_cfg[job_specs['cluster_name']]['progs'][job_specs['prog']]['command'],
        "output_folder" : config[job_specs['prog']]['output-folder'],
        "results_folder" : config['results']['main_folder'],
        "chains_folder" : chains_path,
        "check_folder" : check_script_path,
        "job_manifest" : rnd_manifest,
        "config_file" : misc['config_name'],
        "benchmark" : config['general']['benchmark'],
        "benchmark_folder" : config['general']['benchmark-folder'],
        "prog" : job_specs['prog'],
        "jobscale_label" : job_specs['scale_label'],
        "scaling_function" : job_specs['scaling_fct'],
        "scale_index" : job_specs['scale_index']
        }
    
    rendered_content[rnd_manifest] = jinja_render(misc['path_tpl_dir'], tpl_manifest, render_vars)

    print('%12s' % "[ DONE ]")
   
    # Rendering the jinja template for the orca input file
  
    print("\nRendering the jinja template for the orca input file ...  ", end="")

    orca_mem_per_cpu = int(0.75 * job_specs['mem_per_cpu']) # in MB
    
    render_vars = {
        "method" : config[job_specs['prog']]['method'],
        "basis_set" : config[job_specs['prog']]['basis-set'],
        "aux_basis_set" : config[job_specs['prog']]['aux-basis-set'],
        "job_type" : config[job_specs['prog']]['job-type'],
        "other" : config[job_specs['prog']]['other'],
        "job_cores" : job_specs['cores'],
        "orca_mem_per_cpu" : orca_mem_per_cpu,
        "charge" : config['general']['charge'],
        "multiplicity" : config['general']['multiplicity'],
        "coordinates" : file_data['atomic_coordinates']
        }
      
    rendered_content[rnd_input] = jinja_render(misc['path_tpl_dir'], tpl_inp, render_vars)

    print('%12s' % "[ DONE ]")

    return rendered_content

def qchem_render(mendeleev:dict, clusters_cfg:dict, config:dict, file_data:dict, job_specs:dict, misc:dict):
    """Renders the job manifest and the input file associated with the program qchem

    Parameters
    ----------
    mendeleev : dict
        Content of AlexGustafsson's Mendeleev Table YAML file (found at https://github.com/AlexGustafsson/molecular-data).
        Unused in this function.
    clusters_cfg : dict
        Content of the YAML clusters file
    config : dict
        Content of the YAML configuration file
    file_data : dict
        The extracted informations of the molecule file (see mol_scan.py for more details)
    job_specs : dict
        Contains all information related to the job (see abin_launcher.py for more details)
    misc : dict
        Contains all the additional variables that did not pertain to the other arguments (see abin_launcher.py for more details)

    Returns
    -------
    rendered_content : dict
        Dictionary containing the text of all the rendered files in the form of <filename>: <rendered_content>
    
    Advice
    -------
    Pay a particular attention to the render_vars dictionary, it contains all the definitions of the variables appearing in your jinja template and should be modified accordingly.
    """

    # Define the names of all the template and rendered files, given in the YAML cluster file.

    tpl_inp = clusters_cfg[job_specs['cluster_name']]['progs'][job_specs['prog']]['jinja']['templates']['input']                     # Jinja template file for the qchem input
    tpl_manifest = clusters_cfg[job_specs['cluster_name']]['progs'][job_specs['prog']]['jinja']['templates']['job_manifest']         # Jinja template file for the qchem job manifest (job submitting script)

    rnd_input = misc['mol_name'] + ".in"                                                                                             # Name of the rendered input file (automatically named after the molecule and not defined in the clusters file)
    rnd_manifest = clusters_cfg[job_specs['cluster_name']]['progs'][job_specs['prog']]['jinja']['renders']['job_manifest']           # Name of the rendered job manifest file

    # Initialize our dictionary that will contain all the text of the rendered files

    rendered_content = {}   

    # Get the path to the chains folder and the check_scripts folder because the job manifest needs to execute check_qchem.py and source load_modules.sh

    chains_path = os.path.dirname(misc['code_dir'])                      # Get the parent folder from the codes_dir (which is the abin_launcher folder)                         
    check_script_path = os.path.join(chains_path,"check_scripts")

    # Rendering the jinja template for the qchem job manifest
  
    print("\nRendering the jinja template for the qchem job manifest ...", end="")
  
    render_vars = {
        "mol_name" : misc['mol_name'],
        "user_email" : config['general']['user-email'],
        "mail_type" : config['general']['mail-type'],
        "job_walltime" : job_specs['walltime'],
        "job_cores" : job_specs['cores'],
        "job_mem_per_cpu" : job_specs['mem_per_cpu'], # in MB
        "partition" : job_specs['partition'],     
        "set_env" : clusters_cfg[job_specs['cluster_name']]['progs'][job_specs['prog']]['set_env'],       
        "command" : clusters_cfg[job_specs['cluster_name']]['progs'][job_specs['prog']]['command'],
        "output_folder" : config[job_specs['prog']]['output-folder'],
        "results_folder" : config['results']['main_folder'],
        "chains_folder" : chains_path,
        "check_folder" : check_script_path,
        "job_manifest" : rnd_manifest,
        "config_file" : misc['config_name'],
        "benchmark" : config['general']['benchmark'],
        "benchmark_folder" : config['general']['benchmark-folder'],
        "prog" : job_specs['prog'],
        "jobscale_label" : job_specs['scale_label'],
        "scaling_function" : job_specs['scaling_fct'],
        "scale_index" : job_specs['scale_index']
        }
    
    rendered_content[rnd_manifest] = jinja_render(misc['path_tpl_dir'], tpl_manifest, render_vars)

    print('%12s' % "[ DONE ]")
   
    # Rendering the jinja template for the qchem input file
  
    print("\nRendering the jinja template for the qchem input file ...  ", end="")
    
    render_vars = {
        "job_type" : config[job_specs['prog']]['job-type'],
        "exchange" : config[job_specs['prog']]['exchange'],
        "basis_set" : config[job_specs['prog']]['basis-set'],
        "cis_n_roots" : config[job_specs['prog']]['cis-n-roots'],
        "charge" : config['general']['charge'],
        "multiplicity" : config['general']['multiplicity'],
        "coordinates" : file_data['atomic_coordinates']
        }
      
    rendered_content[rnd_input] = jinja_render(misc['path_tpl_dir'], tpl_inp, render_vars)

    print('%12s' % "[ DONE ]")

    return rendered_content