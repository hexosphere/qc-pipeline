#!/usr/bin/python
# -*- coding: utf-8 -*-

import re

###
# Some important refs which helped to build this code:
# - https://sopython.com/canon/92/extract-text-from-a-file-between-two-markers/
# - https://docs.python.org/3/tutorial/errors.html
# - https://www.geeksforgeeks.org/python-extract-key-value-of-dictionary-in-variables/
# - https://book.pythontips.com/en/latest/ternary_operators.html
# - https://regex101.com/
###


def ev_to_cm1(ev: float) -> float:
    """Converts a value from eV to cm-1.

    Parameters
    ----------
    ev : float
        The value in eV we need to convert
    
    Returns
    -------
    cm : float
        The eV value converted to cm-1
    """

    cm = ev * 8065.6

    return cm

def get_states_list(file_content):
    """Parses the content of a qchem TDDFT calculation output file looking to build a list of the excited electronic states of the molecule. That list will contain their state number, multiplicity, energy and label.

    Parameters
    ----------
    file_content : list
        Content of the qchem output file
    
    Returns
    -------
    states_list : list
        A list of tuples of the form [[0, Multiplicity, Energy, Label], [1, Multiplicity, Energy, Label], [2, Multiplicity, Energy, Label], ...]
        The first element of each tuple is the state number, starting at 0
        Multiplicity corresponds to the first letter of the multiplicity of the state (ex : S for a singlet, T for a triplet)
        Energy is the energy of the state, in cm-1
        Label is the label of the state, in the form of multiplicity + number of that state of this multiplicity (ex : T1 for the first triplet, S3 for the third singlet)

    Advice
    -------
        This function makes heavy use of regex (Regular Expressions). If you're unfamiliar with them, please consult https://docs.python.org/3/library/re.html for information
    """

    # Initialization of the variables

    section_found = False
    section_in = False
    states_list = [(0, 'Singlet', 0.0, 'S0')] # Starts with information about the ground state
    curr_state = -1
    curr_energy = -1
    exc_state = -1
    exc_energy = -1
    cpt_triplet = 0
    cpt_singlet = 0
    multiplicity = ""
    first_letter = ""
    search_energy = True

    # Define the START and END expression patterns of the "TDDFT/TDA Excitation Energies" section of the output file

    section_rx = {
        'section_start': re.compile(
            r'TDDFT/TDA Excitation Energies'),
        'dashes': re.compile(
            r'----------------------------------------')
    }

    # Define the expression patterns for the lines containing information about the states

    states_rx = {
        # Pattern for finding lines looking like 'Excited state   1: excitation energy (eV) =    4.6445'
        'state_energy': re.compile(
            r'^Excited state\s+(?P<state>\d+): excitation energy \(eV\) =\s+(?P<energy>[-+]?\d*\.\d+|\d+)$'),
        # Pattern for finding lines looking like '    Multiplicity: Triplet'
        'state_mp': re.compile(
            r'^\s*Multiplicity: (?P<mplicity>\w+)$')
    }

    # Parse the source file to get the information and build the states list

    for line in file_content:
        if not section_found:
            if section_rx['section_start'].match(line):
                # The section has been found
                section_found = True
            continue
        if not section_in and section_rx['dashes'].match(line):
            # The section starts now
            section_in = True
            continue
        if section_in and section_rx['dashes'].match(line):
            # End of the section
            break
        
        # Process the section lines
        else:
            # First, look for the excited energy of the state
            if search_energy:
                m = states_rx['state_energy'].match(line)
                if m is not None: # m will be None if the line does not match the regex
                    exc_state = int(m.group("state"))
                    exc_energy = float(m.group("energy"))
                    if exc_state < 0:
                        raise ValueError("Excited state illegal value (<0)")
                    if exc_energy < 0:
                        raise ValueError("Excitation energy illegal value (<0)")
                    curr_state = exc_state #! Why?
                    curr_energy = exc_energy
                    search_energy = False
                    continue
            # Second, look for the corresponding state multiplicity
            else:
                m = states_rx['state_mp'].match(line)
                if m is not None:
                    multiplicity = m.group("mplicity")
                    cpt = -1
                    if multiplicity == "Triplet":
                        first_letter = "T"
                        cpt_triplet += 1
                        cpt = cpt_triplet
                    elif multiplicity == "Singlet":
                        first_letter = "S"
                        cpt_singlet += 1
                        cpt = cpt_singlet
                    else:
                        raise ValueError("Multiplicity unknown value")
                    search_energy = True
                    # Format: (state_number, state_multiplicity, energy value (cm-1), label)
                    states_list.append((curr_state, multiplicity, ev_to_cm1(curr_energy), (first_letter + str(cpt))))
                    continue

    return states_list


def get_coupling_list(file_content):
    """Parses the content of a qchem TDDFT calculation output file looking to build a list of the spin-orbit couplings of the molecule. That list will contain the two states numbers and their coupling value.

    Parameters
    ----------
    file_content : list
        Content of the qchem output file
    
    Returns
    -------
    soc_list : list
        List of tuples of the form [[State0, State1, SOC_0-1], [State0, State2, SOC_0-2], [State1, State2, SOC_1-2], ...]
        The first two elements of each tuple are the number of the two states and the third one is the value of the spin-orbit coupling between them (in cm-1)

    Advice
    -------
        This function makes heavy use of regex (Regular Expressions). If you're unfamiliar with them, please consult https://docs.python.org/3/library/re.html for information
    """

    # Initialization of the variables

    section_found = False
    section_in = False
    soc_list = []
    state_1 = ''
    state_2 = ''
    value = 0.0
    tpl = None   # Tuple that will look like "(state_1, state_2, value)"
    
    # Define the START and END expression patterns of the "SPIN-ORBIT COUPLING" section of the output file

    section_rx = {
        # Pattern for finding lines looking like '*********SPIN-ORBIT COUPLING JOB BEGINS HERE*********'
        'section_start': re.compile(
            r'^\*+SPIN-ORBIT COUPLING JOB BEGINS HERE\*+$'),
        # Pattern for finding lines looking like '            *********SOC CODE ENDS HERE*********'
        'section_end': re.compile(
            r'^\*+SOC CODE ENDS HERE\*+$')
    }

    # Define the expression patterns for the lines containing information about the SOC
    
    soc_rx = {
        # Pattern for finding lines looking like 'Total SOC between the singlet ground state and excited triplet states:'
        'ground_to_triplets': re.compile(
            r'^Total SOC between the singlet ground state and excited triplet states:$'),
        # Pattern for finding lines looking like 'Total SOC between the S1 state and excited triplet states:'
        'between_excited_states': re.compile(
            r'^Total SOC between the (?P<s_key>[A-Z]\d) state and excited triplet states:$'),
        # Pattern for finding lines looking like 'T2      76.018382    cm-1'
        'soc_value': re.compile(
            r'^(?P<soc_key>T\d)\s+(?P<soc_value>\d+\.?\d*)\s+cm-1$')
    }

    # Parse the source file to get the information and build the SOC list

    for line in file_content:
        if not section_found:
            if section_rx['section_start'].match(line):
                # The section has been found
                section_found = True
                section_in = True #! Needed?
            continue
        if section_in and section_rx['section_end'].match(line):
            # End of the section
            break

        # Process the section lines
        else:
            # Compare each line to all the soc_rx expressions
            for key, rx in soc_rx.items():
                m = rx.match(line)
                if m is not None: # m will be None if the line does not match one of the regex defined in soc_rx
                    # In this case, all soc_rx expressions are mutually exclusive
                    if key == 'ground_to_triplets':
                        state_1 = 'S0' # The ground state label is S0 by convention
                    elif key == 'between_excited_states':
                        state_1 = m.group('s_key')
                    elif key == 'soc_value':
                        state_2 = m.group('soc_key')
                        value = float(m.group('soc_value'))
                        tpl = (state_1, state_2, value)
                    break #! Why?
            if tpl is not None:
                soc_list.append(tpl)
                tpl = None
                continue

    # Rewrite soc_list by replacing all state labels by their state number

    states_list = get_states_list(file_content) # Needed to get the correspondence between state number and state label
    
    for idx, soc in enumerate(soc_list):
        soc_list[idx] = (
            # Filter the states_list, looking for the state corresponding to the label (see https://stackoverflow.com/questions/3013449/list-comprehension-vs-lambda-filter for reference)
            int([ x for x in states_list if x[3] == soc[0] ][0][0]),
            int([ x for x in states_list if x[3] == soc[1] ][0][0]),
            soc[2]
        )

    return soc_list


def get_momdip_list (file_content):
    """Parses the content of a qchem TDDFT calculation output file looking to build a list of the transition dipole moments between the electronic excited states of the molecule. That list will contain the two states numbers and the dipole value of their transition.

    Parameters
    ----------
    file_content : list
        Content of the qchem output file
    
    Returns
    -------
    moment_list : list
        List of tuples of the form [[State0, State1, MomDip0-1], [State0, State2, MomDip0-2], [State1, State2, MomDip1-2], ...]
        The first two elements of each tuple are the number of the two states and the third one is the value of the transition dipole moment associated with the transition between them (in atomic units)

    Advice
    -------
        This function makes heavy use of regex (Regular Expressions). If you're unfamiliar with them, please consult https://docs.python.org/3/library/re.html for information
    """

    # Initialization of the variables

    section_found = False
    section_in = False
    moment_list = []
    state_1 = ''
    state_2 = ''
    value = 0.0
    tpl = None

    # Define the START and END expression patterns of the "STATE-TO-STATE TRANSITION MOMENTS" section of the output file

    section_rx = {
        # Pattern for finding lines looking like '                    STATE-TO-STATE TRANSITION MOMENTS'
        'section_start': re.compile(
            r'^STATE-TO-STATE TRANSITION MOMENTS$'),
        # Pattern for finding lines looking like '                    END OF TRANSITION MOMENT CALCULATION'
        'section_end': re.compile(
            r'^END OF TRANSITION MOMENT CALCULATION$')
    }

    # Define the expression patterns for the lines containing information about the dipole moments

    moment_rx = {
        # Pattern for finding lines looking like '    1    2   0.001414  -0.001456   0.004860   1.240659E-10'
        'moment': re.compile(
            r'^(?P<mom_key1>\d+)\s+(?P<mom_key2>\d+)(\s+-?\d\.\d+){3}\s+(?P<strength>(\d|\d\.\d+|\d\.\d+E[-+]\d{2}))$')
    }

    # Parse the source file to get the information and build the dipole moments list

    for line in file_content:
        if not section_found:
            if section_rx['section_start'].match(line):
                # The section has been found
                section_found = True
                section_in = True #! Needed?
            continue
        if section_in and section_rx['section_end'].match(line):
            # End of the section
            break

        # Process the section lines
        else:
            # Compare each line to all the moment_rx expressions (there's only one for now, but that might change)
            for key, rx in moment_rx.items():
                m = rx.match(line)
                if m is not None: # m will be None if the line does not match one of the regex defined in moment_rx
                    if key == 'moment':
                        state_1 = m.group('mom_key1')
                        state_2 = m.group('mom_key2')
                        value = float(m.group('strength'))
                        tpl = (state_1, state_2, value)
                    break
            if tpl is not None:
                moment_list.append(tpl)
                tpl = None
                continue
    
    return moment_list

