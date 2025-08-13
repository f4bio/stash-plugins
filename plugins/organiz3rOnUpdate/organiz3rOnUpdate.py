import json
import sys

import stashapi.log as log
from stashapi.stashapp import StashInterface

from scene_information import SceneInformation

per_page = 100
skip_tag = "[organiz3rOnUpdate: Skip]"

# Defaults if nothing has changed in the stash ui
settings = {
    "useStudioHierarchy": True,
    "useTags": "Amateur|/data/xxx/Amateur,Gangbang|/data/xxx/Gangbang"
}

json_input = json.loads(sys.stdin.read())

FRAGMENT_SERVER = json_input["server_connection"]
stash = StashInterface(FRAGMENT_SERVER)
config = stash.get_configuration()["plugins"]
if "organiz3rOnUpdate" in config:
    settings.update(config["organiz3rOnUpdate"])
log.info("config: {} ".format(settings))


def calculate_filename(filename: str):
    _filename = filename.lower()

    return _filename


def calculate_directory_name(directory: str):
    _directory = directory.lower()

    return _directory


def move_scene(stash_scene: SceneInformation, destination_directory: str, destination_filename: str):
    log.debug("move_scene(stash_scene={}, destination_directory={}, destination_filename={})".format(stash_scene,
                                                                                                     destination_directory,
                                                                                                     destination_filename))
    log.debug("_new_filename: {}".format(destination_filename))
    log.debug("_new_directory: {}".format(destination_directory))

    _result = stash.move_files(dict({
        "ids": [
            stash_scene.id
        ],
        "destination_folder": destination_directory,
        "destination_basename": destination_filename
    }))
    log.debug("move_files result: {}".format(_result))

    return None


def process_single_scene(stash_scene: SceneInformation):
    log.debug("processing single scene: {}".format(stash_scene))

    # if the scene has [organiz3rOnUpdate: Skip] then skip it
    if skip_tag in stash_scene.tags:
        log.info("skipping scene")
        return None

    _new_filename = calculate_filename(stash_scene.filename)
    _new_directory = "/tmp"

    if settings["useStudioHierarchy"]:
        log.debug("useStudioHierarchy(stash_scene)")

        _studio = stash.find_studio(stash_scene.studio)
        log.debug("found studio: {}".format(_studio))

        _new_directory = calculate_directory_name(stash_scene.studio)

    if settings["useTags"]:
        log.debug("useTags(stash_scene)")

        _tagsFolders = settings["useTags"].split(",")

        for _tagFolder in _tagsFolders:
            _tag, _folder = _tagFolder.split("|")
            if _tag in stash_scene.tags:
                _new_directory = calculate_directory_name(_folder)
                break

    move_scene(stash_scene, _new_directory, _new_filename)

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
    PLUGIN_ARGS = json_input["args"]["mode"]
    log.debug("PLUGIN_ARGS: {}".format(PLUGIN_ARGS))
    if "processScenes" in PLUGIN_ARGS:
        if "scene_id" in json_input["args"]:
            _stash_scene = stash.find_scene(json_input["args"]["scene_id"])
            _stash_scene_information = SceneInformation(_stash_scene)
            process_single_scene(_stash_scene_information)
        else:
            process_all_scenes()

elif "hookContext" in json_input["args"]:
    scene_id = json_input["args"]["hookContext"]["id"]
    if json_input["args"]["hookContext"]["type"] == "Scene.Update.Post":
        stash.run_plugin_task("organiz3rOnUpdate", "Process all", args={"scene_id": scene_id})
#        stash_scene = stash.find_scene(id)
#        process_scene(stash_scene)
