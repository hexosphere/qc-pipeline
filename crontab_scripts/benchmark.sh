#!/bin/bash
# vim:ai et  sw=2 ts=2 sts=2

#########################################################################################################
###                This script will be called via a cron task to execute benchmark.py                 ###
#########################################################################################################

# Command line arguments
PROGRAM = $1
CLUSTER_NAME = $2

# Pretty print for log messages
log_msg () {
  echo -e "$(date +"%Y-%m-%d %T")\t$1"
}

# Define CECIHOME (might not be known by the crontab)
CECIHOME = "/home/ulb/cqp/niacobel/CECIHOME"

# Define the tmp file we want to scan
WATCH_FILE = "${CECIHOME}/BENCHMARK/benchmark_${PROGRAM}_${CLUSTER_NAME}_tmp.csv"

# Define the folder where the tmp file will be archived
ARCHIVE="${CECIHOME}/BENCHMARK/archive"

# Define the folder where the log files will be stored
BENCH_LOGS="${CECIHOME}/BENCHMARK/bench_logs"

# Exit immediately if there's no file to process
if [ ! -f "${WATCH_FILE}" ]; then
  exit

# Otherwise execute benchmark.py
else

  # Archive the original tmp file (it will be renamed by benchmark.py)
  mkdir -p ${ARCHIVE}
  mv ${WATCH_FILE} ${ARCHIVE}/

  # Execute benchmark.py
  mkdir -p ${BENCH_LOGS}
  source ${CECIHOME}/CHAINS/load_modules.sh
  python ${CECIHOME}/CHAINS/abin_launcher/benchmark.py --tmp ${ARCHIVE}/benchmark_${PROGRAM}_${CLUSTER_NAME}_tmp.csv --final benchmark_${PROGRAM}_${CLUSTER_NAME}.csv > ${BENCH_LOGS}/${PROGRAM}_${CLUSTER_NAME}_$(date +"%Y%m%d_%H%M%S").log

  log_msg "INFO - Processed new lines in ${WATCH_FILE}"

fi