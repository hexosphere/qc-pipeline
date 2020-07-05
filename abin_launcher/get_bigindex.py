################################################################################################################################################
##                                                            Big Index Definitions                                                           ##
##                                                                                                                                            ##
##                     This script contains the possible definition functions for the big index used in abin-launcher.py                      ##
################################################################################################################################################

import os
import yaml

# 1st definition: total number of electrons

def total_nb_elec(code_dir,file_data:dict):

    # Loading AlexGustafsson's Mendeleev Table (found at https://github.com/AlexGustafsson/molecular-data)

    print("\nLoading AlexGustafsson's Mendeleev Table ...", end="")
    with open(os.path.join(code_dir,'elements.yml'), 'r') as f_elements:
      elements = yaml.load(f_elements, Loader=yaml.FullLoader)
    print('%18s' % "[ DONE ]")

    # Definition of the function that can fecth the number of electrons associated with each element in Gustafsson's table

    def getNbElecFromMdlvTbl(symbol:str, mdlvTbl:dict) -> int:
      for elm in mdlvTbl:
        if (elm['symbol'] == symbol):
          return elm['number']

    # BIGINDEX definition as the total number of electrons in the molecule

    total_elec = 0

    print("")
    print(''.center(68, '-'))
    print ("{:<12} {:<16} {:<18} {:<22}".format('Atom Type','Atomic Number','Number of atoms','Number of electrons'))
    print(''.center(68, '-'))
    for atom,nb_atom in file_data['elm_list'].items():
      atomic_number = getNbElecFromMdlvTbl(atom,elements)
      subtotal_elec = nb_atom * atomic_number
      print ("{:<12} {:<16} {:<18} {:<22}".format(atom, atomic_number, nb_atom, subtotal_elec))
      total_elec += subtotal_elec
    print(''.center(68, '-'))
    print ("{:<29} {:<18} {:<22}".format('Total',file_data['#atoms'],total_elec))
    print(''.center(68, '-'))

    bigindex = total_elec

    return bigindex