#!/bin/bash
# vim:ai et  sw=2 ts=2 sts=2


###
# Kinda script that will be called via a cron task
###

# Pretty print log messages: e.g.: 2020-06-28 21:22:50     No file to process. 
log_msg () {
  echo -e "$(date +"%Y-%m-%d %T")\t$1"
}


# ! FINAL content is   folders   !
RESULTS_FILEPATH="/sulb2/niacobel/FINAL"
OUTPUT_FILEPATH="/sulb2/niacobel/Q-CHEM/qchem_out_queue/"
WARNING=false

# if no file at all to process; early exit
outputs_exist=false
results_exist=false
if [ $(ls $OUTPUT_FILEPATH/*.out 2>/dev/null | wc -l) -ne 0 ]; then
  outputs_exist=true
fi
if [ $(ls $RESULTS_FILEPATH 2>/dev/null | wc -l) -ne 0 ]; then
  results_exist=true
fi

if [ ! $outputs_exist ] && [ ! $results_exist ]; then
  log_msg "INFO - No file to process in any directories"
  exit 0

else
  # Verify that the required ssh key is loaded in ssh-agent key-ring || exit
  if [ $(ssh-add -l 2>/dev/null | grep ceci | wc -l) -eq 0 ]; then
    log_msg "ERROR - SSH Key not loaded. Please add your CECI ssh key to the key-ring using ssh-add command (or the ssh-agent is not reachable from this environment)." && exit 1       # + Notif mail
  fi

  inconsistent_molnames=""
  mol_list=""
  for filepath in $(ls $OUTPUT_FILEPATH/*.out 2>/dev/null); do
    filename="$(basename -- $filepath)"
    MOL_NAME=${filename%.*}
    mol_list+=" $MOL_NAME"
    # If the molecule doesn't exist there, raise a Warning
    if [ -z $(ls $RESULTS_FILEPATH/$MOL_NAME 2>/dev/null) ]; then
      inconsistent_molnames+=" $MOL_NAME"
      WARNING=true
    fi
  done

  # Just warn if a file is found in the output queue but not in the archive folder... inconsistent manual op ??
  if [ $WARNING ]; then
    log_msg "WARNING - I found those molecules in the out queue, but not in the result folder: $inconsistent_molnames"
  fi

  if [ $results_exist ]; then
    _filelist=$(ls $RESULTS_FILEPATH 2>/dev/null)
    # Send $RESULTS_FILEPATH/* to vega:/CECI/home/ulb/cqp/niacobel/FINAL
    rsync -q -a --remove-source-files $RESULTS_FILEPATH/* vega:/CECI/home/ulb/cqp/niacobel/FINAL && log_msg "INFO - Successfully processed (Results):\n$_filelist"
    # rsync doesn't remove sent files/directories with option "remove-source-files"   --   we force it by another way
    find $RESULTS_FILEPATH -depth -type d -empty -not -path $RESULTS_FILEPATH -delete || (log_msg "WARNING - Cleaning of $RESULTS_FILEPATH didn't run correctly. Possibility of remaining empty folders...")
  fi
  if [ $outputs_exist ]; then
    rsync -q -a --remove-source-files $OUTPUT_FILEPATH/*.out vega:/CECI/home/ulb/cqp/niacobel/Q-CHEM && log_msg "INFO - Successfully processed (qchem_queue):\n$mol_list"
  fi
  #log_msg "DEBUG - It will move  files to FINAL_sent instead of removing it from FINAL"
  #rsync -q -a $RESULTS_FILEPATH/* vega:/CECI/home/ulb/cqp/niacobel/FINAL
  #mkdir -p /sulb2/niacobel/FINAL_sent ; mv /sulb2/niacobel/FINAL/* /sulb2/niacobel/FINAL_sent

fi
