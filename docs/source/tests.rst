Tests
=====


.. code-block:: python

   import image
   print("this is my nice thesis !")



.. code-block:: jinja

   ! {{  method  }} {{  basis_set  }} {{  aux_basis_set  }} {{  job_type  }} {{  other  }} xyzfile 
   %maxcore {{  orca_mem_per_cpu  }} {# It is recommended to set this value to 75% of the physical memory available (see https://sites.google.com/site/orcainputlibrary/orca-common-problems) #}
   %pal 
   nprocs {{  job_cores  }}
   end
   * xyz {{  charge  }} {{  multiplicity  }}
   {% for coordinate_line in coordinates -%}
   {{  coordinate_line  }}
   {% endfor -%}
   *



.. code-block:: yaml

   # General information that is not specific to any program in particular.
   general: 
      charge: 0
      multiplicity: 1
      user-email: niacobel@ulb.ac.be
      mail-type: FAIL
   # Benchmarking options
      benchmark: True
      benchmark-folder: $CECIHOME/BENCHMARK



.. code-block:: bash

   #!/bin/bash
   # vim:ai et  sw=2 ts=2 sts=2

   #########################################################################################################
   ###                This script will be called via a cron task to execute benchmark.py                 ###
   #########################################################################################################

   # Command line arguments
   PROGRAM=$1
   export CLUSTER_NAME=$2

   # Define the timestamp
   timestamp=$(date +"%Y%m%d_%H%M%S")

   # Pretty print for log messages
   log_msg () {
   echo -e "$(date +"%Y-%m-%d %T")\t$1"
   }



.. code-block:: shell

   #!/bin/bash
   # vim:ai et  sw=2 ts=2 sts=2

   #########################################################################################################
   ###                This script will be called via a cron task to execute benchmark.py                 ###
   #########################################################################################################

   # Command line arguments
   PROGRAM=$1
   export CLUSTER_NAME=$2

   # Define the timestamp
   timestamp=$(date +"%Y%m%d_%H%M%S")

   # Pretty print for log messages
   log_msg () {
   echo -e "$(date +"%Y-%m-%d %T")\t$1"
   }
