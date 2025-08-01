import json
import os
import re
import sqlite3
import sys
import time
import traceback
from datetime import datetime

import stashapi.log as log
from stashapi.stashapp import StashInterface

import helpers
import renamerOnUpdateDevelop_config as defaultConfig
from config_operations import ConfigOperations
from db_operations import DBOperations
from file_operations import FileOperations
from graphql_custom import graphql_getBuild
from plugins.renamerOnUpdateDevelop.scene_information import SceneInformation
from text_operations import TextOperations

IS_UNIDECODE_AVAILABLE: bool = helpers.is_module_available("unidecode")
IS_CONFIG_AVAILABLE: bool = helpers.is_module_available("config")

if IS_UNIDECODE_AVAILABLE:
  import unidecode  # pip install unidecode
else:
  log.error(
    f"Please install the 'unidecode' module via 'pip install unidecode', '[docker exec stash] apk install py3-unidecode'"
  )
  sys.exit()

if IS_CONFIG_AVAILABLE:
  import config as config
else:
  config = defaultConfig

DB_VERSION_FILE_REFACTOR = 32
DB_VERSION_SCENE_STUDIO_CODE = 38

DRY_RUN_FILE = None

if config.log_file:
  log.info("Logging to file ({})".format(config.log_file))

if config.dry_run:
  log.info("Dry mode on")

START_TIME = time.time()
FRAGMENT = json.loads(sys.stdin.read())

FRAGMENT_SERVER = FRAGMENT["server_connection"]
PLUGIN_DIR = FRAGMENT_SERVER["PluginDir"]
PLUGIN_ARGS = FRAGMENT["args"].get("mode")

stash_scheme = FRAGMENT_SERVER["Scheme"]
stash_domain = FRAGMENT_SERVER["Host"]
stash_port = str(FRAGMENT_SERVER["Port"])
if stash_domain == "0.0.0.0":
  stash_domain = "localhost"
stash = StashInterface(
  {"scheme": stash_scheme, "host": stash_domain, "port": stash_port, "logger": log}
)

configOperations = ConfigOperations(log, config, stash)
textOperations = TextOperations(log)
fileOperations = FileOperations(log, config, stash)
dbOperations = DBOperations(log, config, stash)


def get_template_path(_scene: dict):
  template = {"destination": "", "option": [], "opt_details": {}}
  # Change by Path
  if config.p_path_templates:
    for match, job in config.p_path_templates.items():
      if match in _scene["path"]:
        template["destination"] = job
        break

  # Change by Studio
  if _scene.get("studio") and config.p_studio_templates:
    if "name" in _scene["studio"]:
      studio_name = _scene["studio"]["name"]
      if config.p_studio_templates.get(studio_name):
        template["destination"] = config.p_studio_templates[studio_name]
      # by Parent
      if _scene["studio"].get("parent_studio"):
        if config.p_studio_templates.get(studio_name):
          template["destination"] = config.p_studio_templates[studio_name]

  # Change by Tag
  tags = [x["name"] for x in _scene["tags"]]
  if _scene.get("tags") and config.p_tag_templates:
    for match, job in config.p_tag_templates.items():
      if match in tags:
        template["destination"] = job
        break

  if _scene.get("tags") and config.p_tag_option:
    for tag in _scene["tags"]:
      if config.p_tag_option.get(tag["name"]):
        opt = config.p_tag_option[tag["name"]]
        template.get("option").extend(opt)
        if "clean_tag" in opt:
          if template["opt_details"].get("clean_tag"):
            template["opt_details"]["clean_tag"].append(tag["id"])
          else:
            template["opt_details"] = {"clean_tag": [tag["id"]]}
  if not _scene["organized"] and PATH_NON_ORGANIZED:
    template["destination"] = PATH_NON_ORGANIZED
  return template

def field_replacer(text: str, scene_information: dict):
  field_found = re.findall(r"\$\w+", text)
  result = text
  title = None
  if len(field_found) > 1:
    field_found.sort(key=len, reverse=True)
  for i in range(0, len(field_found)):
    f = field_found[i].replace("$", "").strip("_")

    log.debug("field_replacer(f): {}".format(f))

    # If $performer is before $title, prevent having duplicate text.
    if (
      f == "performer"
      and len(field_found) > i + 1
      and scene_information.get("performer")
    ):

      if (
        field_found[i + 1] == "$title"
        and scene_information.get("title")
        and PREVENT_TITLE_PERF
      ):
        if re.search(
          f"^{scene_information['performer'].lower()}",
          scene_information["title"].lower(),
        ):
          log.debug(
            "Ignoring the performer field because it's already in start of title"
          )
          result = result.replace("$performer", "")
          continue
    replaced_word = scene_information.get(f)
    if not replaced_word:
      replaced_word = ""
    if FIELD_REPLACER.get(f"${f}"):
      replaced_word = replaced_word.replace(
        FIELD_REPLACER[f"${f}"]["replace"], FIELD_REPLACER[f"${f}"]["with"]
      )
    if f == "title":
      title = replaced_word.strip()
      continue
    if replaced_word == "":
      result = result.replace(field_found[i], replaced_word)
    else:
      result = result.replace(f"${f}", replaced_word)
  return result, title


def make_filename(scene_information: dict, query: str) -> str:
  new_filename = str(query)
  r, t = field_replacer(new_filename, scene_information)
  if config.replace_words:
    r = textOperations.replace_text(r, config.replace_words)
  if not t:
    r = r.replace("$title", "")
  r = textOperations.cleanup_text(r)
  if t:
    r = r.replace("$title", t)
  # Replace spaces with splitchar
  r = r.replace(" ", FILENAME_SPLITCHAR)
  return r


def make_path(scene_information: dict, query: str) -> str:
  new_filename = str(query)
  new_filename = new_filename.replace("$performer", "$performer_path")
  r, t = field_replacer(new_filename, scene_information)
  if not t:
    r = r.replace("$title", "")
  r = textOperations.cleanup_text(r)
  if t:
    r = r.replace("$title", t)
  return r


def create_new_filename(scene_info: dict, template: str):
  new_filename = (
    make_filename(scene_info, template)
    + DUPLICATE_SUFFIX[scene_info["file_index"]]
    + scene_info["file_extension"]
  )
  log.debug("create_new_filename(new): {}".format(new_filename))

  if FILENAME_LOWER:
    new_filename = new_filename.lower()
  if FILENAME_TITLECASE:
    new_filename = textOperations.capitalize_words(new_filename)
  # Remove illegal character for Windows
  new_filename = re.sub("[/:\"*?<>|]+", "", new_filename)

  if config.removecharac_Filename:
    new_filename = re.sub(f"[{config.removecharac_Filename}]+", "", new_filename)

  # Trying to remove non-standard character
  if IS_UNIDECODE_AVAILABLE and UNICODE_USE:
    new_filename = unidecode.unidecode(new_filename, errors="preserve")
  else:
    # Using typewriter for Apostrophe
    new_filename = re.sub("[’‘”“]+", "'", new_filename)
  return new_filename


def remove_consecutive(liste: list):
  new_list = []
  for i in range(0, len(liste)):
    if i != 0 and liste[i] == liste[i - 1]:
      continue
    new_list.append(liste[i])
  return new_list


def create_new_path(scene_info: dict, template: dict):
  # Create the new path
  # Split the template path
  path_split = scene_info["template_split"]
  path_list = []
  for part in path_split:
    if ":" in part and path_split[0]:
      path_list.append(part)
    elif part == "$studio_hierarchy":
      if not scene_info.get("studio_hierarchy"):
        continue
      for p in scene_info["studio_hierarchy"]:
        path_list.append(re.sub("[/:\"*?<>|]+", "", p).strip())
    else:
      path_list.append(
        re.sub("[/:\"*?<>|]+", "", make_path(scene_info, part)).strip()
      )
  # Remove blank, empty string
  path_split = [x for x in path_list if x]
  # The first character was a seperator, so put it back.
  if path_list[0] == "":
    path_split.insert(0, "")

  if PREVENT_CONSECUTIVE:
    # remove consecutive (/FolderName/FolderName/video.mp4 -> FolderName/video.mp4
    path_split = remove_consecutive(path_split)

  if "^*" in template["path"]["destination"]:
    if scene_info["current_directory"] != os.sep.join(path_split):
      path_split.pop(len(scene_info["current_directory"]))

  path_edited = os.sep.join(path_split)

  if config.removecharac_Filename:
    path_edited = re.sub(f"[{config.removecharac_Filename}]+", "", path_edited)

  # Using typewriter for Apostrophe
  new_path = re.sub("[’‘”“]+", "'", path_edited)

  return new_path


def connect_db(path: str):
  try:
    sqlite_connection = sqlite3.connect(path, timeout=10)
    log.debug("Python successfully connected to SQLite")
    return sqlite_connection
  except sqlite3.Error as error:
    log.error(f"FATAL SQLITE Error: {error}")
    return None


def has_duplicate(path: str):
  _scenes = stash.find_scenes(
    f={"path": {"modifier": "EQUALS", "value": path}},
    filter={"direction": "ASC", "page": 1, "per_page": 40, "sort": "updated_at"},
    get_count=True,
  )
  if _scenes[0] > 0:
    log.error("Duplicate path detected")
    return True
  return False

def prepare_scene_information(stash_scene):
  # Prepare `template`
  # Tags > Studios > Default
  template = dict()
  template["filename"] = fileOperations.get_template_filename(stash_scene)
  template["path"] = get_template_path(stash_scene)
  if not template["path"].get("destination"):
    if config.p_use_default_template:
      log.debug("[PATH] Using default template")
      template["path"] = {
        "destination": config.p_default_template,
        "option": [],
        "opt_details": {},
      }
    else:
      template["path"] = None
  else:
    if template["path"].get("option"):
      if "dry_run" in template["path"]["option"] and not config.dry_run:
        log.info("Dry-Run on (activate by option)")
  if not template["filename"] and config.use_default_template:
    log.debug("[FILENAME] Using default template")
    template["filename"] = config.default_template

  if not template["filename"] and not template["path"]:
    log.warning(f"[{stash_scene['id']}] No template for this scene.")
    return None

  log.debug(f"[{stash_scene['id']}] Template: {template}")
  # `template` prepared

  # Prepare `scene_information`
  scene_information = SceneInformation(log, config, stash, stash_scene).extract_info(template)
  log.debug(f"[{stash_scene['id']}] Scene information: {scene_information}")
  log.debug(f"[{stash_scene['id']}] Template: {template}")

  scene_information["scene_id"] = stash_scene["id"]

  for removed_field in config.order_field:
    if removed_field:
      if scene_information.get(removed_field.replace("$", "")):
        del scene_information[removed_field.replace("$", "")]
        log.warning(f"removed {removed_field} to reduce the length path")
      else:
        continue
    if template["filename"]:
      scene_information["new_filename"] = create_new_filename(
        scene_information, template["filename"]
      )
    else:
      scene_information["new_filename"] = scene_information[
        "current_filename"
      ]
    if template.get("path"):
      scene_information["new_directory"] = create_new_path(
        scene_information, template
      )
    else:
      scene_information["new_directory"] = scene_information[
        "current_directory"
      ]
    scene_information["final_path"] = os.path.join(
      scene_information["new_directory"], scene_information["new_filename"]
    )
    # check the length of the final path
    if IGNORE_PATH_LENGTH or len(scene_information["final_path"]) <= 240:
      break

  if scene_information["final_path"] == scene_information["current_path"]:
    log.info(f"Nothing to do. ({scene_information['current_filename']})")
    return None

  if scene_information["current_directory"] != scene_information["new_directory"]:
    log.info("File will be moved to another directory")
    log.debug(f"[OLD directory] {scene_information['current_directory']}")
    log.debug(f"[NEW directory] {scene_information['new_directory']}")

  if scene_information["current_filename"] != scene_information["new_filename"]:
    log.info("The filename will be changed")
    log.debug(f"[OLD filename] {scene_information['current_filename']}")
    log.debug(f"[NEW filename] {scene_information['new_filename']}")

  return scene_information


def renamer_ng(scene_id):
  stash_scene = stash.find_scene(id=scene_id)
  scene_information = prepare_scene_information(stash_scene)
  if not scene_information:
    log.error(f"unable to get scene information for scene: {scene_id}")
    return None

  _result = stash.move_files([
    {
      "ids": [
        scene_information["scene_id"]
      ],
      "destination_folder": scene_information["new_directory"],
      "destination_basename": scene_information["new_filename"]
    }
  ])
  if _result:
    log.info(f"Scene (id={scene_id}) moved")
    return _result
  else:
    log.error(f"Error when trying to move scene (id={scene_id})")
    return None


def exit_plugin(msg=None, _error=None):
  if msg is None and _error is None:
    msg = "plugin ended"
  log.debug("Execution time: {}s".format(round(time.time() - START_TIME, 5)))
  output_json = {"output": msg, "error": _error}
  print(json.dumps(output_json))
  sys.exit()


FRAGMENT_HOOK_TYPE = None
FRAGMENT_SCENE_ID = None

if PLUGIN_ARGS:
  log.debug("--Starting Plugin 'Renamer'--")
  if "bulk" not in PLUGIN_ARGS:
    if "enable" in PLUGIN_ARGS:
      log.info("Enable hook")
      success = configOperations.config_edit("enable_hook", True)
    elif "disable" in PLUGIN_ARGS:
      log.info("Disable hook")
      success = configOperations.config_edit("enable_hook", False)
    elif "dryrun" in PLUGIN_ARGS:
      if config.dry_run:
        log.info("Disable dryrun")
        success = configOperations.config_edit("dry_run", False)
      else:
        log.info("Enable dryrun")
        success = configOperations.config_edit("dry_run", True)
    # if not success:
    #     log.error("Script failed to change the value")
    exit_plugin("script finished")
else:
  if not config.enable_hook:
    exit_plugin("Hook disabled")
  log.debug("--Starting Hook 'Renamer'--")
  FRAGMENT_HOOK_TYPE = FRAGMENT["args"]["hookContext"]["type"]
  FRAGMENT_SCENE_ID = FRAGMENT["args"]["hookContext"]["id"]

LOGFILE = config.log_file

# Gallery.Update.Post
# if FRAGMENT_HOOK_TYPE == "Scene.Update.Post":

STASH_CONFIG = stash.get_configuration()
STASH_DATABASE = STASH_CONFIG["general"]["databasePath"]
DB_VERSION = graphql_getBuild(FRAGMENT_SERVER)

# READING CONFIG
ASSOCIATED_EXT = config.associated_extension

FIELD_WHITESPACE_SEP = config.field_whitespaceSeperator
FIELD_REPLACER = config.field_replacer

FILENAME_LOWER = config.lowercase_Filename
FILENAME_TITLECASE = config.titlecase_Filename
FILENAME_SPLITCHAR = config.filename_splitchar

PERFORMER_SPLITCHAR = config.performer_splitchar
PERFORMER_LIMIT = config.performer_limit
PERFORMER_LIMIT_KEEP = config.performer_limit_keep
PERFORMER_SORT = config.performer_sort
PREVENT_TITLE_PERF = config.prevent_title_performer

DUPLICATE_SUFFIX = config.duplicate_suffix

PREPOSITIONS_LIST = config.prepositions_list

RATING_FORMAT = config.rating_format

TAGS_SPLITCHAR = config.tags_splitchar
TAGS_WHITELIST = config.tags_whitelist
TAGS_BLACKLIST = config.tags_blacklist

IGNORE_PATH_LENGTH = config.ignore_path_length

PREVENT_CONSECUTIVE = config.prevent_consecutive
REMOVE_EMPTY_FOLDER = config.remove_emptyfolder

PROCESS_KILL = config.process_kill_attach
UNICODE_USE = config.use_ascii

# ORDER_SHORTFIELD = config.order_field
# TODO: why?
# ORDER_SHORTFIELD.insert(0, None)

PATH_NOPERFORMER_FOLDER = config.path_noperformer_folder
PATH_KEEP_ALRPERF = config.path_keep_alrperf
PATH_NON_ORGANIZED = config.p_non_organized

if PLUGIN_ARGS:
  if "bulk" in PLUGIN_ARGS:
    scenes = stash.find_scene(config.batch_number_scene, "ASC")
    log.debug(f"Count scenes: {len(scenes["scenes"])}")
    progress = 0
    progress_step = 1 / len(scenes["scenes"])
    for scene in scenes["scenes"]:
      log.debug(f"** Checking scene: {scene["title"]} - {scene["id"]} **")
      try:
        renamer_ng(scene)
      except Exception as err:
        log.error(f"main function error: {err}")
      progress += progress_step
      log.progress(progress)
else:
  try:
    renamer_ng(FRAGMENT_SCENE_ID)
  except Exception as err:
    log.error(f"main function error: {err}")
    traceback.print_exc()

exit_plugin("Successful!")
