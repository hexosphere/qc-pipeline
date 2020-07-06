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

def orca_render(vars):
    """Renders the job manifest and the input file associated with the program orca

    Parameters
    ----------
    vars : dict
        Dictionary containing the definitions of all the variables that were defined in abin_launcher (this can be defined with either vars() or locals() in abin_launcher)
        This way, everything can be accessed without having to define specific parameters

    Returns
    -------
    rendered_content : dict
        Dictionary containing the text of all the rendered files in the form of <filename>: <rendered_content>
    
    Advice
    -------
    Pay a particular attention to the render_vars dictionary, it contains all the definitions of the variables appearing in your jinja template and should be modified accordingly.
    """

    # Define the names of all the template and rendered files, given in the main configuration YAML file.

    tpl_inp = vars['config'][vars['prog']]['jinja_templates']['input']                 # Jinja template file for the orca input
    tpl_manifest = vars['config'][vars['prog']]['jinja_templates']['manifest']         # Jinja template file for the orca job manifest (slurm script)

    rnd_input = vars['mol_name'] + ".inp"                                              # Name of the rendered input file, this one is automatically named after the molecule and not defined in the configuration file
    rnd_manifest = vars['config'][vars['prog']]['rendered_files']['manifest']          # Name of the rendered job manifest file

    # Initialize our dictionary that will content all the text of the rendered files

    rendered_content = {}                                    

    # Rendering the jinja template for the orca job manifest
  
    print("\nRendering the jinja template for the orca job manifest ...", end="")

    render_vars = {  
        "mol_name" : vars['mol_name'],
        "user_email" : vars['config']['general']['user-email'],
        "mail_type" : vars['config']['general']['mail-type'],
        "job_duration" : vars['job_time'],
        "job_cores" : vars['job_cores'],
        "partition" : vars['job_partition'],     
        "set_env" : vars['clusters_cfg'][vars['cluster_name']]['progs'][vars['prog']]['set_env'],       
        "command" : vars['clusters_cfg'][vars['cluster_name']]['progs'][vars['prog']]['command'],
        "output_folder" : vars['config'][vars['prog']]['output-folder'],
        "results_folder" : vars['config']['general']['results-folder'],
        "codes_folder" : vars['code_dir'],
        "job_manifest" : rnd_manifest,
        "config_file" : vars['config_filename']
        }
    
    rendered_content[rnd_manifest] = jinja_render(vars['path_tpl_dir'], tpl_manifest, render_vars)

    print('%12s' % "[ DONE ]")
   
    # Rendering the jinja template for the orca input file
  
    print("\nRendering the jinja template for the orca input file ...  ", end="")
    
    render_vars = {
        "method" : vars['config'][vars['prog']]['method'],
        "basis_set" : vars['config'][vars['prog']]['basis-set'],
        "aux_basis_set" : vars['config'][vars['prog']]['aux-basis-set'],
        "job_type" : vars['config'][vars['prog']]['job-type'],
        "other" : vars['config'][vars['prog']]['other'],
        "job_cores" : vars['job_cores'],
        "charge" : vars['config']['general']['charge'],
        "multiplicity" : vars['config']['general']['multiplicity'],
        "coordinates" : vars['file_data']['atom_coordinates']
        }
      
    rendered_content[rnd_input] = jinja_render(vars['path_tpl_dir'], tpl_inp, render_vars)

    print('%12s' % "[ DONE ]")

    return rendered_content

def qchem_render(vars):
    """Renders the job manifest and the input file associated with the program qchem

    Parameters
    ----------
    vars : dict
        Dictionary containing the definitions of all the variables that were defined in abin_launcher (this can be defined with either vars() or locals() in abin_launcher)
        This way, everything can be accessed without having to define specific parameters

    Returns
    -------
    rendered_content : dict
        Dictionary containing the text of all the rendered files in the form of <filename>: <rendered_content>
    
    Advice
    -------
    Pay a particular attention to the render_vars dictionary, it contains all the definitions of the variables appearing in your jinja template and should be modified accordingly.
    """

    # Define the names of all the template and rendered files, given in the main configuration YAML file.

    tpl_inp = vars['config'][vars['prog']]['jinja_templates']['input']                 # Jinja template file for the qchem input
    tpl_manifest = vars['config'][vars['prog']]['jinja_templates']['manifest']         # Jinja template file for the qchem job manifest (slurm script)

    rnd_input = vars['mol_name'] + ".in"                                               # Name of the rendered input file, this one is automatically named after the molecule and not defined in the configuration file
    rnd_manifest = vars['config'][vars['prog']]['rendered_files']['manifest']          # Name of the rendered job manifest file

    # Initialize our dictionary that will content all the text of the rendered files

    rendered_content = {}   

    # Rendering the jinja template for the qchem job manifest
  
    print("\nRendering the jinja template for the qchem job manifest ...", end="")
  
    render_vars = {
        "mol_name" : vars['mol_name'],
        "user_email" : vars['config']['general']['user-email'],
        "mail_type" : vars['clusters_cfg'][vars['cluster_name']]['mail-type'],
        "job_duration" : vars['job_time'],
        "job_cores" : vars['job_cores'],
        "set_env" : vars['clusters_cfg'][vars['cluster_name']]['progs'][vars['prog']]['set_env'],       
        "command" : vars['clusters_cfg'][vars['cluster_name']]['progs'][vars['prog']]['command'],
        "output_folder" : vars['config'][vars['prog']]['output-folder'],
        "results_folder" : vars['config']['general']['results-folder'],
        "codes_folder" : vars['code_dir']
        }
    
    rendered_content[rnd_manifest] = jinja_render(vars['path_tpl_dir'], tpl_manifest, render_vars)

    print('%12s' % "[ DONE ]")
   
    # Rendering the jinja template for the qchem input file
  
    print("\nRendering the jinja template for the qchem input file ...  ", end="")
    
    render_vars = {
        "job_type" : vars['config'][vars['prog']]['job-type'],
        "exchange" : vars['config'][vars['prog']]['exchange'],
        "basis_set" : vars['config'][vars['prog']]['basis-set'],
        "cis_n_roots" : vars['config'][vars['prog']]['cis-n-roots'],
        "charge" : vars['config']['general']['charge'],
        "multiplicity" : vars['config']['general']['multiplicity'],
        "coordinates" : vars['file_data']['atom_coordinates']
        }
      
    rendered_content[rnd_input] = jinja_render(vars['path_tpl_dir'], tpl_inp, render_vars)

    print('%12s' % "[ DONE ]")

    return rendered_content