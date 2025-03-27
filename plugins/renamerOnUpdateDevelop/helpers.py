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

def find_diff_text(a: str, b: str):
  addi = minus = stay = ""
  minus_ = addi_ = 0
  for _, s in enumerate(difflib.ndiff(a, b)):
    if s[0] == " ":
      stay += s[-1]
      minus += "*"
      addi += "*"
    elif s[0] == "-":
      minus += s[-1]
      minus_ += 1
    elif s[0] == "+":
      addi += s[-1]
      addi_ += 1
  if minus_ > 20 or addi_ > 20:
    log.debug(f"Diff Checker: +{addi_}; -{minus_};")
    log.debug(f"OLD: {a}")
    log.debug(f"NEW: {b}")
  else:
    log.debug(
      f"Original: {a}\n- Character: {minus}\n+ Character: {addi}\n  Result: {b}"
    )
  return

def check_long_path(path: str):
  # Trying to prevent error with long paths for Win10
  # https://docs.microsoft.com/en-us/windows/win32/fileio/maximum-file-path-limitation?tabs=cmd
  if len(path) > 240:
    log.error(
      f"The path is too long ({len(path)} > 240). You can look at 'order_field'/'ignore_path_length' in config."
    )
    return 1
