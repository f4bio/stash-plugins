import json
import sys

import stashapi.log as log
from stashapi.stashapp import StashInterface

from scene_information import SceneInformation

per_page = 100
skip_tag = "[organizerOnUpdate: Skip]"

# Defaults if nothing has changed in the stash ui
settings = {
    "useStudio": "BBB->/data/xxx/BBB,GGG->/data/xxx/GGG",
    "useTags": "Amateur->/data/xxx/Amateur,Gangbang->/data/xxx/Gangbang"
}

json_input = json.loads(sys.stdin.read())

FRAGMENT_SERVER = json_input["server_connection"]
stash = StashInterface(FRAGMENT_SERVER)
config = stash.get_configuration()["plugins"]
if "organizerOnUpdate" in config:
    settings.update(config["organizerOnUpdate"])
log.info("settings: {} ".format(settings))


def calculate_filename(filename: str):
    _filename = filename.lower()
    _filename = _filename.replace(" ", "_")

    return _filename


def calculate_directory_name(directory: str):
    _directory = directory.lower()
    _directory = _directory.replace(" ", "_")

    return _directory


def strip_ascii(text):
    return "".join(
        char for char
        in text
        if 31 < ord(char) < 127 or char in "\n\r"
    )


def clean_array_elements(arr):
    return [strip_ascii(x) for x in [y.strip() for y in arr]]


def move_scene(ids, destination_directory: str, destination_filename: str):
    log.debug("move_scene()")

    log.debug("ids: {}".format(ids))
    log.debug("destination_filename: {}".format(destination_filename))
    log.debug("destination_directory: {}".format(destination_directory))

    _result = stash.move_files(dict({
        "ids": [
            ids
        ],
        "destination_folder": destination_directory,
        "destination_basename": destination_filename
    }))
    log.debug("move_files result: {}".format(_result))

    return None


def process_single_scene(stash_scene: SceneInformation):
    log.debug("processing single scene {}".format(stash_scene))

    # if the scene has [organizerOnUpdate: Skip] then skip it
    if skip_tag in stash_scene.tags:
        log.info("skipping scene")
        return None

    _new_filename = calculate_filename(stash_scene.filename)
    _new_directory = None

    if settings["useStudio"]:
        log.debug("useStudio()")

        _stash_studio = stash.find_studio(stash_scene.studio)
        log.debug("found studio: {}".format(_stash_studio))

        _studioFolders = clean_array_elements(settings["useStudio"].split(","))
        for _studioFolder in _studioFolders:
            _studio, _folder = _studioFolder.split("->")
            if _studio in _stash_studio["name"]:
                _new_directory = calculate_directory_name(_folder)
                break

    if settings["useTags"]:
        log.debug("useTags()")

        _tagsFolders = clean_array_elements(settings["useTags"].split(","))
        for _tagFolder in _tagsFolders:
            _tag, _folder = _tagFolder.split("->")
            if _tag in stash_scene.tags:
                _new_directory = calculate_directory_name(_folder)
                break

    if _new_filename and _new_directory:
        move_scene(stash_scene.files[0].get("id"), _new_directory, _new_filename)
    else:
        log.info(
            "no changes to scene. filename ('{}') or directory ('{}') not set".format(_new_filename, _new_directory))
        log.info("skipping scene")

    return None


def process_all_scenes():
    log.debug("processing all scenes")
    all_scenes = stash.find_scenes({}, {}, get_count=True)
    log.info("{} scenes to process.".format(all_scenes[0]))

    for scene in all_scenes[1]:
        log.debug("processing scene: {}".format(scene))
        scene_information = SceneInformation(scene)

        process_single_scene(scene_information)

    return None


if "mode" in json_input["args"]:
    log.debug("Plugin Args: {}".format(json_input["args"]))
    if "processScenes" in json_input["args"]["mode"]:
        if "scene_id" in json_input["args"]:
            _stash_scene = stash.find_scene(json_input["args"]["scene_id"])
            _stash_scene_information = SceneInformation(_stash_scene)
            process_single_scene(_stash_scene_information)
        else:
            process_all_scenes()

elif "hookContext" in json_input["args"]:
    scene_id = json_input["args"]["hookContext"]["id"]
    if json_input["args"]["hookContext"]["type"] == "Scene.Update.Post":
        stash.run_plugin_task("organizerOnUpdate", "Process all", args={"scene_id": scene_id})
#        stash_scene = stash.find_scene(id)
#        process_scene(stash_scene)
