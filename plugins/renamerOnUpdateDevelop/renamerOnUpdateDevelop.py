import json
import os
import re
import shutil
import sqlite3
import sys
import time
import traceback
from datetime import datetime

import stashapi.log as log
from stashapi.stashapp import StashInterface

import helpers
import renamerOnUpdateDevelop_config as defaultConfig
from graphql_custom import graphql_getBuild
from plugins.renamerOnUpdateDevelop.config_operations import ConfigOperations
from plugins.renamerOnUpdateDevelop.file_operations import FileOperations
from plugins.renamerOnUpdateDevelop.string_operations import StringOperations

IS_UNIDECODE_AVAILABLE: bool = helpers.is_module_available("unidecode")
IS_CONFIG_AVAILABLE: bool = helpers.is_module_available("config")

if IS_UNIDECODE_AVAILABLE:
    import unidecode  # pip install unidecode

if IS_CONFIG_AVAILABLE:
    import config as config
else:
    config = defaultConfig

DB_VERSION_FILE_REFACTOR = 32
DB_VERSION_SCENE_STUDIO_CODE = 38

DRY_RUN_FILE = None

if config.log_file:
    DRY_RUN_FILE = os.path.join(
        os.path.dirname(config.log_file), "renamerOnUpdateDevelop_dryrun.txt"
    )

if config.dry_run:
    if DRY_RUN_FILE and not config.dry_run_append:
        if os.path.exists(DRY_RUN_FILE):
            os.remove(DRY_RUN_FILE)
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
stringOperations = StringOperations(log, config, stash)
fileOperations = FileOperations(log, config, stash)

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

    def __init__(self, _scene):
        self.scene = _scene
        self.path = str(_scene.get("path"))
        self.checksum = _scene.get("checksum")
        self.directory = os.path.dirname(self.path)
        self.directory_split = os.path.normpath(self.path).split(os.sep)
        self.extension = os.path.splitext(self.path)[1]
        self.filename = os.path.basename(self.path)
        self.oshash = _scene.get("oshash")
        self.studio_code = _scene.get("code")


def extract_info(_scene: dict, template: dict):
    scene_info = SceneInformation(_scene)

    scene_path = str(_scene.get("path"))
    scene_audio_codec = _scene["file"]["audio_codec"].upper()
    scene_checksum = _scene.get("checksum")
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
    scene_oshash = _scene.get("oshash")
    scene_parent_studio = None
    scene_performer = None
    scene_performer_path = None
    scene_rating = None
    scene_stashid_performer = None
    scene_studio = None
    scene_studio_code = _scene.get("code")
    scene_studio_family = None
    scene_studio_hierarchy = None
    scene_tags = None
    scene_template_split = None
    scene_title = None
    scene_video_codec = _scene["file"]["video_codec"].upper()
    scene_year = None
    scene_bit_rate = str(round(int(_scene["file"]["bit_rate"]) / 1000000, 2))

    if _scene.get("stash_ids"):
        # TODO: support other db then stashdb ?
        scene_id = _scene["stash_ids"][0]["stash_id"]
        scene_info.id = _scene["stash_ids"][0]["stash_id"]

    if template.get("path"):
        if "^*" in template["path"]["destination"]:
            template["path"]["destination"] = template["path"]["destination"].replace(
                "^*", scene_directory
            )
        scene_template_split = os.path.normpath(template["path"]["destination"]).split(
            os.sep
        )

    if config.filename_as_title and not _scene.get("title"):
        _scene["title"] = scene_filename

    # Grab Title (without extension if present)
    if _scene.get("title"):
        # Removing extension if present in title
        scene_title = re.sub(rf"{scene_extension}$", "", _scene["title"])
        if config.prepositions_removal:
            for word in PREPOSITIONS_LIST:
                scene_title = re.sub(rf"^{word}[\s_-]", "", scene_title)

    # Grab Date
    scene_date = _scene.get("date")
    if scene_date:
        date_scene = datetime.strptime(scene_date, r"%Y-%m-%d")
        scene_date_format = datetime.strftime(date_scene, config.date_format)

    # Grab Duration
    scene_duration = _scene["file"]["duration"]
    if config.duration_format:
        scene_duration = time.strftime(
            config.duration_format, time.gmtime(scene_duration)
        )
    else:
        scene_duration = str(scene_duration)

    # Grab Rating
    if _scene.get("rating100"):
        scene_rating = RATING_FORMAT.format(_scene["rating100"])

    # Grab Performer
    if _scene.get("performers"):
        perf_list = []
        perf_list_stashid = []
        perf_rating = {"0": []}
        perf_favorite = {"yes": [], "no": []}
        for perf in _scene["performers"]:
            if perf.get("gender"):
                if perf["gender"] in config.performer_ignoreGender:
                    continue
            elif "UNDEFINED" in config.performer_ignoreGender:
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
                # if the path already contains the name we keep this one
                if (
                    perf_name in scene_directory_split
                    and scene_performer_path is None
                    and PATH_KEEP_ALRPERF
                ):
                    scene_performer_path = perf_name
                    log.debug(
                        f"[PATH] Keeping the current name of the performer '{perf['name']}'"
                    )
        perf_rating = sort_rating(perf_rating)
        # sort performer
        if PERFORMER_SORT == "rating":
            # sort alpha
            perf_list = sort_performer(perf_rating, [])
        elif PERFORMER_SORT == "favorite":
            perf_list = sort_performer(perf_favorite, [])
        elif PERFORMER_SORT == "mix":
            perf_list = []
            for p in perf_favorite:
                perf_favorite[p].sort()
            for p in perf_favorite.get("yes"):
                perf_list.append(p)
            perf_list = sort_performer(perf_rating, perf_list)
        elif PERFORMER_SORT == "mixid":
            perf_list = []
            for p in perf_favorite.get("yes"):
                perf_list.append(p)
            for p in perf_rating.values():
                for n in p:
                    if n not in perf_list:
                        perf_list.append(n)
        elif PERFORMER_SORT == "name":
            perf_list.sort()
        if not scene_performer_path and perf_list:
            scene_performer_path = perf_list[0]
        if len(perf_list) > PERFORMER_LIMIT:
            if not PERFORMER_LIMIT_KEEP:
                log.info(
                    f"More than {PERFORMER_LIMIT} performer(s). Ignoring $performer"
                )
                perf_list = []
            else:
                log.info(f"Limited the amount of performer to {PERFORMER_LIMIT}")
                perf_list = perf_list[0:PERFORMER_LIMIT]
        scene_performer = PERFORMER_SPLITCHAR.join(perf_list)
        if perf_list:
            for p in perf_list:
                for perf in _scene["performers"]:
                    # TODO: support other db then stashdb ?
                    if "name" in perf:
                        perf_name = perf["name"]
                        if p == perf_name and perf.get("stash_ids"):
                            perf_list_stashid.append(perf["stash_ids"][0]["stash_id"])
                            break
            scene_stashid_performer = PERFORMER_SPLITCHAR.join(perf_list_stashid)
        if not config.path_one_performer:
            scene_performer_path = PERFORMER_SPLITCHAR.join(perf_list)
    elif PATH_NOPERFORMER_FOLDER:
        scene_performer_path = "NoPerformer"

    # Grab Studio name
    if _scene.get("studio"):
        if "name" in _scene["studio"]:
            studio_name = _scene["studio"]["name"]
            if config.squeeze_studio_names:
                scene_studio = studio_name.replace(" ", "")
            else:
                scene_studio = studio_name
            scene_studio_family = scene_studio
            studio_hierarchy = [scene_studio]
            # Grab Parent name
            if _scene["studio"].get("parent_studio"):
                if config.squeeze_studio_names:
                    scene_parent_studio = _scene["studio"]["parent_studio"][
                        "name"
                    ].replace(" ", "")
                else:
                    scene_parent_studio = _scene["studio"]["parent_studio"]["name"]
                scene_studio_family = scene_parent_studio

                studio_p = _scene["studio"]
                while studio_p.get("parent_studio"):
                    studio_p = stash.find_studio(studio_p["parent_studio"]["id"])
                    if studio_p:
                        if config.squeeze_studio_names:
                            studio_hierarchy.append(studio_p["name"].replace(" ", ""))
                        else:
                            studio_hierarchy.append(studio_p["name"])
                studio_hierarchy.reverse()
            scene_studio_hierarchy = studio_hierarchy
    # Grab Tags
    if _scene.get("tags"):
        tag_list = []
        for tag in _scene["tags"]:
            # ignore tag in blacklist
            if tag["name"] in TAGS_BLACKLIST:
                continue
            # check if there is a whitelist
            if len(TAGS_WHITELIST) > 0:
                if tag["name"] in TAGS_WHITELIST:
                    tag_list.append(tag["name"])
            else:
                tag_list.append(tag["name"])
        scene_tags = TAGS_SPLITCHAR.join(tag_list)

    scene_resolution = "SD"
    scene_height = f"{_scene['file']['height']}p"
    if _scene["file"]["height"] >= 720:
        scene_resolution = "HD"
    if _scene["file"]["height"] >= 2160:
        scene_height = "4k"
        scene_resolution = "UHD"
    if _scene["file"]["height"] >= 2880:
        scene_height = "5k"
    if _scene["file"]["height"] >= 3384:
        scene_height = "6k"
    if _scene["file"]["height"] >= 4320:
        scene_height = "8k"
    # For Phone ?
    if _scene["file"]["height"] > _scene["file"]["width"]:
        scene_resolution = "VERTICAL"

    if _scene.get("movies"):
        scene_movie_title = _scene["movies"][0]["movie"]["name"]
        if _scene["movies"][0]["movie"].get("date"):
            scene_movie_year = _scene["movies"][0]["movie"]["date"][0:4]
        if _scene["movies"][0].get("scene_index"):
            scene_movie_index = _scene["movies"][0]["scene_index"]
            scene_movie_scene = f"scene {scene_movie_index}"

    if scene_date:
        scene_year = scene_date[0:4]

    # Grabbing things from Stash
    scene_information = dict()

    scene_information["current_path"] = scene_path
    scene_information["audio_codec"] = scene_audio_codec
    scene_information["bit_rate"] = scene_bit_rate
    scene_information["checksum"] = scene_checksum
    scene_information["current_directory"] = scene_directory
    scene_information["current_filename"] = scene_filename
    scene_information["current_path_split"] = scene_directory_split
    scene_information["date"] = scene_date
    scene_information["date_format"] = scene_date_format
    scene_information["duration"] = scene_duration
    scene_information["file_extension"] = scene_extension
    scene_information["height"] = scene_height
    scene_information["movie_index"] = scene_movie_index
    scene_information["movie_scene"] = scene_movie_scene
    scene_information["movie_title"] = scene_movie_title
    scene_information["movie_year"] = scene_movie_year
    scene_information["oshash"] = scene_oshash
    scene_information["parent_studio"] = scene_parent_studio
    scene_information["performer"] = scene_performer
    scene_information["performer_path"] = scene_performer_path
    scene_information["rating"] = scene_rating
    scene_information["resolution"] = scene_resolution
    scene_information["stashid_performer"] = scene_stashid_performer
    scene_information["stashid_scene"] = scene_id
    scene_information["studio"] = scene_studio
    scene_information["studio_code"] = scene_studio_code
    scene_information["studio_family"] = scene_studio_family
    scene_information["studio_hierarchy"] = scene_studio_hierarchy
    scene_information["tags"] = scene_tags
    scene_information["template_split"] = scene_template_split
    scene_information["title"] = scene_title
    scene_information["video_codec"] = scene_video_codec
    scene_information["year"] = scene_year

    if FIELD_WHITESPACE_SEP:
        for key, value in scene_information.items():
            if key in [
                "current_path",
                "current_filename",
                "current_directory",
                "current_path_split",
                "template_split",
            ]:
                continue
            if type(value) is str:
                scene_information[key] = value.replace(" ", FIELD_WHITESPACE_SEP)
            elif type(value) is list:
                scene_information[key] = [
                    x.replace(" ", FIELD_WHITESPACE_SEP) for x in value
                ]

    return scene_information


def replace_text(text: str):
    tmp = ""
    for old, new in config.replace_words.items():
        if type(new) is str:
            new = [new]
        if len(new) > 1:
            if new[1] == "regex":
                tmp = re.sub(old, new[0], text)
                if tmp != text:
                    log.debug(f"Regex matched: {text} -> {tmp}")
            else:
                if new[1] == "word":
                    tmp = re.sub(rf"([\s_-])({old})([\s_-])", f"\\1{new[0]}\\3", text)
                elif new[1] == "any":
                    tmp = text.replace(old, new[0])
                if tmp != text:
                    log.debug(f"'{old}' changed with '{new[0]}'")
        else:
            tmp = re.sub(rf"([\s_-])({old})([\s_-])", f"\\1{new[0]}\\3", text)
            if tmp != text:
                log.debug(f"'{old}' changed with '{new[0]}'")
        text = tmp
    return tmp


def cleanup_text(text: str):
    text = re.sub(r"\(\W*\)|\[\W*]|{[^a-zA-Z0-9]*}", "", text)
    text = re.sub(r"[{}]", "", text)
    text = remove_consecutive_nonword(text)
    return text.strip(" -_.")


def remove_consecutive_nonword(text: str):
    for _ in range(0, 10):
        m = re.findall(r"(\W+)\1+", text)
        if m:
            text = re.sub(r"(\W+)\1+", r"\1", text)
        else:
            break
    return text


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
        r = replace_text(r)
    if not t:
        r = r.replace("$title", "")
    r = cleanup_text(r)
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
    r = cleanup_text(r)
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
      new_filename = stringOperations.capitalize_words(new_filename)
    # Remove illegal character for Windows
    new_filename = re.sub('[/:"*?<>|]+', "", new_filename)

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
                path_list.append(re.sub('[/:"*?<>|]+', "", p).strip())
        else:
            path_list.append(
              re.sub('[/:"*?<>|]+', "", make_path(scene_info, part)).strip()
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


def checking_duplicate_db(scene_info: dict):
    # find scenes in db with the same path
    _scenes = stash.find_scenes(
        f={"path": {"modifier": "EQUALS", "value": scene_info["final_path"]}},
        filter={"direction": "ASC", "page": 1, "per_page": 40, "sort": "updated_at"},
        get_count=True,
    )
    if _scenes[0] > 0:
        log.error("Duplicate path detected")
        for dupl_row in _scenes[1]:
          log.warning(f"Identical path: [{dupl_row}]")
        return 1  # TODO: is this needed?

    # result type of find_scenes with get_count: (<number>, <list>); <number> is the count of scenes
    _scenes = stash.find_scenes(
        f={"path": {"modifier": "EQUALS", "value": scene_info["new_filename"]}},
        filter={"direction": "ASC", "page": 1, "per_page": 40, "sort": "updated_at"},
        get_count=True,
    )
    if _scenes[0] > 0:
        for dupl_row in _scenes[1]:
            if dupl_row["id"] != scene_info["scene_id"]:
              log.warning(f"Duplicate filename: [{dupl_row}]")


def db_rename(_stash_db: sqlite3.Connection, scene_info):
    cursor = _stash_db.cursor()
    # Database rename
    cursor.execute(
        "UPDATE scenes SET path=? WHERE id=?;",
        [scene_info["final_path"], scene_info["scene_id"]],
    )
    _stash_db.commit()
    # Close DB
    cursor.close()


def db_rename_refactor(_stash_db: sqlite3.Connection, scene_info):
    cursor = _stash_db.cursor()
    # 2022-09-17T11:25:52+02:00
    mod_time = datetime.now().astimezone().isoformat("T", "seconds")

    # get the next id that we should use if needed
    cursor.execute("SELECT MAX(id) from folders")
    new_id = cursor.fetchall()[0][0] + 1

    # get the old folder id
    cursor.execute(
        "SELECT id FROM folders WHERE path=?", [scene_info["current_directory"]]
    )
    old_folder_id = cursor.fetchall()[0][0]

    # check if the folder of file is created in db
    cursor.execute("SELECT id FROM folders WHERE path=?", [scene_info["new_directory"]])
    folder_id = cursor.fetchall()
    if not folder_id:
        _dir = scene_info["new_directory"]
        # reduce the path to find a parent folder
        for _ in range(1, len(scene_info["new_directory"].split(os.sep))):
            _dir = os.path.dirname(_dir)
            cursor.execute("SELECT id FROM folders WHERE path=?", [_dir])
            parent_id = cursor.fetchall()
            if parent_id:
                # create a new row with the new folder with the parent folder find above
                cursor.execute(
                    "INSERT INTO 'main'.'folders'('id', 'path', 'parent_folder_id', 'mod_time', 'created_at', 'updated_at', 'zip_file_id') VALUES (?, ?, ?, ?, ?, ?, ?);",
                    [
                        new_id,
                        scene_info["new_directory"],
                        parent_id[0][0],
                        mod_time,
                        mod_time,
                        mod_time,
                        None,
                    ],
                )
                _stash_db.commit()
                folder_id = new_id
                break
    else:
        folder_id = folder_id[0][0]
    if folder_id:
        cursor.execute(
            "SELECT file_id from scenes_files WHERE scene_id=?",
            [scene_info["scene_id"]],
        )
        file_ids = cursor.fetchall()
        file_id = None
        for f in file_ids:
            # it can have multiple file for a scene
            cursor.execute("SELECT parent_folder_id from files WHERE id=?", [f[0]])
            check_parent = cursor.fetchall()[0][0]
            # if the parent id is the one found above section, we find our file.s
            if check_parent == old_folder_id:
                file_id = f[0]
                break
        if file_id:
            # log.debug(f"UPDATE files SET basename={scene_info['new_filename']}, parent_folder_id={folder_id}, updated_at={mod_time} WHERE id={file_id};")
            cursor.execute(
                "UPDATE files SET basename=?, parent_folder_id=?, updated_at=? WHERE id=?;",
                [scene_info["new_filename"], folder_id, mod_time, file_id],
            )
            cursor.close()
            _stash_db.commit()
        else:
            raise Exception("Failed to find file_id")
    else:
        cursor.close()
        raise Exception(
            f"You need to setup a library with the new location ({scene_info['new_directory']}) and scan at least 1 file"
        )


def file_rename(current_path: str, new_path: str, scene_info: dict):
    # OS Rename
    if not os.path.isfile(current_path):
        log.warning(f"[OS] File doesn't exist in your Disk/Drive ({current_path})")
        return 1
    # moving/renaming
    new_dir = os.path.dirname(new_path)
    current_dir = os.path.dirname(current_path)
    if not os.path.exists(new_dir):
        log.info(f"Creating folder because it don't exist ({new_dir})")
        os.makedirs(new_dir)
    try:
      move_file(current_path, new_path)
    except PermissionError as _error:
        log.error(f"Something prevents renaming the file. {_error}")
        return 1
    # checking if the move/rename work correctly
    if os.path.isfile(new_path):
        log.info(f"[OS] File Renamed! ({current_path} -> {new_path})")
        if LOGFILE:
            try:
                with open(LOGFILE, "a", encoding="utf-8") as f:
                    f.write(
                        f"{scene_info['scene_id']}|{current_path}|{new_path}|{scene_info['oshash']}\n"
                    )
            except Exception as _error:
                move_file(new_path, current_path)
                log.error(
                    f"Restoring the original path, error writing the logfile: {_error}"
                )
                return 1
        if config.remove_emptyfolder:
            with os.scandir(current_dir) as it:
                if not any(it):
                    log.info(f"Removing empty folder ({current_dir})")
                    try:
                        os.rmdir(current_dir)
                    except Exception as _error:
                        log.warning(
                            f"Fail to delete empty folder {current_dir} - {_error}"
                        )
    else:
        # I don't think it's possible.
        log.error(f"[OS] Failed to rename the file ? {new_path}")
        return 1

def move_file(current_location: str, new_location: str):
  if config.copy_file:
    # os.link(current_path, new_path)
    shutil.copytree(current_location, new_location, copy_function=os.link)
  else:
    shutil.move(current_location, new_location)

def associated_rename(scene_info: dict):
    if config.associated_extension:
        for ext in config.associated_extension:
            p = os.path.splitext(scene_info["current_path"])[0] + "." + ext
            p_new = os.path.splitext(scene_info["final_path"])[0] + "." + ext
            if os.path.isfile(p):
                try:
                    move_file(p, p_new)
                except Exception as _error:
                    log.error(
                        f"Something prevents renaming this file '{p}' - err: {_error}"
                    )
                    continue
            if os.path.isfile(p_new):
                log.info(f"[OS] Associate file renamed ({p_new})")
                if LOGFILE:
                    try:
                        with open(LOGFILE, "a", encoding="utf-8") as f:
                            f.write(f"{scene_info['scene_id']}|{p}|{p_new}\n")
                    except Exception as _error:
                        move_file(p_new, p)
                        log.error(
                            f"Restoring the original name, error writing the logfile: {_error}"
                        )


def renamer(scene_id, db_conn=None):
    stash_scene = None
    option_dryrun = False
    if type(scene_id) is dict:
        stash_scene = scene_id
    elif type(scene_id) is int:
        stash_scene = stash.find_scene(scene_id)

    log.debug("renamer(stash_scene_id): {}".format(stash_scene["id"]))

    if (
        config.only_organized
        and not stash_scene["organized"]
        and not PATH_NON_ORGANIZED
    ):
        log.debug(f"[{stash_scene['id']}] Scene ignored (not organized)")
        return

    # connect to the db
    _stash_db = None
    if not db_conn:
        _stash_db = connect_db(STASH_DATABASE)
        if _stash_db is None:
            return
    else:
        _stash_db = db_conn

    # refactor file support
    fingerprint = []
    if stash_scene.get("path"):
        stash_scene["file"]["path"] = stash_scene["path"]
        if stash_scene.get("checksum"):
            fingerprint.append({"type": "md5", "value": stash_scene["checksum"]})
        if stash_scene.get("oshash"):
            fingerprint.append({"type": "oshash", "value": stash_scene["oshash"]})
        stash_scene["file"]["fingerprints"] = fingerprint
        scene_files = [stash_scene["file"]]
        del stash_scene["path"]
        del stash_scene["file"]
    elif stash_scene.get("files"):
        scene_files = stash_scene["files"]
        del stash_scene["files"]
    else:
        scene_files = []
    for i in range(0, len(scene_files)):
        scene_file = scene_files[i]
        # refactor file support
        for f in scene_file["fingerprints"]:
            if f.get("oshash"):
                stash_scene["oshash"] = f["oshash"]
            if f.get("md5"):
                stash_scene["checksum"] = f["md5"]
            if f.get("checksum"):
                stash_scene["checksum"] = f["checksum"]
        stash_scene["path"] = scene_file["path"]
        stash_scene["file"] = scene_file
        if scene_file.get("bit_rate"):
            stash_scene["file"]["bit_rate"] = scene_file["bit_rate"]
        if scene_file.get("frame_rate"):
            stash_scene["file"]["framerate"] = scene_file["frame_rate"]

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
                    option_dryrun = True
        if not template["filename"] and config.use_default_template:
            log.debug("[FILENAME] Using default template")
            template["filename"] = config.default_template

        if not template["filename"] and not template["path"]:
            log.warning(f"[{scene['id']}] No template for this scene.")
            return

        log.debug(f"[{stash_scene['id']}] Template: {template}")
        # `template` prepared

        # Prepare `scene_information`
        scene_information = extract_info(stash_scene, template)

        scene_information["scene_id"] = stash_scene['id']
        scene_information["file_index"] = i

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
            # check length of path
            if IGNORE_PATH_LENGTH or len(scene_information["final_path"]) <= 240:
                break

        if not IGNORE_PATH_LENGTH and helpers.check_long_path(scene_information["final_path"]):
            if (config.dry_run or option_dryrun) and LOGFILE:
                with open(DRY_RUN_FILE, "a", encoding="utf-8") as f:
                    f.write(
                        f"[LENGTH LIMIT] {scene_information['scene_id']}|{scene_information['final_path']}\n"
                    )
            continue

        if scene_information["final_path"] == scene_information["current_path"]:
            log.info(f"Everything is ok. ({scene_information['current_filename']})")
            continue

        if scene_information["current_directory"] != scene_information["new_directory"]:
            log.info("File will be moved to another directory")
            log.debug(f"[OLD path] {scene_information['current_path']}")
            log.debug(f"[NEW path] {scene_information['final_path']}")

        if scene_information["current_filename"] != scene_information["new_filename"]:
            log.info("The filename will be changed")
            if ALT_DIFF_DISPLAY:
              helpers.find_diff_text(
                    scene_information["current_filename"],
                    scene_information["new_filename"],
                )
            else:
                log.debug(f"[OLD filename] {scene_information['current_filename']}")
                log.debug(f"[NEW filename] {scene_information['new_filename']}")

        if (config.dry_run or option_dryrun) and LOGFILE:
            with open(DRY_RUN_FILE, "a", encoding="utf-8") as f:
                f.write(
                    f"{scene_information['scene_id']}|{scene_information['current_path']}|{scene_information['final_path']}\n"
                )
            continue
        # check if there is already a file where the new path is
        _error = checking_duplicate_db(scene_information)
        while _error and scene_information["file_index"] <= len(DUPLICATE_SUFFIX):
            log.debug("Duplicate filename detected, increasing file index")
            scene_information["file_index"] = scene_information["file_index"] + 1
            scene_information["new_filename"] = create_new_filename(
                scene_information, template["filename"]
            )
            scene_information["final_path"] = os.path.join(
                scene_information["new_directory"], scene_information["new_filename"]
            )
            log.debug(f"[NEW filename] {scene_information['new_filename']}")
            log.debug(f"[NEW path] {scene_information['final_path']}")
            _error = checking_duplicate_db(scene_information)
        # abort
        if _error:
            raise Exception("duplicate")
        try:
            # rename the file on your disk
            _error = file_rename(
                scene_information["current_path"],
                scene_information["final_path"],
                scene_information,
            )
            if _error:
                raise Exception("rename")
            # rename file on your db
            try:
                if DB_VERSION >= DB_VERSION_FILE_REFACTOR:
                    db_rename_refactor(_stash_db, scene_information)
                else:
                    db_rename(_stash_db, scene_information)
            except Exception as _error:
                log.error(
                    f"error when trying to update the database ({_error}), revert the move..."
                )
                _error = file_rename(
                    scene_information["final_path"],
                    scene_information["current_path"],
                    scene_information,
                )
                if _error:
                    raise Exception("rename")
                raise Exception("database update")
            if i == 0:
                associated_rename(scene_information)
            if template.get("path"):
                if "clean_tag" in template["path"]["option"]:
                    stash.update_scenes(
                        {
                            "ids": [scene_information["scene_id"]],
                            "tag_ids": {
                                "ids": template["path"]["opt_details"]["clean_tag"],
                                "mode": "REMOVE",
                            },
                        }
                    )
        except Exception as _error:
            log.error(f"Error during database operation ({_error})")
            if not db_conn:
                log.debug("[SQLITE] Database closed")
                _stash_db.close()
            continue
    if not db_conn and _stash_db:
        _stash_db.close()
        log.info("[SQLITE] Database updated and closed!")


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

ALT_DIFF_DISPLAY = config.alt_diff_display

PATH_NOPERFORMER_FOLDER = config.path_noperformer_folder
PATH_KEEP_ALRPERF = config.path_keep_alrperf
PATH_NON_ORGANIZED = config.p_non_organized

if PLUGIN_ARGS:
    if "bulk" in PLUGIN_ARGS:
        scenes = stash.find_scene(config.batch_number_scene, "ASC")
        log.debug(f"Count scenes: {len(scenes['scenes'])}")
        progress = 0
        progress_step = 1 / len(scenes["scenes"])
        stash_db = connect_db(STASH_DATABASE)
        if stash_db is None:
            exit_plugin()
        for scene in scenes["scenes"]:
            log.debug(f"** Checking scene: {scene['title']} - {scene['id']} **")
            try:
                renamer(scene, stash_db)
            except Exception as err:
                log.error(f"main function error: {err}")
            progress += progress_step
            log.progress(progress)
        stash_db.close()
        log.info("[SQLITE] Database closed!")
else:
    try:
        renamer(FRAGMENT_SCENE_ID)
    except Exception as err:
        log.error(f"main function error: {err}")
        traceback.print_exc()

exit_plugin("Successful!")
