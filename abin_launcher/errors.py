#!/usr/bin/env python3

################################################################################################################################################
##                                      Errors and exceptions of Ab Initio Input Builder & Job Launcher                                       ##
##                                                                                                                                            ##
##                            This script contains all the custom exceptions and functions built to handle errors                             ##
##                               of the Ab Initio Input Builder & Job Launcher python script and its subscripts.                              ##
################################################################################################################################################

import os

# ===================================================================
# ===================================================================
# Exception definitions
# ===================================================================
# ===================================================================

class Error(Exception):
    """Base class for exceptions in this module."""
    pass

class AbinError(Error):
    """Exception raised for errors specific to certain instructions in our script.

    Attributes:
        message -- explanation of the error
    """

    def __init__(self, message):
        self.message = message

# ===================================================================
# ===================================================================
# Function definitions
# ===================================================================
# ===================================================================

def check_abspath(path,type="either"):
    """Checks if a path towards a file or folder exists and makes sure it's absolute.

    Parameters
    ----------
    path : str
        The path towards the file or directory you want to test
    type : str (optional)
        The type of element for which you would like to test the path (file, folder or either)
        By default, checks if the path leads to either a file or a folder (type = either)
    
    Returns
    -------
    abspath : str
        Normalized absolutized version of the path
    """

    if type not in ["file","folder","either"]:
      # Not in try/except structure because the full error message will be need in this case
      raise AbinError ("The specified type for which the check_abspath function has been called is not one of 'file', 'folder' or 'either'")

    # For more informations on try/except structures, see https://www.tutorialsteacher.com/python/exception-handling-in-python
    try:
      if not os.path.exists(path):
        raise AbinError ("ERROR: The argument %s does not seem to exist." % path)
      elif type == "file":
        if not os.path.isfile(path):
          raise AbinError ("ERROR: The argument %s is not a file" % path)
      elif type == "folder":
        if not os.path.isdir(path):
          raise AbinError ("ERROR: The argument %s is not a directory" % path)
      elif type == "either":
        if not os.path.isdir(path) and not os.path.isfile(path):
          raise AbinError ("ERROR: The argument %s is neither a file nor a directory" % path)
    except AbinError as error:
      print(error)
      exit(1)

    # If everything went well, get the normalized absolutized version of the path
    abspath = os.path.abspath(path)

    return abspath