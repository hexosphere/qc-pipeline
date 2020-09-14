#!/usr/bin/env python3

################################################################################################################################################
##                                          Benchmarking script for jobs running on the CECI clusters                                         ##
##                                                                                                                                            ##
##                                   Use it in conjunction with the jinja template benchmark.sh.jinja as it                                   ##
##                                  will complete the lines from the CSV file created by that jinja template                                  ##
################################################################################################################################################

import argparse
import csv
import datetime
import fileinput
import os
import shutil
import subprocess

# ===================================================================
# ===================================================================
# Functions definition
# ===================================================================
# ===================================================================

# Benchmarking values fetching functions
# All the values are obtained through the use of sacct command, see https://slurm.schedmd.com/sacct.html for more informations. The docstrings of these functions are issued from the SLURM sacct documentation.

def get_CPUTime(jobID:int) -> str:
  """ Time used (Elapsed time * CPU count) by a job or step in HH:MM:SS format. """
  CPU_time = str(subprocess.check_output("sacct -j {} --format=CPUTime%20 --noheader | head -n1 | tr -d [:space:]".format(jobID), shell=True).decode('utf-8'))
  return str(CPU_time)

def get_Elapsed(jobID:int) -> str:
  """ The jobs elapsed time. The format of this fields output is as follows: [DD-[HH:]]MM:SS """
  elapsed = str(subprocess.check_output("sacct -j {} --format=Elapsed%20 --noheader | head -n1 | tr -d [:space:]".format(jobID), shell=True).decode('utf-8'))
  return str(elapsed)

def get_MaxRSS(jobID:int) -> int:
  """ Maximum resident set size of all tasks in job. (Note: expressed in KB, converted in MB) """
  maxRSS_k = str(subprocess.check_output("sacct -j {} --format=MaxRSS%12 --noheader | head -n2 | tr -d [:space:]".format(jobID), shell=True).decode('utf-8'))
  maxRSS_k = maxRSS_k.strip()
  maxRSS_m = "-1"
  if (maxRSS_k is not None and maxRSS_k != ''):
    # Cut the K at the end of MaxRSS
    maxRSS_k = maxRSS_k.rstrip('k')
    maxRSS_k = maxRSS_k.rstrip('K')
    # Convert to MB
    maxRSS_m = int(int(maxRSS_k) / 1024)
  return maxRSS_m

def get_ReqCPUs(jobID:int) -> int:
  """ Number of requested CPUs. """
  req_cpus = str(subprocess.check_output("sacct -j {} --format=ReqCPUs --noheader | head -n1 | tr -d [:space:]".format(jobID), shell=True).decode('utf-8'))
  return int(req_cpus)

def get_ReqMem(jobID:int) -> int:
  """ Minimum required memory for the job, in MB. A 'c' at the end of number represents Memory Per CPU, a 'n' represents Memory Per Node. Note: This value is only from the job allocation, not the step. """
  req_mem = str(subprocess.check_output("sacct -j {} --format=ReqMem%10 --noheader | head -n1 | tr -d [:space:]".format(jobID), shell=True).decode('utf-8'))
  req_mem = req_mem.rstrip('Mc')
  return int(req_mem)

def get_Reserved(jobID:int) -> str:
  """ How much wall clock time was used as reserved time for this job. This is derived from how long a job was waiting from eligible time to when it actually started. Format is the same as Elapsed. """
  reserved = str(subprocess.check_output("sacct -j {} --format=Reserved%20 --noheader | head -n1 | tr -d [:space:]".format(jobID), shell=True).decode('utf-8'))
  return str(reserved)

def get_Timelimit(jobID:int) -> str:
  """ What the timelimit was for the job. Format is the same as Elapsed. """
  time_limit = str(subprocess.check_output("sacct -j {} --format=Timelimit%20 --noheader | head -n1 | tr -d [:space:]".format(jobID), shell=True).decode('utf-8'))
  return str(time_limit)

def get_TotCPU(jobID:int) -> str:
  """ The sum of the SystemCPU and UserCPU time used by the job or job step. The total CPU time of the job may exceed the job's elapsed time for jobs that include multiple job steps. Format is the same as Elapsed.
  Note: TotalCPU provides a measure of the task's parent process and does not include CPU time of child processes. """
  totCPU = str(subprocess.check_output("sacct -j {} --format=TotalCPU%20 --noheader | head -n1 | tr -d [:space:]".format(jobID), shell=True).decode('utf-8'))
  return str(totCPU)

# Additional functions

def slurm_time_to_seconds(time:str) -> int:
  """ Converts a time string given by SLURM into seconds """
  # Get rid of the milliseconds and change the separator for day to hours from "-" to ":"
  time_tmp = (time.replace("-",":")).rsplit('.',1)[0]
  # Split each units of time (seconds, minutes, hours and days) and convert them into seconds before adding them together.
  seconds=sum(x * int(t) for x, t in zip([1, 60, 3600, 86400], reversed(time_tmp.split(":"))))
  return seconds

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

optional = parser.add_argument_group('Optional arguments')
optional.add_argument('-h','--help',action='help',default=argparse.SUPPRESS,help='Show this help message and exit')
optional.add_argument("-k","--keep",action="store_true",help="Do not rename the treated CSV file")

args = parser.parse_args()

# Define the variables corresponding to those arguments

csv_tmp = args.tmp                      # Name of the CSV file that needs to be processed (likely created by benchmark.sh.jinja)
csv_final = args.final                  # Name of the new CSV file that will be created, with completed lines
keep = args.keep                        # Flag to not rename the treated CSV file

# ===================================================================
# ===================================================================
#                       PREPARATION STEP
# ===================================================================
# ===================================================================

# Get the size of the terminal in order to have a prettier output, if you need something more robust, go check http://granitosaurus.rocks/getting-terminal-size.html

columns, rows = shutil.get_terminal_size()

# Output Header

print("".center(columns,"*"))
print("")
print("EXECUTION OF THE BENCHMARKING SCRIPT FOR CECI CLUSTERS JOBS BEGINS NOW".center(columns))
print("")
print("".center(columns,"*"))

section_title = "0. Preparation step"

print("")
print("")
print(''.center(len(section_title)+10, '*'))
print(section_title.center(len(section_title)+10))
print(''.center(len(section_title)+10, '*'))

# =========================================================
# Check csv_tmp argument
# =========================================================

if (not os.path.exists(csv_tmp) or not os.path.isfile(csv_tmp)):
  print("Error - No such file: {}".format(csv_tmp))
  print("Aborting...")
  exit(1)

# =========================================================
# Initialize some variables
# =========================================================

tmp_list = []
csv_tmp_header = ""
final_list = []
csv_final_header = ""

# =========================================================
# Load temporary CSV file
# =========================================================

print("\nScanning tmp file {} ... ".format(csv_tmp))
with open(csv_tmp, 'r', newline='') as inputfile:
  csv_content = csv.DictReader(inputfile, delimiter=';')
  tmp_list = list(csv_content)
  csv_tmp_header = csv_content.fieldnames
  dialect = csv_content.dialect
  print("    Detected CSV dialect in tmp file: {}".format(dialect))
  print("    Detected CSV header in tmp file : {}".format(csv_tmp_header))

# Rename the tmp file with the time_stamp to preserve it if needed (if keep has not been set)

if not keep:
  current_date = datetime.datetime.today().strftime('_%Y-%m-%d_%H-%M-%S')
  new_name = os.path.splitext(csv_tmp)[0] + str(current_date) + os.path.splitext(csv_tmp)[1]
  os.rename(csv_tmp,new_name)
  print("    CSV tmp file has been renamed to {}".format(new_name))

# ===================================================================
# ===================================================================
#                         GETTING THE VALUES
# ===================================================================
# ===================================================================

section_title = "1. Get benchmarking values"

print("")
print("")
print(''.center(len(section_title)+10, '*'))
print(section_title.center(len(section_title)+10))
print(''.center(len(section_title)+10, '*'))

print("\nProcessing lines ...")

for line in tmp_list:
  
  # For more informations on try/except structures, see https://www.tutorialsteacher.com/python/exception-handling-in-python
  try:

    # Header

    print("")
    print(''.center(60, '-'))
    mol_name = str(line['Mol Name'])
    print("{:>20}: {:<}".format("Mol Name",mol_name))

    jobID = str(line['Job ID'])
    if (jobID is ""):
      print("No JobID found. Skipping line... \n")
      continue
    print("{:>20}: {:<}".format("Job ID",jobID))
    
    print(''.center(60, '-'))

    # Time information

    reserved = get_Reserved(jobID)
    print("{:>20}: {:<}".format("Reserved",reserved))
    line['Reserved'] = reserved

    elapsed = get_Elapsed(jobID)
    print("{:>20}: {:<}".format("Elapsed",elapsed))
    line['Elapsed'] = elapsed

    walltime = get_Timelimit(jobID)
    print("{:>20}: {:<}".format("Walltime",walltime))

    elapsed_raw = slurm_time_to_seconds(elapsed)
    walltime_raw = slurm_time_to_seconds(walltime)
    time_eff = round(elapsed_raw / walltime_raw, 4)
    print("{:>20}: {:<}".format("Time Efficiency","{:.0%}".format(time_eff)))
    line['Time Efficiency'] = time_eff

    print(''.center(60, '-'))

    # Memory information

    maxRSS = get_MaxRSS(jobID)
    print("{:>20}: {:<} MB".format("MaxRSS",maxRSS))
    line['Max RSS'] = maxRSS

    nb_cpus = get_ReqCPUs(jobID)
    mem_per_cpu = get_ReqMem(jobID)
    tot_mem = nb_cpus * mem_per_cpu
    print("{:>20}: {:<} MB ({} MB for each of {} CPUs)".format("Total MEM",tot_mem,mem_per_cpu,nb_cpus))

    mem_eff = round(maxRSS / tot_mem, 4)
    print("{:>20}: {:<}".format("RAM Efficiency","{:.0%}".format(mem_eff)))
    line['RAM Efficiency'] = mem_eff

    print(''.center(60, '-'))

    # CPU Information

    totCPU = get_TotCPU(jobID)
    print("{:>20}: {:<}".format("TotalCPU",totCPU))
    line['Total CPU'] = totCPU

    wallCPU = get_CPUTime(jobID)
    print("{:>20}: {:<}".format("Wall CPU",wallCPU))
    line['Wall CPU'] = wallCPU

    totCPU_raw = slurm_time_to_seconds(totCPU)
    wallCPU_raw = slurm_time_to_seconds(wallCPU)
    cpu_eff = round(totCPU_raw / wallCPU_raw, 4)
    print("{:>20}: {:<}".format("CPU Efficiency","{:.0%}".format(cpu_eff)))
    line['CPU Efficiency'] = cpu_eff

    print(''.center(60, '-'))
    print("")

    # Add informations to our final CSV

    final_list.append(line)
    tmp_list.remove(line)

  except Exception as error:
    print(error)
    continue

if final_list == []:
  print("None of the lines were processed correctly")
  print("Aborting ...")
  exit(1)

print("\nEnd of processing")

# ===================================================================
# ===================================================================
#                            THE END STEP
# ===================================================================
# ===================================================================

section_title = "2. Writing new information to final CSV file"

print("")
print("")
print(''.center(len(section_title)+10, '*'))
print(section_title.center(len(section_title)+10))
print(''.center(len(section_title)+10, '*'))
print("")

# Define the final CSV header

csv_final_header = csv_tmp_header + ["Reserved", "Elapsed", "Time Efficiency", "Max RSS", "RAM Efficiency", "Total CPU", "Wall CPU", "CPU Efficiency"]
print("Used dialect in the final CSV file: {}".format(dialect))
print("Header used in final CSV file: {}".format(csv_final_header))

# Define if we have to write the header or not (only write it if the file does not exist or is empty)

write_header = True
if (os.path.exists(csv_final) and os.path.isfile(csv_final)):
  with open(csv_final, 'r') as f:
    write_header = (not f.readline()) # If the file is empty, write_header = True. Otherwise, write_header = False

# Open the final benchmark file in 'Append' mode and add processed lines (+ write header if required)

print("\nWriting newly processed lines to the final file {} ...".format(csv_final), end='')

with open(csv_final, 'a', newline='') as final_f:
  csv_writer = csv.DictWriter(final_f, fieldnames=csv_final_header, delimiter=';', quoting=csv.QUOTE_MINIMAL)
  if write_header:
    csv_writer.writeheader()
  for line in final_list:
    csv_writer.writerow(line)

print("{:>12}".format("[DONE]"))

print("")
print("".center(columns,"*"))
print("")
print("END OF EXECUTION".center(columns))
print("")
print("".center(columns,"*"))