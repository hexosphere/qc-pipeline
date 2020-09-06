#!/usr/bin/python
# -*- coding: utf-8 -*-

import re

###
# Some important refs which helped me to build this code:
# - https://sopython.com/canon/92/extract-text-from-a-file-between-two-markers/
# - https://docs.python.org/3/tutorial/errors.html
# - https://www.geeksforgeeks.org/python-extract-key-value-of-dictionary-in-variables/
# - https://book.pythontips.com/en/latest/ternary_operators.html
# - https://regex101.com/
###


def ev_to_cm1(ev: float) -> float:
    return ev * 8065.6


# input: contenu du fichier qchem à parser
# output: list de list format [(1, 'S', 0.0, 'S0')] // n°etat; multiplicity; energy (cm-1); label (combination of state_n°-1 & multiplicity)
def get_states_list (file_content):
    # Init useful vars
    section_found = False
    section_in = False
    states_list = [(1, 'S', 0.0, 'S0')]
    curr_state = -1
    curr_energy = -1
    exc_state = -1
    exc_energy = -1
    cpt_triplet = 0
    cpt_singlet = 0
    multiplicity = ""
    search_multiplicity = False
    # Those expressions are Regex - For more information, see https://docs.python.org/3/library/re.html
    section_rx = {
        'section_start': re.compile(
            r'TDDFT/TDA Excitation Energies'),
        'dashes': re.compile(
            r'----------------------------------------')
    }
    states_rx = {
        # Pattern for finding lines looking like 'Excited state   1: excitation energy (eV) =    4.6445'
        'state_energy': re.compile(
            r'^Excited state\s+(?P<state>\d+): excitation energy \(eV\) =\s+(?P<energy>[-+]?\d*\.\d+|\d+)$'),
        # Pattern for finding lines looking like '    Multiplicity: Triplet'
        'state_mp': re.compile(
            r'^\s*Multiplicity: (?P<mplicity>\w+)$')
    }
    # Process source file for State definitions
    for line in file_content:
        if not section_found:
            if section_rx['section_start'].match(line):
                # the specific table section has been found
                section_found = True
            continue
        if not section_in and section_rx['dashes'].match(line):
            # Table starts onward
            section_in = True
            continue
        if section_in and section_rx['dashes'].match(line):
            # End of table found
            break
        else:
            # Process in-between lines
            # We're not searching the multiplicity if we didn't found the excited energy yet
            if not search_multiplicity:
                m = states_rx['state_energy'].match(line)
                if m is not None:
                    exc_state = int(m.group("state"))
                    exc_energy = float(m.group("energy"))
                    if exc_state < 0:
                        raise ValueError("Excited state illegal value (<0)")
                    if exc_energy < 0:
                        raise ValueError("Excitation energy illegal value (<0)")
                    curr_state = exc_state
                    curr_energy = exc_energy
                    search_multiplicity = True
                    continue
            else:
                m = states_rx['state_mp'].match(line)
                if m is not None:
                    multiplicity = m.group("mplicity")
                    cpt = -1
                    if multiplicity == "Triplet":
                        multiplicity = "T"
                        cpt_triplet += 1
                        cpt = cpt_triplet
                    elif multiplicity == "Singlet":
                        multiplicity = "S"
                        cpt_singlet += 1
                        cpt = cpt_singlet
                    else:
                        raise ValueError("Multiplicity unknown value")
                    search_multiplicity = False
                    # (#state, multiplicity, cm-1, multiplicity_order)
                    # #State +1 because of S0 being artificially added at pos.0
                    states_list.append((curr_state + 1, multiplicity, ev_to_cm1(curr_energy), (multiplicity + str(cpt))))
                    continue
    return states_list


def get_soc_list (file_content):
    # Init useful vars
    section_found = False
    section_in = False
    # Those expressions are Regex - For more information, see https://docs.python.org/3/library/re.html
    section_rx = {
        # Pattern for finding lines looking like '*********SPIN-ORBIT COUPLING JOB BEGINS HERE*********'
        'section_start': re.compile(
            r'^\*+SPIN-ORBIT COUPLING JOB BEGINS HERE\*+$'),
        # Pattern for finding lines looking like '            *********SOC CODE ENDS HERE*********'
        'section_end': re.compile(
            r'^\*+SOC CODE ENDS HERE\*+$')
    }
    soc_rx = {
        'ground_to_triplets': re.compile(
            r'^Total SOC between the singlet ground state and excited triplet states:$'),
        # Pattern for finding lines looking like 'Total SOC between the T1 state and excited triplet states:'
        'triplets_to_triplets': re.compile(
            r'^Total SOC between the (?P<tp_key>T\d) state and excited triplet states:$'),
        # Pattern for finding lines looking like 'Total SOC between the S1 state and excited triplet states:'
        'singlets_to_triplets': re.compile(
            r'^Total SOC between the (?P<sg_key>S\d) state and excited triplet states:$'),
        #TODO - Check to fusion both key lines in one (seems the letter or the fact it's Triplet or Singlet doesn't matter here)
        #TODO - could replace Singlet/Triplet lines to be more general. ex: Quintlet ...
        # Pattern for finding lines looking like 'Total SOC between the S1 state and excited triplet states:'
        #'between_excited_states': re.compile(
        #    r'^Total SOC between the (?P<key>[A-Z]\d) state and excited triplet states:$'),
        # Pattern for finding lines looking like 'T2      76.018382    cm-1'
        'soc_value': re.compile(
            r'^(?P<soc_key>T\d)\s+(?P<soc_value>\d+\.?\d*)\s+cm-1$')
    }
    soc_list = []   # List of Tuple : [(state_1, state_2, value), (state_1, state_2, value), ...]
    prim_key = ''
    sub_key = ''
    value = 0.0
    tpl = None   # Tuple that will look like "(prim_key, sub_key, value)"

    # Process source file for SOC values (cm-1 values)
    for line in file_content:
        if not section_found:
            if section_rx['section_start'].match(line):
                # the specific section has been found
                section_found = True
                section_in = True
            continue
        if section_in and section_rx['section_end'].match(line):
            # End of section found
            break
        else:
            # Process lines
            # For each line, we've to test all soc_rx expressions
            for key, rx in soc_rx.items():
                m = rx.match(line)
                if m is not None:
                    # Match found >> Do what you have to, then break the loop
                    # >> In this case, all soc_rx expressions are mutually exclusive
                    if key == 'ground_to_triplets':
                        prim_key = 'S0'
                    elif key == 'triplets_to_triplets':
                        prim_key = m.group('tp_key')
                    elif key == 'singlets_to_triplets':
                        prim_key = m.group('sg_key')
                    #TODO - add here corresponding code for the modification related to "between_excited_states"
                    elif key == 'soc_value':
                        sub_key = m.group('soc_key')
                        value = float(m.group('soc_value'))
                        tpl = (prim_key, sub_key, value)
                    break
            if tpl is not None:
                soc_list.append(tpl)
                tpl = None
                continue
    return soc_list


def get_momdip_list (file_content):
    section_found = False
    section_in = False
    # Those expressions are Regex - For more information, see https://docs.python.org/3/library/re.html
    section_rx = {
        # Pattern for finding lines looking like '                    STATE-TO-STATE TRANSITION MOMENTS'
        'section_start': re.compile(
            r'^STATE-TO-STATE TRANSITION MOMENTS$'),
        # Pattern for finding lines looking like '                    END OF TRANSITION MOMENT CALCULATION'
        'section_end': re.compile(
            r'^END OF TRANSITION MOMEMT CALCULATION$')
    }
    moment_rx = {
        # Fortunately the 'Electron Dipole Moments' table doesn't have the same line syntax that tables we're seeking for
        # Pattern for finding lines looking like '    1    2   0.001414  -0.001456   0.004860   1.240659E-10'
        'moment': re.compile(
            r'^(?P<mom_key1>\d+)\s+(?P<mom_key2>\d+)(\s+-?\d\.\d+){3}\s+(?P<strength>(\d|\d\.\d+|\d\.\d+E[-+]\d{2}))$')
    }
    moment_list = []
    prim_key = ''
    sub_key = ''
    value = 0.0
    tpl = None

    # Process source file for MOMENT values (a.u. values)
    for line in file_content:
        if not section_found:
            if section_rx['section_start'].match(line):
                # the specific section has been found
                section_found = True
                section_in = True
            continue
        if section_in and section_rx['section_end'].match(line):
            # End of section found
            break
        else:
            # Process lines
            # For each line, we've to test all moment_rx expressions
            for key, rx in moment_rx.items():
                m = rx.match(line)
                if m is not None:
                    # Match found >> Do what you have to, then break the loop
                    # >> In this case, all moment_rx expressions are mutually exclusive
                    if key == 'moment':
                        prim_key = m.group('mom_key1')
                        sub_key = m.group('mom_key2')
                        value = float(m.group('strength'))
                        tpl = (prim_key, sub_key, value)
                    break
            if tpl is not None:
                moment_list.append(tpl)
                tpl = None
                continue
    
    return moment_list

