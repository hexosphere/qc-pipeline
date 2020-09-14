#!/bin/bash
# vim:ai et  sw=2 ts=2 sts=2

#########################################################################################################
###   This script will be called via a cron task to execute abin_launcher.py for the Q-CHEM program   ###
#########################################################################################################

# Pretty print for log messages
log_msg () {
  echo -e "$(date +"%Y-%m-%d %T")\t$1"
}

# Define CECIHOME (might not be known by the crontab)
CECIHOME="/home/ulb/cqp/niacobel/CECIHOME"

# Define the folder we want to scan
WATCH_DIR="${CECIHOME}/ORCA_OUT"

# Define the type of file we are looking for
XYZ_FILEPATH="${WATCH_DIR}/*.xyz"

# Define the folder where the log files will be stored
ABIN_LOGS="${WATCH_DIR}/abin_logs"

# Exit immediately if there's no file to process
if [ $(ls $XYZ_FILEPATH 2>/dev/null | wc -l) -eq 0 ]; then
  exit

# Otherwise execute abin_launcher.py for each file present in the WATCH_DIR folder

else

  file_list=$(ls $XYZ_FILEPATH 2>/dev/null)
  source ${CECIHOME}/CHAINS/load_modules.sh
  mkdir -p "${ABIN_LOGS}"

  for filepath in $file_list
  do
    filename="$(basename -- $filepath)"
    MOL_NAME=${filename%.*}
    mkdir -p ~/QCHEM
    python ${CECIHOME}/CHAINS/abin_launcher/abin_launcher.py -p qchem -m ${filepath} -cf ${CECIHOME}/RESULTS/${MOL_NAME}/${MOL_NAME}.yml -o ~/QCHEM/ -ow  > ${ABIN_LOGS}/$(date +"%Y%m%d_%H%M%S")_${MOL_NAME}.log
  done

  log_msg "INFO - Successfully processed:\n$file_list"

fi