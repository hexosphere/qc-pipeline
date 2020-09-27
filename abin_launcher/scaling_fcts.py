################################################################################################################################################
##                                                             Scaling functions                                                              ##
##                                                                                                                                            ##
##                    This script contains the possible definition functions for the scale_index used in abin-launcher.py                     ##
################################################################################################################################################

import errors

#! ATTENTION: All the functions defined below need to:
#! - receive two dictionaries (mendeleev and file_data) as arguments
#! - return an integer or a float (that will act as the scale_index)
#! Otherwise, you will need to modify abin_launcher.py accordingly.
#! Additionnaly, their name will be called as is in the YAML clusters file, pertaining to the "scaling_function" key (total_nb_elec, total_nb_atoms, etc)

"""  
file_data is considered to follow the following pattern: {'chemical_formula':{dict}; 'atomic_coordinates':[list]} (as it should have been given by the mol_scan functions)
If this is not the case, the functions below will need to be modified accordingly.
"""

def total_nb_elec(mendeleev:dict,file_data:dict):
    """Calculates the total number of electrons in a molecule

    Parameters
    ----------
    mendeleev : dict
        Content of AlexGustafsson's Mendeleev Table YAML file (found at https://github.com/AlexGustafsson/molecular-data).
    file_data : dict
        The extracted informations of the molecule file

    Returns
    -------
    total_elec : int
        Total number of electrons in the molecule
    
    Advice
    -------
    Do not alter the mendeleev.yml file from AlexGustafsson as it will be used as is.
    """

    # Definition of the function that can fetch the number of electrons associated with each element in Gustafsson's table

    def get_nb_elec_for_element(symbol:str, mendeleev:dict) -> int:
        """Return the number of electrons for a specific element

        Parameters
        ----------
        symbol : str
            The atom symbol of the element
        mendeleev : dict
            Content of AlexGustafsson's Mendeleev Table YAML file (found at https://github.com/AlexGustafsson/molecular-data).

        Returns
        -------
        nb_elec : int
           Number of electrons
        
        Advice
        -------
        Do not alter the mendeleev.yml file from AlexGustafsson as it will be used as is.
        """

        nb_elec = 0

        # Scan the mendeleev table and get the atomic number of our atom
        for element in mendeleev:
          if (element['symbol'] == symbol):
            nb_elec = element['number']
        
        if nb_elec == 0:
          raise errors.AbinError ("ERROR: There is no atomic number defined for %s in AlexGustafsson's Mendeleev Table YAML file (mendeleev.yml)" % symbol)

        return nb_elec

    # Calculating the total number of electrons in the molecule

    total_elec = 0

    print("")
    print(''.center(68, '-'))
    print("{:<12} {:<16} {:<18} {:<22}".format('Atom Type','Atomic Number','Number of atoms','Number of electrons'))
    print(''.center(68, '-'))
    for atom,nb_atom in file_data['chemical_formula'].items():
      atomic_number = get_nb_elec_for_element(atom,mendeleev)
      subtotal_elec = nb_atom * atomic_number
      print("{:<12} {:<16} {:<18} {:<22}".format(atom, atomic_number, nb_atom, subtotal_elec))
      total_elec += subtotal_elec
    print(''.center(68, '-'))
    print("{:<29} {:<18} {:<22}".format('Total',sum(file_data['chemical_formula'].values()),total_elec))
    print(''.center(68, '-'))

    return total_elec

def total_nb_atoms(mendeleev:dict,file_data:dict):
    """Returns the total number of atoms in a molecule

    Parameters
    ----------
    mendeleev : dict
        Content of AlexGustafsson's Mendeleev Table YAML file (found at https://github.com/AlexGustafsson/molecular-data).
        Unused for this particular function.
    file_data : dict
        The extracted informations of the molecule file

    Returns
    -------
    total_atoms : int
        Total number of atoms in the molecule    
    """

    # Returns the total number of atoms in the molecule by summing all the values given in the chemical_formula dictionary

    total_atoms = sum(file_data['chemical_formula'].values())

    print("")
    print("Total number of atoms in the molecule: ",total_atoms)

    return total_atoms
