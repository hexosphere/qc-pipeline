#!/bin/bash
# vim:ai et  sw=2 ts=2 sts=2


###
# Kinda script that will be called via a cron task
###

# Pretty print log messages: e.g.: 2020-06-28 21:22:50     No file to process. 
log_msg () {
  echo -e "$(date +"%Y-%m-%d %T")\t$1"
}

XYZ_FILEPATH="/sulb2/niacobel/Q-CHEM/qchem_queue/*.xyz"
LOGS_PATH="/sulb2/niacobel/logs"
ABIN_LOGS="${LOGS_PATH}/abin_launcher"

# if no file to process; early exit
if [ $(ls $XYZ_FILEPATH 2>/dev/null | wc -l) -eq 0 ]; then
  log_msg "INFO - No file to process."
  exit
else
  file_list=$(ls $XYZ_FILEPATH 2>/dev/null)
  source /sulb2/niacobel/Pipeline/load_modules.sh
  mkdir -p "${ABIN_LOGS}"
  for filepath in $file_list
  do
    filename="$(basename -- $filepath)"
    MOL_NAME=${filename%.*}
    python ~/Pipeline/abin_launcher.py -p qchem -i ~/Q-CHEM/qchem_queue/${filename} -o ~/Q-CHEM/ -ow -cfg ~/Q-CHEM/qchem_queue/${MOL_NAME}_config.yml > ${ABIN_LOGS}/$(date +"%Y%m%d_%H%M%S")_stdout.log
    mv ~/Q-CHEM/qchem_queue/${MOL_NAME}_config.yml ~/Q-CHEM/qchem_queue/Launched/
    #log_msg "DEBUG - It will move .xyz files to qchem_queue/sent instead of removing it from qchem_queue/"
    #rsync -q -a $CECIHOME/ORCA/*.xyz hydra:~/Q-CHEM/qchem_queue
    #mkdir -p ~/Q-CHEM/qchem_queue/sent ; mv ~/Q-CHEM/qchem_queue/*.xyz ~/Q-CHEM/qchem_queue/sent/
  done
  log_msg "INFO - Successfully processed:\n$file_list"

fi