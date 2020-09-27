#!/usr/bin/env python3

################################################################################################################################################
##                                                Errors and exceptions of Results Treatments                                                 ##
##                                                                                                                                            ##
##                            This script contains all the custom exceptions and functions built to handle errors                             ##
##                                         of the Results Treatment python script and its subscripts.                                         ##
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

class ResultsError(Error):
    """Exception raised for errors specific to certain instructions in our scripts.

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

def check_abspath(path:str,context:str,type="either",SkipError=False):
    """Checks if a path towards a file or folder exists and makes sure it's absolute.

    Parameters
    ----------
    path : str
        The path towards the file or directory you want to test
    context : str
        Message to show on screen to give more information in case of an exception (e.g. the role of the folder or file that was checked, where the checked path was given, etc.)
    type : str (optional)
        The type of element for which you would like to test the path (file, folder or either)
        By default, checks if the path leads to either a file or a folder (type = either)
    SkipError : bool (optional)
        By default, ResultsError exceptions will be caught and will cause the function to exit the script.
        Specify True to skip the error treatment and simply raise the exception.
    
    Returns
    -------
    abspath : str
        Normalized absolutized version of the path
    """

    # For more informations on try/except structures, see https://www.tutorialsteacher.com/python/exception-handling-in-python
    try:
      if type not in ["file","folder","either"]:
        raise ValueError ("The specified type for which the check_abspath function has been called is not one of 'file', 'folder' or 'either'")
      if not os.path.exists(path):
        raise ResultsError ("ERROR: %s does not seem to exist." % path)
      elif type == "file":
        if not os.path.isfile(path):
          raise ResultsError ("ERROR: %s is not a file" % path)
      elif type == "folder":
        if not os.path.isdir(path):
          raise ResultsError ("ERROR: %s is not a directory" % path)
      elif type == "either":
        if not os.path.isdir(path) and not os.path.isfile(path):
          raise ResultsError ("ERROR: %s is neither a file nor a directory" % path)
    except ResultsError as error:
        print("Something went wrong when checking the path ", path)
        print("Context: ",context)
        if not SkipError:
          print(error)
          exit(1)
        else:
          raise

    # If everything went well, get the normalized absolutized version of the path
    abspath = os.path.abspath(path)

    return abspath