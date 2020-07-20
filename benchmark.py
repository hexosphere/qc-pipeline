#!/usr/bin/env python3

import fileinput
import os
import subprocess
import shlex
import csv
import argparse


# ===================================================================
# ===================================================================
# Command line arguments
# ===================================================================
# ===================================================================

# Define the arguments needed for the script (here they are defined as named arguments rather than positional arguments, check https://stackoverflow.com/questions/24180527/argparse-required-arguments-listed-under-optional-arguments for more info).
parser = argparse.ArgumentParser(add_help=False, description="")
required = parser.add_argument_group('Required arguments')
required.add_argument("--tmp", type=str, help="CSV file name you want to enrich", required=True)
required.add_argument("--final", type=str, help="Destination CSV file name", required=True)
args = parser.parse_args()

# Define the variables corresponding to those arguments
csv_tmp = args.tmp                      # Name of the program for which files need to be created
csv_final = args.final                  # Molecule file or folder containing the molecule files

# Check if arguments are valid
if (not os.path.exists(csv_tmp) or not os.path.isfile(csv_tmp)):
  print("Error - No such file: {}".format(csv_tmp))
  print("Aborting...")
  exit(1)
if (not os.path.exists(csv_final) or not os.path.isfile(csv_final)):
  print("Error - No such file: {}".format(csv_final))
  print("Aborting...")
  exit(1)

# =========================================================
# Functions definition
# =========================================================

def get_MaxRSS(jobID:int) -> str:
  maxRSS_k = str(subprocess.check_output("sacct -j {} --format=MaxRSS --noheader | head -n2 | tr -d [:space:]".format(jobID), shell=True).decode('utf-8'))
  maxRSS_k = maxRSS_k.strip()
  maxRSS_m = "0"
  if (maxRSS_k is not None and maxRSS_k != ''):
    #Cut the K at the end of MaxRSS
    maxRSS_k = maxRSS_k.rstrip('k')
    maxRSS_k = maxRSS_k.rstrip('K')
    #Convert to MB
    maxRSS_m = str(int(maxRSS_k) / 1024)
  return maxRSS_m

def get_TotCPU(jobID:int) -> str:
  totCPU = str(subprocess.check_output("sacct -j {} --format=TotalCPU --noheader | head -n1 | tr -d [:space:]".format(jobID), shell=True).decode('utf-8'))
  return str(totCPU)


# =========================================================
# Initialize some vars
# =========================================================

tmp_list = []
csv_tmp_header = ""
final_list = []
csv_final_header = ""


# =========================================================
# Load temporary file into a in-memory data structure
# =========================================================

# load tmp file into a list of dict
with open(csv_tmp, 'r', newline='') as inputfile:
  csv_reader = csv.DictReader(inputfile, delimiter=';')
  tmp_list = list(csv_reader)
  csv_tmp_header = csv_reader.fieldnames
  dialect = csv_reader.dialect
  print("Detected CSV dialect in tmp file: {}".format(dialect))
  print("Detected CSV header in tmp file : {}".format(csv_tmp_header))


for line in tmp_list.copy():
  print("\n------------------")
  jobID = str(line['Job ID'])
  if (jobID is ""):
    print("No JobID found. Skipping line...")
    continue
  print("Job ID : {}".format(jobID))
  maxRSS = get_MaxRSS(jobID)
  print("MaxRSS: {}".format(maxRSS))
  line['Max RSS'] = maxRSS
  totCPU = get_TotCPU(jobID)
  print("TotCPU: {}".format(totCPU))
  line['Total CPU'] = totCPU
  final_list.append(line)
  tmp_list.remove(line)

print("\n=====================")
csv_final_header = csv_tmp_header + ["Max RSS", "Total CPU"]
print("Used dialect in the final CSV file: {}".format(dialect))
print("Header used in final CSV file: {}".format(csv_final_header))


# =========================================================
# Write back / Update files
# =========================================================

# Append newly process data to the final file
# Check if the final file exist, contains something, and if not, request to write the csv header -> brand new file or not ?
write_header = False
print("\nWriting newly processed lines to the final file...", end='')
if (os.path.exists(csv_final) and os.path.isfile(csv_final)):
  with open(csv_final, 'r') as f:
    write_header = (not f.readline())
# Open the final benchmark file in 'Append' mode and add processed lines (+ write header if required)
with open(csv_final, 'a', newline='') as final_f:
  csv_writer = csv.DictWriter(final_f, fieldnames=csv_final_header, delimiter=';', quoting=csv.QUOTE_MINIMAL)
  if write_header:
    csv_writer.writeheader()
  for line in final_list:
    csv_writer.writerow(line)
print("[DONE]")


# Write back resulting list to tmp file for later processing
print("\nPruning processed lines from tmp file...", end='')
with open(csv_tmp, 'w', newline='') as tmp_f:
  csv_writer = csv.DictWriter(tmp_f, fieldnames=csv_tmp_header, delimiter=';', quoting=csv.QUOTE_MINIMAL)
  csv_writer.writeheader()
  for line in tmp_list:
    csv_writer.writerow(line)
print("[DONE]")



# =========================================================
# Goodbye, hope you enjoyed your flight !
# =========================================================