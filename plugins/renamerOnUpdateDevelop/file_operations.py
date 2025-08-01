import os


class FileOperations:
  """Class with all the file operations"""
  config = None
  log = None
  stash = None

  def __init__(self, log, config, stash):
    self.config = config
    self.log = log
    self.stash = stash

  def get_template_filename(self, scene: dict):
    template = None
    # Change by Studio
    if scene.get("studio") and self.config.studio_templates:
      template_found = False
      current_studio = scene.get("studio")
      if self.config.studio_templates.get(current_studio["name"]):
        template = self.config.studio_templates[current_studio["name"]]
        template_found = True
      # by first Parent found
      while current_studio.get("parent_studio") and not template_found:
        if self.config.studio_templates.get(
          current_studio.get("parent_studio").get("name")
        ):
          template = self.config.studio_templates[
            current_studio["parent_studio"]["name"]
          ]
          template_found = True
        current_studio = self.stash.find_studio(
          current_studio.get("parent_studio")["id"]
        )
        self.log.debug(
          "get_template_filename(current_studio): {}".format(current_studio)
        )

    # Change by Tag
    tags = [x["name"] for x in scene["tags"]]
    if scene.get("tags") and self.config.tag_templates:
      for match, job in self.config.tag_templates.items():
        if match in tags:
          template = job
          break
    return template

  def file_rename(self, current_path: str, new_path: str, scene_info: dict):
    # OS Rename
    if not os.path.isfile(current_path):
      self.log.warning(f"[OS] File doesn't exist in your Disk/Drive ({current_path})")
      return 1
    # moving/renaming
    new_dir = os.path.dirname(new_path)
    current_dir = os.path.dirname(current_path)
    if not os.path.exists(new_dir):
      self.log.info(f"Creating folder because it don't exist ({new_dir})")
      os.makedirs(new_dir)
    try:
      self.move_or_copy_file(current_path, new_path)
    except PermissionError as _error:
      self.log.error(f"Something prevents renaming the file. {_error}")
      return 1
    # checking if the move/rename work correctly
    if os.path.isfile(new_path):
      self.log.info(f"[OS] File Renamed! ({current_path} -> {new_path})")
      if self.config.logfile:
        try:
          with open(self.config.logfile, "a", encoding="utf-8") as f:
            f.write(
              f"{scene_info['scene_id']}|{current_path}|{new_path}|{scene_info['oshash']}\n"
            )
        except Exception as _error:
          self.move_or_copy_file(new_path, current_path)
          self.log.error(
            f"Restoring the original path, error writing the logfile: {_error}"
          )
          return 1
      if self.config.remove_emptyfolder:
        with os.scandir(current_dir) as it:
          if not any(it):
            self.log.info(f"Removing empty folder ({current_dir})")
            try:
              os.rmdir(current_dir)
            except Exception as _error:
              self.log.warning(
                f"Fail to delete empty folder {current_dir} - {_error}"
              )
      return None
    else:
      # I don't think it's possible.
      self.log.error(f"[OS] Failed to rename the file ? {new_path}")
      return 1

  def move_or_copy_file(self, current_location: str, new_location: str):
    if self.config.copy_file:
      self.log.info(f"Copying/Hard-Linking file {current_location} -> {new_location}")
      os.link(current_location, new_location)
      # shutil.copy(current_location, new_location)
    else:
      self.log.info(f"Moving file {current_location} -> {new_location}")
      os.rename(current_location, new_location)
      # shutil.move(current_location, new_location)
