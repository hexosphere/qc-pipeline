import os
import jinja2

# Define the function that will render an input file based on its jinja template
def jinja_render(path_tpl_dir, tpl, path_rnd_dir, rnd, var):

    template_file_path = os.path.join(path_tpl_dir, tpl)
    print("  Template path:  ",template_file_path)
    
    #rendered_file_path = os.path.join(path_rnd_dir, rnd)
    #print("  Output path:    ",rendered_file_path)
    
    environment = jinja2.Environment(loader=jinja2.FileSystemLoader(path_tpl_dir))
    output_text = environment.get_template(tpl).render(var)
    
    #TODO: store the file content in a variable and write it later in abin_launcher.py
    # with open(rendered_file_path, "w") as result_file:
    #     result_file.write(output_text)
    
    return output_text

def orca_render(vars):

    tpl_inp = "orca.inp.jinja"                             # Jinja template file for the orca input
    tpl_manifest = "orca_job.sh.jinja"                     # Jinja template file for the orca job manifest (slurm script)
    rnd_manifest = "orca_job.sh"                           # Name of the orca job manifest that will be created by this script

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
  

def qchem_render(vars):

    tpl_inp = "qchem.in.jinja"                           # Jinja template file for the q-chem input
    tpl_manifest = "qchem_job.sh.jinja"                   # Jinja template file for the q-chem job manifest (slurm script)
    rnd_manifest = "qchem_job.sh"                         # Name of the q-chem job manifest that will be created by this script

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
  
    jinja_render(path_tpl_dir, tpl_inp, mol_dir, rnd_input, render_vars)