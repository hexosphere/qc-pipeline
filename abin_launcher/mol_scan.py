################################################################################################################################################
##                                                                Molecule Scanner                                                            ##
##                                                                                                                                            ##
##             This script contains the different functions that will scan the content of a molecule file according to its format             ##
################################################################################################################################################

import re
import errors

#! ATTENTION: All the functions defined below need to:
#! - be called fmt_scan, where fmt is the name of the format of the molecule file as it will be given in the command line (stored in the mol_fmt variable in abin_launcher.py) 
#! - receive a list (mol_content) as argument
#! - return a dictionary (file_data), following the pattern {'chemical_formula':{}, 'atomic_coordinates':[]}
#!   * The first key of file_data is a dictionary stating the chemical formula of the molecule in the form {'atom type 1':number of type 1 atoms, 'atom type 2':number of type 2 atoms, ...}, ex: {'Si':17, 'O':4, 'H':28}
#!   * The second key is a list containing all atomic coordinates, as they will be used in the input file of the ab initio program
#! If a problem arises when scanning the molecule file, a MoleculeError exception should be raised with a proper error message (see errors.py for more informations)
#! Otherwise, you will need to modify abin_launcher.py accordingly.

def xyz_scan(mol_content:list):
    """Scan the content of an xyz file and extract the chemical formula and atomic coordinates of the molecule

    Parameters
    ----------
    mol_content : list
        Content of the xyz file

    Returns
    -------
    file_data : dict
        The extracted informations of the xyz file, following the pattern {'chemical_formula':{}, 'atomic_coordinates':[]}
    """

    file_data = {'chemical_formula':{}, 'atomic_coordinates':[]}
    
    # Determining the number of atoms (first line of the xyz file)
    
    nb_atoms = int(mol_content[0])

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
    
    if checksum_nlines != nb_atoms:
      raise errors.AbinError("ERROR: Number of atoms lines (%s) doesn't match the number of atoms mentioned in the first line of the .xyz file (%s) !" % (checksum_nlines, nb_atoms))
  
    return file_data