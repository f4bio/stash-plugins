import configparser

class ConfigOperations:
  """Class with all the file operations"""
  config = None
  log = None
  stash = None

  def __init__(self, log, config, stash):
    self.config = config
    self.log = log
    self.stash = stash

  def config_edit(self, name: str, state: bool):
    found = 0
    try:
      with open(self.config.__file__, "r", encoding="utf8") as file:
        config_lines = file.readlines()
      with open(self.config.__file__, "w", encoding="utf8") as file_w:
        for line in config_lines:
          if len(line.split("=")) > 1:
            if name == line.split("=")[0].strip():
              file_w.write(f"{name} = {state}\n")
              found += 1
              continue
          file_w.write(line)
    except PermissionError as _err:
      self.log.error(f"You don't have the permission to edit config.py ({_err})")
    return found
