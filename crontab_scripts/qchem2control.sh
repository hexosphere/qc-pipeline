#!/bin/bash
# vim:ai et  sw=2 ts=2 sts=2

#########################################################################################################
###      This script will be called via a cron task to execute control_launcher.py (with QOCT-RA)     ###
#########################################################################################################

# Pretty print for log messages
log_msg () {
  echo -e "$(date +"%Y-%m-%d %T")\t$1"
}

# Define CECIHOME (might not be known by the crontab)
CECIHOME="/CECI/home/ulb/cqp/niacobel"

# Define the folder we want to scan
WATCH_DIR="${CECIHOME}/QCHEM_OUT"

# Define the type of file we are looking for
OUT_FILEPATH="${WATCH_DIR}/*.out"

# Exit immediately if there's no file to process
if [ $(ls $OUT_FILEPATH 2>/dev/null | wc -l) -eq 0 ]; then
  exit

# Otherwise execute control_launcher.py for each file present in the WATCH_DIR folder

else

  file_list=$(ls $OUT_FILEPATH 2>/dev/null)
  source ${CECIHOME}/CHAINS/load_modules.sh

  for filepath in $file_list
  do
    filename="$(basename -- $filepath)"
    MOL_NAME=${filename%.*}
    mkdir -p ~/CONTROL
    python ${CECIHOME}/CHAINS/control_launcher/control_launcher.py -i ${filepath} -cf ${CECIHOME}/RESULTS/${MOL_NAME}/config.yml -o ~/CONTROL/ -ow  > ~/CONTROL/${MOL_NAME}.log
    status=$?

    if [ ${status} -eq 0 ]; then
      # If successful, archive the source file and the log file
      mv ~/CONTROL/${MOL_NAME}.log ~/CONTROL/${MOL_NAME}/${MOL_NAME}.log
      mkdir -p ${WATCH_DIR}/Launched
      mv ${filepath} ${WATCH_DIR}/Launched/
    fi
  done

  log_msg "INFO - Successfully processed:\n$file_list"

fi