################################################################################################################################################
##                                                             Scaling functions                                                              ##
##                                                                                                                                            ##
##                    This script contains the possible definition functions for the scale_index used in abin-launcher.py                     ##
################################################################################################################################################

import os

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
    
#! ATTENTION: All the functions defined below need to:
#! - receive three dictionaries (elements, config_prog_scaling_function and file_data) as arguments
#! - return an integer or a float (scale_index)
#! Otherwise, you will need to modify abin_launcher.py accordingly.
#! Additionnaly, their name will be called as is in the YAML config file, pertaining to the "scaling_function" key

def elec_power_scaling(elements:dict, config_prog_scaling_function:dict, file_data:dict):
    """Offers a power scaling option for the scale index, based on the total number of electrons in the molecule

    Parameters
    ----------
    elements : dict
        Content of AlexGustafsson's Mendeleev Table YAML file (found at https://github.com/AlexGustafsson/molecular-data).
    config_prog_scaling_function : dict
        Content of the "scaling_function" key, pertaining to the program key in the YAML main configuration file
    file_data : dict
        The extracted informations of the molecule file

    Returns
    -------
    scale_index : int
        Total number of electrons of the molecule
    
    Advice
    -------
    This function will look for an additional key called "power" in the YAML config file, pertaining to the "scaling_function" key in the corresponding program
    """

    power = config_prog_scaling_function["power"]

    exp_str_arr={1:"st", 2:"nd", 3:"rd"}
    print ('\nThe scale index will be defined as the %s%s power of the total number of electrons' % (power, ("th" if not power in exp_str_arr else exp_str_arr[power])))

    scale_index = (total_nb_elec(elements,file_data)**power)

    return scale_index
