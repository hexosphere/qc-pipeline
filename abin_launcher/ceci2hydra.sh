#!/bin/bash
# vim:ai et  sw=2 ts=2 sts=2


###
# Kinda script that will be called via a cron task
###

# Pretty print log messages: e.g.: 2020-06-28 21:22:50     No file to process. 
log_msg () {
  echo -e "$(date +"%Y-%m-%d %T")\t$1"
}

XYZ_FILEPATH="$CECIHOME/ORCA/*.xyz"

# if no file to process; early exit
if [ $(ls $XYZ_FILEPATH 2>/dev/null | wc -l) -eq 0 ]; then
  log_msg "INFO - No file to process."
  exit
else
  file_list=$(ls $XYZ_FILEPATH 2>/dev/null)
  SSH_OPTS="-o PasswordAuthentication=no -o ConnectTimeout=10 -o ConnectionAttempts=3"
  # Verify that the required ssh key is loaded in ssh-agent key-ring || exit
  if [ $(ssh-add -l 2>/dev/null | grep hydra | wc -l) -eq 0 ]; then
    log_msg "ERROR - SSH Key not loaded. Please add your Hydra ssh key to the key-ring using ssh-add command (or the ssh-agent is not reachable from this environment)." && exit 1       # + Notif mail
  fi

  # Verify hydra:~/Pipeline exists || create it
  ssh -q $SSH_OPTS hydra "mkdir -p ~/Pipeline" || (log_msg "ERROR - Verification of the hydra:~/Pipeline existance (or creation) failed. Command returned err_code: $?." && exit 1)     # + Notif mail

  # Sync CECIHOME/Pipeline/ -> hydra:~/Pipeline/
  rsync -q -a --delete $CECIHOME/Pipeline/ hydra:~/Pipeline || (log_msg "ERROR - Something wrong happened in Pipeline sync from Vega:CECIHOME to Hydra. Command returned err_code: $?." && exit 1)    # + Notif mail

  # Send CECIHOME/ORCA/*.xyz to hydra:~/Q-CHEM/qchem_queue
  #scp -q $CECIHOME/ORCA/*.xyz hydra:~/Q-CHEM/qchem_queue
  rsync -q -a --remove-source-files $CECIHOME/ORCA/*.xyz hydra:~/Q-CHEM/qchem_queue
  rsync -q -a --remove-source-files $CECIHOME/ORCA/*.yml hydra:~/Q-CHEM/qchem_queue
  #log_msg "DEBUG - It will move .xyz files to ORCA/sent instead of removing it from ORCA/"
  #rsync -q -a $CECIHOME/ORCA/*.xyz hydra:~/Q-CHEM/qchem_queue
  #mkdir -p $CECIHOME/ORCA/sent ; mv $CECIHOME/ORCA/*.xyz $CECIHOME/ORCA/sent/
 

  # Launch abin_launcher.py on Hydra
#  SSH_CMD="source ~/Pipeline/load_modules.sh && python abin_launcher.py -p qchem -i ~/Q-CHEM/qchem_queue/ -w ~/Q-CHEM/"
#  ssh -q $SSH_OPTS hydra $SSH_CMD || (log_msg "ERROR - Something wrong happened by trying to launch abin_launcher.py remotely. Command returned err_code: $?." && exit 1)     # + Notif mail

  log_msg "INFO - Successfully processed:\n$file_list"
fi