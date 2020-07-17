################################################################################################################################################
##                                                             Scaling functions                                                              ##
##                                                                                                                                            ##
##                    This script contains the possible definition functions for the scale_index used in abin-launcher.py                     ##
################################################################################################################################################

import os

#! ATTENTION: All the functions defined below need to:
#! - receive two dictionaries (elements and file_data) as arguments
#! - return an integer or a float (that will act as the scale_index)
#! Otherwise, you will need to modify abin_launcher.py accordingly.
#! Additionnaly, their name will be called as is in the YAML config file, pertaining to the "scaling_function" key (total_nb_elec, total_nb_atoms, etc)

"""  
file_data is considered to follow the following pattern: {'nb_atoms': int; 'chemical_formula':{dict}; 'atomic_coordinates':[list]} (as it should have been given by the mol_scan functions)
If this is not the case, the functions below will need to be modified accordingly.
"""

def total_nb_elec(elements:dict,file_data:dict):
    """Calculates the total number of electrons in a molecule

    Parameters
    ----------
    elements : dict
        Content of AlexGustafsson's Mendeleev Table YAML file (found at https://github.com/AlexGustafsson/molecular-data).
    file_data : dict
        The extracted informations of the molecule file

    Returns
    -------
    total_elec : int
        Total number of electrons in the molecule
    
    Advice
    -------
    Do not alter the elements.yml file from AlexGustafsson as it will be used as is.
    """

    # Definition of the function that can fecth the number of electrons associated with each element in Gustafsson's table

    def get_nb_elec_for_element(symbol:str, elements:dict) -> int:
      for elm in elements:
        if (elm['symbol'] == symbol):
          return elm['number']

    # Calculating the total number of electrons in the molecule

    total_elec = 0

    print("")
    print(''.center(68, '-'))
    print ("{:<12} {:<16} {:<18} {:<22}".format('Atom Type','Atomic Number','Number of atoms','Number of electrons'))
    print(''.center(68, '-'))
    for atom,nb_atom in file_data['chemical_formula'].items():
      atomic_number = get_nb_elec_for_element(atom,elements)
      subtotal_elec = nb_atom * atomic_number
      print ("{:<12} {:<16} {:<18} {:<22}".format(atom, atomic_number, nb_atom, subtotal_elec))
      total_elec += subtotal_elec
    print(''.center(68, '-'))
    print ("{:<29} {:<18} {:<22}".format('Total',file_data['nb_atoms'],total_elec))
    print(''.center(68, '-'))

    return total_elec

def total_nb_atoms(elements:dict,file_data:dict):
    """Returns the total number of atoms in a molecule

    Parameters
    ----------
    elements : dict
        Content of AlexGustafsson's Mendeleev Table YAML file (found at https://github.com/AlexGustafsson/molecular-data).
        Unused for this particular function.
    file_data : dict
        The extracted informations of the molecule file

    Returns
    -------
    total_atoms : int
        Total number of atoms in the molecule    
    """

    # Returns the total number of atoms in the molecule

    total_atoms = file_data['nb_atoms']

    print("")
    print("Total number of atoms in the molecule : ",total_atoms)

    return total_atoms
