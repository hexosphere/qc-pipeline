#!/usr/bin/env python3

import fileinput
import os
import subprocess
import csv
import argparse
import datetime


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
""" if (not os.path.exists(csv_final) or not os.path.isfile(csv_final)):
  print("Error - No such file: {}".format(csv_final))
  print("Aborting...")
  exit(1) """

# =========================================================
# Functions definition
# =========================================================

# All the values are obtained through the use of sacct command, see https://slurm.schedmd.com/sacct.html for more informations

def get_Reserved(jobID:int) -> str:
  reserved = str(subprocess.check_output("sacct -j {} --format=Reserved%20 --noheader | head -n1 | tr -d [:space:]".format(jobID), shell=True).decode('utf-8'))
  return str(reserved)

def get_Elapsed(jobID:int) -> str:
  elapsed = str(subprocess.check_output("sacct -j {} --format=Elapsed%20 --noheader | head -n1 | tr -d [:space:]".format(jobID), shell=True).decode('utf-8'))
  return str(elapsed)

def get_Timelimit(jobID:int) -> str:
  time_limit = str(subprocess.check_output("sacct -j {} --format=Timelimit%20 --noheader | head -n1 | tr -d [:space:]".format(jobID), shell=True).decode('utf-8'))
  return str(time_limit)

def get_MaxRSS(jobID:int) -> int:
  maxRSS_k = str(subprocess.check_output("sacct -j {} --format=MaxRSS%12 --noheader | head -n2 | tr -d [:space:]".format(jobID), shell=True).decode('utf-8'))
  maxRSS_k = maxRSS_k.strip() #! est-ce necessaire? 
  maxRSS_m = "-1"
  if (maxRSS_k is not None and maxRSS_k != ''): #! est-ce necessaire? 
    #Cut the K at the end of MaxRSS
    maxRSS_k = maxRSS_k.rstrip('k')
    maxRSS_k = maxRSS_k.rstrip('K')
    #Convert to MB
    maxRSS_m = int(int(maxRSS_k) / 1024)
  return maxRSS_m

def get_ReqCPUs(jobID:int) -> int:
  req_cpus = str(subprocess.check_output("sacct -j {} --format=ReqCPUs --noheader | head -n1 | tr -d [:space:]".format(jobID), shell=True).decode('utf-8'))
  return int(req_cpus)

def get_ReqMem(jobID:int) -> int:
  req_mem = str(subprocess.check_output("sacct -j {} --format=ReqMem%10 --noheader | head -n1 | tr -d [:space:]".format(jobID), shell=True).decode('utf-8'))
  req_mem = req_mem.rstrip('Mc')
  return int(req_mem)

def get_TotCPU(jobID:int) -> str:
  totCPU = str(subprocess.check_output("sacct -j {} --format=TotalCPU%20 --noheader | head -n1 | tr -d [:space:]".format(jobID), shell=True).decode('utf-8'))
  return str(totCPU)

def get_CPUTime(jobID:int) -> str:
  CPU_time = str(subprocess.check_output("sacct -j {} --format=CPUTime%20 --noheader | head -n1 | tr -d [:space:]".format(jobID), shell=True).decode('utf-8'))
  return str(CPU_time)

def slurm_time_to_seconds(time:str) -> int:
  # Get rid of the milliseconds and change the separator for day to hours from "-" to ":"
  time_tmp = (time.replace("-",":")).rsplit('.',1)[0]
  # Split each units of time (seconds, minutes, hours and days) and convert them into seconds before adding them together.
  seconds=sum(x * int(t) for x, t in zip([1, 60, 3600, 86400], reversed(time_tmp.split(":"))))
  return seconds

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
print("Scanning tmp file {} ... \n".format(csv_tmp))
with open(csv_tmp, 'r', newline='') as inputfile:
  csv_reader = csv.DictReader(inputfile, delimiter=';')
  tmp_list = list(csv_reader)
  csv_tmp_header = csv_reader.fieldnames
  dialect = csv_reader.dialect
  print("Detected CSV dialect in tmp file: {}".format(dialect))
  print("Detected CSV header in tmp file : {}".format(csv_tmp_header))

# rename the tmp file with the time_stamp to preserve it if needed
current_date = datetime.datetime.today().strftime('_%Y-%m-%d_%H-%M-%S')
os.rename(csv_tmp,os.path.splitext(csv_tmp)[0] + str(current_date) + os.path.splitext(csv_tmp)[1])

# get everything we need to add to the csv
print("\nProcessing lines ...")
for line in tmp_list.copy():
  print("")
  print(''.center(60, '-'))
  mol_name = str(line['Mol Name'])
  print("          Mol Name: {}".format(mol_name))

  jobID = str(line['Job ID'])
  if (jobID is ""):
    print("No JobID found. Skipping line... \n")
    continue
  print("            Job ID: {}".format(jobID))
  
  print(''.center(60, '-'))

  reserved = get_Reserved(jobID)
  print("          Reserved: {}".format(reserved))
  line['Reserved'] = reserved

  elapsed = get_Elapsed(jobID)
  print("           Elapsed: {}".format(elapsed))
  line['Elapsed'] = elapsed

  walltime = get_Timelimit(jobID)
  print("          Walltime: {}".format(walltime))

  elapsed_raw = slurm_time_to_seconds(elapsed)
  walltime_raw = slurm_time_to_seconds(walltime)
  time_eff = round(elapsed_raw / walltime_raw, 4)
  print("   Time Efficiency: {}".format("{:.0%}".format(time_eff)))
  line['Time Efficiency'] = time_eff

  print(''.center(60, '-'))

  maxRSS = get_MaxRSS(jobID)
  print("            MaxRSS: {} MB".format(maxRSS))
  line['Max RSS'] = maxRSS

  nb_cpus = get_ReqCPUs(jobID)
  mem_per_cpu = get_ReqMem(jobID)
  tot_mem = nb_cpus * mem_per_cpu
  print("         Total MEM: {} MB ({} MB for each of {} CPUs)".format(tot_mem,mem_per_cpu,nb_cpus))

  mem_eff = round(maxRSS / tot_mem, 4)
  print("    RAM Efficiency: {}".format("{:.0%}".format(mem_eff)))
  line['RAM Efficiency'] = mem_eff

  print(''.center(60, '-'))

  totCPU = get_TotCPU(jobID)
  print("          TotalCPU: {}".format(totCPU))
  line['Total CPU'] = totCPU

  wallCPU = get_CPUTime(jobID)
  print("          Wall CPU: {}".format(wallCPU))
  line['Wall CPU'] = wallCPU

  totCPU_raw = slurm_time_to_seconds(totCPU)
  wallCPU_raw = slurm_time_to_seconds(wallCPU)
  cpu_eff = round(totCPU_raw / wallCPU_raw, 4)
  print("    CPU Efficiency: {}".format("{:.0%}".format(cpu_eff)))
  line['CPU Efficiency'] = cpu_eff

  print(''.center(60, '-'))
  print("")

  final_list.append(line)
  tmp_list.remove(line)

print("\n=====================")
csv_final_header = csv_tmp_header + ["Reserved", "Elapsed", "Time Efficiency", "Max RSS", "RAM Efficiency", "Total CPU", "Wall CPU", "CPU Efficiency"]
print("Used dialect in the final CSV file: {}".format(dialect))
print("Header used in final CSV file: {}".format(csv_final_header))


# =========================================================
# Write back / Update files
# =========================================================

# Append newly process data to the final file
# Check if the final file exists and contains something. If not, request to write the csv header -> brand new file or not ?
write_header = True
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

# =========================================================
# Goodbye, hope you enjoyed your flight !
# =========================================================