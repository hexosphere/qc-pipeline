#!/bin/bash
# vim:ai et  sw=2 ts=2 sts=2

#########################################################################################################
###      This script will be called via a cron task to execute control_launcher.py (with QOCT-RA)     ###
#########################################################################################################

# Pretty print for log messages

log_msg () {
  echo -e "$(date +"%Y-%m-%d %T")\t$1"
}

# Define important files and folders

OUT_FILEPATH="/home/ulb/cqp/niacobel/CECIHOME/Q-CHEM_OUT/*.out"

# Exit immediately if there's no file to process

if [ $(ls $OUT_FILEPATH 2>/dev/null | wc -l) -eq 0 ]; then
  exit

# Otherwise execute abin_launcher.py for each file present in the ORCA_OUT folder

else

  file_list=$(ls $OUT_FILEPATH 2>/dev/null)
  source /home/ulb/cqp/niacobel/CECIHOME/CHAINS/load_modules.sh

  for filepath in $file_list
  do
    filename="$(basename -- $filepath)"
    MOL_NAME=${filename%.*}
    mkdir -p ~/CONTROL
    python ~/CHAINS/control_launcher/control_launcher.py -i ${filepath} -cf /home/ulb/cqp/niacobel/CECIHOME/RESULTS/${MOL_NAME}/${MOL_NAME}.yml -o ~/CONTROL/ -ow  > ~/CONTROL/${MOL_NAME}.log
    mv ~/CONTROL/${MOL_NAME}.log ~/CONTROL/${MOL_NAME}/${MOL_NAME}.log
  done

  log_msg "INFO - Successfully processed:\n$file_list"

fi