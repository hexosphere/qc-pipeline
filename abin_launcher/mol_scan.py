################################################################################################################################################
##                                                                Molecule Scanner                                                            ##
##                                                                                                                                            ##
##             This script contains the different functions that will scan the content of a molecule file according to its format             ##
################################################################################################################################################

import re

#! ATTENTION: All the functions defined below need to:
#! - be called fmt_scan, where fmt is the name of the format of the molecule file as it will be given in the command line (stored in the mol_fmt variable in abin_launcher.py) 
#! - receive a list (mol_content) and a dictionary (model_file_data) as arguments
#! - return a dictionary (file_data), following the pattern from model_file_data
#! Otherwise, you will need to modify abin_launcher.py accordingly.

def xyz_scan(mol_content:list,model_file_data:dict):
    """Scan the content of an xyz file and extract the chemical formula and atomic coordinates of the molecule

    Parameters
    ----------
    mol_content : list
        Content of the xyz file
    model_file_data : dict
        The model dictionary that will be used to store the informations of this file
        model_file_data = {'nb_atoms': 0, 'chemical_formula':{}, 'atomic_coordinates':[]}

    Returns
    -------
    file_data : dict
        The extracted informations of the xyz file, following the pattern from model_file_data
    """

    file_data = model_file_data
    
    # Determining the number of atoms (first line of the xyz file)
    
    file_data['nb_atoms'] = mol_content[0]

    # Scanning the content of the XYZ file to determine the chemical formula and atomic coordinates of the molecule
      
    lines_rx = {
        # Pattern for finding lines looking like 'Si        -0.31438        1.89081        0.00000' (this is a regex, for more information, see https://docs.python.org/3/library/re.html)
        'atomLine': re.compile(
            r'^\s{0,4}(?P<atomSymbol>[a-zA-Z]{0,3})\s+[-]?\d+\.\d+\s+[-]?\d+\.\d+\s+[-]?\d+\.\d+$')
    }
    
    checksum_nlines = 0                                                 # This variable will be used to check if the number of coordinate lines matches the number of atoms of the molecule 
    
    for line in mol_content[2:]:                                        # We only start at the 3rd line because the first two won't contain any coordinates
      m = lines_rx['atomLine'].match(line)
      if m is not None:                                                 # We only care if the line looks like an atom coordinates
        checksum_nlines += 1
        file_data['atomic_coordinates'].append(line)                    # All coordinates will be stored in this variable to be rendered in the input file later on
        if m.group("atomSymbol") not in file_data['chemical_formula']:
          file_data['chemical_formula'][m.group("atomSymbol")] = 1
        else:
          file_data['chemical_formula'][m.group("atomSymbol")] += 1
                
    # Check if the number of lines matches the number of atoms defined in the first line of the .xyz file
    
    if checksum_nlines != int(file_data['nb_atoms']):
      print("\n\nERROR: Number of atoms lines (%s) doesn't match the number of atoms mentioned in the first line of the .xyz file (%s) !" % (checksum_nlines, int(file_data['#atoms'])))
      print("Skipping this molecule...")
      file_data = None
  
    return file_data