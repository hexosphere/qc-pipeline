#!/usr/bin/python
# -*- coding: utf-8 -*-

import argparse
import pprint
import os
import sys
import re
import numpy as np
from datetime import datetime, date, time
import math

###
# Some important refs which helped me to build this code:
# - https://sopython.com/canon/92/extract-text-from-a-file-between-two-markers/
# - https://docs.python.org/3/tutorial/errors.html
# - https://docs.python.org/3/tutorial/inputoutput.html
# - https://docs.python.org/3/library/datetime.html
# - https://docs.python.org/fr/3/library/pprint.html
# - https://realpython.com/read-write-files-python/#opening-and-closing-a-file-in-python
# - https://www.geeksforgeeks.org/python-extract-key-value-of-dictionary-in-variables/
# - https://www.geeksforgeeks.org/formatted-text-linux-terminal-using-python/
# - https://stackoverflow.com/questions/4131864/use-a-string-to-call-function-in-python
# - https://stackoverflow.com/questions/4246000/how-to-call-python-functions-dynamically
# - https://book.pythontips.com/en/latest/ternary_operators.html
# - https://www.science-emergence.com/Articles/How-to-create-and-initialize-a-matrix-in-python-using-numpy-/
# - https://docs.scipy.org/doc/numpy-1.15.0/reference/generated/numpy.format_float_scientific.html
# - https://regex101.com/
###

###
# DEBUG switch
###
debug = False

###
# LATEX switch
###
latex = True


class Error(Exception):
    """Base class for exceptions in this module."""
    pass


class InputError(Error):
    """Exception raised for errors in the input.

    Attributes:
        expression -- input expression in which the error occurred
        message -- explanation of the error
    """

    def __init__(self, expression, message):
        self.expression = expression
        self.message = message


# Round 'x' to the nearest greater multiple of 'base'
def roundup(x, base=5) -> int:
    return int(base * math.ceil(x/base))


# Pretty print a structure
def print_struct(struct, header=""):
    print('\n', header)
    pp = pprint.PrettyPrinter(depth=3, indent=2)
    pp.pprint(struct)
    print('')


# Pretty print a matrix
def print_matrix(matrix, header=""):
    print('\n', header)
    format_row = "{:>20}" * len(matrix)
    for row in matrix:
        print(format_row.format(*row))
    print('')


# Write table to file dispatcher - Call the appropriate function based on 'tablename'
def write_table(filename, tablename, table):
    if debug:
        print_struct(table, '== '+tablename+' ==')
    if filename == "":
        raise InputError("filename", "Empty value")
    if tablename not in ('etats', 'mime', 'momdip'):
        raise InputError("tablename", "Unknown value")
    if len(table) < 9:
        raise InputError("table", "Table illegal size (<9)")
    if debug:
        filename = filename + "_" + datetime.strftime(datetime.now(), "%Y-%m-%d-%H-%M-%S")
    with open(filename, "w") as f:
        str_fmt = "\nWriting %s to file: %" + str(roundup(len(filename), 10)) + "s"
        print(str_fmt % (filename, filename), end='')
        # function name dynamically built based on 'tablename' content
        write_fct = "write_" + tablename
        eval(write_fct)(table, f)
        print("%10s" % "[ OK ]\n")
    if debug:
        with open(filename, "r") as f:
            sp = "=" * 10
            print("File content:\n%s\n%s\n%s" % (sp, f.read(), sp))


# Format a State list to what it should be for the 'etats' file (or print if no descriptor is given)
# Params:
# state_list: Tuple list formatted like: [ (#state, multiplicity, eV, state_order), ... ]
# fd: File Descriptor of the file into which print out the table; None to print out to stdout
def write_etats(state_list, fd):
    for state in state_list:
        print("%d %s" % (state[0], state[1]), file=fd)


def write_etats_latex(tablename: str, state_list):
    def ev_to_str(ev: float) -> str:
        return "{:,.4f}".format(ev).replace(',', ' ')

    def cm1_to_str(cm1: float) -> str:
        return "{:,.2f}".format(cm1).replace(',', ' ')

    def nm_to_str(nm: float) -> str:
        return "{:,.2f}".format(nm).replace(',', ' ')

    def get_full_name_of_multiplicity(short_mp: str) -> str:
        if short_mp == 'S':
            return "Singulet"
        elif short_mp == 'T':
            return 'Triplet'
        else:
            raise ValueError("Multiplicity not known", "multiplicity: " + short_mp)

    filename = molecule_dirpath + molecule_name + "_" + tablename
    if debug:
        filename += "_" + datetime.strftime(datetime.now(), "%Y-%m-%d-%H-%M-%S")
    filename += '.tex'
    with open(filename, "w") as f:
        str_fmt = "\nWriting %s to file: %" + str(roundup(len(filename), 10)) + "s"
        print(str_fmt % (filename, filename), end='')
        tab_begin = '\\begin{tabular}{'+('|c' * 6) + '|}'
        tab_header = r'\# & Multiplicité & Etiquette & Energie (eV) & Energie (cm\up{-1}) & Energie (nm) \\'
        tab_end = '\\end{tabular}'
        tab_separator = "\\hline"
        tab_first_line = "0 & Singulet & S0 & - & - & - \\\\"
        print(tab_begin, file=f)		
        print(tab_header, file=f)
        print(tab_separator, file=f)
        print(tab_first_line, file=f)
        # Skip S0 in the iteration on state_list
        for state in state_list[1:]:
            line = ("{} & " * 5) + "{} \\\\"
            print(line.format(
                str(state[0] - 1),                          # state index number -1, because the list starts at 1, not 0
                get_full_name_of_multiplicity(state[1]),    # state multiplicity in full letters
                state[3],                                   # state label
                ev_to_str(state[2]),                        # state eV
                cm1_to_str(ev_to_cm1(state[2])),            # state cm-1
                nm_to_str(cm1_to_nm(ev_to_cm1(state[2])))   # state in nm
            ), file=f)
        print(tab_end, file=f)
        print("%10s" % "[ OK ]\n")
    if debug:
        with open(filename, "r") as f:
            sp = "=" * 10
            print("File content:\n%s\n%s\n%s" % (sp, f.read(), sp))


# Format a SOC list to what it should be for the 'mime' file (or print if no descriptor is given)
def write_mime(soc_list, fd):
    # Quick init of a square 2D array
    mime_mtx = np.zeros((len(states_list), len(states_list)))
    if debug:
        print_matrix(mime_mtx, "== mime_mtx (zeroed) ==")
    for soc in soc_list:
        k1 = soc[0] - 1
        k2 = soc[1] - 1
        val = soc[2]
        mime_mtx[k1][k2] = val
    if debug:
        print_matrix(mime_mtx, "== mime_mtx (completed) ==")
    for row in mime_mtx:
        for val in row:
            print(np.format_float_scientific(val, precision=7, unique=False), end="\t", file=fd)
        # Splitting rows by going at new line
        print('', file=fd)


def write_mime_latex(tablename: str, state_list, soc_list):
    # Quick init of a square 2D array
    mime_mtx = np.zeros((len(state_list), len(state_list)))
    if debug:
        print_matrix(mime_mtx, "== mime_mtx (zeroed) ==")
    for soc in soc_list:
        k1 = soc[0] - 1
        k2 = soc[1] - 1
        val = soc[2]
        mime_mtx[k1][k2] = val
    filename = molecule_dirpath + molecule_name + "_" + tablename
    if debug:
        print_matrix(mime_mtx, "== mime_mtx (completed) ==")
        filename += "_" + datetime.strftime(datetime.now(), "%Y-%m-%d-%H-%M-%S")
    filename += '.tex'
    with open(filename, "w") as f:
        str_fmt = "\nWriting %s to file: %" + str(roundup(len(filename), 10)) + "s"
        print(str_fmt % (filename, filename), end='')
        # Here format the output for Latex file
        format_row_str = ("{:>11} & " * len(state_list))[:-3] + " \\\\"
        format_row_flt = ("{:11.3f} & " * len(state_list))[:-3] + " \\\\"
        tab_begin = '\\begin{tabular}{r|' + ('r' * len(state_list)) + '}'
        tab_end = '\\end{tabular}'
        tab_separator = "\\hline"
        tab_hdr_list = [state[3] for state in state_list]
        if debug:
            print_struct(tab_hdr_list, "== tab_hdr_list ==")
        print(tab_begin, file=f)
        print(' & ', file=f, end='')
        print(format_row_str.format(*tab_hdr_list), file=f)
        print(tab_separator, file=f)
        for idx, item in enumerate(tab_hdr_list):
            print(item, file=f, end='')
            print(' & ', file=f, end='')
            m_row = mime_mtx[idx].tolist()
            print(format_row_flt.format(*m_row), file=f)
        print(tab_end, file=f)
        print("%10s" % "[ OK ]\n")
    if debug:
        with open(filename, "r") as f:
            sp = "=" * 10
            print("File content:\n%s\n%s\n%s" % (sp, f.read(), sp))


def write_momdip(momdip_list, fd):
    # Quick init of a square 2D array
    momdip_mtx = np.zeros((len(states_list), len(states_list)), dtype=float)
    if debug:
        print_matrix(momdip_mtx, "== momdip_mtx (zeroed) ==")
    for momdip in momdip_list:
        k1 = int(momdip[0])
        k2 = int(momdip[1])
        val = float(momdip[2])
        momdip_mtx[k1][k2] = val
    if debug:
        print_matrix(momdip_mtx, "== momdip_mtx (completed) ==")
    for row in momdip_mtx:
        for val in row:
            print(np.format_float_scientific(val, precision=7, unique=False), end="\t", file=fd)
        # Splitting rows by going at new line
        print('', file=fd)


def write_momdip_latex(tablename: str, state_list, momdip_list):
    # Quick init of a square 2D array
    momdip_mtx = np.zeros((len(states_list), len(states_list)), dtype=float)
    if debug:
        print_matrix(momdip_mtx, "== momdip_mtx (zeroed) ==")
    for momdip in momdip_list:
        k1 = int(momdip[0])
        k2 = int(momdip[1])
        val = float(momdip[2])
        momdip_mtx[k1][k2] = val
    filename = molecule_dirpath + molecule_name + "_" + tablename
    if debug:
        print_matrix(momdip_mtx, "== momdip_mtx (completed) ==")
        filename += "_" + datetime.strftime(datetime.now(), "%Y-%m-%d-%H-%M-%S")
    filename += '.tex'
    with open(filename, "w") as f:
        str_fmt = "\nWriting %s to file: %" + str(roundup(len(filename), 10)) + "s"
        print(str_fmt % (filename, filename), end='')
        # Here format the output for Latex file
        format_row_str = ("{: >11} & " * len(state_list))[:-3] + " \\\\"
        format_row_flt = ("{: .3E} & " * len(state_list))[:-3] + " \\\\"
        tab_begin = '\\begin{tabular}{r|' + ('r' * len(state_list)) + '}'
        tab_end = '\\end{tabular}'
        tab_separator = "\\hline"
        tab_hdr_list = [state[3] for state in state_list]
        if debug:
            print_struct(tab_hdr_list, "== tab_hdr_list ==")
        print(tab_begin, file=f)
        print(' & ', file=f, end='')
        print(format_row_str.format(*tab_hdr_list), file=f)
        print(tab_separator, file=f)
        for idx, item in enumerate(tab_hdr_list):
            print(item, file=f, end='')
            print(' & ', file=f, end='')
            m_row = momdip_mtx[idx].tolist()
            print(format_row_flt.format(*m_row), file=f)
        print(tab_end, file=f)
        print("%10s" % "[ OK ]\n")
    if debug:
        with open(filename, "r") as f:
            sp = "=" * 10
            print("File content:\n%s\n%s\n%s" % (sp, f.read(), sp))


# Returns the state number based on passed arguments
# Params:
# - state_list: the States list
# - state_label: the name of the state you want back (i.e. : 'S2', 'T3', ...)
def get_state(state_list, state_label):
    _state = None
    if state_label[0] not in ('T', 'S') or int(state_label[1:]) not in range(0, math.floor(len(state_list)/2) + 1, 1):
        raise ValueError("state_label", "Unexpected value: " + str(state_label))
    _state = list(filter(lambda x: x[3] == state_label, state_list))[0]
    return int(_state[0])


def ev_to_cm1(ev: float) -> float:
    return ev * 8065.6


def cm1_to_nm(cm1: float) -> float:
    return (10 ** 7) / cm1


if __name__ == "__main__":
    print("="*40)
    print("\nStarting execution of qchem-parser.py\n")
    print("="*40)

    print("\nParsing arguments...", end='')
    # Create our Argument parser and set its description
    parser = argparse.ArgumentParser(
        description="Script that converts a QCHem output file into multiple text format matrix for further analysis (i.e by QOCT-RA)",
    )
    # Add the arguments:
    #   - source_file: the source file we want to convert/parse (.out)
    parser.add_argument('source_file', help='The file we want to convert/parse')
    # Parse the args (argparse automatically grabs the values from sys.argv)
    # argparse manage itself missing argument exception
    args = parser.parse_args()
    s_file = args.source_file
    print('%20s' % "[ DONE ]")
    # Solution where all your file go where you executes the script
    molecule_path = list(s_file.split('\\'))          # splitting path passed to the script
    molecule_name = molecule_path[-1][:-4]      # taking last item of the path, stripping the extension
    if len(molecule_path) > 1:
        molecule_dirpath = '\\'.join(molecule_path[:-1]) + '\\'
    else:
        molecule_dirpath = ''
    # Solution where all your files go where the .out file is located
    d_file_mime = molecule_dirpath + 'mime'
    d_file_momdip = molecule_dirpath + 'momdip'
    d_file_etats = molecule_dirpath + 'etats'
    print("\nProcessing Molecule: %s\n" % molecule_name)

    print("\nLoading source file...", end='')
    # Buffering source file into a variable, a List of String, then close & release the file
    with open(s_file, 'r') as reader:
        s_file_content = reader.readlines()
    print('%20s' % "[ Done ]")

    # Cleaning up the source from surrounding spaces and blank lines
    s_file_content = list(map(str.strip, s_file_content))  # removes leading & trailing blank/spaces
    s_file_content = list(filter(None, s_file_content))     # removes blank lines/no chars

    section_found = False
    section_in = False

    # ====================
    # Section: ETATS
    # ====================
    print("\nProcessing 'etats'...")
    states_list = [(1, 'S', 0.0, 'S0')]
    states_triplets = []
    states_singlets = []
    curr_state = -1
    curr_energy = -1
    exc_state = -1
    exc_energy = -1
    cpt_triplet = 0
    cpt_singlet = 0
    multiplicity = ""
    search_multiplicity = False
    section_start = "TDDFT/TDA Excitation Energies"
    section_separator = "----------------------------------------"
    section_rx = {
        'section_start': re.compile(
            r'TDDFT/TDA Excitation Energies'),
        'dashes': re.compile(
            r'----------------------------------------')
    }
    states_rx = {
        'state_energy': re.compile(
            r'^Excited state\s+(?P<state>\d+): excitation energy \(eV\) =\s+(?P<energy>[-+]?\d*\.\d+|\d+)$'),
        'state_mp': re.compile(
            r'^\s*Multiplicity: (?P<mplicity>\w+)$')
    }

    # Process source file for State definitions
    for line in s_file_content:
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
                    # (#state, multiplicity, eV, multiplicity_order)
                    # #State +1 because of S0 being artificially added at pos.0
                    states_list.append((curr_state + 1, multiplicity, curr_energy, (multiplicity + str(cpt))))
                    continue

    # Print the final 'etats' file
    write_table(d_file_etats, 'etats', states_list)
    states_triplets = (list(filter(lambda x: x[1] == 'T', states_list)))
    states_singlets = (list(filter(lambda x: x[1] == 'S', states_list)))
    if latex:
        write_etats_latex('etats', states_list)

    if debug:
        print_struct(states_list, "\n== states_list ==\n")
        print_struct(states_triplets, "\n== states_triplets ==\n")
        print_struct(states_singlets, "\n== states_singlets ==\n")
        print('')
        print("\n== Getting some states from label ==")
        tst_list = ['S0', 'S3', 'T1', 'T4', 'T5', 'S5', 'S-1']
        for state_tst in tst_list:
            try:
                print(state_tst, ": ", get_state(states_list, state_tst))
            except ValueError as err:
                print(state_tst, ": ", err)
        print('')

    # ====================
    # Section: MIME
    # ====================
    print("\nProcessing 'mime'...")
    section_found = False
    section_in = False
    section_rx = {
        'section_start': re.compile(
            r'^\*+SPIN-ORBIT COUPLING JOB BEGINS HERE\*+$'),
        'section_end': re.compile(
            r'^\*+SOC CODE ENDS HERE\*+$')
    }
    soc_rx = {
        'ground_to_triplets': re.compile(
            r'^Total SOC between the singlet ground state and excited triplet states:$'),
        'triplets_to_triplets': re.compile(
            r'^Total SOC between the (?P<tp_key>T\d) state and excited triplet states:$'),
        'singlets_to_triplets': re.compile(
            r'^Total SOC between the (?P<sg_key>S\d) state and excited triplet states:$'),
        'soc_value': re.compile(
            r'^(?P<soc_key>T\d)\s+(?P<soc_value>\d+\.?\d*)\s+cm-1$')
    }
    soc_list = []
    prim_key = ''
    sub_key = ''
    value = 0.0
    tpl = None

    # Process source file for SOC values (cm-1 values)
    for line in s_file_content:
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
                    elif key == 'soc_value':
                        sub_key = m.group('soc_key')
                        value = float(m.group('soc_value'))
                        tpl = (prim_key, sub_key, value)
                    break
            if tpl is not None:
                soc_list.append(tpl)
                tpl = (tpl[1], tpl[0], tpl[2])
                soc_list.append(tpl)
                tpl = None
                continue

    # Add state-to-itself SOC values (converted to cm-1) to the tuple list
    for state in states_list:
        # (prim_key, sub_key, value)
        tpl = (state[3], state[3], ev_to_cm1(state[2]))
        soc_list.append(tpl)
    if debug:
        print_struct(soc_list, "\n== soc_list ==\n")

    # Rewrite in place soc_list with all state_label translated into their #state
    for idx, soc in enumerate(soc_list):
        soc_list[idx] = (
            get_state(states_list, soc[0]),
            get_state(states_list, soc[1]),
            soc[2]
        )

    if debug:
        print_struct(soc_list, "\n== soc_list (rewritten) ==\n")

    # Print the final 'mime' file
    write_table(d_file_mime, 'mime', soc_list)
    if latex:
        write_mime_latex('mime', states_list, soc_list)

    # ====================
    # Section: MOMDIP
    # ====================
    print("\nProcessing 'momdip'...")
    section_found = False
    section_in = False
    section_rx = {
        'section_start': re.compile(
            r'^STATE-TO-STATE TRANSITION MOMENTS$'),
        'section_end': re.compile(
            r'^END OF TRANSITION MOMEMT CALCULATION$')
    }
    moment_rx = {
        # Hopefully the 'Electron Dipole Moments' table doesn't have the same line syntax that tables we're seeking for
        'moment': re.compile(
            r'^(?P<mom_key1>\d+)\s+(?P<mom_key2>\d+)(\s+-?\d\.\d+){3}\s+(?P<strength>(\d|\d\.\d+|\d\.\d+E[-+]\d{2}))$')
    }
    moment_list = []
    prim_key = ''
    sub_key = ''
    value = 0.0
    tpl = None

    # Process source file for MOMENT values (a.u. values)
    for line in s_file_content:
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
                tpl = (tpl[1], tpl[0], tpl[2])
                moment_list.append(tpl)
                tpl = None
                continue

    if debug:
        print_struct(moment_list, "\n== moment_list ==\n")

    # Print the final 'momdip' file
    write_table(d_file_momdip, 'momdip', moment_list)
    if latex:
        write_momdip_latex('momdip', states_list, moment_list)

    # =========================================================








