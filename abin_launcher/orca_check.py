################################################################################################################################################
##                                                     Orca Output Quality Control Script                                                     ##
##                                                                                                                                            ##
##                            This script scans a given orca output file looking for possible errors and warnings                             ##
##                                           that might interfere with the rest of the calculations                                           ##
################################################################################################################################################

import sys

with open(sys.argv[1], 'r') as output:
  output_content = output.read().splitlines()

print("Checking ORCA output file...")

# Check if the second to last line corresponds to what we should have
if "****ORCA TERMINATED NORMALLY****" not in output_content[-2]:
  print("\nERROR: ORCA's output does not mention having terminated normally. Check the output file content before proceeding further.")
  print("Aborting ...")
  exit(1)

print("No errors detected in the output file.")