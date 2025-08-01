import os
import re
import time
from datetime import datetime


def sort_performer(lst_use: dict, lst_app: list):
  if lst_app is None:
    lst_app = []
  for p in lst_use:
    lst_use[p].sort()
  for p in lst_use.values():
    for n in p:
      if n not in lst_app:
        lst_app.append(n)
  return lst_app


def sort_rating(d: dict):
  new_d = {}
  for i in sorted(d.keys(), reverse=True):
    new_d[i] = d[i]
  return new_d


class SceneInformation:
  """A simple example class"""

  scene = None
  scene_information = None
  config = None
  log = None
  stash = None

  path = None
  audio_codec = None
  bit_rate = None
  checksum = None
  date_format = None
  directory = None
  directory_split = None
  extension = None
  filename = None
  id = None
  movie_index = None
  movie_scene = None
  movie_title = None
  movie_year = None
  oshash = None
  parent_studio = None
  performer = None
  performer_path = None
  rating = None
  stashid_performer = None
  studio = None
  studio_code = None
  studio_family = None
  studio_hierarchy = None
  tags = None
  template_split = None
  title = None
  video_codec = None
  year = None

  def __init__(self, log, config, stash, scene: dict):
    self.config = config
    self.log = log
    self.stash = stash

    self.scene = scene
    self.path = str(scene.get("path"))
    self.checksum = scene.get("checksum")
    self.directory = os.path.dirname(self.path)
    self.directory_split = os.path.normpath(self.path).split(os.sep)
    self.extension = os.path.splitext(self.path)[1]
    self.filename = os.path.basename(self.path)
    self.oshash = scene.get("oshash")
    self.studio_code = scene.get("code")

    self.scene_information = dict()

  def extract_info(self, template: dict):
    self.log.debug("Extracting information from scene: {}".format(self.scene))

    if len(self.scene["files"]) > 1:
      self.log.warning(f"Scene has {len(self.scene["files"])} files. Only the first one will be used.")

    scene_path = str(self.scene.get("path"))
    scene_audio_codec = self.scene["file"]["audio_codec"].upper()
    scene_checksum = self.scene.get("checksum")
    scene_date_format = None
    scene_directory = os.path.dirname(scene_path)
    scene_directory_split = os.path.normpath(scene_path).split(os.sep)
    scene_extension = os.path.splitext(scene_path)[1]
    scene_filename = os.path.basename(scene_path)
    scene_id = None
    scene_movie_index = None
    scene_movie_scene = None
    scene_movie_title = None
    scene_movie_year = None
    scene_oshash = self.scene.get("oshash")
    scene_parent_studio = None
    scene_performer = None
    scene_performer_path = None
    scene_rating = None
    scene_stashid_performer = None
    scene_studio = None
    scene_studio_code = self.scene.get("code")
    scene_studio_family = None
    scene_studio_hierarchy = None
    scene_tags = None
    scene_template_split = None
    scene_title = None
    scene_video_codec = self.scene["file"]["video_codec"].upper()
    scene_year = None
    scene_bit_rate = str(round(int(self.scene["file"]["bit_rate"]) / 1000000, 2))

    if self.scene.get("stash_ids"):
      # TODO: support other db then sqlite?
      scene_id = self.scene["stash_ids"][0]["stash_id"]
      self.id = self.scene["stash_ids"][0]["stash_id"]

    if template.get("path"):
      if "^*" in template["path"]["destination"]:
        template["path"]["destination"] = template["path"]["destination"].replace(
          "^*", scene_directory
        )
      scene_template_split = os.path.normpath(template["path"]["destination"]).split(
        os.sep
      )

    if self.config.filename_as_title and not self.scene.get("title"):
      self.scene["title"] = scene_filename

    # Grab Title (without extension if present)
    if self.scene.get("title"):
      # Removing extension if present in title
      scene_title = re.sub(rf"{scene_extension}$", "", self.scene["title"])
      if self.config.prepositions_removal:
        for word in self.config.prepositions_list:
          scene_title = re.sub(rf"^{word}[\s_-]", "", scene_title)

    # Grab Date
    scene_date = self.scene.get("date")
    if scene_date:
      _date = datetime.strptime(scene_date, r"%Y-%m-%d")
      scene_date_format = datetime.strftime(_date, self.config.date_format)

    # Grab Duration
    scene_duration = self.scene["file"]["duration"]
    if self.config.duration_format:
      scene_duration = time.strftime(
        self.config.duration_format, time.gmtime(scene_duration)
      )
    else:
      scene_duration = str(scene_duration)

    # Grab Rating
    if self.scene.get("rating100"):
      scene_rating = self.config.rating_format.format(self.scene["rating100"])

    # Grab Performer
    if self.scene.get("performers"):
      perf_list = []
      perf_list_stashid = []
      perf_rating = {"0": []}
      perf_favorite = {"yes": [], "no": []}
      for perf in self.scene["performers"]:
        if perf.get("gender"):
          if perf["gender"] in self.config.performer_ignoreGender:
            continue
        elif "UNDEFINED" in self.config.performer_ignoreGender:
          continue
        # path related
        if "name" in perf:
          perf_name = perf["name"]
          if template.get("path"):
            if "inverse_performer" in template["path"]["option"]:
              perf_name = re.sub(
                r"([a-zA-Z]+)(\s)([a-zA-Z]+)", r"\3 \1", perf_name
              )
          perf_list.append(perf_name)
          if perf.get("rating100"):
            if perf_rating.get(str(perf["rating100"])) is None:
              perf_rating[str(perf["rating100"])] = []
            perf_rating[str(perf["rating100"])].append(perf_name)
          else:
            perf_rating["0"].append(perf_name)
          if perf.get("favorite"):
            perf_favorite["yes"].append(perf_name)
          else:
            perf_favorite["no"].append(perf_name)
          # if the path already contains the name, we keep this one
          if (
            perf_name in scene_directory_split
            and scene_performer_path is None
            and self.config.path_keep_alrperf
          ):
            scene_performer_path = perf_name
            self.log.debug(
              f"[PATH] Keeping the current name of the performer \"{perf["name"]}\""
            )
      perf_rating = sort_rating(perf_rating)
      # sort performer
      if self.config.performer_sort == "rating":
        # sort alpha
        perf_list = sort_performer(perf_rating, [])
      elif self.config.performer_sort == "favorite":
        perf_list = sort_performer(perf_favorite, [])
      elif self.config.performer_sort == "mix":
        perf_list = []
        for p in perf_favorite:
          perf_favorite[p].sort()
        for p in perf_favorite.get("yes"):
          perf_list.append(p)
        perf_list = sort_performer(perf_rating, perf_list)
      elif self.config.performer_sort == "mixid":
        perf_list = []
        for p in perf_favorite.get("yes"):
          perf_list.append(p)
        for p in perf_rating.values():
          for n in p:
            if n not in perf_list:
              perf_list.append(n)
      elif self.config.performer_sort == "name":
        perf_list.sort()
      if not scene_performer_path and perf_list:
        scene_performer_path = perf_list[0]
      if len(perf_list) > self.config.performer_limit:
        if not self.config.performer_limit_keep:
          self.log.info(
            f"More than {self.config.performer_limit} performer(s). Ignoring $performer"
          )
          perf_list = []
        else:
          self.log.info(f"Limited the amount of performer to {self.config.performer_limit}")
          perf_list = perf_list[0:self.config.performer_limit]
      scene_performer = self.config.performer_split_character.join(perf_list)
      if perf_list:
        for p in perf_list:
          for perf in self.scene["performers"]:
            # TODO: support other db then sqlite?
            if "name" in perf:
              perf_name = perf["name"]
              if p == perf_name and perf.get("stash_ids"):
                perf_list_stashid.append(perf["stash_ids"][0]["stash_id"])
                break
        scene_stashid_performer = self.config.performer_split_character.join(perf_list_stashid)
      if not self.config.path_one_performer:
        scene_performer_path = self.config.performer_split_character.join(perf_list)
    elif self.config.path_no_performer_folder:
      scene_performer_path = "NoPerformer"

    # Grab Studio name
    if self.scene.get("studio"):
      if "name" in self.scene["studio"]:
        studio_name = self.scene["studio"]["name"]
        if self.config.squeeze_studio_names:
          scene_studio = studio_name.replace(" ", "")
        else:
          scene_studio = studio_name
        scene_studio_family = scene_studio
        studio_hierarchy = [scene_studio]
        # Grab Parent name
        if self.scene["studio"].get("parent_studio"):
          if self.config.squeeze_studio_names:
            scene_parent_studio = self.scene["studio"]["parent_studio"][
              "name"
            ].replace(" ", "")
          else:
            scene_parent_studio = self.scene["studio"]["parent_studio"]["name"]
          scene_studio_family = scene_parent_studio

          studio_p = self.scene["studio"]
          while studio_p.get("parent_studio"):
            studio_p = self.stash.find_studio(studio_p["parent_studio"]["id"])
            if studio_p:
              if self.config.squeeze_studio_names:
                studio_hierarchy.append(studio_p["name"].replace(" ", ""))
              else:
                studio_hierarchy.append(studio_p["name"])
          studio_hierarchy.reverse()
        scene_studio_hierarchy = studio_hierarchy
    # Grab Tags
    if self.scene.get("tags"):
      tag_list = []
      for tag in self.scene["tags"]:
        # ignore tag in blacklist
        if tag["name"] in self.config.tags_blacklist:
          continue
        # check if there is a allowlist
        if len(self.config.tags_whitelist) > 0:
          if tag["name"] in self.config.tags_whitelist:
            tag_list.append(tag["name"])
        else:
          tag_list.append(tag["name"])
      scene_tags = self.config.tags_splitchar.join(tag_list)

    scene_resolution = "SD"
    scene_height = f"{self.scene["file"]["height"]}p"
    if self.scene["file"]["height"] >= 720:
      scene_resolution = "HD"
    if self.scene["files"][0]["height"] >= 2160:
      scene_height = "4k"
      scene_resolution = "UHD"
    if self.scene["files"][0]["height"] >= 2880:
      scene_height = "5k"
    if self.scene["files"][0]["height"] >= 3384:
      scene_height = "6k"
    if self.scene["files"][0]["height"] >= 4320:
      scene_height = "8k"
    # For Phone?
    if self.scene["files"][0]["height"] > self.scene["files"][0]["width"]:
      scene_resolution = "VERTICAL"

    if self.scene.get("movies"):
      scene_movie_title = self.scene["movies"][0]["movie"]["name"]
      if self.scene["movies"][0]["movie"].get("date"):
        scene_movie_year = self.scene["movies"][0]["movie"]["date"][0:4]
      if self.scene["movies"][0].get("scene_index"):
        scene_movie_index = self.scene["movies"][0]["scene_index"]
        scene_movie_scene = f"scene {scene_movie_index}"

    if scene_date:
      scene_year = scene_date[0:4]

    # Grabbing things from Stash
    self.scene_information["current_path"] = scene_path
    self.scene_information["audio_codec"] = scene_audio_codec
    self.scene_information["bit_rate"] = scene_bit_rate
    self.scene_information["checksum"] = scene_checksum
    self.scene_information["current_directory"] = scene_directory
    self.scene_information["current_filename"] = scene_filename
    self.scene_information["current_path_split"] = scene_directory_split
    self.scene_information["date"] = scene_date
    self.scene_information["date_format"] = scene_date_format
    self.scene_information["duration"] = scene_duration
    self.scene_information["file_extension"] = scene_extension
    self.scene_information["height"] = scene_height
    self.scene_information["movie_index"] = scene_movie_index
    self.scene_information["movie_scene"] = scene_movie_scene
    self.scene_information["movie_title"] = scene_movie_title
    self.scene_information["movie_year"] = scene_movie_year
    self.scene_information["oshash"] = scene_oshash
    self.scene_information["parent_studio"] = scene_parent_studio
    self.scene_information["performer"] = scene_performer
    self.scene_information["performer_path"] = scene_performer_path
    self.scene_information["rating"] = scene_rating
    self.scene_information["resolution"] = scene_resolution
    self.scene_information["stashid_performer"] = scene_stashid_performer
    self.scene_information["stashid_scene"] = scene_id
    self.scene_information["studio"] = scene_studio
    self.scene_information["studio_code"] = scene_studio_code
    self.scene_information["studio_family"] = scene_studio_family
    self.scene_information["studio_hierarchy"] = scene_studio_hierarchy
    self.scene_information["tags"] = scene_tags
    self.scene_information["template_split"] = scene_template_split
    self.scene_information["title"] = scene_title
    self.scene_information["video_codec"] = scene_video_codec
    self.scene_information["year"] = scene_year

    if self.config.field_whitespaceSeperator:
      for key, value in self.scene_information.items():
        if key in [
          "current_path",
          "current_filename",
          "current_directory",
          "current_path_split",
          "template_split",
        ]:
          continue
        if type(value) is str:
          self.scene_information[key] = value.replace(" ", self.config.field_whitespaceSeperator)
        elif type(value) is list:
          self.scene_information[key] = [
            x.replace(" ", self.config.field_whitespaceSeperator) for x in value
          ]

    return self.scene_information
