################################################################################################################################################
##                                                    Q-CHEM Output Quality Control Script                                                    ##
##                                                                                                                                            ##
##                           This script scans a given q-chem output file looking for possible errors and warnings                            ##
##                                           that might interfere with the rest of the calculations                                           ##
################################################################################################################################################

import sys

with open(sys.argv[1], 'r') as output:
  output_content = output.read().splitlines()

print("\nChecking Q-CHEM output file...")

# Check if the thank you message is present
if "Thank you very much for using Q-Chem.  Have a nice day." not in output_content[-5]:
  print("\nERROR: The Q-CHEM output file does not mention having terminated normally. Check the output file content before proceeding further.")
  print("Aborting ...")
  exit(1)

print("No errors detected in the output file.")