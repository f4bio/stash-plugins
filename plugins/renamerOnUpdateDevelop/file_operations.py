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
