#!/bin/bash
# vim:ai et  sw=2 ts=2 sts=2


###
# Kinda script that will be called via a cron task
###

# Pretty print log messages: e.g.: 2020-06-28 21:22:50     No file to process. 
log_msg () {
  echo -e "$(date +"%Y-%m-%d %T")\t$1"
}

RESULTS_FILEPATH="/sulb2/niacobel/FINAL"
OUTPUT_FILEPATH="/sulb2/niacobel/Q-CHEM/qchem_out_queue/"

# if no file to process; early exit
if [ $(ls $RESULTS_FILEPATH 2>/dev/null | wc -l) -eq 0 ]; then
  log_msg "INFO - No file to process."
  exit
else
  file_list=$(ls $RESULTS_FILEPATH 2>/dev/null)
  SSH_OPTS="-o PasswordAuthentication=no -o ConnectTimeout=10 -o ConnectionAttempts=3"
  # Verify that the required ssh key is loaded in ssh-agent key-ring || exit
  if [ $(ssh-add -l 2>/dev/null | grep ceci | wc -l) -eq 0 ]; then
    log_msg "ERROR - SSH Key not loaded. Please add your CECI ssh key to the key-ring using ssh-add command (or the ssh-agent is not reachable from this environment)." && exit 1       # + Notif mail
  fi

  # Send $RESULTS_FILEPATH/* to vega:/CECI/home/ulb/cqp/niacobel/FINAL
  rsync -q -a --remove-source-files $RESULTS_FILEPATH/* vega:/CECI/home/ulb/cqp/niacobel/FINAL
  rsync -q -a --remove-source-files $OUTPUT_FILEPATH/*.out vega:/CECI/home/ulb/cqp/niacobel/Q-CHEM
  #log_msg "DEBUG - It will move  files to FINAL_sent instead of removing it from FINAL"
  #rsync -q -a $RESULTS_FILEPATH/* vega:/CECI/home/ulb/cqp/niacobel/FINAL
  #mkdir -p /sulb2/niacobel/FINAL_sent ; mv /sulb2/niacobel/FINAL/* /sulb2/niacobel/FINAL_sent
 
  log_msg "INFO - Successfully processed:\n$file_list"

fi
