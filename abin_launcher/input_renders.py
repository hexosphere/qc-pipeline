import os
import jinja2

# Check the given name of the program and call the corresponding function 
def inputs_render(vars):
    if prog == "orca":
        orca_render(vars)
    elif prog == "qchem":
        qchem_render(vars)
    else:
        print("ERROR: The function for rendering the input files associated with the %s program is absent. Please define it." % prog)
        print("Aborting ...")
        exit(5)

# Define the function that will render an input file based on its jinja template
def jinja_render(path_tpl_dir, tpl, path_rnd_dir, rnd, var):
  template_file_path = os.path.join(path_tpl_dir, tpl)
  print("  Template path:  ",template_file_path)
  
  rendered_file_path = os.path.join(path_rnd_dir, rnd)
  print("  Output path:    ",rendered_file_path)
  
  environment = jinja2.Environment(loader=jinja2.FileSystemLoader(path_tpl_dir))
  output_text = environment.get_template(tpl).render(var)
  
  #TODO: store the file content in a variable and write it later in abin_launcher.py
  with open(rendered_file_path, "w") as result_file:
      result_file.write(output_text)

def orca_render(vars):
    "blablabla"

def qchem_render(vars):
    "blobloblo"