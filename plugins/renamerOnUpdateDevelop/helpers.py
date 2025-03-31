import re
import stashapi.log as log
import difflib

def is_module_available(module_name: str) -> bool:
  """
  Checks whether a specified module is available for import.

  Args:
      module_name (str): The name of the module to check.

  Returns:
      bool: True if the module is available, False otherwise.
  """
  try:
    __import__(module_name)
    return True
  except ImportError:
    return False
